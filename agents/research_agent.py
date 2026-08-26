from typing import Dict, Any
from .base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    """
    Агент для исследования и сбора данных (с YandexGPT).
    """
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("user_query", "")
        
        print(f"🔍 ResearchAgent: Запрос получен (длина: {len(query)})")
        
        self.start_trace(
            name="research",
            input_data={"query": query[:500]},
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
        
        try:
            response = self.invoke_with_observability(prompt)
            print(f"✅ ResearchAgent: LLM ответил (длина: {len(response.content)})")
        except Exception as e:
            print(f"❌ ResearchAgent: Ошибка при вызове LLM: {e}")
            raise
        
        self.end_trace(output_data={"research_data": response.content[:500]})
        
        # ВОЗВРАЩАЕМ ТОЛЬКО ТО, ЧТО ИЗМЕНИЛОСЬ
        # НЕ возвращаем email_from или другие поля, которые не менялись
        return {
            "research_data": response.content,
            "current_agent": self.agent_name,
            "next_agent": "AnalysisAgent"
        }
