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
    OPENAI_BASE_URL: str = "https://api.openai.com/v1" 
    MODEL_NAME: str = "gpt-4o-mini"
    MAX_ITERATIONS: int = 12

    @classmethod
    def load(cls) -> "AppConfig":
        load_dotenv()
        
        repo = os.getenv("REPO_NAME")
        if not repo:
            sys.exit("CRITICAL: REPO_NAME (user/repo) не найден в .env")

        return cls(
            GITHUB_TOKEN=os.getenv("GITHUB_TOKEN", ""),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
            REPO_NAME=repo,
            OPENAI_BASE_URL=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            MODEL_NAME=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            MAX_ITERATIONS=int(os.getenv("MAX_ITERATIONS", 12))
        )

settings = AppConfig.load()
