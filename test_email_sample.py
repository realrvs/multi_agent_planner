import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_test_email():
    """Отправляет тестовое письмо в систему."""
    
    # Получаем настройки из .env
    email_from = os.getenv("EMAIL_ADDRESS")  # Отправляем с вашего адреса
    email_to = os.getenv("EMAIL_ADDRESS")    # На ваш же адрес (или укажите другой)
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not email_to or not email_password:
        print("❌ Ошибка: EMAIL_ADDRESS или EMAIL_PASSWORD не заполнены в .env")
        return
    
    # Создаём письмо
    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = "Вопрос по настройке мультиагентной системы"
    
    body = """
Здравствуйте!

Я пытаюсь настроить мультиагентную систему на базе LangGraph и YandexGPT, но столкнулся с проблемой.

При запуске main.py я получаю ошибку: 
"ValueError: Не указаны YANDEX_API_KEY и YANDEX_FOLDER_ID".

Я создал файл .env и добавил туда свои ключи, но ошибка всё равно появляется.

Подскажите, пожалуйста, что я делаю не так? 
Как правильно настроить переменные окружения?

Спасибо!
"""
    
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    try:
        # Отправляем через SMTP Яндекс.Почты
        with smtplib.SMTP_SSL("smtp.yandex.ru", 465) as server:
            server.login(email_from, email_password)
            server.sendmail(email_from, email_to, msg.as_string())
        
        print("✅ Тестовое письмо отправлено!")
        print(f"📧 От: {email_from}")
        print(f"📧 Кому: {email_to}")
        print(f"📧 Тема: {msg['Subject']}")
        
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        print("💡 Проверьте:")
        print("   1. Правильность EMAIL_ADDRESS в .env")
        print("   2. Правильность EMAIL_PASSWORD (пароль приложения)")
        print("   3. Что включён SMTP в настройках Яндекса")

if __name__ == "__main__":
    send_test_email()
