import pytest
from unittest.mock import MagicMock, patch
from src.tools import ShellTools, FileSystemTools
from src.llm_client import LLMService

# --- ShellTools ---

def test_shell_security_blocks_rm():
    tools = ShellTools()
    result = tools.run_command("rm -rf /")
    assert "Ошибка" in result
    assert "заблокирована" in result.lower()

def test_shell_security_blocks_sudo():
    tools = ShellTools()
    result = tools.run_command("sudo apt update")
    assert "заблокирована" in result.lower() 

def test_shell_allowed_commands():
    """Проверяем, что разрешенные команды проходят (имитация)."""
    with patch("subprocess.run") as mocked_run:
        mocked_run.return_value.returncode = 0
        mocked_run.return_value.stdout = "v1.0.0"
        
        tools = ShellTools()
        result = tools.run_command("pytest --version")
        assert "STDOUT" in result

# --- LLMService ---

def test_llm_json_retry_logic():
    """Проверяем, что клиент делает ретраи, если JSON битый."""
    with patch("openai.resources.chat.completions.Completions.create") as mocked_create:
        # Имитируем: первый раз вернул мусор, второй раз — валидный JSON
        mocked_create.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(content="не json"))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content='{"thought": "ok", "tool": "none"}'))])
        ]
        
        service = LLMService()
        result = service.generate_json([{"role": "user", "content": "test"}], retries=1)
        
        assert result["thought"] == "ok"
        assert mocked_create.call_count == 2

# --- FileSystemTools ---

def test_list_files_excludes_system_folders():
    """Проверяем, что агент не 'видит' лишнего."""
    tools = FileSystemTools()
    result = tools.list_files(".")
    assert "venv" not in result
    assert ".git" not in result
    assert "src" in result
