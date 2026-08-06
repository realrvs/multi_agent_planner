import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from graph.workflow import build_planner_graph
from graph.state import PlannerState
from utils.pdf_generator import PDFGenerator
from utils.metrics_monitor import metrics_monitor
from config.observability import observability
from config.prompt_db import prompt_db

load_dotenv()

def main():
    # Проверяем базу данных промптов
    print("🔍 Проверка базы данных промптов...")
    try:
        # Проверяем, что БД создана и есть данные
        versions = prompt_db.get_all_versions("research")
        if versions:
            print(f"✅ База данных содержит {len(versions)} версий для research")
        else:
            print("⚠️ База данных пуста, будет создана автоматически")
    except Exception as e:
        print(f"⚠️ Ошибка проверки БД: {e}")
    
    # Проверяем переменные окружения
    required_vars = ["YANDEX_API_KEY", "YANDEX_FOLDER_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Ошибка: не найдены переменные в .env файле: {', '.join(missing_vars)}")
        print("\n💡 Создайте файл .env со следующими переменными:")
        print("   YANDEX_API_KEY=ваш_ключ")
        print("   YANDEX_FOLDER_ID=ваш_folder_id")
        print("   YANDEX_MODEL_URI=gpt://ваш_folder_id/yandexgpt/latest")
        return
    
    user_query = """
    Разработай план по запуску нового онлайн-курса по программированию для начинающих.
    Целевая аудитория — студенты без опыта. Бюджет — 500 000 рублей.
    Срок — 3 месяца.
    """
    
    print("🚀 Запуск мультиагентной системы планирования (YandexGPT)...\n")
    print(f"📝 Запрос: {user_query}\n")
    print("=" * 60)
    
    initial_state = {
        "user_query": user_query,
        "messages": [],
        "research_data": None,
        "analysis_result": None,
        "execution_plan": None,
        "current_agent": None,
        "next_agent": None,
        "final_answer": None
    }
    
    try:
        graph = build_planner_graph()
        final_state = graph.invoke(initial_state)
        
        metrics = metrics_monitor.collect_metrics(final_state)
        print("\n" + "=" * 60)
        print("📊 МЕТРИКИ СИСТЕМЫ:")
        print("=" * 60)
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        
        summary = metrics_monitor.get_summary()
        print("\n📈 СВОДКА ПО МЕТРИКАМ:")
        print("=" * 60)
        print(f"✅ Всего выполнений: {summary.get('total_executions', 0)}")
        print(f"✅ Всего вызовов LLM: {summary.get('total_calls', 0)}")
        print(f"✅ Всего токенов: {summary.get('total_tokens', 0)}")
        print(f"✅ Всего затрат: ${summary.get('total_cost', 0):.4f}")
        print(f"✅ Успешность: {summary.get('success_rate', 0):.2%}")
        
        metrics_monitor.export_metrics("metrics_latest.json")
        
        print("\n" + "=" * 60)
        print("📌 ИТОГОВЫЙ ПЛАН:")
        print("=" * 60)
        print(final_state.get("final_answer", "План не был сгенерирован"))
        
        print("\n" + "=" * 60)
        print("📄 СОХРАНЕНИЕ РЕЗУЛЬТАТА В PDF")
        print("=" * 60)
        
        pdf_generator = PDFGenerator()
        pdf_file = pdf_generator.generate_report(final_state)
        print(f"✅ PDF-отчет сохранен: {pdf_file}")
        
        # Отправляем данные в Langfuse
        print("\n📤 Отправка данных в Langfuse...")
        if observability.flush():
            print("✅ Данные успешно отправлены в Langfuse!")
        else:
            print("⚠️ Не удалось отправить данные в Langfuse")
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()