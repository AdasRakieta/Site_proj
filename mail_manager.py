# mail_manager.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import socket
import json
import time
from dotenv import load_dotenv
from cryptography.fernet import Fernet

NOTIFICATIONS_SETTINGS_PATH = "notifications_settings.json"
ENCRYPTED_RECIPIENTS_PATH = "notification_recipients.enc"
FERNET_KEY_PATH = "notification_recipients.key"

# Ładuje zmienne z email_conf.env (ścieżka względna/bezwzględna)
load_dotenv('email_conf.env')  # Jeśli plik jest w głównym folderze

def get_fernet():
    if not os.path.exists(FERNET_KEY_PATH):
        key = Fernet.generate_key()
        with open(FERNET_KEY_PATH, "wb") as f:
            f.write(key)
    else:
        with open(FERNET_KEY_PATH, "rb") as f:
            key = f.read()
    return Fernet(key)

def get_notifications_settings():
    settings = {"recipients": []}
    if os.path.exists(NOTIFICATIONS_SETTINGS_PATH):
        try:
            with open(NOTIFICATIONS_SETTINGS_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    pass  # ignoruj pole enabled
        except Exception as e:
            print(f"[NOTIFY] Błąd odczytu settings.json: {e}")
    recipients = []
    if os.path.exists(ENCRYPTED_RECIPIENTS_PATH):
        try:
            fernet = get_fernet()
            with open(ENCRYPTED_RECIPIENTS_PATH, "rb") as f:
                encrypted = f.read()
                if encrypted:
                    decrypted = fernet.decrypt(encrypted).decode("utf-8")
                    loaded_recipients = json.loads(decrypted)
                    if isinstance(loaded_recipients, list):
                        recipients = loaded_recipients
        except Exception as e:
            print(f"[NOTIFY] Błąd odczytu odbiorców: {e}")
    settings["recipients"] = recipients
    return settings

def set_notifications_settings(settings):
    recipients = settings.get("recipients", [])
    try:
        with open(NOTIFICATIONS_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[NOTIFY] Błąd zapisu settings.json: {e}")
    try:
        fernet = get_fernet()
        encrypted = fernet.encrypt(json.dumps(recipients, ensure_ascii=False).encode("utf-8"))
        with open(ENCRYPTED_RECIPIENTS_PATH, "wb") as f:
            f.write(encrypted)
    except Exception as e:
        print(f"[NOTIFY] Błąd zapisu odbiorców: {e}")

class MailManager:
    def __init__(self):
        self.failed_attempts = {}
        self.smtp_config = {
            'server': os.getenv('SMTP_SERVER'),       # np. smtp.gmail.com
            'port': os.getenv('SMTP_PORT'),      # np. 587
            'username': os.getenv('SMTP_USERNAME'),   # np. twój@gmail.com
            'password': os.getenv('SMTP_PASSWORD')    # hasło SMTP
        }
        self.attempts_expiry = 3600
        self.config = {
            'sender_email': os.getenv('SMTP_USERNAME'),
            'admin_email': os.getenv('ADMIN_EMAIL')
        }

    def send_security_alert(self, event_type, details):
        """Wysyła alert przez SMTP do admina i dodatkowych odbiorców"""
        try:
            # Przygotowanie wiadomości
            message = MIMEMultipart()
            message['From'] = self.config['sender_email']
            message['Subject'] = self._prepare_subject(event_type)
            html = self._prepare_body(event_type, details)
            message.attach(MIMEText(html, 'html'))

            # Pobierz ustawienia powiadomień
            settings = get_notifications_settings()
            recipients = set()
            # Admin zawsze
            if self.config['admin_email']:
                recipients.add(self.config['admin_email'])
            # Dodatkowi odbiorcy tylko jeśli mają enabled==True
            for r in settings.get('recipients', []):
                if r.get('email') and (r.get('enabled', True)):
                    print(f"[MAIL DEBUG] Dodano odbiorcę: {r['email']} (enabled={r.get('enabled', True)})")
                    recipients.add(r['email'])
            print(f"[MAIL DEBUG] Lista wszystkich odbiorców maila: {recipients}")
            if not recipients:
                print("Brak odbiorców powiadomień!")
                return False

            # Wysyłka do wszystkich odbiorców
            for email in recipients:
                print(f"[MAIL DEBUG] Przygotowuję e-mail do: {email}")
                # Tworzymy nowy obiekt wiadomości dla każdego odbiorcy, aby nie duplikować nagłówków
                msg = MIMEMultipart()
                msg['From'] = self.config['sender_email']
                msg['To'] = email
                msg['Subject'] = message['Subject']
                for part in message.get_payload():
                    msg.attach(part)
                with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                    server.starttls()
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                    print(f"[MAIL DEBUG] Wysyłam e-mail do: {email}")
                    server.sendmail(self.config['sender_email'], email, msg.as_string())
                    print(f"Wysłano e-mail na {email}")
            print("[MAIL DEBUG] Wysyłka zakończona.")
            return True
        except smtplib.SMTPAuthenticationError:
            print("Błąd autentykacji SMTP - sprawdź login i hasło")
        except Exception as e:
            print(f"Błąd wysyłania e-maila: {str(e)}")
        return False

    def _prepare_subject(self, event_type):
        """Generuje temat wiadomości"""
        subjects = {
            'failed_login': '⚠️ SmartHome - Nieudana próba logowania',
            'security_alert': '⚠️ SmartHome - Alert bezpieczeństwa',
            'automation_notification': 'ℹ️ SmartHome - Powiadomienie automatyzacji'
        }
        return subjects.get(event_type, 'SmartHome - Powiadomienie')

    def _prepare_body(self, event_type, details):
        """Generuje treść wiadomości HTML"""
        hostname = socket.gethostname()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if event_type == 'failed_login':
            return f"""
            <h2>Nieudana próba logowania</h2>
            <p><strong>System:</strong> {hostname}</p>
            <p><strong>Data:</strong> {timestamp}</p>
            <p><strong>Próba wejścia na użytkownika:</strong> {details.get('username', 'nieznany')}</p>
            <p><strong>IP:</strong> {details.get('ip_address', 'nieznane')}</p>
            <p><strong>Próby:</strong> {details.get('attempt_count', 0)}</p>
            """
        elif event_type == 'automation_notification':
            return f"""
            <h2>Powiadomienie automatyzacji</h2>
            <p><strong>Treść:</strong> {details.get('message', 'brak')}</p>
            """
        else:
            return f"""
            <h2>Zdarzenie bezpieczeństwa</h2>
            <p><strong>Typ:</strong> {event_type}</p>
            <p><strong>Data:</strong> {timestamp}</p>
            <p><strong>Szczegóły:</strong> {details.get('message', 'brak')}</p>
            """

    def track_and_alert_failed_login(self, username, ip_address):
        """Śledzi próby logowania i wysyła alerty z uwzględnieniem czasu"""
        now = time.time()
        
        # Inicjalizacja lub czyszczenie starych prób
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = {
                'count': 0,
                'usernames': set(),
                'last_attempt': now
            }
        else:
            # Resetuj licznik jeśli ostatnia próba była dawno temu
            if now - self.failed_attempts[ip_address]['last_attempt'] > self.attempts_expiry:
                self.failed_attempts[ip_address] = {
                    'count': 0,
                    'usernames': set(),
                    'last_attempt': now
                }
        
        # Aktualizacja danych
        self.failed_attempts[ip_address]['count'] += 1
        self.failed_attempts[ip_address]['usernames'].add(username or 'unknown')
        self.failed_attempts[ip_address]['last_attempt'] = now
        
        # Weryfikacja czy wysłać alert
        if self.failed_attempts[ip_address]['count'] >= 3:
            details = {
                'username': username,
                'ip_address': ip_address,
                'attempt_count': self.failed_attempts[ip_address]['count'],
                'time_since_first_attempt': now - self.failed_attempts[ip_address]['last_attempt']
            }
            return self.send_security_alert('failed_login', details)
        return False