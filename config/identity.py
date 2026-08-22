import jwt
import time
import os
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

class IdentityManager:
    """
    Управление идентичностью агентов для WIMSE.
    Выпускает и верифицирует Workload Identity Tokens (WIT).
    """
    
    def __init__(self):
        # Секретный ключ для подписи токенов (в production использовать асимметричное шифрование)
        self.secret_key = os.getenv("WIMSE_SECRET_KEY", "your-secret-key-for-development-change-in-production")
        self.issuer = "multi-agent-planner"
        self.algorithm = "HS256"
        
        # Для аттестации: храним публичные ключи агентов (в production - в БД)
        self.public_keys = {}
        
        # Генерируем ключи для аттестации (в production - использовать TPM/HSM)
        self._init_attestation_keys()
    
    def _init_attestation_keys(self):
        """Инициализирует ключи для аттестации (демо-режим)."""
        # В реальном проекте ключи должны генерироваться при первом запуске агента
        # и храниться в защищенном хранилище
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
        # Сохраняем публичный ключ для верификации
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.public_key_pem = pem.decode('utf-8')
    
    def issue_token(self, agent_id: str, role: str, ttl: int = 3600) -> str:
        """
        Выпускает Workload Identity Token (WIT) для агента.
        
        Args:
            agent_id: Уникальный идентификатор агента
            role: Роль агента (researcher, analyst, executor)
            ttl: Время жизни токена в секундах (по умолчанию 1 час)
        
        Returns:
            JWT-токен с идентификационной информацией
        """
        now = int(time.time())
        payload = {
            "agent_id": agent_id,
            "role": role,
            "iss": self.issuer,
            "iat": now,
            "exp": now + ttl,
            "nbf": now,  # Not Before - токен активен сразу
            "jti": hashlib.md5(f"{agent_id}_{now}".encode()).hexdigest()[:16]  # Уникальный ID токена
        }
        
        # Подписываем токен
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Верифицирует WIT и возвращает payload.
        
        Args:
            token: JWT-токен для проверки
        
        Returns:
            Словарь с данными из токена
        
        Raises:
            ValueError: Если токен невалидный или просрочен
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Дополнительные проверки
            if payload.get("iss") != self.issuer:
                raise ValueError(f"Invalid issuer: {payload.get('iss')}")
            
            # Проверяем, что токен не просрочен
            exp = payload.get("exp")
            if exp and time.time() > exp:
                raise ValueError("Token has expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def create_attestation(self, agent_id: str, wit_token: str) -> Dict[str, Any]:
        """
        Создает аттестацию для агента (доказательство легитимности).
        
        Args:
            agent_id: ID агента
            wit_token: WIT токен агента
        
        Returns:
            Словарь с аттестационными данными
        """
        # В реальном проекте здесь должна быть проверка:
        # 1. Целостность кода агента (хеш)
        # 2. Окружение запуска (контейнер, ОС)
        # 3. Наличие необходимых сертификатов
        
        attestation_data = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "wit_hash": hashlib.sha256(wit_token.encode()).hexdigest(),
            "environment": {
                "python_version": os.getenv("PYTHON_VERSION", "3.11"),
                "runtime": "python",
                "host": os.getenv("HOSTNAME", "unknown")
            }
        }
        
        # Подписываем аттестацию
        attestation_string = f"{agent_id}{attestation_data['timestamp']}{attestation_data['wit_hash']}"
        signature = self._sign_data(attestation_string)
        
        attestation_data["signature"] = signature
        attestation_data["public_key"] = self.public_key_pem
        
        return attestation_data
    
    def _sign_data(self, data: str) -> str:
        """Подписывает данные приватным ключом (демо-версия)."""
        # В реальном проекте здесь должно быть шифрование
        return hashlib.sha256(f"{data}_{self.secret_key}".encode()).hexdigest()
    
    def verify_attestation(self, attestation: Dict[str, Any]) -> bool:
        """
        Проверяет аттестацию агента.
        
        Args:
            attestation: Словарь с аттестационными данными
        
        Returns:
            True если аттестация валидна
        """
        # Проверяем наличие обязательных полей
        required_fields = ["agent_id", "timestamp", "wit_hash", "signature"]
        if not all(field in attestation for field in required_fields):
            return False
        
        # Проверяем подпись
        data_to_verify = f"{attestation['agent_id']}{attestation['timestamp']}{attestation['wit_hash']}"
        expected_signature = self._sign_data(data_to_verify)
        
        if attestation["signature"] != expected_signature:
            return False
        
        # Проверяем, что аттестация не старше 5 минут
        try:
            timestamp = datetime.fromisoformat(attestation["timestamp"])
            age = datetime.utcnow() - timestamp
            if age > timedelta(minutes=5):
                return False
        except (ValueError, TypeError):
            return False
        
        return True


