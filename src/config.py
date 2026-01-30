import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class AppConfig:
    GH_TOKEN: str
    API_KEY: str
    REPO_NAME: str
    BASE_URL: str
    MODEL_NAME: str
    MAX_ITERATIONS: int

    @classmethod
    def load(cls) -> "AppConfig":
        required_vars = ["GH_TOKEN", "API_KEY", "REPO_NAME"]
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            sys.exit(f"CRITICAL: Отсутствуют обязательные переменные окружения: {', '.join(missing)}")

        return cls(
            GH_TOKEN=os.getenv("GH_TOKEN"),
            API_KEY=os.getenv("API_KEY"),
            REPO_NAME=os.getenv("REPO_NAME"),
            BASE_URL=os.getenv("BASE_URL", "https://api.openai.com/v1"),
            MODEL_NAME=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            MAX_ITERATIONS=int(os.getenv("MAX_ITERATIONS", 12))
        )

settings = AppConfig.load()
