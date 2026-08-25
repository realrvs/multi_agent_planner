import os
import sys
from langfuse import Langfuse

print("🧪 ПРОСТОЙ ТЕСТ LANGFUSE (УНИВЕРСАЛЬНЫЙ СИНТАКСИС)")
print("=" * 60)

# Шаг 1: Переменные окружения
host = os.getenv("LANGFUSE_HOST", "http://localhost:3000").split('#')[0].strip().strip('"').strip("'")
public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key = os.getenv("LANGFUSE_SECRET_KEY")

print(f"✅ LANGFUSE_HOST: {host}")
print(f"✅ LANGFUSE_PUBLIC_KEY: {public_key[:15]}..." if public_key else "❌ LANGFUSE_PUBLIC_KEY не задан")
print(f"✅ LANGFUSE_SECRET_KEY: {secret_key[:15]}..." if secret_key else "❌ LANGFUSE_SECRET_KEY не задан")

if not public_key or not secret_key:
    sys.exit(1)

# Шаг 2: Инициализация клиента
langfuse = Langfuse(
    public_key=public_key,
    secret_key=secret_key,
    host=host,
    timeout=30
)
print("✅ Клиент Langfuse инициализирован")

# Шаг 3: Отправка данных
print("\n📤 Шаг 3: Отправка события...")
try:
    # Базовое создание события без привязок к несуществующим методам
    event = langfuse.create_event(
        name="test_event_direct",
        metadata={"status": "working"}
    )
    print("✅ Event успешно сформирован!")

    print("⏳ Отправка пакета данных через flush()...")
    langfuse.flush()
    print("✅ Данные успешно отправлены в Langfuse!")
except Exception as e:
    print(f"⚠️ Ошибка при выполнении: {e}")

print("=" * 60)
print(f"📊 Проверьте раздел 'Traces' / 'Events' в UI: {host}")
