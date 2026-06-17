from abc import ABC, abstractmethod
from typing import Dict, Any
from .yandex_adapter import YandexGPT
import os

class BaseAgent(ABC):
    """
    Базовый класс для всех агентов с YandexGPT.
    """
    
    def __init__(
        self,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        self.llm = YandexGPT(
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.agent_name = self.__class__.__name__
    
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основной метод выполнения задачи агентом.
        """
        pass
    
    def _get_prompt(self, state: Dict[str, Any]) -> str:
        """
        Формирует промпт для LLM на основе состояния.
        """
        raise NotImplementedError