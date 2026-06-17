import os
from dotenv import load_dotenv

# Загружаем .env ПЕРЕД созданием агентов
load_dotenv()

from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.execution_agent import ExecutionAgent

research_agent = ResearchAgent()
analysis_agent = AnalysisAgent()
execution_agent = ExecutionAgent()

def research_node(state):
    return research_agent.run(state)

def analysis_node(state):
    return analysis_agent.run(state)

def execution_node(state):
    return execution_agent.run(state)

def finalize_node(state):
    final_answer = f"""
    ## ✅ Итоговый план действий

    ### 🔍 Результаты исследования:
    {state.get('research_data', 'Нет данных')}

    ### 📊 Анализ:
    {state.get('analysis_result', 'Нет анализа')}

    ### 📋 План выполнения:
    {state.get('execution_plan', 'Нет плана')}
    """
    
    return {
        "final_answer": final_answer,
        "next_agent": "END"
    }