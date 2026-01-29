import json
import subprocess
import shutil
from pathlib import Path
from typing import List
from src.logger import get_logger

log = get_logger(__name__)

# Белый список команд для безопасности
ALLOWED_COMMANDS = {'pytest', 'ls', 'dir', 'python', 'ruff', 'echo', 'git'}

class FileSystemTools:
    @staticmethod
    def list_files(directory: str = ".") -> str:
        """Возвращает список файлов (исключая скрытые)."""
        log.info(f"Tool: list_files('{directory}')")
        target_dir = Path(directory)
        
        if not target_dir.exists():
            return f"Ошибка: Директория '{directory}' не существует."

        files = []
        for path in target_dir.rglob("*"):
            # Пропускаем скрытые файлы и папки
            if any(part.startswith(".") for part in path.parts):
                continue
            if path.is_file():
                files.append(str(path))
        
        return json.dumps(files)

    @staticmethod
    def read_file(path: str) -> str:
        """Читает файл."""
        log.info(f"Tool: read_file('{path}')")
        file_path = Path(path)
        
        if not file_path.exists():
            return f"Ошибка: Файл '{path}' не найден."
            
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            return f"Ошибка чтения: {e}"

    @staticmethod
    def write_file(path: str, content: str) -> str:
        """Записывает файл (создает директории при необходимости)."""
        log.info(f"Tool: write_file('{path}')")
        file_path = Path(path)
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return f"Файл '{path}' успешно сохранен."
        except Exception as e:
            return f"Ошибка записи: {e}"

class ShellTools:
    @staticmethod
    def run_command(command: str) -> str:
        """Выполняет безопасные shell-команды."""
        log.info(f"Tool: run_command('{command}')")
        
        # Запрещенные паттерны (Базовая защита от инъекций и удаления, чтоб было позопаснее)
        # TODO: Продумать всевозможные защиты
        forbidden_patterns = ['rm -rf', 'sudo', 'env', 'os.environ', '>', '/etc/', '.env']
        
        cmd_lower = command.lower()
        if any(pattern in cmd_lower for pattern in forbidden_patterns):
            return "Ошибка: Команда содержит запрещенные паттерны безопасности."

        cmd_base = command.strip().split()[0]
        if cmd_base not in ALLOWED_COMMANDS:
             return f"Ошибка: Команда '{cmd_base}' запрещена политикой безопасности."
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8'
            )
            output = f"EXIT_CODE: {result.returncode}\nSTDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}"
            return output
        except subprocess.TimeoutExpired:
            return "Ошибка: Превышено время ожидания выполнения (30с)."
        except Exception as e:
            return f"Ошибка выполнения: {e}"
