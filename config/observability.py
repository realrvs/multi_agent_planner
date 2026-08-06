import os
from datetime import datetime
from typing import Dict, Any, Optional

class ObservabilityConfig:
    """Конфигурация для систем observability"""
    
    def __init__(self):
        self.enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        self.client = None
        if self.enabled and self.public_key and self.secret_key:
            try:
                from langfuse import Langfuse
                self.client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host
                )
                print("✅ Langfuse инициализирован успешно!")
                
            except Exception as e:
                print(f"⚠️ Ошибка инициализации Langfuse: {e}")
                self.enabled = False
        else:
            if self.enabled:
                print("⚠️ Langfuse включен, но не настроен. Проверьте переменные окружения.")
                self.enabled = False
    
    def create_trace(self, name: str, metadata: dict = None, input_data: dict = None):
        """
        Создает новый trace для трейсинга
        Возвращает trace_id для дальнейшего использования
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            # Создаем trace_id
            trace_id = self.client.create_trace_id()
            print(f"📝 Создан trace_id: {trace_id[:8]}... для {name}")
            
            # Создаем event с правильным trace_context
            self.client.create_event(
                trace_context={"trace_id": trace_id},
                name=name,
                input=input_data or {},
                metadata=metadata or {}
            )
            
            return trace_id
        except Exception as e:
            print(f"⚠️ Ошибка создания trace: {e}")
            return None
    
    def create_span(self, trace_id: str, name: str, input_data: dict = None, 
                    output_data: dict = None, metadata: dict = None):
        """
        Создает span внутри trace
        """
        if not self.enabled or not self.client or not trace_id:
            return None
        
        try:
            # Создаем event для span
            self.client.create_event(
                trace_context={"trace_id": trace_id},
                name=name,
                input=input_data or {},
                output=output_data or {},
                metadata=metadata or {}
            )
            return True
        except Exception as e:
            print(f"⚠️ Ошибка создания span: {e}")
            return None
    
    def flush(self):
        """Принудительно отправляет все данные в Langfuse"""
        if self.enabled and self.client:
            try:
                self.client.flush()
                print("✅ Данные отправлены в Langfuse")
                return True
            except Exception as e:
                print(f"⚠️ Ошибка отправки данных в Langfuse: {e}")
                return False
        return False

observability = ObservabilityConfig()