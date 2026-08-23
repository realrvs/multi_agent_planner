from typing import List, Dict, Any, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages

class PlannerState(TypedDict):
    user_query: str
    messages: Annotated[List[Dict[str, Any]], add_messages]
    research_data: Optional[str]
    analysis_result: Optional[str]
    execution_plan: Optional[str]
    current_agent: Optional[str]
    next_agent: Optional[str]
    final_answer: Optional[str]
    
    # НОВЫЕ ПОЛЯ ДЛЯ БЕЗОПАСНОСТИ (WIMSE)
    session_id: Optional[str]          # ID сессии пользователя
    user_id: Optional[str]             # ID пользователя
    parent_wit: Optional[str]          # WIT агента-родителя
    current_agent_identity: Optional[Dict[str, Any]]  # Контекст идентичности текущего агента
    delegated_wit: Optional[str]       # WIT для делегирования (аттенуация)
