from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .yandex_adapter import YandexGPT
from config.observability import observability
from config.prompt_db import prompt_db
from config.identity import AgentIdentity, identity_manager
from config.prompts import prompt_versioning
import time
import os
import hashlib
from datetime import datetime

class BaseAgent(ABC):
    """
    Базовый класс для всех агентов с WIMSE-идентичностью, YandexGPT и observability.
    """
    
    def __init__(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        prompt_version: Optional[str] = None,
        require_llm: bool = True
    ):
        # Определяем имя агента и его роль
        self.agent_name = self.__class__.__name__
        self.agent_key = self._get_agent_key()
        self.role = self._determine_role()
        
        # Создаем WIMSE-идентичность
        self.identity = AgentIdentity(self.agent_name, self.role)
        print(f"🆔 Инициализирована идентичность для {self.agent_name}: {self.identity}")
        
        # Получаем промпт из БД (если есть)
        if prompt_version:
            prompt_data = prompt_db.get_prompt(self.agent_key, prompt_version)
        else:
            version = prompt_db.get_active_version(self.agent_key)
            prompt_data = prompt_db.get_prompt(self.agent_key, version)
            self.prompt_version = version
        
        # Используем параметры из БД или переданные
        self.temperature = temperature if temperature is not None else prompt_data.get('temperature', 0.3)
        self.max_tokens = max_tokens if max_tokens is not None else prompt_data.get('max_tokens', 2000)
        self.prompt_version = prompt_version or prompt_data.get('version', 'v1')
        
        # Загружаем политику безопасности из prompts.py
        self.policy = prompt_versioning.get_policy(self.agent_key)
        print(f"📋 Загружена политика для {self.agent_name}: {self.policy}")
        
        # Инициализация LLM (только если require_llm=True)
        self.llm = None
        if require_llm:
            self.llm = YandexGPT(
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        else:
            print(f"ℹ️ {self.agent_name}: LLM не инициализирован (только email-операции)")
        
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
            "prompt_versions": {},
            "agent_id": self.identity.agent_id,
            "agent_role": self.role,
            "wit_hash": self.identity.wit_hash,
            "attestation_valid": True,
            "policy_checks": {},
            "policy_audit": [],
            "session_id": os.getenv("CURRENT_SESSION_ID", f"session_{int(time.time())}"),
            "user_id": os.getenv("CURRENT_USER_ID", "unknown_user")
        }
        
        # Флаг, что агент был вызван
        self.called = False
        
        # Устанавливаем WIMSE-контекст в observability
        self.observability.set_wimse_context({
            "agent_id": self.identity.agent_id,
            "agent_role": self.role,
            "agent_name": self.agent_name,
            "prompt_version": self.prompt_version,
            "session_id": self.metrics["session_id"],
            "user_id": self.metrics["user_id"]
        })
    
    def _determine_role(self) -> str:
        name = self.__class__.__name__.lower()
        if "research" in name:
            return "researcher"
        elif "analysis" in name:
            return "analyst"
        elif "execution" in name:
            return "executor"
        elif "email" in name:
            return "email_agent"
        return "unknown"
    
    def _get_agent_key(self) -> str:
        name = self.__class__.__name__.lower()
        if "research" in name:
            return "research"
        elif "analysis" in name:
            return "analysis"
        elif "execution" in name:
            return "execution"
        elif "email" in name:
            return "email"
        return name.replace("agent", "")
    
    def get_identity_context(self) -> Dict[str, Any]:
        return self.identity.get_identity_context()
    
    def verify_peer(self, peer_context: Dict[str, Any]) -> bool:
        return self.identity.verify_peer_identity(peer_context)
    
    def verify_incoming_request(self, state: Dict[str, Any]) -> bool:
        self.called = True
        parent_wit = state.get("parent_wit")
        
        if parent_wit:
            try:
                payload = identity_manager.verify_token(parent_wit)
                print(f"✅ {self.agent_name}: запрос от агента {payload.get('agent_id')} (роль: {payload.get('role')})")
                self.metrics["parent_agent_id"] = payload.get("agent_id")
                self.metrics["parent_role"] = payload.get("role")
                return True
            except ValueError as e:
                print(f"❌ {self.agent_name}: ошибка верификации родительского WIT: {e}")
                return False
        else:
            print(f"ℹ️ {self.agent_name}: первый в цепочке (нет родительского WIT)")
            return True
    
    def check_policy(self, action: str, target: str = None) -> bool:
        result = prompt_versioning.check_policy(self.agent_key, action, target)
        check_key = f"{action}_{target}" if target else action
        self.metrics["policy_checks"][check_key] = result
        self.metrics["policy_audit"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "target": target,
            "result": result
        })
        if not result:
            print(f"❌ {self.agent_name}: политика запрещает действие '{action}' с целью '{target}'")
        else:
            print(f"✅ {self.agent_name}: политика разрешает действие '{action}' с целью '{target}'")
        return result
    
    def enforce_policy(self, action: str, target: str = None) -> None:
        if not self.check_policy(action, target):
            raise PermissionError(
                f"Агент {self.agent_name} (роль: {self.role}) не имеет прав на действие '{action}' с целью '{target}'"
            )
    
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def _get_formatted_prompt(self, **kwargs) -> str:
        prompt_data = prompt_db.get_prompt(self.agent_key, self.prompt_version)
        template = prompt_data.get('template', '')
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"⚠️ Ошибка форматирования промпта: отсутствует параметр {e}")
            return template
    
    def reload_prompt(self):
        prompt_data = prompt_db.get_prompt(self.agent_key, self.prompt_version)
        self.temperature = prompt_data.get('temperature', 0.3)
        self.max_tokens = prompt_data.get('max_tokens', 2000)
        self.policy = prompt_versioning.get_policy(self.agent_key)
        print(f"🔄 Промпт и политика для {self.agent_name} перезагружены из БД")
    
    def start_trace(self, name: str, metadata: dict = None, input_data: dict = None):
        if self.observability.enabled and self.observability.client:
            wimse_metadata = {
                "agent": self.agent_name,
                "agent_id": self.identity.agent_id,
                "agent_role": self.role,
                "wit_hash": self.identity.wit_hash,
                "prompt_version": self.prompt_version,
                "prompt_hash": prompt_db.get_prompt_hash(self.agent_key, self.prompt_version),
                "called": self.called,
                "policy": self.policy,
                "session_id": self.metrics["session_id"],
                "user_id": self.metrics["user_id"]
            }
            if metadata:
                wimse_metadata.update(metadata)
            self.current_trace_id = self.observability.create_trace(
                name=f"{self.agent_name}_{name}",
                metadata=wimse_metadata,
                input_data=input_data or {}
            )
    
    def end_trace(self, output_data: dict = None):
        if self.current_trace_id:
            try:
                if output_data:
                    self.observability.create_span(
                        trace_id=self.current_trace_id,
                        name=f"{self.agent_name}_result",
                        output_data=output_data,
                        metadata={"status": "completed", "called": self.called}
                    )
            except Exception as e:
                print(f"⚠️ Ошибка завершения trace: {e}")
            finally:
                self.current_trace_id = None
    
    def _track_llm_call(self, prompt: str, response: Any, latency: float):
        self.metrics["calls"] += 1
        token_count = len(response.content) // 4
        self.metrics["total_tokens"] += token_count
        cost = token_count * 0.0001
        self.metrics["total_cost"] += cost
        self.metrics["avg_latency"] = (
            (self.metrics["avg_latency"] * (self.metrics["calls"] - 1) + latency) 
            / self.metrics["calls"]
        )
        self.metrics["prompt_versions"][self.agent_key] = self.prompt_version
        if self.observability.enabled and self.current_trace_id:
            try:
                wimse_context = {
                    "agent_id": self.identity.agent_id,
                    "agent_role": self.role,
                    "wit_hash": self.identity.wit_hash,
                    "attestation_valid": True,
                    "session_id": self.metrics["session_id"],
                    "user_id": self.metrics["user_id"],
                    "parent_agent_id": self.metrics.get("parent_agent_id", "none"),
                    "called": self.called,
                    "policy_checks": self.metrics["policy_checks"]
                }
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
                        "prompt_hash": prompt_db.get_prompt_hash(self.agent_key, self.prompt_version),
                        "wimse": wimse_context
                    }
                )
            except Exception as e:
                print(f"⚠️ Ошибка создания span: {e}")
    
    def invoke_with_observability(self, prompt: str) -> Any:
        self.enforce_policy("call_llm")
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
        prompt_data = prompt_db.get_prompt(self.agent_key, self.prompt_version)
        return {
            **self.metrics,
            "agent_name": self.agent_name,
            "prompt_version": self.prompt_version,
            "called": self.called,
            "policy": self.policy,
            "prompt_info": {
                "version": self.prompt_version,
                "description": prompt_data.get('description', ''),
                "temperature": prompt_data.get('temperature', 0.3),
                "max_tokens": prompt_data.get('max_tokens', 2000),
                "hash": prompt_db.get_prompt_hash(self.agent_key, self.prompt_version)
            }
        }
    
    def reset_metrics(self):
        self.metrics = {
            "calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_latency": 0.0,
            "errors": 0,
            "prompt_versions": {},
            "policy_checks": {},
            "policy_audit": []
        }
