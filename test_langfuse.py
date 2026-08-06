"""
Тест подключения к Langfuse API (версия 4.x)
Проверяет настройки и отправляет тестовый trace
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_langfuse_connection():
    """
    Тестирует подключение к Langfuse.
    Проверяет наличие переменных и отправляет тестовый trace.
    """
    print("=" * 60)
    print("🧪 ТЕСТ ПОДКЛЮЧЕНИЯ К LANGFUSE (v4.x)")
    print("=" * 60)
    
    # 1. Проверяем переменные окружения
    print("\n📋 Шаг 1: Проверка переменных окружения")
    print("-" * 40)
    
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
    
    print(f"✅ LANGFUSE_ENABLED: {enabled}")
    print(f"✅ LANGFUSE_HOST: {host}")
    
    if public_key:
        print(f"✅ LANGFUSE_PUBLIC_KEY: {public_key[:10]}... (скрыто)")
    else:
        print("❌ LANGFUSE_PUBLIC_KEY не найден в .env файле")
        return False
    
    if secret_key:
        print(f"✅ LANGFUSE_SECRET_KEY: {secret_key[:10]}... (скрыто)")
    else:
        print("❌ LANGFUSE_SECRET_KEY не найден в .env файле")
        return False
    
    if not enabled:
        print("\n⚠️ Langfuse отключен (LANGFUSE_ENABLED=false)")
        print("💡 Для теста установите LANGFUSE_ENABLED=true в .env файле")
        return False
    
    # 2. Проверяем установку langfuse
    print("\n📦 Шаг 2: Проверка установки langfuse")
    print("-" * 40)
    
    try:
        import langfuse
        print(f"✅ Langfuse установлен (версия: {langfuse.__version__})")
    except ImportError:
        print("❌ Langfuse не установлен")
        print("💡 Установите: pip install langfuse")
        return False
    
    # 3. Инициализируем клиент
    print("\n🔌 Шаг 3: Инициализация клиента Langfuse")
    print("-" * 40)
    
    try:
        from langfuse import Langfuse
        
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        print("✅ Клиент Langfuse создан успешно!")
        
        # Проверяем доступные методы для версии 4.x
        print("📋 Доступные методы для создания trace:")
        if hasattr(client, 'create_trace_id'):
            print("   ✅ create_trace_id (генерация ID)")
        if hasattr(client, 'create_event'):
            print("   ✅ create_event (создание события)")
        
        # Проверяем сигнатуру метода create_event
        import inspect
        if hasattr(client, 'create_event'):
            sig = inspect.signature(client.create_event)
            print(f"   📝 Сигнатура create_event: {sig}")
            
    except Exception as e:
        print(f"❌ Ошибка инициализации клиента: {e}")
        return False
    
    # 4. Отправляем тестовый trace через API 4.x
    print("\n📤 Шаг 4: Отправка тестового trace (API 4.x)")
    print("-" * 40)
    
    try:
        from langfuse import Langfuse
        
        # Создаем клиент заново для чистоты
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        
        # В версии 4.x используем create_trace_id и create_event с правильными параметрами
        trace_id = client.create_trace_id()
        print(f"✅ Создан trace_id: {trace_id[:8]}...")
        
        # Создаем span (в версии 4.x это делается через create_event с trace_id)
        # Сначала создаем span через API
        try:
            # Пробуем создать span с правильными параметрами
            from langfuse import get_client
            langfuse_client = get_client()
            
            # Используем span через контекст
            with langfuse_client.span(
                trace_id=trace_id,
                name="test_span",
                input={"test_input": "Hello from span!"},
                metadata={"test_metadata": "test_value"}
            ) as span:
                span.update(
                    output={"test_output": "Success!"}
                )
            print("✅ Создан span через контекстный менеджер")
            
        except Exception as e:
            print(f"⚠️ Ошибка создания span через контекст: {e}")
            
            # Альтернативный способ: используем create_span напрямую
            try:
                span = client.create_span(
                    trace_id=trace_id,
                    name="test_span",
                    input={"test_input": "Hello from span!"},
                    metadata={"test_metadata": "test_value"}
                )
                span.update(
                    output={"test_output": "Success!"}
                )
                print("✅ Создан span через create_span")
            except Exception as e2:
                print(f"⚠️ Ошибка создания span через create_span: {e2}")
                print("   💡 Продолжаем без span...")
        
        # Создаем score для оценки
        try:
            client.score(
                trace_id=trace_id,
                name="test_score",
                value=0.95,
                comment="Test score from connection test"
            )
            print("✅ Создан score")
        except Exception as e:
            print(f"⚠️ Ошибка создания score: {e}")
        
        # Отправляем данные
        client.flush()
        print("✅ Данные отправлены в Langfuse!")
        
        # Даем время на отправку
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print("🎉 ТЕСТ УСПЕШНО ЗАВЕРШЕН!")
        print("=" * 60)
        print("\n📊 Проверьте результаты в Langfuse:")
        print(f"   🔗 {host}")
        print(f"   🔍 Trace ID: {trace_id}")
        print("   👉 Перейдите в раздел 'Traces'")
        print("   👉 Найдите trace с ID или поищите по имени 'test_span'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки данных: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_langfuse_installation():
    """
    Проверяет установку langfuse и показывает информацию
    """
    print("\n" + "=" * 60)
    print("🔍 ИНФОРМАЦИЯ О LANGFUSE")
    print("=" * 60)
    
    try:
        import langfuse
        print(f"📦 Версия langfuse: {langfuse.__version__}")
        
        # Показываем доступные методы для версии 4.x
        from langfuse import Langfuse
        client_methods = [m for m in dir(Langfuse) if not m.startswith('_')]
        print(f"\n📋 Доступные методы клиента ({len(client_methods)}):")
        
        # Показываем ключевые методы для версии 4.x
        key_methods = ['create_trace_id', 'create_event', 'create_span', 'flush', 'score']
        for method in key_methods:
            if hasattr(Langfuse, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ {method}")
        
        # Определяем версию API
        print("\n📌 Версия API:")
        if hasattr(Langfuse, 'create_trace_id'):
            print("   ✅ Langfuse 4.x (create_trace_id + create_event)")
        elif hasattr(Langfuse, 'create_trace'):
            print("   ✅ Langfuse 3.x (create_trace)")
        elif hasattr(Langfuse, 'trace'):
            print("   ✅ Langfuse 2.x (trace)")
        else:
            print("   ⚠️ Неизвестная версия API")
            
    except ImportError:
        print("❌ Langfuse не установлен")
        print("💡 Установите: pip install langfuse")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_simple_connection():
    """
    Простой тест соединения через HTTP
    """
    print("\n" + "=" * 60)
    print("🌐 ПРОВЕРКА HTTP СОЕДИНЕНИЯ")
    print("=" * 60)
    
    try:
        import requests
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        response = requests.get(f"{host}/api/public/health", timeout=5)
        print(f"✅ HTTP статус: {response.status_code}")
        if response.status_code == 200:
            print("✅ Сервер Langfuse доступен")
            return True
        else:
            print(f"⚠️ Сервер вернул статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def create_env_example():
    """
    Создает пример .env файла для Langfuse
    """
    env_example = """
