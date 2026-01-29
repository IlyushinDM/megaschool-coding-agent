import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class AppConfig:
    GITHUB_TOKEN: str
    OPENAI_API_KEY: str
    REPO_NAME: str
    MODEL_NAME: str = "gpt-4o-mini"
    MAX_ITERATIONS: int = 10

    @classmethod
    def load(cls) -> "AppConfig":
        """Загружает и валидирует конфигурацию."""
        github_token = os.getenv("GITHUB_TOKEN")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not github_token:
            sys.exit("CRITICAL: GITHUB_TOKEN не найден в переменных окружения.")
        if not openai_key:
            sys.exit("CRITICAL: OPENAI_API_KEY не найден в переменных окружения.")

        return cls(
            GITHUB_TOKEN=github_token,
            OPENAI_API_KEY=openai_key,
            REPO_NAME=os.getenv("REPO_NAME", "IlyushinDM/megaschool-coding-agent"),
            MODEL_NAME=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            MAX_ITERATIONS=int(os.getenv("MAX_ITERATIONS", 10))
        )

settings = AppConfig.load()
