import os
from dotenv import load_dotenv
from graph.workflow import build_planner_graph
from graph.state import PlannerState
from utils.pdf_generator import PDFGenerator

load_dotenv()

def main():
    required_vars = ["YANDEX_API_KEY", "YANDEX_FOLDER_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Ошибка: не найдены переменные в .env файле: {', '.join(missing_vars)}")
        return
    
    graph = build_planner_graph()
    
    user_query = """
    Разработай план по запуску нового онлайн-курса по программированию для начинающих.
    Целевая аудитория — студенты без опыта. Бюджет — 500 000 рублей.
    Срок — 3 месяца.
    """
    
    print("🚀 Запуск мультиагентной системы планирования (YandexGPT)...\n")
    print(f"📝 Запрос: {user_query}\n")
    print("=" * 60)
    
    initial_state: PlannerState = {
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
        final_state = graph.invoke(initial_state)
        
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
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()