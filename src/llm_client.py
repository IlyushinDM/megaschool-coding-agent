import json
import httpx
from typing import List, Dict, Any, Optional
from openai import OpenAI, APIError, APITimeoutError
from src.config import settings
from src.logger import log

class LLMService:
    def __init__(self):
        # дл OpenRouter
        headers = {
            "HTTP-Referer": "https://github.com/IlyushinDM/megaschool-coding-agent",
            "X-Title": "SDLC Coding Agent"
        }

        http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers=headers
        )
        
        self.client = OpenAI(
            api_key=settings.API_KEY,
            base_url=settings.BASE_URL,
            http_client=http_client
        )

    def generate_json(self, messages: List[Dict[str, str]], retries: int = 3) -> Optional[Dict[str, Any]]:
        current_messages = messages.copy()
        
        for attempt in range(retries + 1):
            try:
                log.info(f"Запрос к LLM (попытка {attempt+1})...")
                
                response = self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=current_messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    extra_body={
                        "transforms": ["middle-out"] 
                    }
                )
                content = response.choices[0].message.content
                
                if not content:
                    raise ValueError("Получен пустой ответ от LLM")
                
                return json.loads(content)

            except json.JSONDecodeError:
                log.warning(f"Попытка {attempt + 1}: LLM вернула битый JSON.")
                if attempt < retries:
                    current_messages.append({
                        "role": "user", 
                        "content": "Error: Your response is not valid JSON. Fix formatting. Return JSON only."
                    })
            except APITimeoutError:
                log.warning(f"Попытка {attempt + 1}: Таймаут. Пробуем снова...")
            except Exception as e:
                log.error(f"Ошибка LLM: {e}")
                if attempt == retries:
                    return {"error": str(e)}
        
        return {"error": "Failed after retries"}
