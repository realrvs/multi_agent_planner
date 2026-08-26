"""
Тест email-пайплайна без реального вызова YandexGPT
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock
from graph.workflow import build_planner_graph
from dotenv import load_dotenv
import uuid

load_dotenv()

def test_email_pipeline_without_llm():
    """
    Тестирует полный email-пайплайн без вызова LLM.
    Вместо YandexGPT используется мок-объект.
    """
    print("🧪 ТЕСТ EMAIL-ПАЙПЛАЙНА БЕЗ LLM")
    print("=" * 60)

    # 1. Создаём мок для YandexGPT
    mock_response = MagicMock()
    mock_response.content = "Это тестовый ответ от мока. Система работает без реального вызова LLM."

    # 2. Патчим правильный путь: agents.yandex_adapter.YandexGPT
    with patch('agents.yandex_adapter.YandexGPT') as mock_llm:
        # Настраиваем мок
        mock_llm.return_value.invoke.return_value = mock_response

        # 3. Создаём состояние с тестовым письмом
        session_id = str(uuid.uuid4())
        initial_state = {
            "user_query": "Тестовый запрос без вызова LLM",
            "messages": [],
            "research_data": None,
            "analysis_result": None,
            "execution_plan": None,
            "current_agent": None,
            "next_agent": None,
            "final_answer": None,
            "session_id": session_id,
            "user_id": "test_user",
            "parent_wit": None,
            "current_agent_identity": None,
            "delegated_wit": None,
            "emails": [],
            "email_from": "test@example.com",
            "email_subject": "Тест без LLM",
            "email_body": "Тестовое тело письма",
            "email_error": None,
            "send_status": None
        }

        # 4. Запускаем граф
        print("⏳ Запуск графа (без реальных LLM-вызовов)...")
        graph = build_planner_graph()
        result = graph.invoke(initial_state)

        # 5. Проверяем результат
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print(f"   ✅ Финальный ответ: {result.get('final_answer', 'Нет ответа')[:100]}...")
        print(f"   ✅ Статус отправки: {result.get('send_status', 'не указан')}")
        print(f"   ✅ email_from: {result.get('email_from', 'не указан')}")

        # 6. Проверяем, что моки были вызваны
        print("\n📋 Статистика вызовов моков:")
        print(f"   - YandexGPT вызван: {mock_llm.return_value.invoke.call_count} раз")

    print("\n" + "=" * 60)
    print("🎉 ТЕСТ БЕЗ LLM ЗАВЕРШЕН!")

if __name__ == "__main__":
    test_email_pipeline_without_llm()
