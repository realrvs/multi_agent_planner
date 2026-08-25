import os
import time
from langfuse import Langfuse

# Настройки
os.environ['LANGFUSE_HOST'] = 'http://localhost:3000'
os.environ['LANGFUSE_PUBLIC_KEY'] = 'pk-lf-a9f0fa74-7ea6-4120-9813-5804c7d0c58b'
os.environ['LANGFUSE_SECRET_KEY'] = 'sk-lf-318a1b8a-38cf-4754-9a97-7a253676e977'

print("🧪 ТЕСТ OTLP")
print("=" * 60)

# Создаём клиент с увеличенным таймаутом
langfuse = Langfuse(timeout=60)

# Создаём trace
trace_id = langfuse.create_trace_id()
print(f"✅ Trace ID: {trace_id[:16]}...")

# Создаём событие
langfuse.create_event(
    trace_context={"trace_id": trace_id},
    name="otlp_test",
    input={"message": "Тест OTLP через Python"},
    metadata={"source": "otlp_test", "time": time.time()}
)

print("✅ Event создан")

# Отправляем данные
print("⏳ Отправка данных...")
langfuse.flush()
print("✅ Данные отправлены!")

print("=" * 60)
print(f"📊 Проверьте результаты в Langfuse: http://localhost:3000")
print(f"🔍 Trace ID: {trace_id}")
