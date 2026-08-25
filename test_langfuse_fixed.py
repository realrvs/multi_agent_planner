import os
import time
from dotenv import load_dotenv
from langfuse import Langfuse

# Загружаем .env
load_dotenv()

print("🧪 ТЕСТ LANGFUSE (ИСПРАВЛЕННЫЙ)")
print("=" * 60)

# Проверка переменных
print("\n📋 Шаг 1: Проверка переменных окружения")
print("-" * 40)
print(f"✅ LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST')}")
print(f"✅ LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY')[:20]}... (скрыто)")

# Создание клиента с увеличенным таймаутом
print("\n🔌 Шаг 2: Создание клиента Langfuse")
print("-" * 40)

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
    timeout=30  # Таймаут для сетевых запросов
)

print("✅ Клиент создан с таймаутом 30 секунд")

# Отправка тестовых данных
print("\n📤 Шаг 3: Отправка тестовых данных")
print("-" * 40)

trace_id = langfuse.create_trace_id()
print(f"✅ Trace ID создан: {trace_id[:16]}...")

langfuse.create_event(
    trace_context={"trace_id": trace_id},
    name="test_fixed",
    input={"message": "Тестовое сообщение с исправленным flush()"},
    metadata={"source": "test_fixed", "timestamp": time.time()}
)

print("✅ Event создан")

# ПРАВИЛЬНЫЙ ВЫЗОВ: flush() без аргументов
print("\n⏳ Отправка данных...")
try:
    langfuse.flush()
    print("✅ Данные отправлены!")
except Exception as e:
    print(f"⚠️ Ошибка при отправке: {e}")
    print("💡 Проверьте, что контейнеры Langfuse полностью запущены")

print("\n" + "=" * 60)
print("🎉 ТЕСТ ЗАВЕРШЕН!")
print(f"📊 Проверьте результаты в Langfuse: {os.getenv('LANGFUSE_HOST')}")
print(f"🔍 Trace ID: {trace_id}")
