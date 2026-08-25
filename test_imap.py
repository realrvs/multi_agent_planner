import os
import imaplib
from dotenv import load_dotenv

load_dotenv()

email = os.getenv("EMAIL_ADDRESS")
password = os.getenv("EMAIL_PASSWORD")
host = os.getenv("EMAIL_IMAP_HOST", "imap.yandex.ru")
port = int(os.getenv("EMAIL_IMAP_PORT", 993))

print("🧪 ПРОВЕРКА IMAP-ПОДКЛЮЧЕНИЯ")
print("=" * 60)
print(f"📧 Хост: {host}:{port}")
print(f"📧 Логин: {email}")

if not email or not password:
    print("❌ Ошибка: EMAIL_ADDRESS или EMAIL_PASSWORD не заполнены в .env")
    exit(1)

try:
    print("⏳ Подключение...")
    mail = imaplib.IMAP4_SSL(host, port)
    mail.login(email, password)
    mail.select("INBOX")
    print("✅ ПОДКЛЮЧЕНИЕ УСПЕШНО!")
    status, data = mail.status("INBOX", "(MESSAGES UNSEEN)")
    if status == "OK":
        print("📊 Статистика: " + data[0].decode("utf-8"))
    mail.close()
    mail.logout()
except imaplib.IMAP4.error as e:
    print("❌ Ошибка IMAP: " + str(e))
    print("💡 Проверьте:")
    print("   1. Включён ли IMAP в настройках Яндекса")
    print("   2. Правильность пароля приложения (не основной пароль)")
    print("   3. Что пароль создан для типа Почта")
except Exception as e:
    print("❌ Ошибка: " + str(e))
