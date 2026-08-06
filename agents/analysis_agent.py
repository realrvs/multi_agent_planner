from typing import Dict, Any
from .base_agent import BaseAgent

class AnalysisAgent(BaseAgent):
    """
    Агент для анализа данных (с YandexGPT).
    """
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        research_data = state.get("research_data", "Нет данных для анализа")
        query = state.get("user_query", "")
        
        # Начинаем trace
        self.start_trace(
            name="analysis",
            input_data={"query": query, "research_data": research_data[:500]},
            metadata={"agent": "AnalysisAgent"}
        )
        
        prompt = f"""
        Ты — агент-аналитик. Твоя задача — глубоко проанализировать предоставленные данные 
        и подготовить основу для планирования действий.

        ИСХОДНЫЙ ЗАПРОС: {query}
        
        ДАННЫЕ ОТ ИССЛЕДОВАТЕЛЯ:
        {research_data}

        Выполни следующие действия:
        1. Проанализируй все факты и данные.
        2. Выяви ключевые зависимости и паттерны.
        3. Определи приоритеты и критические точки.
        4. Сформулируй выводы, которые лягут в основу плана действий.

        Ответ представь в виде аналитической записки на русском языке.
        """
        
        response = self.invoke_with_observability(prompt)
        
        # Завершаем trace
        self.end_trace(output_data={"analysis_result": response.content[:500]})
        
        return {
            "analysis_result": response.content,
            "current_agent": self.agent_name,
            "next_agent": "ExecutionAgent"
        }