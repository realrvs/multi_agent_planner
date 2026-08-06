import requests
import json
import os
from typing import List, Dict, Any, Optional

class YandexGPT:
    """
    Адаптер для работы с YandexGPT через REST API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        folder_id: Optional[str] = None,
        model_uri: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        self.api_key = api_key or os.getenv("YANDEX_API_KEY")
        self.folder_id = folder_id or os.getenv("YANDEX_FOLDER_ID")
        self.model_uri = model_uri or os.getenv("YANDEX_MODEL_URI")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key or not self.folder_id:
            raise ValueError(
                "Не указаны YANDEX_API_KEY и YANDEX_FOLDER_ID. "
                "Добавьте их в файл .env"
            )
        
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def invoke(self, prompt: str) -> Any:
        """
        Отправляет запрос к YandexGPT и возвращает ответ.
        Возвращает объект с атрибутом .content для совместимости с LangChain.
        """
        payload = {
            "modelUri": self.model_uri or f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": self.temperature,
                "maxTokens": self.max_tokens
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Извлекаем текст ответа
            if "result" in data and "alternatives" in data["result"]:
                text = data["result"]["alternatives"][0]["message"]["text"]
            else:
                text = "Не удалось получить ответ от YandexGPT"
            
            # Возвращаем объект, совместимый с интерфейсом LangChain
            return type('Response', (), {
                'content': text,
                'text': text
            })()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка при запросе к YandexGPT: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f"\nОтвет сервера: {e.response.text}"
            return type('Response', (), {
                'content': error_msg,
                'text': error_msg
            })()