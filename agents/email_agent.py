"""
Агенты для работы с Яндекс.Почтой (IMAP/SMTP)
"""

import os
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import re
from dotenv import load_dotenv

# Загружаем .env при импорте модуля
load_dotenv()

from .base_agent import BaseAgent


class ReadEmailAgent(BaseAgent):
    """
    Агент для чтения входящих писем из Яндекс.Почты (IMAP).
    """

    def __init__(self, poll_interval: int = 60, max_emails: int = 5, **kwargs):
        """
        Args:
            poll_interval: Интервал проверки новых писем (сек)
            max_emails: Максимальное количество писем за один раз
        """
        super().__init__(require_llm=False, **kwargs)
        self.poll_interval = poll_interval
        self.max_emails = max_emails
        self.host = os.getenv("EMAIL_IMAP_HOST", "imap.yandex.ru")
        self.port = int(os.getenv("EMAIL_IMAP_PORT", 993))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.processed_ids_file = "processed_emails.txt"
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        if os.path.exists(self.processed_ids_file):
            with open(self.processed_ids_file, "r") as f:
                return set(line.strip() for line in f)
        return set()

    def _save_processed_id(self, email_id: str):
        with open(self.processed_ids_file, "a") as f:
            f.write(f"{email_id}\n")
        self.processed_ids.add(email_id)

    def _decode_subject(self, subject: str) -> str:
        if not subject:
            return ""
        decoded_parts = decode_header(subject)
        decoded_str = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_str += part.decode(encoding if encoding else "utf-8", errors="replace")
                except (LookupError, UnicodeDecodeError):
                    decoded_str += part.decode("utf-8", errors="replace")
            else:
                decoded_str += str(part)
        return decoded_str.strip()

    def _get_email_body(self, msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode("utf-8", errors="replace")
                    except Exception:
                        continue
                elif content_type == "text/html":
                    try:
                        html = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        text = re.sub(r"<[^>]+>", "", html)
                        return text.strip()
                    except Exception:
                        continue
        else:
            try:
                return msg.get_payload(decode=True).decode("utf-8", errors="replace")
            except Exception:
                return ""
        return ""

    def connect(self) -> Optional[imaplib.IMAP4_SSL]:
        try:
            mail = imaplib.IMAP4_SSL(self.host, self.port)
            mail.login(self.email_address, self.password)
            mail.select("INBOX")
            return mail
        except Exception as e:
            print(f"❌ Ошибка подключения к почте: {e}")
            return None

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print(f"📧 Чтение новых писем из {self.email_address}...")

        mail = self.connect()
        if not mail:
            return {
                "emails": [],
                "email_error": "Не удалось подключиться к почте",
                "current_agent": self.agent_name,
                "next_agent": "FINISH"
            }

        try:
            status, messages = mail.search(None, "UNSEEN")
            if status != "OK":
                print("⚠️ Нет новых писем")
                mail.close()
                mail.logout()
                return {
                    "emails": [],
                    "current_agent": self.agent_name,
                    "next_agent": "FINISH"
                }

            email_ids = messages[0].split()
            print(f"📨 Найдено {len(email_ids)} новых писем")

            if not email_ids:
                mail.close()
                mail.logout()
                return {
                    "emails": [],
                    "current_agent": self.agent_name,
                    "next_agent": "FINISH"
                }

            email_ids = email_ids[:self.max_emails]
            emails = []

            for e_id in email_ids:
                e_id_str = e_id.decode("utf-8")
                if e_id_str in self.processed_ids:
                    continue

                status, msg_data = mail.fetch(e_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = self._decode_subject(msg.get("Subject", ""))
                from_addr = msg.get("From", "")
                date = msg.get("Date", "")

                body = self._get_email_body(msg)

                email_data = {
                    "id": e_id_str,
                    "from": from_addr,
                    "subject": subject,
                    "date": date,
                    "body": body,
                }
                emails.append(email_data)
                self._save_processed_id(e_id_str)

            mail.close()
            mail.logout()

            print(f"✅ Обработано {len(emails)} писем")
            return {
                "emails": emails,
                "current_agent": self.agent_name,
                "next_agent": "ClassifyIntentAgent" if emails else "FINISH"
            }

        except Exception as e:
            print(f"❌ Ошибка при чтении писем: {e}")
            mail.close()
            mail.logout()
            return {
                "emails": [],
                "email_error": str(e),
                "current_agent": self.agent_name,
                "next_agent": "FINISH"
            }


class SendEmailAgent(BaseAgent):
    """
    Агент для отправки ответов через Яндекс.Почту (SMTP).
    """

    def __init__(self, **kwargs):
        super().__init__(require_llm=False, **kwargs)
        self.host = os.getenv("EMAIL_SMTP_HOST", "smtp.yandex.ru")
        self.port = int(os.getenv("EMAIL_SMTP_PORT", 465))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.password = os.getenv("EMAIL_PASSWORD")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("📤 Отправка ответа...")

        to_addr = state.get("email_from")
        subject = state.get("email_subject", "Ответ на ваше обращение")
        reply_body = state.get("final_answer")

        if not to_addr:
            print("⚠️ Нет адреса для отправки")
            return {
                "send_status": "no_recipient",
                "current_agent": self.agent_name,
                "next_agent": "FINISH"
            }

        if not reply_body:
            print("⚠️ Нет текста ответа")
            return {
                "send_status": "no_content",
                "current_agent": self.agent_name,
                "next_agent": "FINISH"
            }

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_addr
            msg["Subject"] = f"Re: {subject}"

            msg.attach(MIMEText(reply_body, "plain", "utf-8"))

            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.email_address, self.password)
                server.sendmail(self.email_address, to_addr, msg.as_string())

            print(f"✅ Ответ отправлен на {to_addr}")
            return {
                "send_status": "success",
                "current_agent": self.agent_name,
                "next_agent": "FINISH"
            }

        except Exception as e:
            print(f"❌ Ошибка отправки письма: {e}")
            return {
                "send_status": f"error: {str(e)}",
                "current_agent": self.agent_name,
                "next_agent": "FINISH"
            }
