import os
import time
from dotenv import load_dotenv
from langfuse import Langfuse

# Принудительно загружаем .env
load_dotenv(override=True)

print("🧪 ТЕСТ ОБЛАЧНОГО LANGFUSE")
print("=" * 60)

# Читаем переменные
host = os.getenv('LANGFUSE_HOST')
public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
secret_key = os.getenv('LANGFUSE_SECRET_KEY')

print(f"✅ Хост: {host}")
print(f"✅ Публичный ключ: {public_key[:20]}...")
print(f"✅ Секретный ключ: {secret_key[:20]}...")

# Создаём клиент
langfuse = Langfuse(
    public_key=public_key,
    secret_key=secret_key,
    host=host,
    timeout=30
)

# Создаём trace
trace_id = langfuse.create_trace_id()
print(f"✅ Trace ID: {trace_id[:16]}...")

# Создаём событие
langfuse.create_event(
    trace_context={"trace_id": trace_id},
    name="cloud_test_final",
    input={"message": "Финальный тест облачного Langfuse"},
    metadata={"source": "cloud_final", "time": time.time()}
)

print("✅ Event создан")
print("⏳ Отправка данных...")
langfuse.flush()
print("✅ Данные отправлены!")

print("=" * 60)
print(f"📊 Проверьте результаты: {host}")
print(f"🔍 Trace ID: {trace_id}")
