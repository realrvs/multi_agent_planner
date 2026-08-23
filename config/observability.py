import os
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib
import json

class ObservabilityConfig:
    """Конфигурация для систем observability с WIMSE-поддержкой"""
    
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
        
        # Хранилище для WIMSE-контекста
        self._wimse_context = {}
    
    def set_wimse_context(self, context: Dict[str, Any]):
        """
        Устанавливает WIMSE-контекст для текущей сессии.
        """
        self._wimse_context.update(context)
        print(f"🔐 WIMSE-контекст обновлён: {list(context.keys())}")
    
    def get_wimse_context(self) -> Dict[str, Any]:
        """
        Возвращает текущий WIMSE-контекст.
        """
        return self._wimse_context.copy()
    
    def create_trace(self, name: str, metadata: dict = None, input_data: dict = None):
        """
        Создает новый trace для трейсинга с WIMSE-контекстом
        Возвращает trace_id для дальнейшего использования
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            trace_id = self.client.create_trace_id()
            
            # Добавляем WIMSE-контекст в метаданные
            wimse_metadata = {
                "wimse_version": "1.0",
                "timestamp": datetime.utcnow().isoformat(),
                **self._wimse_context
            }
            
            if metadata:
                wimse_metadata.update(metadata)
            
            self.client.create_event(
                trace_context={"trace_id": trace_id},
                name=name,
                input=input_data or {},
                metadata=wimse_metadata
            )
            
            print(f"📝 Создан trace: {trace_id[:8]}... для {name} (WIMSE-контекст: {len(wimse_metadata)} полей)")
            return trace_id
            
        except Exception as e:
            print(f"⚠️ Ошибка создания trace: {e}")
            return None
    
    def create_span(self, trace_id: str, name: str, input_data: dict = None, 
                    output_data: dict = None, metadata: dict = None):
        """
        Создает span внутри trace с WIMSE-контекстом
        """
        if not self.enabled or not self.client or not trace_id:
            return None
        
        try:
            # Добавляем WIMSE-контекст в span
            wimse_metadata = {
                "span_type": "wimse_audit",
                "timestamp": datetime.utcnow().isoformat(),
                **self._wimse_context
            }
            
            if metadata:
                wimse_metadata.update(metadata)
            
            self.client.create_event(
                trace_context={"trace_id": trace_id},
                name=name,
                input=input_data or {},
                output=output_data or {},
                metadata=wimse_metadata
            )
            return True
        except Exception as e:
            print(f"⚠️ Ошибка создания span: {e}")
            return None
    
    def create_policy_check_event(self, trace_id: str, agent_name: str, 
                                   action: str, target: str, result: bool):
        """
        Создает специальное событие для проверки политик безопасности
        """
        if not self.enabled or not self.client or not trace_id:
            return None
        
        try:
            event_name = f"policy_check_{action}"
            event_data = {
                "agent": agent_name,
                "action": action,
                "target": target,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "wimse_version": "1.0",
                **self._wimse_context
            }
            
            self.client.create_event(
                trace_context={"trace_id": trace_id},
                name=event_name,
                output={"policy_check": event_data},
                metadata={"type": "wimse_policy"}
            )
            
            status = "✅ РАЗРЕШЕНО" if result else "❌ ЗАПРЕЩЕНО"
            print(f"📊 Политика: {agent_name} → {action} → {target}: {status}")
            return True
            
        except Exception as e:
            print(f"⚠️ Ошибка создания policy-check события: {e}")
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
