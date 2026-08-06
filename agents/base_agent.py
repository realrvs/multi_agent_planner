from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .yandex_adapter import YandexGPT
from config.observability import observability
from config.prompt_db import prompt_db
import time
from datetime import datetime

class BaseAgent(ABC):
    """
    Базовый класс для всех агентов с YandexGPT и observability.
    Использует базу данных для хранения промптов
    """
    
    def __init__(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        prompt_version: Optional[str] = None
    ):
        self.agent_key = self._get_agent_key()
        
        # Получаем промпт из БД
        if prompt_version:
            prompt_data = prompt_db.get_prompt(self.agent_key, prompt_version)
        else:
            # Берем активную версию
            version = prompt_db.get_active_version(self.agent_key)
            prompt_data = prompt_db.get_prompt(self.agent_key, version)
            self.prompt_version = version
        
        # Используем параметры из БД или переданные
        self.temperature = temperature if temperature is not None else prompt_data.get('temperature', 0.3)
        self.max_tokens = max_tokens if max_tokens is not None else prompt_data.get('max_tokens', 2000)
        self.prompt_version = prompt_version or prompt_data.get('version', 'v1')
        
        # Инициализация LLM
        self.llm = YandexGPT(
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        self.agent_name = self.__class__.__name__
        
        # Observability
        self.observability = observability
        self.current_trace_id = None
        
        # Метрики
        self.metrics = {
            "calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_latency": 0.0,
            "errors": 0,
            "prompt_versions": {}
        }
    
    def _get_agent_key(self) -> str:
        """Возвращает ключ агента для доступа к промптам"""
        name = self.__class__.__name__.lower()
        if "research" in name:
            return "research"
        elif "analysis" in name:
            return "analysis"
        elif "execution" in name:
            return "execution"
        return name.replace("agent", "")
    
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основной метод выполнения задачи агентом.
        """
        pass
    
    def _get_formatted_prompt(self, **kwargs) -> str:
        """
        Получает отформатированный промпт из БД с учетом версионирования
        """
        prompt_data = prompt_db.get_prompt(self.agent_key, self.prompt_version)
        template = prompt_data.get('template', '')
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"⚠️ Ошибка форматирования промпта: отсутствует параметр {e}")
            return template
    
    def reload_prompt(self):
        """Перезагружает промпт из БД (для динамических изменений)"""
        prompt_data = prompt_db.get_prompt(self.agent_key, self.prompt_version)
        self.temperature = prompt_data.get('temperature', 0.3)
        self.max_tokens = prompt_data.get('max_tokens', 2000)
        print(f"🔄 Промпт для {self.agent_name} перезагружен из БД")
    
    def start_trace(self, name: str, metadata: dict = None, input_data: dict = None):
        """Начинает новый trace для агента"""
        if self.observability.enabled and self.observability.client:
            self.current_trace_id = self.observability.create_trace(
                name=f"{self.agent_name}_{name}",
                metadata=metadata or {
                    "agent": self.agent_name,
                    "prompt_version": self.prompt_version,
                    "prompt_hash": prompt_db.get_prompt_hash(self.agent_key, self.prompt_version)
                },
                input_data=input_data or {}
            )
    
    def end_trace(self, output_data: dict = None):
        """Завершает текущий trace"""
        if self.current_trace_id:
            try:
                if output_data:
                    self.observability.create_span(
                        trace_id=self.current_trace_id,
                        name=f"{self.agent_name}_result",
                        output_data=output_data,
                        metadata={"status": "completed"}
                    )
            except Exception as e:
                print(f"⚠️ Ошибка завершения trace: {e}")
            finally:
                self.current_trace_id = None
    
    def _track_llm_call(self, prompt: str, response: Any, latency: float):
        """
        Отслеживает вызов LLM.
        """
        self.metrics["calls"] += 1
        token_count = len(response.content) // 4
        self.metrics["total_tokens"] += token_count
        
        # Примерная стоимость
        cost = token_count * 0.0001
        self.metrics["total_cost"] += cost
        
        # Обновляем среднюю задержку
        self.metrics["avg_latency"] = (
            (self.metrics["avg_latency"] * (self.metrics["calls"] - 1) + latency) 
            / self.metrics["calls"]
        )
        
        # Сохраняем информацию о версии промпта
        self.metrics["prompt_versions"][self.agent_key] = self.prompt_version
        
        # Создаем span внутри текущего trace
        if self.observability.enabled and self.current_trace_id:
            try:
                self.observability.create_span(
                    trace_id=self.current_trace_id,
                    name="llm_call",
                    input_data={"prompt": prompt[:500]},
                    output_data={"response": response.content[:500]},
                    metadata={
                        "latency": latency,
                        "tokens": token_count,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "prompt_version": self.prompt_version,
                        "prompt_hash": prompt_db.get_prompt_hash(self.agent_key, self.prompt_version)
                    }
                )
            except Exception as e:
                print(f"⚠️ Ошибка создания span: {e}")
    
    def invoke_with_observability(self, prompt: str) -> Any:
        """
        Вызывает LLM с отслеживанием метрик.
        """
        start_time = time.time()
        
        try:
            response = self.llm.invoke(prompt)
            latency = time.time() - start_time
            
            self._track_llm_call(prompt, response, latency)
            
            return response
            
        except Exception as e:
            self.metrics["errors"] += 1
            raise e
    
    def get_metrics(self) -> Dict[str, Any]:
        """Возвращает собранные метрики"""
        prompt_data = prompt_db.get_prompt(self.agent_key, self.prompt_version)
        return {
            **self.metrics,
            "agent_name": self.agent_name,
            "prompt_version": self.prompt_version,
            "prompt_info": {
                "version": self.prompt_version,
                "description": prompt_data.get('description', ''),
                "temperature": prompt_data.get('temperature', 0.3),
                "max_tokens": prompt_data.get('max_tokens', 2000),
                "hash": prompt_db.get_prompt_hash(self.agent_key, self.prompt_version)
            }
        }
    
    def reset_metrics(self):
        """Сброс метрик"""
        self.metrics = {
            "calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_latency": 0.0,
            "errors": 0,
            "prompt_versions": {}
        }