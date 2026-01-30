import json
import subprocess
from pathlib import Path
from src.logger import log

# Разрешенные команды - белый список
ALLOWED_COMMANDS = {'pytest', 'ls', 'dir', 'python', 'ruff', 'echo', 'git'}

MAX_CHARS = 8000  # ~1000 токенов на вывод

class FileSystemTools:
    @staticmethod
    def list_files(directory: str = ".") -> str:
        """Возвращает список файлов (только на 2 уровня вглубь)."""
        log.info(f"Tool: list_files('{directory}')")
        target_dir = Path(directory)
        
        if not target_dir.exists():
            return f"Ошибка: Директория '{directory}' не существует."

        files = []
        # Ограничиваем обход, чтобы не сканировать venv / системные папки слишком глубоко
        for path in target_dir.rglob("*"):
            # Игнорируем всё, что связано с окружением и гитом 
            # ! Добавить принеобходимости еще ограничения
            if any(part.startswith(".") or part in {"__pycache__", "venv", "env", "node_modules", "dist"} for part in path.parts):
                continue
            
            if path.is_file():
                # Не выводим больше 50 файлов, чтобы не перегружать контекст
                if len(files) > 50:
                    files.append("... (список слишком длинный, уточните директорию)")
                    break
                files.append(str(path))
        
        return json.dumps(files, ensure_ascii=False)

    @staticmethod
    def read_file(path: str) -> str:
        file_path = Path(path)
        if not file_path.exists():
            return f"Ошибка: Файл '{path}' не найден."
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            return f"Ошибка чтения файла: {e}"

    @staticmethod
    def write_file(path: str, content: str) -> str:
        file_path = Path(path)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return f"Файл '{path}' успешно сохранен."
        except Exception as e:
            return f"Ошибка записи файла: {e}"

class ShellTools:
    @staticmethod
    def run_command(command: str) -> str:
        """Выполняет shell-команду с защитой от инъекций."""
        log.info(f"Выполнение команды: {command}")
        
        # Basic Security Rails
        forbidden_patterns = ['rm -rf', 'sudo', 'env', 'os.environ', '>', '/etc/', '.env', '|']
        cmd_lower = command.lower()
        
        if any(p in cmd_lower for p in forbidden_patterns):
            return "Ошибка: Команда заблокирована системой безопасности."

        cmd_base = command.strip().split()[0]
        if cmd_base not in ALLOWED_COMMANDS:
             return f"Ошибка: Утилита '{cmd_base}' не входит в белый список разрешенных."
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=45,
                encoding='utf-8',
                errors='replace'
            )
            
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if len(stdout) > MAX_CHARS:
                stdout = f"... (начало обрезано) ...\n{stdout[-MAX_CHARS:]}"
            
            if len(stderr) > MAX_CHARS:
                stderr = f"... (начало обрезано) ...\n{stderr[-MAX_CHARS:]}"
            
            output = ""
            if stdout:
                output += f"STDOUT:\n{stdout}\n"
            if stderr:
                output += f"STDERR:\n{stderr}\n"
            if not output:
                output = f"Команда выполнена (Код возврата: {result.returncode}), вывод пуст."
                
            return output

        except subprocess.TimeoutExpired:
            return "Ошибка: Превышено время ожидания выполнения команды."
        except Exception as e:
            return f"Ошибка выполнения: {e}"
