"""
Простой тест для Langfuse 4.x
Проверяет отправку данных без сложных оберток
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_langfuse_simple():
    """
    Простой тест отправки данных в Langfuse
    """
    print("=" * 60)
    print("🧪 ПРОСТОЙ ТЕСТ LANGFUSE")
    print("=" * 60)
    
    # 1. Проверяем переменные
    print("\n📋 Шаг 1: Проверка переменных окружения")
    print("-" * 40)
    
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    print(f"✅ LANGFUSE_HOST: {host}")
    
    if public_key:
        print(f"✅ LANGFUSE_PUBLIC_KEY: {public_key[:15]}... (скрыто)")
    else:
        print("❌ LANGFUSE_PUBLIC_KEY не найден")
        return False
    
    if secret_key:
        print(f"✅ LANGFUSE_SECRET_KEY: {secret_key[:15]}... (скрыто)")
    else:
        print("❌ LANGFUSE_SECRET_KEY не найден")
        return False
    
    # 2. Импортируем Langfuse
    print("\n📦 Шаг 2: Импорт Langfuse")
    print("-" * 40)
    
    try:
        from langfuse import Langfuse
        print("✅ Langfuse импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    
    # 3. Создаем клиент
    print("\n🔌 Шаг 3: Создание клиента Langfuse")
    print("-" * 40)
    
    try:
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        print("✅ Клиент создан успешно")
        print(f"📌 Тип клиента: {type(client)}")
        
        # Проверяем доступные методы
        print("\n📋 Доступные методы:")
        methods = [m for m in dir(client) if not m.startswith('_')]
        for m in methods[:15]:
            print(f"   - {m}")
        
    except Exception as e:
        print(f"❌ Ошибка создания клиента: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Отправляем тестовые данные
    print("\n📤 Шаг 4: Отправка тестовых данных")
    print("-" * 40)
    
    try:
        # Создаем trace_id
        trace_id = client.create_trace_id()
        print(f"✅ Trace ID создан: {trace_id[:8]}...")
        
        # Создаем событие с правильными параметрами
        # В Langfuse 4.x используем trace_context для связи с trace
        event = client.create_event(
            trace_context={"trace_id": trace_id},
            name="test_simple",
            input={"message": "Hello from simple test!", "timestamp": time.time()},
            metadata={"test_type": "simple", "version": "1.0"}
        )
        print(f"✅ Event создан: {event}")
        
        # Отправляем данные
        print("⏳ Отправка данных...")
        client.flush()
        print("✅ Данные отправлены!")
        
        # Даем время на отправку
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print("🎉 ТЕСТ УСПЕШНО ЗАВЕРШЕН!")
        print("=" * 60)
        print(f"\n📊 Проверьте результаты в Langfuse:")
        print(f"   🔗 {host}")
        print(f"   🔍 Trace ID: {trace_id}")
        print("   👉 Перейдите в раздел 'Traces'")
        print("   👉 Найдите trace с именем 'test_simple'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки данных: {e}")
        print("\n📝 Детали ошибки:")
        import traceback
        traceback.print_exc()
        return False

def check_langfuse_installation():
    """Проверяет установленную версию Langfuse"""
    print("\n" + "=" * 60)
    print("🔍 ИНФОРМАЦИЯ О LANGFUSE")
    print("=" * 60)
    
    try:
        import langfuse
        print(f"📦 Версия langfuse: {langfuse.__version__}")
    except ImportError:
        print("❌ Langfuse не установлен")
        print("💡 Установите: pip install langfuse")
        return False
    
    try:
        from langfuse import Langfuse
        # Проверяем основные методы
        print("\n📋 Проверка ключевых методов:")
        
        if hasattr(Langfuse, 'create_trace_id'):
            print("   ✅ create_trace_id - доступен")
        else:
            print("   ❌ create_trace_id - НЕ доступен")
            
        if hasattr(Langfuse, 'create_event'):
            print("   ✅ create_event - доступен")
        else:
            print("   ❌ create_event - НЕ доступен")
            
        if hasattr(Langfuse, 'flush'):
            print("   ✅ flush - доступен")
        else:
            print("   ❌ flush - НЕ доступен")
            
        # Проверяем, что методы работают
        print("\n🔧 Проверка создания клиента...")
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "test")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "test")
        
        if public_key and secret_key:
            try:
                client = Langfuse(public_key=public_key, secret_key=secret_key)
                print("   ✅ Клиент создается корректно")
            except Exception as e:
                print(f"   ⚠️ Ошибка создания клиента: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("\n🚀 ЗАПУСК ПРОСТОГО ТЕСТА LANGFUSE\n")
    
    # Проверяем установку
    check_langfuse_installation()
    
    # Запускаем тест
    print("\n" + "=" * 60)
    print("🧪 ЗАПУСК ОСНОВНОГО ТЕСТА")
    print("=" * 60)
    
    success = test_langfuse_simple()
    
    if not success:
        print("\n" + "=" * 60)
        print("❌ ТЕСТ НЕ УДАЛСЯ")
        print("=" * 60)
        print("\n💡 Возможные причины:")
        print("   1. Неправильные ключи в .env файле")
        print("   2. Нет интернет-соединения")
        print("   3. Неверный хост (проверьте LANGFUSE_HOST)")
        print("   4. Проблемы с версией Langfuse")
        print("\n📝 Проверьте .env файл:")
        print("   LANGFUSE_ENABLED=true")
        print("   LANGFUSE_PUBLIC_KEY=pk-lf-...")
        print("   LANGFUSE_SECRET_KEY=sk-lf-...")
        print("   LANGFUSE_HOST=https://cloud.langfuse.com")