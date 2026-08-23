import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from config.observability import observability

class WIMSEAudit:
    """
    Модуль для аудита WIMSE-событий в Langfuse.
    Обеспечивает полную отслеживаемость всех действий агентов.
    """
    
    def __init__(self):
        self.session_id = None
        self.user_id = None
        self.trace_id = None
        self.audit_events = []
        self.enabled = observability.enabled
    
    def start_session(self, session_id: str, user_id: str, metadata: Dict[str, Any] = None):
        """
        Начинает новую сессию аудита.
        """
        self.session_id = session_id
        self.user_id = user_id
        
        # Устанавливаем WIMSE-контекст
        wimse_context = {
            "session_id": session_id,
            "user_id": user_id,
            "audit_version": "1.0",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            wimse_context.update(metadata)
        
        # Проверяем, существует ли метод set_wimse_context
        if hasattr(observability, 'set_wimse_context'):
            observability.set_wimse_context(wimse_context)
        else:
            print("⚠️ Observability не имеет метода set_wimse_context, пропускаем")
        
        print(f"📋 Начата сессия аудита: {session_id} (user: {user_id})")
    
    def log_agent_action(self, agent_name: str, action: str, 
                         input_data: Dict[str, Any] = None,
                         output_data: Dict[str, Any] = None,
                         metadata: Dict[str, Any] = None,
                         trace_id: str = None) -> Optional[str]:
        """
        Логирует действие агента с полным контекстом.
        """
        if not self.enabled:
            return None
        
        try:
            current_trace_id = trace_id or self.trace_id
            
            if not current_trace_id:
                # Создаём новый trace если нет активного
                current_trace_id = observability.create_trace(
                    name=f"wimse_audit_{agent_name}_{action}",
                    metadata={
                        "agent_name": agent_name,
                        "action": action,
                        "session_id": self.session_id,
                        "user_id": self.user_id
                    },
                    input_data=input_data
                )
                self.trace_id = current_trace_id
            else:
                # Создаём span внутри существующего trace
                observability.create_span(
                    trace_id=current_trace_id,
                    name=f"wimse_audit_{agent_name}_{action}",
                    input_data=input_data,
                    output_data=output_data,
                    metadata=metadata
                )
            
            # Сохраняем событие в локальный журнал
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": agent_name,
                "action": action,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "trace_id": current_trace_id
            }
            self.audit_events.append(event)
            
            return current_trace_id
            
        except Exception as e:
            print(f"⚠️ Ошибка логирования аудита: {e}")
            return None
    
    def log_policy_check(self, agent_name: str, policy_action: str, 
                         target: str, result: bool, trace_id: str = None) -> bool:
        """
        Логирует проверку политики безопасности.
        """
        if not self.enabled:
            return False
        
        try:
            current_trace_id = trace_id or self.trace_id
            
            if current_trace_id:
                if hasattr(observability, 'create_policy_check_event'):
                    observability.create_policy_check_event(
                        trace_id=current_trace_id,
                        agent_name=agent_name,
                        action=policy_action,
                        target=target,
                        result=result
                    )
                return True
            else:
                # Если нет активного trace, создаём новый для политики
                new_trace_id = observability.create_trace(
                    name=f"wimse_policy_{agent_name}",
                    metadata={
                        "agent_name": agent_name,
                        "action": policy_action,
                        "target": target,
                        "result": result,
                        "session_id": self.session_id,
                        "user_id": self.user_id
                    }
                )
                self.trace_id = new_trace_id
                return True
                
        except Exception as e:
            print(f"⚠️ Ошибка логирования политики: {e}")
            return False
    
    def log_llm_call(self, agent_name: str, prompt: str, response: str,
                     metrics: Dict[str, Any], trace_id: str = None) -> bool:
        """
        Логирует вызов LLM с полными метриками.
        """
        if not self.enabled:
            return False
        
        try:
            current_trace_id = trace_id or self.trace_id
            
            if current_trace_id:
                observability.create_span(
                    trace_id=current_trace_id,
                    name="llm_call",
                    input_data={"prompt": prompt[:500]},
                    output_data={"response": response[:500]},
                    metadata={
                        "agent_name": agent_name,
                        "latency": metrics.get("latency", 0),
                        "tokens": metrics.get("tokens", 0),
                        "cost": metrics.get("cost", 0),
                        "temperature": metrics.get("temperature", 0.3),
                        "max_tokens": metrics.get("max_tokens", 2000),
                        "prompt_version": metrics.get("prompt_version", "unknown"),
                        "session_id": self.session_id,
                        "user_id": self.user_id
                    }
                )
                return True
            else:
                # Создаём новый trace для LLM вызова
                new_trace_id = observability.create_trace(
                    name=f"wimse_llm_{agent_name}",
                    metadata={
                        "agent_name": agent_name,
                        "session_id": self.session_id,
                        "user_id": self.user_id
                    },
                    input_data={"prompt": prompt[:500]}
                )
                self.trace_id = new_trace_id
                return True
                
        except Exception as e:
            print(f"⚠️ Ошибка логирования LLM вызова: {e}")
            return False
    
    def log_delegation(self, from_agent: str, to_agent: str, 
                       wit_token: str, trace_id: str = None) -> bool:
        """
        Логирует делегирование между агентами.
        """
        if not self.enabled:
            return False
        
        try:
            current_trace_id = trace_id or self.trace_id
            
            # Хешируем токен для безопасности
            wit_hash = hashlib.sha256(wit_token.encode()).hexdigest()[:16]
            
            if current_trace_id:
                observability.create_span(
                    trace_id=current_trace_id,
                    name="wimse_delegation",
                    input_data={
                        "from_agent": from_agent,
                        "to_agent": to_agent,
                        "wit_hash": wit_hash,
                        "session_id": self.session_id,
                        "user_id": self.user_id
                    },
                    metadata={"delegation_type": "WIT_transfer"}
                )
                return True
            else:
                # Создаём новый trace для делегирования
                new_trace_id = observability.create_trace(
                    name=f"wimse_delegation_{from_agent}_to_{to_agent}",
                    metadata={
                        "from_agent": from_agent,
                        "to_agent": to_agent,
                        "session_id": self.session_id,
                        "user_id": self.user_id
                    }
                )
                self.trace_id = new_trace_id
                return True
                
        except Exception as e:
            print(f"⚠️ Ошибка логирования делегирования: {e}")
            return False
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку по аудиту текущей сессии.
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "trace_id": self.trace_id,
            "events_count": len(self.audit_events),
            "enabled": self.enabled,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def flush(self):
        """
        Принудительно отправляет все данные в Langfuse.
        """
        if self.enabled:
            return observability.flush()
        return False

# Глобальный экземпляр для использования
wimse_audit = WIMSEAudit()
