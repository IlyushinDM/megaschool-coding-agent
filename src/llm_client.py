import json
from typing import List, Dict, Any, Optional
from openai import OpenAI, APIError
from src.config import settings
from src.logger import get_logger

log = get_logger(__name__)

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_json(self, messages: List[Dict[str, str]], retries: int = 2) -> Optional[Dict[str, Any]]:
            for attempt in range(retries + 1):
                try:
                    response = self.client.chat.completions.create(
                        model=settings.MODEL_NAME,
                        messages=messages,
                        response_format={"type": "json_object"}
                    )
                    content = response.choices[0].message.content
                    return json.loads(content)
                except (json.JSONDecodeError, Exception) as e:
                    log.warning(f"Попытка {attempt + 1} не удалась: {e}")
                    if attempt < retries:
                        messages.append({"role": "user", "content": "Твой предыдущий ответ был невалидным JSON. Повтори ответ строго в формате JSON."})
                    else:
                        log.error("Все попытки получить валидный JSON исчерпаны.")
                        return {"error": "Failed to get valid JSON after retries"}
