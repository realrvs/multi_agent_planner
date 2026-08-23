import os
from dotenv import load_dotenv

# Загружаем .env ПЕРЕД созданием агентов
load_dotenv()

from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.execution_agent import ExecutionAgent
from config.identity import identity_manager

research_agent = ResearchAgent()
analysis_agent = AnalysisAgent()
execution_agent = ExecutionAgent()

def research_node(state):
    # Проверяем входящий запрос
    research_agent.verify_incoming_request(state)
    
    # Проверяем политику делегирования
    research_agent.enforce_policy("delegate", "AnalysisAgent")
    
    # Сохраняем WIT текущего агента в состояние
    state["parent_wit"] = research_agent.identity.wit_token
    state["current_agent_identity"] = research_agent.get_identity_context()
    state["current_agent"] = "ResearchAgent"
    
    # Вызываем агента
    result = research_agent.run(state)
    
    # Передаём WIT дальше
    result["parent_wit"] = research_agent.identity.wit_token
    result["current_agent_identity"] = research_agent.get_identity_context()
    result["next_agent"] = "AnalysisAgent"
    
    return result

def analysis_node(state):
    # Проверяем входящий запрос
    analysis_agent.verify_incoming_request(state)
    
    # Проверяем политику делегирования
    analysis_agent.enforce_policy("delegate", "ExecutionAgent")
    
    # Сохраняем WIT текущего агента в состояние
    state["parent_wit"] = analysis_agent.identity.wit_token
    state["current_agent_identity"] = analysis_agent.get_identity_context()
    state["current_agent"] = "AnalysisAgent"
    
    # Вызываем агента
    result = analysis_agent.run(state)
    
    # Передаём WIT дальше
    result["parent_wit"] = analysis_agent.identity.wit_token
    result["current_agent_identity"] = analysis_agent.get_identity_context()
    result["next_agent"] = "ExecutionAgent"
    
    return result

def execution_node(state):
    # Проверяем входящий запрос
    execution_agent.verify_incoming_request(state)
    
    # Проверяем политику: ExecutionAgent может делегировать только FINISH
    execution_agent.enforce_policy("delegate", "FINISH")
    
    # Сохраняем WIT текущего агента
    state["current_agent_identity"] = execution_agent.get_identity_context()
    state["current_agent"] = "ExecutionAgent"
    
    # Вызываем агента
    result = execution_agent.run(state)
    
    # Проверяем, требуется ли одобрение человека для выполнения плана
    requires_approval = execution_agent.check_policy("human_approval")
    if requires_approval:
        print("⚠️ ВНИМАНИЕ: Действие требует одобрения человека!")
        result["requires_human_approval"] = True
        result["execution_plan_approved"] = False
    else:
        result["requires_human_approval"] = False
        result["execution_plan_approved"] = True
    
    # Передаём WIT дальше
    result["parent_wit"] = execution_agent.identity.wit_token
    result["next_agent"] = "FINISH"
    
    return result

def finalize_node(state):
    # Проверяем, был ли выполнен хотя бы один агент
    agents_called = []
    if hasattr(research_agent, 'called') and research_agent.called:
        agents_called.append("ResearchAgent")
    if hasattr(analysis_agent, 'called') and analysis_agent.called:
        agents_called.append("AnalysisAgent")
    if hasattr(execution_agent, 'called') and execution_agent.called:
        agents_called.append("ExecutionAgent")
    
    # Получаем статус одобрения
    approved = state.get("execution_plan_approved", False)
    requires_approval = state.get("requires_human_approval", False)
    
    final_answer = f"""
    ## ✅ Итоговый план действий
    
    ### 🔍 Результаты исследования:
    {state.get('research_data', 'Нет данных')}
    
    ### 📊 Анализ:
    {state.get('analysis_result', 'Нет анализа')}
    
    ### 📋 План выполнения:
    {state.get('execution_plan', 'Нет плана')}
    """
    
    # Добавляем информацию о безопасности и политиках
    security_info = f"""
    ### 🔐 Информация о безопасности (WIMSE):
    - Выполненные агенты: {', '.join(agents_called) if agents_called else 'Ни один агент не был вызван'}
    - Цепочка агентов: ResearchAgent → AnalysisAgent → ExecutionAgent
    - Сессия: {state.get('session_id', 'не указана')}
    - User ID: {state.get('user_id', 'не указан')}
    
    ### 🛡️ Политики безопасности:
    - Требуется одобрение человека: {'✅ Да' if requires_approval else '❌ Нет'}
    - План одобрен: {'✅ Да' if approved else '⏳ Ожидает одобрения'}
    """
    
    final_answer += security_info
    
    return {
        "final_answer": final_answer,
        "next_agent": "END",
        "current_agent": "FinalizeAgent",
        "execution_plan_approved": approved,
        "requires_human_approval": requires_approval
    }
