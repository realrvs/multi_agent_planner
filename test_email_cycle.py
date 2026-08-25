import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.email_agent import ReadEmailAgent, SendEmailAgent

def test_email_cycle():
    print("🧪 ТЕСТ ПОЛНОГО ЦИКЛА EMAIL")
    print("=" * 60)

    # 1. Читаем письма
    print("\n📧 Шаг 1: Чтение писем...")
    reader = ReadEmailAgent(max_emails=1)
    state = {
        "user_query": "",
        "messages": [],
        "research_data": None,
        "analysis_result": None,
        "execution_plan": None,
        "current_agent": None,
        "next_agent": None,
        "final_answer": None,
        "session_id": "email_test_session",
        "user_id": "email_test_user",
        "parent_wit": None,
        "current_agent_identity": None,
        "delegated_wit": None
    }

    result = reader.run(state)
    emails = result.get("emails", [])
    
    if not emails:
        print("⚠️ Нет новых писем для обработки")
        print("💡 Отправьте тестовое письмо на realrvs@yandex.ru и запустите тест снова")
        return

    print(f"✅ Найдено {len(emails)} писем")
    email = emails[0]
    print(f"   - От: {email.get('from')}")
    print(f"   - Тема: {email.get('subject')}")
    print(f"   - Текст: {email.get('body', '')[:200]}...")

    # 2. Подготавливаем ответ (имитация работы агентов)
    print("\n📝 Шаг 2: Генерация ответа...")
    
    # Сохраняем данные письма в состояние
    state["email_from"] = email.get("from")
    state["email_subject"] = email.get("subject")
    
    # Имитация обработки (здесь будет ваш граф)
    state["final_answer"] = f"""
    Здравствуйте!

    Благодарим за ваше обращение. Мы получили ваше письмо на тему:
    "{email.get('subject')}"

    Ваш запрос будет обработан в ближайшее время.

    С уважением,
    Команда поддержки
    """

    # 3. Отправляем ответ
    print("\n📤 Шаг 3: Отправка ответа...")
    sender = SendEmailAgent()
    send_result = sender.run(state)
    
    if send_result.get("send_status") == "success":
        print("✅ Ответ отправлен!")
    else:
        print(f"❌ Ошибка отправки: {send_result}")

    print("\n" + "=" * 60)
    print("🎉 Тест завершен!")

if __name__ == "__main__":
    test_email_cycle()
