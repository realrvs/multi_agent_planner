from typing import Literal
from langgraph.graph import StateGraph, END
from .state import PlannerState
from .nodes import research_node, analysis_node, execution_node, finalize_node

def build_planner_graph() -> StateGraph:
    workflow = StateGraph(PlannerState)
    
    workflow.add_node("research", research_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("finalize", finalize_node)
    
    workflow.set_entry_point("research")
    
    workflow.add_edge("research", "analysis")
    workflow.add_edge("analysis", "execution")
    workflow.add_edge("execution", "finalize")
    
    workflow.add_edge("finalize", END)
    
    return workflow.compile()