"""
Модуль для отправки email поздравлений.
Поддерживает реальную отправку через SMTP и симуляцию для разработки.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
from pathlib import Path

from src.core.config import settings

# Настройка логирования
logger = logging.getLogger(__name__)


class EmailSender:
    """Класс для отправки email поздравлений."""
    
    def __init__(self):
        """Инициализация отправителя."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        
        # Проверяем конфигурацию
        self.is_configured = all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password
        ])
        
        if not self.is_configured:
            logger.warning(
                "SMTP не настроен. Email будут симулироваться. "
                "Настройте SMTP_HOST, SMTP_USER, SMTP_PASSWORD в .env"
            )
    
    def send_congratulation(
        self,
        to_email: str,
        client_name: str,
        text: str,
        subject: Optional[str] = None,
        event_type: str = "birthday",
        attach_image: Optional[bytes] = None,
        image_filename: str = "congratulation.jpg"
    ) -> Dict[str, Any]:
        """
        Отправить поздравление по email.
        
        Args:
            to_email: Email получателя
            client_name: Имя клиента
            text: Текст поздравления
            subject: Тема письма (если None, будет сгенерирована)
            event_type: Тип события (birthday, holiday, professional)
            attach_image: Байты изображения для прикрепления (опционально)
            image_filename: Имя файла изображения
            
        Returns:
            Результат отправки
        """
        # Генерируем тему письма
        if subject is None:
            if event_type == "birthday":
                subject = f"С Днём рождения, {client_name}!"
            elif event_type == "professional":
                subject = f"С профессиональным праздником, {client_name}!"
            else:
                subject = f"Поздравляем, {client_name}!"
        
        # Ограничиваем длину темы
        if len(subject) > 78:  # RFC 2822 рекомендует не более 78 символов
            subject = subject[:75] + "..."
        
        # Создаем HTML версию письма
        html_content = self._create_html_email(client_name, text, event_type)
        
        # Отправляем или симулируем
        if self.is_configured and not settings.DEBUG:
            result = self._send_real_email(to_email, subject, html_content, text, attach_image, image_filename)
        else:
            result = self._simulate_email(to_email, subject, html_content, text)
        
        # Логируем результат
        if result["status"] == "sent":
            logger.info(f"Email отправлен: {to_email} (id: {result.get('message_id', 'N/A')})")
        else:
            logger.warning(f"Email не отправлен: {to_email} - {result.get('error', 'Unknown error')}")
        
        return result
    
    def _create_html_email(self, client_name: str, text: str, event_type: str) -> str:
        """
        Создает HTML версию письма.
        
        Args:
            client_name: Имя клиента
            text: Текст поздравления
            event_type: Тип события
            
        Returns:
            HTML контент
        """
        # Определяем заголовок в зависимости от типа события
        if event_type == "birthday":
            header = "🎉 С Днём рождения!"
            icon = "🎂"
        elif event_type == "professional":
            header = "🏆 С профессиональным праздником!"
            icon = "🏅"
        else:
            header = "🎊 Поздравляем!"
            icon = "🎁"
        
        # Создаем HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{header}</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #1a6dcc, #4a9eff);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 15px;
                }}
                .content {{
                    padding: 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 20px;
                    color: #555;
                    white-space: pre-line;
                }}
                .client-name {{
                    color: #1a6dcc;
                    font-weight: bold;
                }}
                .footer {{
                    background-color: #f1f5f9;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }}
                .logo {{
                    color: #1a6dcc;
                    font-weight: bold;
                    font-size: 18px;
                }}
                .signature {{
                    margin-top: 30px;
                    border-top: 1px solid #e0e0e0;
                    padding-top: 20px;
                    color: #777;
                }}
                @media only screen and (max-width: 600px) {{
                    .container {{
                        border-radius: 0;
                    }}
                    .content {{
                        padding: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">{icon}</div>
                    <h1>{header}</h1>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        {text.replace(chr(10), '<br>')}
                    </div>
                    
                    <div class="signature">
                        <p>С уважением,<br>
                        <span class="logo">Команда Сбербанка</span></p>
                        
                        <p style="font-size: 12px; color: #999; margin-top: 20px;">
                            Это письмо было сгенерировано автоматически. 
                            Пожалуйста, не отвечайте на него.<br>
                            Если у вас есть вопросы, обратитесь в службу поддержки.
                        </p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>© {datetime.now().year} Сбербанк. Все права защищены.</p>
                    <p style="font-size: 12px; color: #888;">
                        Вы получили это письмо, потому что являетесь клиентом Сбера.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_real_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        attach_image: Optional[bytes] = None,
        image_filename: str = "congratulation.jpg"
    ) -> Dict[str, Any]:
        """
        Реальная отправка email через SMTP.
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            html_content: HTML версия
            text_content: Текстовая версия
            attach_image: Байты изображения
            image_filename: Имя файла изображения
            
        Returns:
            Результат отправки
        """
        try:
            # Создаем сообщение
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = to_email
            msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Добавляем текстовую версию
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            
            # Добавляем HTML версию
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # Добавляем изображение, если есть
            if attach_image:
                image_part = MIMEImage(attach_image)
                image_part.add_header("Content-Disposition", f"attachment; filename={image_filename}")
                image_part.add_header("Content-ID", "<congratulation_image>")
                msg.attach(image_part)
            
            # Создаем безопасное соединение
            context = ssl.create_default_context()
            
            # Подключаемся к SMTP серверу и отправляем
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return {
                "status": "sent",
                "to": to_email,
                "message": "Email успешно отправлен",
                "timestamp": datetime.now().isoformat(),
                "method": "smtp",
                "message_id": f"{datetime.now().timestamp()}-{to_email}"
            }
            
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")
            
            # Fallback: симуляция
            return self._simulate_email(to_email, subject, html_content, text_content, error=str(e))
    
    def _simulate_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Симуляция отправки email (для разработки).
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            html_content: HTML версия
            text_content: Текстовая версия
            error: Сообщение об ошибке (если было)
            
        Returns:
            Результат симуляции
        """
        # Сохраняем в лог или файл для отладки
        log_dir = Path("logs/emails")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"simulated_{timestamp}_{to_email.replace('@', '_at_')}.html"
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"<!-- Subject: {subject} -->\n")
            f.write(f"<!-- To: {to_email} -->\n")
            f.write(f"<!-- Timestamp: {datetime.now().isoformat()} -->\n")
            if error:
                f.write(f"<!-- Error: {error} -->\n")
            f.write(html_content)
        
        logger.info(f"Email симулирован: {to_email} -> {log_file}")
        
        return {
            "status": "simulated",
            "to": to_email,
            "message": f"Email симулирован (режим разработки). Сохранен в {log_file}",
            "timestamp": datetime.now().isoformat(),
            "method": "simulation",
            "log_file": str(log_file),
            "error": error
        }
    
    def send_bulk(
        self,
        recipients: List[Tuple[str, str, str]],
        event_type: str = "birthday"
    ) -> List[Dict[str, Any]]:
        """
        Массовая отправка поздравлений.
        
        Args:
            recipients: Список кортежей (email, client_name, text)
            event_type: Тип события
            
        Returns:
            Список результатов
        """
        results = []
        
        for to_email, client_name, text in recipients:
            try:
                result = self.send_congratulation(
                    to_email=to_email,
                    client_name=client_name,
                    text=text,
                    event_type=event_type
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "to": to_email,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Тестирование подключения к SMTP серверу.
        
        Returns:
            Результат теста
        """
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "SMTP не настроен. Проверьте настройки в .env",
                "configured": False
            }
        
        try:
            # Пробуем подключиться
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                # Просто проверяем подключение
                server.noop()
            
            return {
                "status": "success",
                "message": "Подключение к SMTP успешно",
                "configured": True,
                "host": self.smtp_host,
                "port": self.smtp_port,
                "user": self.smtp_user[:3] + "..." if self.smtp_user else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}",
                "configured": True,
                "error": str(e)
            }


# Синглтон для удобного использования
_email_sender_instance = None

def get_email_sender() -> EmailSender:
    """
    Получить экземпляр отправителя email.
    
    Returns:
        Экземпляр EmailSender
    """
    global _email_sender_instance
    
    if _email_sender_instance is None:
        _email_sender_instance = EmailSender()
    
    return _email_sender_instance


if __name__ == "__main__":
    """Тестирование модуля отправки email."""
    print("🧪 Тестирование модуля отправки email...")
    
    sender = EmailSender()
    
    # Тестируем подключение
    print("1. Тестируем подключение к SMTP:")
    connection_test = sender.test_connection()
    print(f"   Статус: {connection_test['status']}")
    print(f"   Сообщение: {connection_test['message']}")
    
    # Тестируем отправку
    print("\n2. Тестируем отправку email:")
    test_result = sender.send_congratulation(
        to_email="test@example.com",
        client_name="Иван Иванов",
        text="Тестовое поздравление для проверки работы системы.",
        subject="Тестовое письмо от Sber Congratulations Agent"
    )
    
    print(f"   Статус: {test_result['status']}")
    print(f"   Метод: {test_result['method']}")
    print(f"   Сообщение: {test_result['message']}")
    
    if test_result['status'] == 'simulated':
        print(f"   Файл: {test_result.get('log_file', 'N/A')}")
    
    print("\n✅ Тест завершен")