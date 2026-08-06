from typing import Literal
from langgraph.graph import StateGraph, END
from graph.state import PlannerState
from graph.nodes import research_node, analysis_node, execution_node, finalize_node
from config.observability import observability

def build_planner_graph():
    """
    Строит граф мультиагентной системы планирования.
    """
    workflow = StateGraph(PlannerState)
    
    # Добавляем узлы
    workflow.add_node("research", research_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("finalize", finalize_node)
    
    # Устанавливаем начальную точку
    workflow.set_entry_point("research")
    
    # Добавляем ребра (последовательное выполнение)
    workflow.add_edge("research", "analysis")
    workflow.add_edge("analysis", "execution")
    workflow.add_edge("execution", "finalize")
    
    # Завершаем выполнение
    workflow.add_edge("finalize", END)
    
    # Компилируем граф
    return workflow.compile()