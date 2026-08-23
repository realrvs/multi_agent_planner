import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import build_planner_graph
from graph.state import PlannerState
import uuid

def test_context_propagation():
    print("🧪 Тестирование передачи контекста безопасности (WIMSE)\n" + "="*60)
    
    # Создаём состояние с контекстом безопасности
    session_id = str(uuid.uuid4())
    initial_state = {
        "user_query": "Разработай план по запуску нового онлайн-курса по программированию для начинающих.",
        "messages": [],
        "research_data": None,
        "analysis_result": None,
        "execution_plan": None,
        "current_agent": None,
        "next_agent": None,
        "final_answer": None,
        "session_id": session_id,
        "user_id": "test_user_001",
        "parent_wit": None,
        "current_agent_identity": None,
        "delegated_wit": None
    }
    
    print(f"✅ Создано состояние с session_id: {session_id}")
    print(f"   - user_id: {initial_state['user_id']}")
    
    # Строим граф
    graph = build_planner_graph()
    print("✅ Граф построен")
    
    try:
        # Запускаем выполнение
        final_state = graph.invoke(initial_state)
        print("✅ Выполнение завершено")
        
        # Проверяем, что контекст передавался
        print("\n📊 Анализ передачи контекста:")
        print(f"   - Итоговый ответ содержит информацию о безопасности?")
        if "WIMSE" in final_state.get("final_answer", ""):
            print("   ✅ Да, информация о безопасности присутствует")
        else:
            print("   ⚠️ Нет, информация о безопасности отсутствует")
        
        # Проверяем, что агенты были вызваны (через метрики)
        from utils.metrics_monitor import metrics_monitor
        summary = metrics_monitor.get_summary()
        print(f"\n📈 Сводка по метрикам:")
        print(f"   - Всего выполнений: {summary.get('total_executions', 0)}")
        print(f"   - Всего вызовов LLM: {summary.get('total_calls', 0)}")
        print(f"   - Успешность: {summary.get('success_rate', 0):.2%}")
        
        # Дополнительная информация из финального состояния
        print(f"\n📋 Детали выполнения:")
        print(f"   - Research data: {'✅ есть' if final_state.get('research_data') else '❌ нет'}")
        print(f"   - Analysis result: {'✅ есть' if final_state.get('analysis_result') else '❌ нет'}")
        print(f"   - Execution plan: {'✅ есть' if final_state.get('execution_plan') else '❌ нет'}")
        
        print("\n" + "="*60)
        print("🎉 Тестирование передачи контекста завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_propagation()
