import logging
from rich.logging import RichHandler

def configure_logging(level: int = logging.INFO):
    """Настраивает глобальное логирование."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True, markup=True, show_path=False),
            logging.FileHandler("agent_run.log", encoding='utf-8')
        ]
    )
    # Подавляем шум сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("git").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
