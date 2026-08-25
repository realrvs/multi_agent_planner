import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from graph.workflow import build_planner_graph
from graph.state import PlannerState
from utils.pdf_generator import PDFGenerator
from utils.metrics_monitor import metrics_monitor
from config.observability import observability
from config.prompt_db import prompt_db
from config.identity import identity_manager
import uuid

load_dotenv()

def process_email():
    print("🚀 ЗАПУСК EMAIL-ОБРАБОТЧИКА")
    print("=" * 60)

    # Проверяем базу данных промптов
    print("🔍 Проверка базы данных промптов...")
    try:
        versions = prompt_db.get_all_versions("research")
        if versions:
            print(f"✅ База данных содержит {len(versions)} версий для research")
    except Exception as e:
        print(f"⚠️ Ошибка проверки БД: {e}")

    # Проверяем переменные окружения
    required_vars = ["YANDEX_API_KEY", "YANDEX_FOLDER_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Ошибка: не найдены переменные в .env файле: {', '.join(missing_vars)}")
        return

    # Создаём состояние с email-контекстом
    session_id = str(uuid.uuid4())
    initial_state = {
        "user_query": "",
        "messages": [],
        "research_data": None,
        "analysis_result": None,
        "execution_plan": None,
        "current_agent": None,
        "next_agent": None,
        "final_answer": None,
        "session_id": session_id,
        "user_id": "email_processor",
        "parent_wit": None,
        "current_agent_identity": None,
        "delegated_wit": None,
        "emails": [],
        "email_from": None,
        "email_subject": None,
        "email_error": None,
        "send_status": None
    }

    try:
        graph = build_planner_graph()
        final_state = graph.invoke(initial_state)

        metrics = metrics_monitor.collect_metrics(final_state)
        print("\n📊 МЕТРИКИ СИСТЕМЫ:")
        print(json.dumps(metrics, ensure_ascii=False, indent=2))

        summary = metrics_monitor.get_summary()
        print("\n📈 СВОДКА ПО МЕТРИКАМ:")
        print(f"✅ Всего выполнений: {summary.get('total_executions', 0)}")
        print(f"✅ Всего вызовов LLM: {summary.get('total_calls', 0)}")
        print(f"✅ Всего токенов: {summary.get('total_tokens', 0)}")
        print(f"✅ Всего затрат: ${summary.get('total_cost', 0):.4f}")

        if final_state.get("send_status") == "success":
            print("\n📧 Ответ успешно отправлен!")
        else:
            print(f"\n⚠️ Статус отправки: {final_state.get('send_status')}")

        if final_state.get("final_answer"):
            print("\n📌 ИТОГОВЫЙ ОТВЕТ:")
            print("=" * 60)
            print(final_state["final_answer"][:500] + "...")

        # Отправляем данные в Langfuse
        print("\n📤 Отправка данных в Langfuse...")
        if observability.flush():
            print("✅ Данные успешно отправлены в Langfuse!")

    except Exception as e:
        print(f"❌ Ошибка при выполнении: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_email()
