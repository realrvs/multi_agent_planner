from typing import Dict, Any
from .base_agent import BaseAgent

class ExecutionAgent(BaseAgent):
    """
    Агент для разработки плана выполнения (с YandexGPT).
    """
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        analysis = state.get("analysis_result", "Нет анализа для планирования")
        query = state.get("user_query", "")
        
        # Начинаем trace
        self.start_trace(
            name="execution",
            input_data={"query": query, "analysis": analysis[:500]},
            metadata={"agent": "ExecutionAgent"}
        )
        
        prompt = f"""
        Ты — агент-исполнитель и планировщик. Твоя задача — разработать чёткий, 
        пошаговый план действий на основе предоставленного анализа.

        ИСХОДНЫЙ ЗАПРОС: {query}
        
        АНАЛИТИЧЕСКИЕ ВЫВОДЫ:
        {analysis}

        Разработай план, который включает:
        1. Конкретные шаги с указанием последовательности.
        2. Необходимые ресурсы для каждого шага.
        3. Ожидаемые результаты после каждого этапа.
        4. Риски и способы их минимизации.
        5. Временные оценки.

        План должен быть практичным, выполнимым и представлен на русском языке.
        """
        
        # Используем invoke_with_observability для вызова (с поддержкой мок-режима)
        response = self.invoke_with_observability(prompt)
        
        # Завершаем trace
        self.end_trace(output_data={"execution_plan": response.content[:500]})
        
        return {
            "execution_plan": response.content,
            "current_agent": self.agent_name,
            "next_agent": "FINISH"
        }