# Langfuse Configuration (для версии 4.x)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...  # Получите на https://cloud.langfuse.com
LANGFUSE_SECRET_KEY=sk-lf-...  # Получите на https://cloud.langfuse.com
LANGFUSE_HOST=https://cloud.langfuse.com  # Или https://us.cloud.langfuse.com для США
"""
    
    print("\n" + "=" * 60)
    print("📝 ПРИМЕР .env ФАЙЛА ДЛЯ LANGFUSE")
    print("=" * 60)
    print(env_example)
    print("\n💡 Как получить ключи:")
    print("   1. Зарегистрируйтесь на https://cloud.langfuse.com")
    print("   2. Создайте проект")
    print("   3. В настройках проекта -> API Keys создайте новые ключи")
    print("   4. Скопируйте их в .env файл")

if __name__ == "__main__":
    print("\n🚀 Запуск тестов Langfuse (версия 4.x)\n")
    
    # Проверяем установку
    check_langfuse_installation()
    
    # Проверяем HTTP соединение
    test_simple_connection()
    
    # Показываем пример .env
    create_env_example()
    
    # Запускаем тест
    print("\n" + "=" * 60)
    print("🧪 ЗАПУСК ТЕСТА ПОДКЛЮЧЕНИЯ")
    print("=" * 60)
    
    success = test_langfuse_connection()
    
    if not success:
        print("\n" + "=" * 60)
        print("❌ ТЕСТ НЕ УДАЛСЯ")
        print("=" * 60)
        print("\n💡 Возможные причины:")
        print("   1. Неправильные ключи в .env файле")
        print("   2. Langfuse 4.x требует правильного формата ключей")
        print("   3. Нет интернет-соединения")
        print("   4. Неверный хост (проверьте LANGFUSE_HOST)")
        print("\n📝 Проверьте .env файл:")
        print("   LANGFUSE_ENABLED=true")
        print("   LANGFUSE_PUBLIC_KEY=pk-lf-...")
        print("   LANGFUSE_SECRET_KEY=sk-lf-...")
        print("   LANGFUSE_HOST=https://cloud.langfuse.com")
        
        print("\n🔧 Альтернативное решение:")
        print("   Если тест не работает, отключите Langfuse в .env:")
        print("   LANGFUSE_ENABLED=false")
        print("   Проект будет работать без отправки данных в Langfuse")