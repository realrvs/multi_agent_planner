from typing import Dict, Any
from .base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    """
    Агент для исследования и сбора данных (с YandexGPT).
    """
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("user_query", "")
        
        # Начинаем trace
        self.start_trace(
            name="research",
            input_data={"query": query},
            metadata={"agent": "ResearchAgent"}
        )
        
        prompt = f"""
        Ты — агент-исследователь. Твоя задача — собрать и структурировать всю необходимую информацию 
        для выполнения следующего запроса пользователя:

        ЗАПРОС: {query}

        Выполни следующие действия:
        1. Определи ключевые сущности и факты, упомянутые в запросе.
        2. Если запрос требует внешних данных, укажи, какие именно данные нужны.
        3. Структурируй запрос в виде четких пунктов для дальнейшего анализа.
        4. Выдели возможные риски или неоднозначности.

        Ответ представь в виде структурированного отчёта на русском языке.
        """
        
        # ВАЖНО: используем invoke_with_observability для вызова
        response = self.invoke_with_observability(prompt)
        
        # Завершаем trace
        self.end_trace(output_data={"research_data": response.content[:500]})
        
        return {
            "research_data": response.content,
            "current_agent": self.agent_name,
            "next_agent": "AnalysisAgent"
        }
