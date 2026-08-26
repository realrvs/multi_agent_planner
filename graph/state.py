from typing import List, Dict, Any, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages

class PlannerState(TypedDict):
    # Основные поля
    user_query: str
    messages: Annotated[List[Dict[str, Any]], add_messages]
    
    # Результаты агентов
    research_data: Optional[str]
    analysis_result: Optional[str]
    execution_plan: Optional[str]
    
    # Управление потоком
    current_agent: Optional[str]
    next_agent: Optional[str]
    
    # Финальный ответ
    final_answer: Optional[str]
    
    # ===== WIMSE БЕЗОПАСНОСТЬ =====
    session_id: Optional[str]
    user_id: Optional[str]
    parent_wit: Optional[str]
    current_agent_identity: Optional[Dict[str, Any]]
    delegated_wit: Optional[str]
    
    # ===== EMAIL ДАННЫЕ (ДОБАВЛЯЕМ!) =====
    emails: Optional[List[Dict[str, Any]]]
    email_from: Optional[str]
    email_subject: Optional[str]
    email_body: Optional[str]
    email_id: Optional[str]
    email_data: Optional[Dict[str, Any]]
    email_error: Optional[str]
    send_status: Optional[str]
    
    # ===== ФЛАГИ =====
    requires_human_approval: Optional[bool]
    execution_plan_approved: Optional[bool]
