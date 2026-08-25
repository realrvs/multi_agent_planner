from typing import Literal
from langgraph.graph import StateGraph, END
from graph.state import PlannerState
from graph.nodes import (
    read_email_node,
    research_node,
    analysis_node,
    execution_node,
    finalize_node,
    send_email_node
)
from config.observability import observability

def build_planner_graph():
    """
    Строит граф мультиагентной системы планирования с email-интеграцией.
    """
    workflow = StateGraph(PlannerState)

    # Добавляем узлы
    workflow.add_node("read_email", read_email_node)
    workflow.add_node("research", research_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("finalize", finalize_node)
    workflow.add_node("send_email", send_email_node)

    # Устанавливаем начальную точку
    workflow.set_entry_point("read_email")

    # Добавляем ребра (последовательное выполнение)
    workflow.add_edge("read_email", "research")
    workflow.add_edge("research", "analysis")
    workflow.add_edge("analysis", "execution")
    workflow.add_edge("execution", "finalize")
    workflow.add_edge("finalize", "send_email")

    # Завершаем выполнение
    workflow.add_edge("send_email", END)

    # Компилируем граф
    return workflow.compile()
