import argparse
import json
import re
import subprocess
from typing import Dict, Any, Callable

from github import Github, Auth
from src.config import settings
from src.logger import log, configure_logging
from src.llm_client import LLMService
from src.tools import FileSystemTools, ShellTools

class DeveloperAgent:
    """
    Автономный агент-разработчик, работающий по паттерну ReAct.
    Умеет исследовать код, писать тесты, исправлять баги и создавать PR.
    """

    SYSTEM_PROMPT = """
    Ты — Senior Python Developer. Твоя задача — решить проблему из GitHub Issue.
    Ты работаешь в цикле: Мысль -> Действие -> Наблюдение.

    АЛГОРИТМ ДЕЙСТВИЙ:
    1. Изучи структуру проекта и прочитай содержимое нужных файлов.
    2. ОБЯЗАТЕЛЬНО: Если тесты отсутствуют или не покрывают задачу, создай их (write_file в папку tests/).
    3. Исправь код или реализуй функционал (write_file).
    4. Запусти тесты (run_shell_command "pytest").
    5. Если тесты упали — проанализируй ошибку, исправь код и повтори запуск тестов.
    6. Только когда тесты прошли ("зеленые"), создавай Pull Request (create_pr).

    ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
    - list_files: Просмотр файлов в директории.
    - read_file: Чтение содержимого файла.
    - write_file: Запись или обновление файла. Принимает аргументы {"path": "...", "content": "..."}.
    - run_shell_command: Запуск команд (pytest, ruff).
    - create_pr: Финальное действие. Создает коммит и Pull Request.

    ВАЖНЫЕ ПРАВИЛА:
    - Всегда пиши "thought" (рассуждения) на русском языке.
    - Передавай аргументы инструментов ТОЛЬКО в формате JSON словаря с именованными ключами.
    - Не используй команды git вручную через run_shell_command.
    - Не завершай работу, пока не убедишься, что тесты проходят и PR создан.

    Если инструмент create_pr возвращает ошибку Git, не пытайся использовать git-команды через run_shell_command. Просто опиши проблему.

    СПЕЦИФИКАЦИЯ ИНСТРУМЕНТА CREATE_PR:
    Ты ОБЯЗАН использовать эти ключи в args:
    {
      "issue_number": <число>,
      "commit_message": "строка",
      "pr_title": "строка",
      "pr_body": "строка"
    }

    ЗАПРЕЩЕНО:
    - Использовать ключи "title", "description", "body" в create_pr. Только те, что указаны выше.
    - Использовать git, curl, gh через run_shell_command.

    ФОРМАТ ОТВЕТА (СТРОГИЙ JSON)!!!:
    {
      "thought": "Твои рассуждения на русском", 
      "tool": "название_инструмента", 
      "args": {"аргумент_1": "значение_1"}
    }
    """

    def __init__(self):
        auth = Auth.Token(settings.GITHUB_TOKEN)
        self.gh = Github(auth=auth)
        self.repo = self.gh.get_repo(settings.REPO_NAME)
        self.llm = LLMService()
        self.fs_tools = FileSystemTools()
        self.shell_tools = ShellTools()
        
        # Реестр инструментов для вызова через LLM
        self.tools: Dict[str, Callable] = {
            "list_files": self.fs_tools.list_files,
            "read_file": self.fs_tools.read_file,
            "write_file": self.fs_tools.write_file,
            "run_shell_command": self.shell_tools.run_command,
            "create_pr": self.create_pr_tool
        }

    def create_pr_tool(self, issue_number: int, commit_message: str, pr_title: str, pr_body: str) -> str:
        """Автоматизирует Git flow: checkout -> commit -> push -> PR."""
        log.info(f"Запуск процесса создания PR для задачи #{issue_number}")
        
        try:
            branch_name = f"feature/issue-{issue_number}"
            auth_url = f"https://x-access-token:{settings.GITHUB_TOKEN}@github.com/{settings.REPO_NAME}.git"
            
            # Последовательность команд для подготовки ветки и пуша
            git_commands = [
                'git config user.name "AI Developer Agent"',
                'git config user.email "agent@bot.local"',
                f"git checkout -B {branch_name}",
                "git add .",
                f'git commit -m "{commit_message}"',
                f"git push \"{auth_url}\" {branch_name} --force"
            ]

            for cmd in git_commands:
                # токен в логах прячем 
                safe_log = cmd.replace(settings.GITHUB_TOKEN, "***")
                log.info(f"Выполнение Git: {safe_log}")
                
                # Используем subprocess.run с проверкой ошибок
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, encoding='utf-8'
                )
                
                if result.returncode != 0:
                    if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                        continue
                    return f"Git Error: {result.stderr or result.stdout}"

            pulls = self.repo.get_pulls(state='open', head=f"{settings.REPO_NAME.split('/')[0]}:{branch_name}")
            
            if pulls.totalCount > 0:
                pr = pulls[0]
                pr.create_issue_comment(f"**Обновление:** Агент применил новые правки. Коммит: {commit_message}")
                return f"PR успешно обновлен: {pr.html_url}"
            
            # Создаем новый PR, если нет еще
            pr = self.repo.create_pull(
                title=pr_title,
                body=f"{pr_body}\n\nCloses #{issue_number}",
                head=branch_name,
                base="main"
            )
            return f"Создан новый PR: {pr.html_url}"

        except Exception as e:
            log.exception("Ошибка при создании Pull Request")
            return f"GitHub API Error: {e}"

    def _inject_file_context(self, text: str) -> str:
        """Автоматически считывает файлы, упомянутые через @ в описании."""
        matches = re.findall(r'@([\w./\-_]+\.\w+)', text)
        if not matches:
            return ""
        
        context = "\n--- Содержимое упомянутых файлов ---\n"
        for fname in matches:
            content = self.fs_tools.read_file(fname)
            context += f"Файл: {fname}\n```\n{content}\n```\n"
        return context

    def run(self, issue_number: int):
        log.info(f"Запуск Developer Agent для Issue #{issue_number}")
        
        try:
            issue = self.repo.get_issue(issue_number)
        except Exception as e:
            log.error(f"Не удалось загрузить Issue #{issue_number}: {e}")
            return

        # Даем агенту список файлов сразу, чтобы сэкономить итерации
        project_tree = self.fs_tools.list_files(".")

        initial_message = f"""
        ЗАДАЧА #{issue.number}: {issue.title}
        ОПИСАНИЕ:
        {issue.body}
        
        СТРУКТУРА ПРОЕКТА:
        {project_tree}
        
        {self._inject_file_context(issue.body or "")}
        """

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": initial_message}
        ]

        for i in range(settings.MAX_ITERATIONS):
            log.info(f"\n[bold blue]Итерация {i + 1}/{settings.MAX_ITERATIONS}[/bold blue]")
            
            response_data = self.llm.generate_json(messages)
            
            if not response_data or "error" in response_data:
                log.error("Остановка: получена ошибка от LLM.")
                break

            thought = response_data.get("thought", "...")
            tool_name = response_data.get("tool")
            tool_args = response_data.get("args", {})

            log.info(f"[bold]Мысль:[/bold] {thought}")
            log.info(f"[bold]Инструмент:[/bold] {tool_name} | [dim]Args: {tool_args}[/dim]")

            if tool_name not in self.tools:
                result = f"Ошибка: Инструмент '{tool_name}' не найден. Доступные: {', '.join(self.tools.keys())}"
            else:
                # Внедряем номер issue для инструмента создания PR
                if tool_name == "create_pr":
                    tool_args["issue_number"] = issue_number
                
                try:
                    result = self.tools[tool_name](**tool_args)
                    # Выводим кусочек результата для визуального контроля
                    # 300 500
                    log.info(f"[bold]Наблюдение:[/bold] {str(result)[:150]}...")
                except Exception as e:
                    result = f"Исключение при работе инструмента: {e}"

            messages.append({"role": "assistant", "content": json.dumps(response_data)})
            messages.append({"role": "user", "content": f"Наблюдение: {result}"})

            if tool_name == "create_pr" and "Успешно" in str(result) or "PR" in str(result):
                log.info("Задача выполнена успешно!")
                break
            
            if i == settings.MAX_ITERATIONS - 1:
                log.warning("Исчерпан лимит итераций. PR не был создан.")

if __name__ == "__main__":
    configure_logging()
    parser = argparse.ArgumentParser(description="SDLC Coding Agent")
    parser.add_argument("--issue-number", type=int, required=True, help="Номер GitHub Issue")
    args = parser.parse_args()
    
    agent = DeveloperAgent()
    agent.run(args.issue_number)
