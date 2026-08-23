import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import build_planner_graph
from graph.state import PlannerState
from config.prompts import prompt_versioning
import uuid

def test_policies():
    print("🧪 Тестирование политик безопасности (WIMSE Phase 3)\n" + "="*60)
    
    # 1. Проверяем политики агентов
    print("\n📋 Проверка политик агентов:")
    agents = ["research", "analysis", "execution"]
    for agent in agents:
        policy = prompt_versioning.get_policy(agent)
        print(f"   - {agent.upper()}: {policy}")
    
    # 2. Проверяем конкретные разрешения
    print("\n🔍 Проверка разрешений:")
    
    # ResearchAgent может делегировать AnalysisAgent
    can_delegate = prompt_versioning.check_policy("research", "delegate", "AnalysisAgent")
    print(f"   - ResearchAgent → AnalysisAgent: {'✅ РАЗРЕШЕНО' if can_delegate else '❌ ЗАПРЕЩЕНО'}")
    
    # ResearchAgent НЕ может делегировать ExecutionAgent
    can_delegate_wrong = prompt_versioning.check_policy("research", "delegate", "ExecutionAgent")
    print(f"   - ResearchAgent → ExecutionAgent: {'✅ РАЗРЕШЕНО' if can_delegate_wrong else '❌ ЗАПРЕЩЕНО'}")
    
    # ExecutionAgent требует одобрения
    requires_approval = prompt_versioning.check_policy("execution", "human_approval")
    print(f"   - ExecutionAgent требует одобрения: {'✅ ДА' if requires_approval else '❌ НЕТ'}")
    
    # 3. Запускаем полный рабочий процесс с проверкой политик
    print("\n🚀 Запуск рабочего процесса с политиками...")
    
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
    
    graph = build_planner_graph()
    
    try:
        final_state = graph.invoke(initial_state)
        print("✅ Выполнение завершено")
        
        # Проверяем результат
        print("\n📊 Результаты выполнения:")
        print(f"   - Исследование: {'✅ есть' if final_state.get('research_data') else '❌ нет'}")
        print(f"   - Анализ: {'✅ есть' if final_state.get('analysis_result') else '❌ нет'}")
        print(f"   - План: {'✅ есть' if final_state.get('execution_plan') else '❌ нет'}")
        print(f"   - Требуется одобрение: {final_state.get('requires_human_approval', False)}")
        print(f"   - План одобрен: {final_state.get('execution_plan_approved', False)}")
        
        # Выводим финальный ответ (сокращённо)
        if final_state.get("final_answer"):
            print("\n📝 Фрагмент финального ответа:")
            print(final_state["final_answer"][:500] + "...\n")
        
        print("\n" + "="*60)
        print("🎉 Тестирование политик завершено!")
        
    except PermissionError as e:
        print(f"❌ Ошибка политики безопасности: {e}")
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_policies()
