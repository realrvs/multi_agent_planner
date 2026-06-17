from typing import Dict, Any
from .base_agent import BaseAgent

class ExecutionAgent(BaseAgent):
    """
    Агент для разработки плана выполнения (с YandexGPT).
    """
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        analysis = state.get("analysis_result", "Нет анализа для планирования")
        query = state.get("user_query", "")
        
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
        
        response = self.llm.invoke(prompt)
        
        return {
            "execution_plan": response.content,
            "current_agent": self.agent_name,
            "next_agent": "FINISH"
        }