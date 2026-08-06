from typing import Dict, Any
import json
import hashlib
from datetime import datetime

class PromptVersioning:
    """Система версионирования промптов"""
    
    PROMPTS = {
        "research": {
            "v1": {
                "template": """
                Ты — агент-исследователь. Твоя задача — собрать и структурировать всю необходимую информацию 
                для выполнения следующего запроса пользователя:

                ЗАПРОС: {query}

                Выполни следующие действия:
                1. Определи ключевые сущности и факты, упомянутые в запросе.
                2. Если запрос требует внешних данных, укажи, какие именно данные нужны.
                3. Структурируй запрос в виде четких пунктов для дальнейшего анализа.
                4. Выдели возможные риски или неоднозначности.

                Ответ представь в виде структурированного отчёта на русском языке.
                """,
                "version": "v1",
                "created_at": "2024-01-01",
                "temperature": 0.3,
                "max_tokens": 2000
            },
            "v2": {
                "template": """
                Ты — агент-исследователь с расширенными возможностями анализа. 

                КОНТЕКСТ ЗАПРОСА: {query}

                Проведи комплексное исследование:
                1. Проанализируй запрос на предмет скрытых требований.
                2. Выяви все заинтересованные стороны и их ожидания.
                3. Определи необходимые источники информации.
                4. Составь структурированный план сбора данных.
                5. Оцени риски и предложи стратегии их минимизации.

                Результат представь в формате:
                - Ключевые факты
                - Требуемые данные
                - Риски и ограничения
                - Рекомендации по сбору информации
                """,
                "version": "v2",
                "created_at": "2024-01-15",
                "temperature": 0.4,
                "max_tokens": 2500
            }
        },
        "analysis": {
            "v1": {
                "template": """
                Ты — агент-аналитик. Твоя задача — глубоко проанализировать предоставленные данные 
                и подготовить основу для планирования действий.

                ИСХОДНЫЙ ЗАПРОС: {query}
                
                ДАННЫЕ ОТ ИССЛЕДОВАТЕЛЯ:
                {research_data}

                Выполни следующие действия:
                1. Проанализируй все факты и данные.
                2. Выяви ключевые зависимости и паттерны.
                3. Определи приоритеты и критические точки.
                4. Сформулируй выводы, которые лягут в основу плана действий.

                Ответ представь в виде аналитической записки на русском языке.
                """,
                "version": "v1",
                "created_at": "2024-01-01",
                "temperature": 0.3,
                "max_tokens": 2000
            }
        },
        "execution": {
            "v1": {
                "template": """
                Ты — агент-исполнитель и планировщик. Твоя задача — разработать чёткий, 
                пошаговый план действий на основе предоставленного анализа.

                ИСХОДНЫЙ ЗАПРОС: {query}
                
                АНАЛИТИЧЕСКИЕ ВЫВОДЫ:
                {analysis}

                Разработай план, который включает:
                1. Конкретные шаги с указанием последовательности.
                2. Необходимые ресурсы для каждого шага.
                3. Ожидаемые результаты после каждого этапа.
                4. Риски и способы их минимизации.
                5. Временные оценки.

                План должен быть практичным, выполнимым и представлен на русском языке.
                """,
                "version": "v1",
                "created_at": "2024-01-01",
                "temperature": 0.3,
                "max_tokens": 2000
            }
        }
    }
    
    def __init__(self):
        self.current_versions = {
            "research": "v2",  # Используем новую версию
            "analysis": "v1",
            "execution": "v1"
        }
        self.version_history = {}
    
    def get_prompt(self, agent_name: str, version: str = None) -> Dict[str, Any]:
        """Получить промпт для конкретного агента"""
        if version is None:
            version = self.current_versions.get(agent_name, "v1")
        
        return self.PROMPTS.get(agent_name, {}).get(version, {})
    
    def get_prompt_hash(self, agent_name: str, version: str = None) -> str:
        """Получить хеш промпта для отслеживания изменений"""
        prompt_data = self.get_prompt(agent_name, version)
        if not prompt_data:
            return ""
        
        # Хешируем содержимое промпта
        content = prompt_data.get("template", "")
        return hashlib.md5(content.encode()).hexdigest()
    
    def switch_version(self, agent_name: str, version: str):
        """Переключить версию промпта для агента"""
        if agent_name in self.PROMPTS and version in self.PROMPTS[agent_name]:
            self.current_versions[agent_name] = version
            return True
        return False
    
    def get_version_info(self, agent_name: str) -> Dict[str, Any]:
        """Получить информацию о текущей версии"""
        version = self.current_versions.get(agent_name, "v1")
        prompt_data = self.get_prompt(agent_name, version)
        
        return {
            "agent": agent_name,
            "version": version,
            "hash": self.get_prompt_hash(agent_name, version),
            "metadata": prompt_data
        }

prompt_versioning = PromptVersioning()