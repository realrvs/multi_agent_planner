import os
from dotenv import load_dotenv

load_dotenv()

from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.execution_agent import ExecutionAgent
from agents.email_agent import ReadEmailAgent, SendEmailAgent
from config.identity import identity_manager

# Инициализация агентов
research_agent = ResearchAgent()
analysis_agent = AnalysisAgent()
execution_agent = ExecutionAgent()
read_email_agent = ReadEmailAgent()
send_email_agent = SendEmailAgent()

# ============================================================
# УЗЛЫ ДЛЯ EMAIL-ОБРАБОТКИ
# ============================================================

def read_email_node(state):
    """Узел чтения писем."""
    result = read_email_agent.run(state)
    
    # Если есть письма, берём первое для обработки
    if result.get("emails"):
        email = result["emails"][0]
        # Сохраняем данные письма в состояние
        state["user_query"] = email.get("body", "")
        state["email_from"] = email.get("from")
        state["email_subject"] = email.get("subject")
        state["email_id"] = email.get("id")
        state["email_body"] = email.get("body", "")
        state["email_data"] = email  # Полный объект письма
        
        print(f"📧 Письмо от: {state['email_from']}")
        print(f"📧 Тема: {state['email_subject']}")
        print(f"📧 Текст: {state['email_body'][:200]}...")
    else:
        print("⚠️ Нет писем для обработки")
    
    # Возвращаем обновлённое состояние
    return {
        "emails": result.get("emails", []),
        "email_error": result.get("email_error"),
        "email_from": state.get("email_from"),
        "email_subject": state.get("email_subject"),
        "email_body": state.get("email_body"),
        "email_data": state.get("email_data"),
        "user_query": state.get("user_query", ""),
        "current_agent": "ReadEmailAgent",
        "next_agent": "ResearchAgent" if result.get("emails") else "FINISH"
    }

def send_email_node(state):
    """Узел отправки ответа."""
    return send_email_agent.run(state)

# ============================================================
# ОСНОВНЫЕ УЗЛЫ АГЕНТОВ (Research, Analysis, Execution)
# ============================================================

def research_node(state):
    """Узел исследования."""
    # Проверяем входящий запрос
    research_agent.verify_incoming_request(state)
    
    # Сохраняем WIT текущего агента
    state["parent_wit"] = research_agent.identity.wit_token
    state["current_agent_identity"] = research_agent.get_identity_context()
    state["current_agent"] = "ResearchAgent"
    
    result = research_agent.run(state)
    result["parent_wit"] = research_agent.identity.wit_token
    result["next_agent"] = "AnalysisAgent"
    return result

def analysis_node(state):
    """Узел анализа."""
    analysis_agent.verify_incoming_request(state)
    
    state["parent_wit"] = analysis_agent.identity.wit_token
    state["current_agent_identity"] = analysis_agent.get_identity_context()
    state["current_agent"] = "AnalysisAgent"
    
    result = analysis_agent.run(state)
    result["parent_wit"] = analysis_agent.identity.wit_token
    result["next_agent"] = "ExecutionAgent"
    return result

def execution_node(state):
    """Узел исполнения (генерация плана)."""
    execution_agent.verify_incoming_request(state)
    
    state["current_agent_identity"] = execution_agent.get_identity_context()
    state["current_agent"] = "ExecutionAgent"
    
    result = execution_agent.run(state)
    result["parent_wit"] = execution_agent.identity.wit_token
    result["next_agent"] = "FINISH"
    
    # Проверяем, требуется ли одобрение человека
    requires_approval = execution_agent.check_policy("human_approval")
    result["requires_human_approval"] = requires_approval
    result["execution_plan_approved"] = not requires_approval
    
    return result

def finalize_node(state):
    """Узел финализации — формирует итоговый ответ."""
    # Проверяем, какие агенты были вызваны
    agents_called = []
    if hasattr(research_agent, 'called') and research_agent.called:
        agents_called.append("ResearchAgent")
    if hasattr(analysis_agent, 'called') and analysis_agent.called:
        agents_called.append("AnalysisAgent")
    if hasattr(execution_agent, 'called') and execution_agent.called:
        agents_called.append("ExecutionAgent")
    
    # Формируем ответ
    final_answer = f"""
## ✅ Итоговый ответ

### 🔍 Результаты исследования:
{state.get('research_data', 'Нет данных')}

### 📊 Анализ:
{state.get('analysis_result', 'Нет анализа')}

### 📋 План выполнения:
{state.get('execution_plan', 'Нет плана')}
"""
    
    # Добавляем информацию о безопасности
    security_info = f"""
### 🔐 Информация о безопасности (WIMSE):
- Выполненные агенты: {', '.join(agents_called) if agents_called else 'Ни один агент не был вызван'}
- Цепочка: ResearchAgent → AnalysisAgent → ExecutionAgent
- Сессия: {state.get('session_id', 'не указана')}
- User ID: {state.get('user_id', 'не указан')}
- Требуется одобрение человека: {'✅ Да' if state.get('requires_human_approval', False) else '❌ Нет'}
"""
    
    final_answer += security_info
    
    return {
        "final_answer": final_answer,
        "next_agent": "END",
        "current_agent": "FinalizeAgent"
    }