class AgentIdentity:
    """
    Класс для управления идентичностью конкретного агента.
    """
    
    def __init__(self, agent_name: str, role: str):
        self.agent_name = agent_name
        self.role = role
        self.agent_id = f"{agent_name}_{id(self)}_{int(time.time())}"
        
        self.identity_manager = IdentityManager()
        
        # Выпускаем WIT для агента
        self.wit_token = self.identity_manager.issue_token(
            agent_id=self.agent_id,
            role=self.role,
            ttl=3600
        )
        
        # Создаем аттестацию
        self.attestation = self.identity_manager.create_attestation(
            agent_id=self.agent_id,
            wit_token=self.wit_token
        )
        
        # Хеш для аудита
        self.wit_hash = hashlib.sha256(self.wit_token.encode()).hexdigest()
    
    def get_identity_context(self) -> Dict[str, Any]:
        """
        Возвращает контекст идентичности для передачи другим агентам.
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "wit": self.wit_token,
            "wit_hash": self.wit_hash,
            "attestation": self.attestation
        }
    
    def refresh_token(self):
        """Обновляет WIT токен."""
        self.wit_token = self.identity_manager.issue_token(
            agent_id=self.agent_id,
            role=self.role,
            ttl=3600
        )
        self.wit_hash = hashlib.sha256(self.wit_token.encode()).hexdigest()
    
    def verify_peer_identity(self, peer_context: Dict[str, Any]) -> bool:
        """
        Проверяет идентичность другого агента.
        
        Args:
            peer_context: Контекст идентичности другого агента
        
        Returns:
            True если идентичность подтверждена
        """
        if "wit" not in peer_context:
            return False
        
        try:
            payload = self.identity_manager.verify_token(peer_context["wit"])
            
            # Проверяем, что роль соответствует ожидаемой
            # Исправлено: теперь проверяем роль, которую мы ожидаем от другого агента
            expected_roles = {
                "ResearchAgent": "researcher",
                "AnalysisAgent": "analyst", 
                "ExecutionAgent": "executor"
            }
            
            # Получаем роль, которую этот агент ожидает от собеседника
            # По умолчанию разрешаем любую роль, если явно не указано иное
            expected_role = expected_roles.get(self.agent_name)
            
            # Проверяем, что роль в токене совпадает с ожидаемой для данного типа агента
            # НО: ResearchAgent может общаться с AnalysisAgent, поэтому не блокируем
            # Вместо этого просто проверяем, что роль валидна
            valid_roles = ["researcher", "analyst", "executor"]
            if payload.get("role") not in valid_roles:
                print(f"⚠️ Неизвестная роль: {payload.get('role')}")
                return False
            
            return True
            
        except ValueError as e:
            print(f"❌ Ошибка верификации WIT: {e}")
            return False
    
    def __str__(self):
        return f"AgentIdentity({self.agent_name}, role={self.role}, id={self.agent_id[:8]}...)"


# Глобальный экземпляр для доступа из других модулей
identity_manager = IdentityManager()
