import os
from dotenv import load_dotenv

load_dotenv()

from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.execution_agent import ExecutionAgent
from agents.email_agent import ReadEmailAgent, SendEmailAgent
from config.identity import identity_manager
from graph.state import PlannerState

# ============================================================
# ИНИЦИАЛИЗАЦИЯ АГЕНТОВ
# ============================================================

research_agent = ResearchAgent()
analysis_agent = AnalysisAgent()
execution_agent = ExecutionAgent()
read_email_agent = ReadEmailAgent()
send_email_agent = SendEmailAgent()

# ============================================================
# УЗЕЛ: ЧТЕНИЕ EMAIL
# ============================================================

def read_email_node(state: PlannerState) -> dict:
    """
    Читает новые письма из почтового ящика.
    Возвращает ТОЛЬКО изменённые поля.
    """
    print("📧 Чтение новых писем...")
    
    result = read_email_agent.run(state)
    emails = result.get("emails", [])
    
    if emails:
        email = emails[0]
        print(f"📧 Письмо от: {email.get('from')}")
        print(f"📧 Тема: {email.get('subject')}")
        
        # Возвращаем ТОЛЬКО то, что изменилось
        return {
            "emails": emails,
            "email_from": email.get("from"),
            "email_subject": email.get("subject"),
            "email_body": email.get("body", ""),
            "email_data": email,
            "user_query": email.get("body", ""),
            "next_agent": "ResearchAgent",
            "current_agent": "ReadEmailAgent"
        }
    else:
        print("⚠️ Нет новых писем")
        return {
            "emails": [],
            "next_agent": "FINISH",
            "current_agent": "ReadEmailAgent"
        }

# ============================================================
# УЗЕЛ: ИССЛЕДОВАНИЕ (ResearchAgent)
# ============================================================

def research_node(state: PlannerState) -> dict:
    """
    Анализирует запрос и собирает структурированную информацию.
    """
    print("🔍 ResearchAgent: начало обработки...")
    print(f"📧 email_from на входе: {state.get('email_from')}")
    
    research_agent.verify_incoming_request(state)
    
    result = research_agent.run(state)
    
    # Возвращаем ТОЛЬКО то, что изменилось
    return {
        **result,  # research_data, current_agent, next_agent
        "parent_wit": research_agent.identity.wit_token,
        "current_agent_identity": research_agent.get_identity_context()
    }

# ============================================================
# УЗЕЛ: АНАЛИЗ (AnalysisAgent)
# ============================================================

def analysis_node(state: PlannerState) -> dict:
    """
    Глубоко анализирует данные и выявляет паттерны.
    """
    print("📊 AnalysisAgent: начало обработки...")
    print(f"📧 email_from на входе: {state.get('email_from')}")
    
    analysis_agent.verify_incoming_request(state)
    
    result = analysis_agent.run(state)
    
    return {
        **result,
        "parent_wit": analysis_agent.identity.wit_token,
        "current_agent_identity": analysis_agent.get_identity_context()
    }

# ============================================================
# УЗЕЛ: ИСПОЛНЕНИЕ (ExecutionAgent)
# ============================================================

def execution_node(state: PlannerState) -> dict:
    """
    Разрабатывает пошаговый план действий.
    """
    print("📋 ExecutionAgent: начало обработки...")
    print(f"📧 email_from на входе: {state.get('email_from')}")
    
    execution_agent.verify_incoming_request(state)
    
    result = execution_agent.run(state)
    
    requires_approval = execution_agent.check_policy("human_approval")
    
    return {
        **result,
        "parent_wit": execution_agent.identity.wit_token,
        "current_agent_identity": execution_agent.get_identity_context(),
        "requires_human_approval": requires_approval,
        "execution_plan_approved": not requires_approval
    }

# ============================================================
# УЗЕЛ: ФИНАЛИЗАЦИЯ (формирование ответа)
# ============================================================

def finalize_node(state: PlannerState) -> dict:
    """
    Формирует итоговый ответ на основе работы всех агентов.
    """
    print("📝 FinalizeNode: формирование ответа...")
    print(f"📧 email_from на входе: {state.get('email_from')}")
    
    agents_called = []
    if hasattr(research_agent, 'called') and research_agent.called:
        agents_called.append("ResearchAgent")
    if hasattr(analysis_agent, 'called') and analysis_agent.called:
        agents_called.append("AnalysisAgent")
    if hasattr(execution_agent, 'called') and execution_agent.called:
        agents_called.append("ExecutionAgent")
    
    final_answer = f"""
## ✅ Итоговый ответ

### 🔍 Результаты исследования:
{state.get('research_data', 'Нет данных')}

### 📊 Анализ:
{state.get('analysis_result', 'Нет анализа')}

### 📋 План выполнения:
{state.get('execution_plan', 'Нет плана')}
"""
    
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
        "next_agent": "SendEmailAgent",
        "current_agent": "FinalizeAgent"
    }

# ============================================================
# УЗЕЛ: ОТПРАВКА EMAIL
# ============================================================

def send_email_node(state: PlannerState) -> dict:
    """
    Отправляет сгенерированный ответ обратно отправителю.
    """
    print("📤 SendEmailAgent: отправка ответа...")
    print(f"📧 email_from на входе: {state.get('email_from')}")
    
    to_addr = state.get("email_from")
    
    if not to_addr:
        print("⚠️ Нет адреса для отправки")
        return {
            "send_status": "no_recipient",
            "next_agent": "FINISH"
        }
    
    reply_body = state.get("final_answer")
    if not reply_body:
        print("⚠️ Нет текста ответа")
        return {
            "send_status": "no_content",
            "next_agent": "FINISH"
        }
    
    result = send_email_agent.run(state)
    
    if result.get("send_status") == "success":
        print(f"✅ Ответ отправлен на {to_addr}")
    
    return {
        **result,
        "next_agent": "FINISH"
    }

# ============================================================
# СПИСОК ЭКСПОРТИРУЕМЫХ ФУНКЦИЙ
# ============================================================

__all__ = [
    'read_email_node',
    'research_node',
    'analysis_node',
    'execution_node',
    'finalize_node',
    'send_email_node'
]
