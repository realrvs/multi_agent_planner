"""
Управление промптами через SQLite базу данных
Позволяет изменять промпты без изменения кода
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import os

class PromptDB:
    """Класс для работы с промптами в SQLite"""
    
    def __init__(self, db_path: str = "prompts.db"):
        """Инициализация базы данных"""
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Создает таблицы если они не существуют"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица для промптов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    template TEXT NOT NULL,
                    description TEXT,
                    temperature REAL DEFAULT 0.3,
                    max_tokens INTEGER DEFAULT 2000,
                    is_active INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(agent_name, version)
                )
            """)
            
            # Таблица для истории изменений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER,
                    action TEXT,
                    old_version TEXT,
                    new_version TEXT,
                    changed_by TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                )
            """)
            
            # Таблица для текущих активных версий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_versions (
                    agent_name TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
            # Загружаем начальные данные если таблица пуста
            self._seed_initial_data()
    
    def _seed_initial_data(self):
        """Загружает начальные промпты если таблица пуста"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем есть ли данные
            cursor.execute("SELECT COUNT(*) FROM prompts")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Загружаем начальные промпты
                initial_prompts = self._get_initial_prompts()
                
                for agent, versions in initial_prompts.items():
                    for version, data in versions.items():
                        cursor.execute("""
                            INSERT INTO prompts 
                            (agent_name, version, template, description, temperature, max_tokens, is_active)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            agent,
                            version,
                            data['template'],
                            data.get('description', ''),
                            data.get('temperature', 0.3),
                            data.get('max_tokens', 2000),
                            1 if version == 'v1' else 0
                        ))
                    
                    # Устанавливаем v1 как активную для каждого агента
                    cursor.execute("""
                        INSERT OR REPLACE INTO active_versions (agent_name, version)
                        VALUES (?, ?)
                    """, (agent, 'v1'))
                
                conn.commit()
                print("✅ Загружены начальные промпты в базу данных")
    
    def _get_initial_prompts(self) -> Dict[str, Any]:
        """Возвращает начальные промпты для базы данных"""
        return {
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
                    "description": "Базовая версия исследователя",
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                "v2": {
                    "template": """
Ты — агент-исследователь с расширенными возможностями анализа. 

КОНТЕКСТ ЗАПРОСА: {query}

Проведи комплексное исследование:
1. Проанализируй запрос на предмет скрытых требований и подтекста.
2. Выяви все заинтересованные стороны и их ожидания.
3. Определи необходимые источники информации и методы сбора данных.
4. Составь структурированный план сбора информации.
5. Оцени риски и предложи стратегии их минимизации.

Результат представь в формате:
### Ключевые факты
- факт 1
- факт 2

### Требуемые данные
- данные 1
- данные 2

### Риски и ограничения
- риск 1
- риск 2

### Рекомендации по сбору информации
- рекомендация 1
- рекомендация 2
""",
                    "description": "Расширенная версия с детальным анализом",
                    "temperature": 0.4,
                    "max_tokens": 2500
                },
                "v3": {
                    "template": """
Ты — опытный исследователь и аналитик. Выполни глубокий анализ запроса.

ЗАПРОС: {query}

Проведи исследование по следующей структуре:

1. **Декомпозиция запроса**:
   - Разбей запрос на составные части
   - Определи приоритеты

2. **Анализ контекста**:
   - Кто заинтересованные стороны?
   - Какие ресурсы доступны?
   - Какие ограничения существуют?

3. **Сбор данных**:
   - Какие данные необходимы?
   - Где их можно получить?
   - Как проверить достоверность?

4. **Оценка рисков**:
   - Технические риски
   - Бизнес-риски
   - Временные риски

5. **Выводы и рекомендации**:
   - Ключевые инсайты
   - Следующие шаги

Ответ должен быть структурированным, практичным и на русском языке.
""",
                    "description": "Детальная версия с пошаговой структурой",
                    "temperature": 0.35,
                    "max_tokens": 3000
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
                    "description": "Базовая версия аналитика",
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                "v2": {
                    "template": """
Ты — эксперт-аналитик с опытом стратегического планирования.

КОНТЕКСТ: {query}

ДАННЫЕ ДЛЯ АНАЛИЗА:
{research_data}

Проведи комплексный анализ по схеме:

1. **SWOT-анализ**:
   - Сильные стороны
   - Слабые стороны
   - Возможности
   - Угрозы

2. **Анализ стейкхолдеров**:
   - Кто заинтересован?
   - Какие у них ожидания?
   - Как управлять ожиданиями?

3. **Анализ ресурсов**:
   - Доступные ресурсы
   - Необходимые ресурсы
   - Дефицит и как его покрыть

4. **Приоритизация**:
   - Критические факторы успеха
   - Что делать в первую очередь?
   - Что можно отложить?

5. **Ключевые выводы**:
   - Основные инсайты
   - Рекомендации для планирования

Ответ должен быть практичным, структурированным и на русском языке.
""",
                    "description": "Расширенная версия с SWOT-анализом",
                    "temperature": 0.35,
                    "max_tokens": 3000
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
                    "description": "Базовая версия планировщика",
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                "v2": {
                    "template": """
Ты — опытный менеджер проектов. Разработай детальный план выполнения.

КОНТЕКСТ: {query}

АНАЛИТИЧЕСКИЕ ВЫВОДЫ:
{analysis}

Создай детальный план по структуре:

1. **Этапы и вехи**:
   - Основные этапы проекта
   - Ключевые вехи с датами
   - Зависимости между этапами

2. **Задачи и ресурсы**:
   - Конкретные задачи по каждому этапу
   - Необходимые ресурсы (люди, деньги, технологии)
   - Ответственные лица

3. **Бюджет**:
   - Разбивка по статьям затрат
   - Резервный фонд
   - Контроль бюджета

4. **Риски и управление**:
   - Идентификация рисков
   - Стратегии смягчения
   - План действий при наступлении рисков

5. **Критерии успеха и контроль**:
   - KPI проекта
   - Точки контроля
   - Механизмы отчетности

План должен быть детальным, практичным и представлен на русском языке.
""",
                    "description": "Детальная версия с управлением проектами",
                    "temperature": 0.35,
                    "max_tokens": 3500
                }
            }
        }
    
    def get_prompt(self, agent_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Получает промпт из базы данных
        
        Args:
            agent_name: Имя агента (research, analysis, execution)
            version: Версия промпта (если None, берется активная)
        
        Returns:
            Dict с данными промпта
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Если версия не указана, берем активную
            if version is None:
                cursor.execute("""
                    SELECT version FROM active_versions WHERE agent_name = ?
                """, (agent_name,))
                result = cursor.fetchone()
                if result:
                    version = result['version']
                else:
                    # Если нет активной, берем первую версию
                    cursor.execute("""
                        SELECT version FROM prompts WHERE agent_name = ? 
                        ORDER BY version LIMIT 1
                    """, (agent_name,))
                    result = cursor.fetchone()
                    if result:
                        version = result['version']
                    else:
                        return {}
            
            # Получаем промпт
            cursor.execute("""
                SELECT * FROM prompts 
                WHERE agent_name = ? AND version = ?
            """, (agent_name, version))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            return {}
    
    def get_active_version(self, agent_name: str) -> str:
        """Получает активную версию для агента"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version FROM active_versions WHERE agent_name = ?
            """, (agent_name,))
            result = cursor.fetchone()
            return result[0] if result else 'v1'
    
    def set_active_version(self, agent_name: str, version: str, changed_by: str = 'user') -> bool:
        """
        Устанавливает активную версию для агента
        
        Args:
            agent_name: Имя агента
            version: Новая версия
            changed_by: Кто изменил (user, system)
        
        Returns:
            True если успешно, False если версия не найдена
        """
        # Проверяем существование версии
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, is_active FROM prompts 
                WHERE agent_name = ? AND version = ?
            """, (agent_name, version))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            prompt_id = result[0]
            
            # Снимаем активность со всех версий
            cursor.execute("""
                UPDATE prompts SET is_active = 0 
                WHERE agent_name = ?
            """, (agent_name,))
            
            # Устанавливаем активность для новой версии
            cursor.execute("""
                UPDATE prompts SET is_active = 1 
                WHERE agent_name = ? AND version = ?
            """, (agent_name, version))
            
            # Обновляем активную версию
            cursor.execute("""
                INSERT OR REPLACE INTO active_versions (agent_name, version, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (agent_name, version))
            
            # Записываем историю
            cursor.execute("""
                INSERT INTO prompt_history (prompt_id, action, new_version, changed_by)
                VALUES (?, ?, ?, ?)
            """, (prompt_id, 'activate', version, changed_by))
            
            conn.commit()
            return True
    
    def add_version(self, agent_name: str, version: str, template: str, 
                    description: str = '', temperature: float = 0.3, 
                    max_tokens: int = 2000, changed_by: str = 'user') -> bool:
        """
        Добавляет новую версию промпта
        
        Args:
            agent_name: Имя агента
            version: Версия (например, v4)
            template: Текст промпта
            description: Описание
            temperature: Температура
            max_tokens: Максимальное количество токенов
            changed_by: Кто добавил
        
        Returns:
            True если успешно
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем существование версии
            cursor.execute("""
                SELECT id FROM prompts 
                WHERE agent_name = ? AND version = ?
            """, (agent_name, version))
            
            if cursor.fetchone():
                return False  # Версия уже существует
            
            # Добавляем новую версию
            cursor.execute("""
                INSERT INTO prompts 
                (agent_name, version, template, description, temperature, max_tokens, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (agent_name, version, template, description, temperature, max_tokens))
            
            prompt_id = cursor.lastrowid
            
            # Записываем историю
            cursor.execute("""
                INSERT INTO prompt_history (prompt_id, action, new_version, changed_by)
                VALUES (?, ?, ?, ?)
            """, (prompt_id, 'add', version, changed_by))
            
            conn.commit()
            return True
    
    def update_version(self, agent_name: str, version: str, template: str,
                       description: str = None, temperature: float = None,
                       max_tokens: int = None, changed_by: str = 'user') -> bool:
        """
        Обновляет существующую версию промпта
        
        Args:
            agent_name: Имя агента
            version: Версия
            template: Новый текст промпта
            description: Новое описание
            temperature: Новая температура
            max_tokens: Новое максимальное количество токенов
            changed_by: Кто изменил
        
        Returns:
            True если успешно
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем существование версии
            cursor.execute("""
                SELECT id FROM prompts 
                WHERE agent_name = ? AND version = ?
            """, (agent_name, version))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            prompt_id = result[0]
            
            # Собираем поля для обновления
            updates = ["template = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [template]
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if temperature is not None:
                updates.append("temperature = ?")
                params.append(temperature)
            
            if max_tokens is not None:
                updates.append("max_tokens = ?")
                params.append(max_tokens)
            
            params.extend([agent_name, version])
            
            # Обновляем
            cursor.execute(f"""
                UPDATE prompts 
                SET {', '.join(updates)}
                WHERE agent_name = ? AND version = ?
            """, tuple(params))
            
            # Записываем историю
            cursor.execute("""
                INSERT INTO prompt_history (prompt_id, action, new_version, changed_by)
                VALUES (?, ?, ?, ?)
            """, (prompt_id, 'update', version, changed_by))
            
            conn.commit()
            return True
    
    def get_all_versions(self, agent_name: str) -> List[Dict[str, Any]]:
        """Получает все версии для агента"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM prompts 
                WHERE agent_name = ? 
                ORDER BY version
            """, (agent_name,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_history(self, agent_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает историю изменений"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if agent_name:
                cursor.execute("""
                    SELECT h.*, p.agent_name, p.version 
                    FROM prompt_history h
                    JOIN prompts p ON h.prompt_id = p.id
                    WHERE p.agent_name = ?
                    ORDER BY h.changed_at DESC
                    LIMIT ?
                """, (agent_name, limit))
            else:
                cursor.execute("""
                    SELECT h.*, p.agent_name, p.version 
                    FROM prompt_history h
                    JOIN prompts p ON h.prompt_id = p.id
                    ORDER BY h.changed_at DESC
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_prompt_hash(self, agent_name: str, version: str) -> str:
        """Вычисляет хеш промпта"""
        prompt_data = self.get_prompt(agent_name, version)
        template = prompt_data.get('template', '')
        return hashlib.md5(template.encode()).hexdigest()[:8]
    
    def delete_version(self, agent_name: str, version: str, changed_by: str = 'user') -> bool:
        """
        Удаляет версию промпта (только если она не активна)
        
        Args:
            agent_name: Имя агента
            version: Версия
            changed_by: Кто удалил
        
        Returns:
            True если успешно
        """
        active_version = self.get_active_version(agent_name)
        
        if version == active_version:
            return False  # Нельзя удалить активную версию
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Получаем id
            cursor.execute("""
                SELECT id FROM prompts 
                WHERE agent_name = ? AND version = ?
            """, (agent_name, version))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            prompt_id = result[0]
            
            # Удаляем
            cursor.execute("""
                DELETE FROM prompts 
                WHERE agent_name = ? AND version = ?
            """, (agent_name, version))
            
            # Записываем историю
            cursor.execute("""
                INSERT INTO prompt_history (prompt_id, action, old_version, changed_by)
                VALUES (?, ?, ?, ?)
            """, (prompt_id, 'delete', version, changed_by))
            
            conn.commit()
            return True

# Создаем глобальный экземпляр
prompt_db = PromptDB("prompts.db")