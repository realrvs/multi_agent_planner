import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import build_planner_graph
from config.wimse_audit import wimse_audit
from config.prompts import prompt_versioning
import uuid
import json

def test_full_wimse():
    print("🧪 Финальное тестирование WIMSE (все этапы)\n" + "="*60)
    
    # 1. Создаём сессию аудита
    session_id = str(uuid.uuid4())
    user_id = "test_user_001"
    
    wimse_audit.start_session(session_id, user_id, {
        "test_name": "full_wimse_test",
        "version": "1.0"
    })
    
    print(f"📋 Сессия аудита: {session_id}")
    
    # 2. Проверяем политики
    print("\n📋 Политика агентов:")
    for agent in ["research", "analysis", "execution"]:
        policy = prompt_versioning.get_policy(agent)
        print(f"   - {agent.upper()}: {policy.get('role', 'N/A')}")
    
    # 3. Запускаем рабочий процесс
    print("\n🚀 Запуск рабочего процесса...")
    
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
        "user_id": user_id,
        "parent_wit": None,
        "current_agent_identity": None,
        "delegated_wit": None
    }
    
    graph = build_planner_graph()
    
    try:
        final_state = graph.invoke(initial_state)
        print("✅ Выполнение завершено")
        
        # 4. Выводим результаты
        print("\n📊 Результаты выполнения:")
        print(f"   - Исследование: {'✅ есть' if final_state.get('research_data') else '❌ нет'}")
        print(f"   - Анализ: {'✅ есть' if final_state.get('analysis_result') else '❌ нет'}")
        print(f"   - План: {'✅ есть' if final_state.get('execution_plan') else '❌ нет'}")
        print(f"   - Требуется одобрение: {final_state.get('requires_human_approval', False)}")
        print(f"   - План одобрен: {final_state.get('execution_plan_approved', False)}")
        
        # 5. Выводим информацию об аудите
        print("\n📋 Сводка по аудиту:")
        audit_summary = wimse_audit.get_audit_summary()
        print(f"   - Сессия: {audit_summary.get('session_id')}")
        print(f"   - User: {audit_summary.get('user_id')}")
        print(f"   - Событий: {audit_summary.get('events_count', 0)}")
        print(f"   - Trace ID: {audit_summary.get('trace_id', 'N/A')}")
        
        # 6. Отправляем данные в Langfuse (если включен)
        print("\n📤 Отправка аудита в Langfuse...")
        if wimse_audit.flush():
            print("✅ Аудит успешно отправлен в Langfuse")
        else:
            print("ℹ️ Аудит не отправлен (Langfuse отключен или не настроен)")
        
        # 7. Выводим финальный ответ (сокращённо)
        if final_state.get("final_answer"):
            print("\n📝 Фрагмент финального ответа:")
            lines = final_state["final_answer"].split('\n')[:10]
            print('\n'.join(lines) + "...\n")
        
        print("="*60)
        print("🎉 Финальное тестирование WIMSE завершено!")
        
        # 8. Сохраняем отчёт об аудите
        audit_report = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "state": {
                "research": bool(final_state.get("research_data")),
                "analysis": bool(final_state.get("analysis_result")),
                "execution": bool(final_state.get("execution_plan")),
                "requires_approval": final_state.get("requires_human_approval", False),
                "approved": final_state.get("execution_plan_approved", False)
            },
            "audit_summary": audit_summary
        }
        
        with open("audit_report.json", "w", encoding="utf-8") as f:
            json.dump(audit_report, f, ensure_ascii=False, indent=2)
        print("📄 Отчёт об аудите сохранён в audit_report.json")
        
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from datetime import datetime
    test_full_wimse()
