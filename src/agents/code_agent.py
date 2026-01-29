import argparse
import json
import re
from typing import Dict, Any, Callable

from github import Github
from github import Auth

from src.config import settings
from src.logger import get_logger, configure_logging
from src.llm_client import LLMService
from src.tools import FileSystemTools, ShellTools

log = get_logger(__name__)

class DeveloperAgent:

    SYSTEM_PROMPT = """
    Ты — Senior Python-разработчик. Решай задачи из GitHub Issue в цикле ReAct.

    ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
    1. list_files(directory="."): Посмотреть список файлов.
    2. read_file(path): Прочитать содержимое файла.
    3. write_file(path, content): СОЗДАТЬ или ИЗМЕНИТЬ файл. (Используй для правки кода и создания тестов).
    4. run_shell_command(command): Запустить терминальную команду (например, pytest или ruff).
    5. create_pr(issue_number, commit_message, pr_title, pr_body): Создать Pull Request.

    ВАЖНЫЕ ПРАВИЛА:
    - Чтобы обновить код, используй ТОЛЬКО write_file, перезаписывая файл целиком с твоими правками.
    - Перед созданием PR обязательно создай/обнови тесты в папке tests/ и запусти их через run_shell_command(command="pytest").
    - Если тесты упали — исправляй код, пока они не пройдут.

    ПРАВИЛА:
    1. Если тесты не видят модули, не используй sys.path. У тебя в корне уже есть pytest.ini.
    2. Твоя конечная цель — вызвать инструмент 'create_pr'. Пока ты его не вызвал, задача не выполнена.
    3. Если ты исправил код и тесты прошли — СРАЗУ создавай PR. Не жди.

    Ответ строго JSON:
    {
      "thought": "Твои рассуждения", 
      "tool": "название_инструмента", 
      "args": {"аргумент": "значение"}
    }
    """

    def __init__(self):
        auth = Auth.Token(settings.GITHUB_TOKEN)
        self.gh = Github(auth=auth)
        self.repo = self.gh.get_repo(settings.REPO_NAME)
        self.llm = LLMService()
        self.fs_tools = FileSystemTools()
        self.shell_tools = ShellTools()
        
        # Реестр инструментов
        self.tools: Dict[str, Callable] = {
            "list_files": self.fs_tools.list_files,
            "read_file": self.fs_tools.read_file,
            "write_file": self.fs_tools.write_file,
            "run_shell_command": self.shell_tools.run_command,
            "create_pr": self.create_pr_tool
        }

    def create_pr_tool(self, issue_number: int, commit_message: str, pr_title: str, pr_body: str) -> str:
        """Создает ветку, коммит и PR (или обновляет существующий)."""
        log.info(f"Tool: create_pr для Issue #{issue_number}")
        try:
            issue = self.repo.get_issue(issue_number)
            branch_name = f"feature/issue-{issue_number}"
            
            # 1. Настройка Git для пуша от имени бота
            # Используем токен из настроек для формирования URL
            repo_url = f"https://x-access-token:{settings.GITHUB_TOKEN}@github.com/{settings.REPO_NAME}.git"
            
            cmds = [
                # Настройка юзера (на всякий случай, если в env нет)
                "git config user.name 'AI Agent'",
                "git config user.email 'agent@bot.com'",
                
                # По хорошему нужно знать о ветках
                "git fetch origin",
                
                # Создаем ветку ИЛИ сбрасывает её на текущий commit, если она есть
                f"git checkout -B {branch_name}",
                
                "git add .",
                f'git commit -m "{commit_message}"',
                
                # Push с токеном
                f"git push {repo_url} {branch_name}"
            ]
            
            for cmd in cmds:
                # Скрываем токен в логах, если вдруг что
                log_cmd = cmd.replace(settings.GITHUB_TOKEN, "***") if settings.GITHUB_TOKEN else cmd
                log.info(f"Running: {log_cmd}")
                
                res = self.shell_tools.run_command(cmd)
                
                # Смело игнорируем
                if "nothing to commit" in res:
                    continue
                if "Ошибка" in res or "STDERR" in res:
                     if "Everything up-to-date" not in res and "To https" not in res:
                        return f"Ошибка Git: {res}"

            # 2. Создание или поиск PR
            existing_prs = self.repo.get_pulls(state='open', head=f"{settings.REPO_NAME.split('/')[0]}:{branch_name}")
            if existing_prs.totalCount > 0:
                pr = existing_prs[0]
                pr.create_issue_comment(f"🔄 Агент обновил код: {commit_message}")
                return f"Код обновлен! Ссылка на PR: {pr.html_url}"

            # Если нет открытого PR для этой ветки, создаем новый
            pr = self.repo.create_pull(
                title=pr_title,
                body=f"{pr_body}\n\nCloses #{issue_number}",
                head=branch_name,
                base="main"
            )
            return f"Успешно! Новый PR создан: {pr.html_url}"

        except Exception as e:
            return f"Ошибка GitHub API: {e}"

    def _inject_file_context(self, text: str) -> str:
        """Ищет @filename в тексте и добавляет их контент."""
        matches = re.findall(r'@([\w./\-_]+\.\w+)', text)
        if not matches:
            return ""
        
        context = "\n--- Context Files ---\n"
        for fname in matches:
            content = self.fs_tools.read_file(fname)
            context += f"File: {fname}\n```\n{content}\n```\n"
        return context

    def run(self, issue_number: int):
        log.info(f"Запуск агента по Issue #{issue_number}")
        issue = self.repo.get_issue(issue_number)
        
        initial_context = f"TASK: {issue.title}\nDESCR: {issue.body}\n"
        initial_context += self._inject_file_context(issue.body)
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": initial_context}
        ]

        for i in range(settings.MAX_ITERATIONS):
            log.info(f"--- Iteration {i+1} ---")
            
            response = self.llm.generate_json(messages)
            if not response or "error" in response:
                log.error("Остановка: ошибка LLM.")
                break

            thought = response.get("thought", "...")
            tool_name = response.get("tool")
            tool_args = response.get("args", {})

            log.info(f"мысль: {thought}")
            log.info(f"вызов: {tool_name}({tool_args})")

            if tool_name not in self.tools:
                available = ", ".join(self.tools.keys())
                result = f"Ошибка: Инструмент '{tool_name}' не существует. Используй только: {available}"
            else:
                # Хак для передачи issue_number в PR тулзу, если LLM забыла
                if tool_name == "create_pr" and "issue_number" not in tool_args:
                    tool_args["issue_number"] = issue_number
                
                try:
                    result = self.tools[tool_name](**tool_args)
                except Exception as e:
                    result = f"Tool Exception: {e}"

            messages.append({"role": "assistant", "content": json.dumps(response)})
            messages.append({"role": "user", "content": result})

            if tool_name == "create_pr" and "Успешно" in result:
                log.info("Задача выполнена! :)")
                break

if __name__ == "__main__":
    configure_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-number", type=int, required=True)
    args = parser.parse_args()

    agent = DeveloperAgent()
    agent.run(args.issue_number)
