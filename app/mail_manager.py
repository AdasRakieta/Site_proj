# mail_manager.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import socket


# Nowa obsługa powiadomień i odbiorców przez bazę danych
import random
import string
import time
from utils.db_manager import (
    get_notification_settings,
    set_notification_settings,
    get_notification_recipients,
    set_notification_recipients
)

def get_notifications_settings(home_id=None):
    """
    Zwraca słownik z kluczem 'recipients' (lista odbiorców) oraz innymi ustawieniami z bazy.
    """
    settings = get_notification_settings(home_id)
    recipients = get_notification_recipients(home_id)
    return {"recipients": recipients, **settings}

def set_notifications_settings(settings, home_id=None):
    """
    Zapisuje ustawienia i odbiorców do bazy.
    """
    recipients = settings.get("recipients", [])
    set_notification_recipients(recipients, home_id)
    # Pozostałe ustawienia (jeśli są)
    other_settings = {k: v for k, v in settings.items() if k != "recipients"}
    if other_settings:
        set_notification_settings(other_settings, home_id)

class MailManager:
    def __init__(self):
        self.failed_attempts = {}
        self.verification_codes = {}  # Store verification codes: {email: {'code': str, 'expires': timestamp, 'attempts': int}}
        self.password_reset_codes = {}  # Store password reset codes: {email: {'code': str, 'expires': timestamp, 'attempts': int, 'user_id': str}}
        # Wymuś obecność wszystkich danych SMTP
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        # Port musi być liczbą
        try:
            smtp_port = int(smtp_port) if smtp_port else None
        except Exception:
            smtp_port = None
        self.smtp_config = {
            'server': smtp_server,
            'port': smtp_port,
            'username': smtp_username,
            'password': smtp_password
        }
        self.attempts_expiry = 3600
        self.verification_expiry = 900  # 15 minut na weryfikację
        self.max_verification_attempts = 3
        self.config = {
            'sender_email': smtp_username,
            'admin_email': os.getenv('ADMIN_EMAIL')
        }

    def generate_verification_code(self):
        """Generuje 6-cyfrowy kod weryfikacyjny"""
        return ''.join(random.choices(string.digits, k=6))
    
    def store_verification_code(self, email, code):
        """Przechowuje kod weryfikacyjny dla danego emaila"""
        self.verification_codes[email] = {
            'code': code,
            'expires': time.time() + self.verification_expiry,
            'attempts': 0
        }
    
    def store_password_reset_code(self, email, code, user_id):
        """Przechowuje kod resetowania hasła dla danego emaila"""
        self.password_reset_codes[email] = {
            'code': code,
            'expires': time.time() + self.verification_expiry,
            'attempts': 0,
            'user_id': user_id
        }
    
    def verify_password_reset_code(self, email, code):
        """Weryfikuje kod resetowania hasła dla danego emaila"""
        if email not in self.password_reset_codes:
            return False, "Kod resetowania hasła nie istnieje lub wygasł", None
        
        stored_data = self.password_reset_codes[email]
        
        # Sprawdź czy kod nie wygasł
        if time.time() > stored_data['expires']:
            del self.password_reset_codes[email]
            return False, "Kod resetowania hasła wygasł", None
        
        # Sprawdź liczbę prób
        if stored_data['attempts'] >= self.max_verification_attempts:
            del self.password_reset_codes[email]
            return False, "Przekroczono maksymalną liczbę prób weryfikacji", None
        
        # Zwiększ liczbę prób
        stored_data['attempts'] += 1
        
        # Sprawdź poprawność kodu
        if stored_data['code'] != code:
            return False, "Nieprawidłowy kod resetowania hasła", None
        
        # Kod poprawny - pobierz user_id i usuń z pamięci
        user_id = stored_data['user_id']
        del self.password_reset_codes[email]
        return True, "Kod resetowania hasła poprawny", user_id
    
    def verify_code(self, email, code):
        """Weryfikuje kod dla danego emaila"""
        if email not in self.verification_codes:
            return False, "Kod weryfikacyjny nie istnieje lub wygasł"
        
        stored_data = self.verification_codes[email]
        
        # Sprawdź czy kod nie wygasł
        if time.time() > stored_data['expires']:
            del self.verification_codes[email]
            return False, "Kod weryfikacyjny wygasł"
        
        # Sprawdź liczbę prób
        if stored_data['attempts'] >= self.max_verification_attempts:
            del self.verification_codes[email]
            return False, "Przekroczono maksymalną liczbę prób weryfikacji"
        
        # Zwiększ liczbę prób
        stored_data['attempts'] += 1
        
        # Sprawdź poprawność kodu
        if stored_data['code'] != code:
            return False, "Nieprawidłowy kod weryfikacyjny"
        
        # Kod poprawny - usuń z pamięci
        del self.verification_codes[email]
        return True, "Kod weryfikacyjny poprawny"
    
    def send_verification_email(self, email: str, code: str):
        """Wysyła email z kodem weryfikacyjnym"""
        email = email or ""
        code = code or ""
        try:
            # Sprawdź czy mamy pełną konfigurację SMTP
            smtp = self.smtp_config
            if not (smtp.get('server') and smtp.get('port') and smtp.get('username') and smtp.get('password')):
                print(f"[VERIFICATION] TEST MODE: Kod weryfikacyjny dla {email}: {code}")
                print("[VERIFICATION] Brak pełnej konfiguracji SMTP. Uzupełnij SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD w pliku email_conf.env")
                return False

            message = MIMEMultipart()
            message['From'] = self.config['sender_email'] or ""
            message['To'] = email
            message['Subject'] = '🔐 SmartHome - Kod weryfikacyjny rejestracji'

            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Weryfikacja adresu email</h2>
                <p>Witaj!</p>
                <p>Aby ukończyć rejestrację w systemie SmartHome, wprowadź poniższy kod weryfikacyjny:</p>
                <div style="background-color: #ecf0f1; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                    <h1 style="color: #2c3e50; font-size: 32px; margin: 0; letter-spacing: 8px;">{code}</h1>
                </div>
                <p><strong>Uwaga:</strong></p>
                <ul>
                    <li>Kod jest ważny przez 15 minut</li>
                    <li>Masz maksymalnie 3 próby wprowadzenia kodu</li>
                    <li>Jeśli nie prosiłeś o rejestrację, zignoruj tę wiadomość</li>
                </ul>
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 40px;">
                    Wiadomość wysłana automatycznie z systemu SmartHome<br>
                    Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
            """

            message.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(smtp['server'], smtp['port']) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp['username'], smtp['password'])
                server.sendmail(self.config['sender_email'] or "", email, message.as_string())

            print(f"[VERIFICATION] Wysłano kod weryfikacyjny na {email}")
            return True
        except smtplib.SMTPAuthenticationError:
            print("[VERIFICATION] Błąd autentykacji SMTP - sprawdź login i hasło SMTP w email_conf.env")
            return False
        except Exception as e:
            print(f"[VERIFICATION] Błąd wysyłania kodu na {email}: {str(e)}")
            return False

    def send_password_reset_email(self, email: str, code: str):
        """Wysyła email z kodem resetowania hasła"""
        email = email or ""
        code = code or ""
        try:
            # Sprawdź czy mamy pełną konfigurację SMTP
            smtp = self.smtp_config
            if not (smtp.get('server') and smtp.get('port') and smtp.get('username') and smtp.get('password')):
                print(f"[PASSWORD_RESET] TEST MODE: Kod resetowania hasła dla {email}: {code}")
                print("[PASSWORD_RESET] Brak pełnej konfiguracji SMTP. Uzupełnij SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD w pliku email_conf.env")
                return False

            message = MIMEMultipart()
            message['From'] = self.config['sender_email'] or ""
            message['To'] = email
            message['Subject'] = '🔑 SmartHome - Resetowanie hasła'

            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Resetowanie hasła</h2>
                <p>Witaj!</p>
                <p>Otrzymałeś tę wiadomość, ponieważ złożono prośbę o zresetowanie hasła do Twojego konta SmartHome.</p>
                <p>Aby zresetować hasło, wprowadź poniższy kod weryfikacyjny:</p>
                <div style="background-color: #ecf0f1; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                    <h1 style="color: #2c3e50; font-size: 32px; margin: 0; letter-spacing: 8px;">{code}</h1>
                </div>
                <p><strong>Uwaga:</strong></p>
                <ul>
                    <li>Kod jest ważny przez 15 minut</li>
                    <li>Masz maksymalnie 3 próby wprowadzenia kodu</li>
                    <li>Jeśli nie prosiłeś o reset hasła, zignoruj tę wiadomość</li>
                    <li>Twoje hasło nie zostanie zmienione dopóki nie wprowadzisz prawidłowego kodu</li>
                </ul>
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 40px;">
                    Wiadomość wysłana automatycznie z systemu SmartHome<br>
                    Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
            """

            message.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(smtp['server'], smtp['port']) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp['username'], smtp['password'])
                server.sendmail(self.config['sender_email'] or "", email, message.as_string())

            print(f"[PASSWORD_RESET] Wysłano kod resetowania hasła na {email}")
            return True
        except smtplib.SMTPAuthenticationError:
            print("[PASSWORD_RESET] Błąd autentykacji SMTP - sprawdź login i hasło SMTP w email_conf.env")
            return False
        except socket.gaierror as e:
            print(f"[PASSWORD_RESET] Błąd połączenia z serwerem SMTP - sprawdź połączenie internetowe i ustawienia serwera: {str(e)}")
            return False
        except ConnectionRefusedError as e:
            print(f"[PASSWORD_RESET] Odmowa połączenia z serwerem SMTP - sprawdź port i ustawienia: {str(e)}")
            return False
        except Exception as e:
            print(f"[PASSWORD_RESET] Błąd wysyłania kodu na {email}: {str(e)}")
            return False
    def send_security_alert(self, event_type: str, details: str):
        """Wysyła alert przez SMTP do admina i dodatkowych odbiorców"""
        event_type = event_type or ""
        details = details or ""
        try:
            # Przygotowanie wiadomości
            message = MIMEMultipart()
            message['From'] = self.config['sender_email'] or ""
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
                msg['From'] = self.config['sender_email'] or ""
                msg['To'] = email
                msg['Subject'] = message['Subject']
                for part in message.get_payload():
                    msg.attach(part)
                with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                    server.starttls()
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                    print(f"[MAIL DEBUG] Wysyłam e-mail do: {email}")
                    server.sendmail(self.config['sender_email'] or "", email, msg.as_string())
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
            return self.send_security_alert('failed_login', str(details))
        return False

    def send_invitation_email(self, email: str, invitation_code: str, home_name: str, 
                             inviter_name: str, role: str, base_url: str = "http://localhost:5000"):
        """Wysyła email z zaproszeniem do domu"""
        email = email or ""
        try:
            # Sprawdź czy mamy pełną konfigurację SMTP
            smtp = self.smtp_config
            if not (smtp.get('server') and smtp.get('port') and smtp.get('username') and smtp.get('password')):
                print(f"[INVITATION] TEST MODE: Kod zaproszenia dla {email}: {invitation_code}")
                print(f"[INVITATION] Link: {base_url}/invite/accept?code={invitation_code}")
                print("[INVITATION] Brak pełnej konfiguracji SMTP. Uzupełnij SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD w pliku email_conf.env")
                return False

            message = MIMEMultipart()
            message['From'] = self.config['sender_email'] or ""
            message['To'] = email
            message['Subject'] = f'🏠 SmartHome - Zaproszenie do domu "{home_name}"'

            role_names = {
                'admin': 'Administrator',
                'member': 'Członek',
                'guest': 'Gość'
            }
            role_display = role_names.get(role, role)

            accept_link = f"{base_url}/invite/accept?code={invitation_code}"

            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
                <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #2c3e50; text-align: center; margin-bottom: 30px;">🏠 Zaproszenie do SmartHome</h2>
                    
                    <p style="font-size: 16px; color: #333;">Witaj!</p>
                    
                    <p style="font-size: 16px; color: #333;">
                        <strong>{inviter_name}</strong> zaprasza Cię do dołączenia do domu 
                        <strong>"{home_name}"</strong> w systemie SmartHome.
                    </p>
                    
                    <div style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                        <p style="margin: 0; color: #2c3e50;">
                            <strong>Rola:</strong> {role_display}
                        </p>
                    </div>

                    <h3 style="color: #2c3e50; margin-top: 30px;">Jak zaakceptować zaproszenie?</h3>
                    
                    <div style="margin: 20px 0;">
                        <p style="color: #555;"><strong>Opcja 1:</strong> Kliknij w poniższy przycisk</p>
                        <div style="text-align: center; margin: 20px 0;">
                            <a href="{accept_link}" 
                               style="display: inline-block; padding: 15px 30px; background-color: #3498db; color: white; 
                                      text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                                Zaakceptuj zaproszenie
                            </a>
                        </div>
                    </div>

                    <div style="margin: 20px 0;">
                        <p style="color: #555;"><strong>Opcja 2:</strong> Użyj kodu zaproszenia</p>
                        <div style="background-color: #ecf0f1; padding: 20px; text-align: center; border-radius: 5px;">
                            <p style="margin: 0 0 10px 0; color: #7f8c8d; font-size: 14px;">Kod zaproszenia:</p>
                            <h1 style="color: #2c3e50; font-size: 32px; margin: 0; letter-spacing: 4px; font-family: 'Courier New', monospace;">
                                {invitation_code}
                            </h1>
                        </div>
                        <p style="color: #777; font-size: 14px; margin-top: 10px;">
                            Wpisz ten kod na stronie: <a href="{base_url}/invite/accept" style="color: #3498db;">{base_url}/invite/accept</a>
                        </p>
                    </div>

                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 30px 0;">
                        <p style="margin: 0; color: #856404; font-size: 14px;">
                            <strong>⚠️ Ważne informacje:</strong>
                        </p>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #856404; font-size: 14px;">
                            <li>Zaproszenie jest ważne przez 7 dni</li>
                            <li>Musisz zalogować się lub zarejestrować tym samym adresem email</li>
                            <li>Jeśli nie prosiłeś o to zaproszenie, zignoruj tę wiadomość</li>
                        </ul>
                    </div>

                    <p style="color: #7f8c8d; font-size: 12px; margin-top: 40px; text-align: center;">
                        Wiadomość wysłana automatycznie z systemu SmartHome<br>
                        Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>
            """

            message.attach(MIMEText(html, 'html'))

            print(f"[INVITATION] Próba wysłania zaproszenia na {email}")
            print(f"[INVITATION] SMTP Server: {smtp['server']}:{smtp['port']}")
            print(f"[INVITATION] SMTP User: {smtp['username']}")
            
            with smtplib.SMTP(smtp['server'], smtp['port']) as server:
                server.ehlo()
                print("[INVITATION] EHLO successful")
                server.starttls()
                print("[INVITATION] STARTTLS successful")
                server.ehlo()
                server.login(smtp['username'], smtp['password'])
                print("[INVITATION] Login successful")
                server.sendmail(self.config['sender_email'] or "", email, message.as_string())
                print(f"[INVITATION] ✓ Wysłano zaproszenie na {email} (kod: {invitation_code})")

            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"[INVITATION] ✗ Błąd autentykacji SMTP: {str(e)}")
            print("[INVITATION] Sprawdź SMTP_USERNAME i SMTP_PASSWORD w pliku .env")
            return False
        except smtplib.SMTPException as e:
            print(f"[INVITATION] ✗ Błąd SMTP: {str(e)}")
            return False
        except Exception as e:
            print(f"[INVITATION] ✗ Błąd wysyłania zaproszenia na {email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def send_bug_report_email(self, reporter_email: str, reporter_name: str, 
                             bug_title: str, bug_description: str, 
                             user_agent: str = "", url: str = ""):
        """Wysyła email z raportem błędu do administratora systemu"""
        try:
            # Sprawdź czy mamy pełną konfigurację SMTP
            smtp = self.smtp_config
            if not (smtp.get('server') and smtp.get('port') and smtp.get('username') and smtp.get('password')):
                print(f"[BUG_REPORT] TEST MODE: Raport błędu od {reporter_email}")
                print(f"[BUG_REPORT] Tytuł: {bug_title}")
                print(f"[BUG_REPORT] Opis: {bug_description}")
                print("[BUG_REPORT] Brak pełnej konfiguracji SMTP. Uzupełnij SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD w pliku .env")
                return False

            admin_email = self.config.get('admin_email')
            if not admin_email:
                print("[BUG_REPORT] ADMIN_EMAIL nie jest skonfigurowany w .env")
                return False

            # HTML-escape all user inputs to prevent XSS
            import html
            bug_title_escaped = html.escape(bug_title)
            bug_description_escaped = html.escape(bug_description)
            reporter_name_escaped = html.escape(reporter_name)
            reporter_email_escaped = html.escape(reporter_email)
            url_escaped = html.escape(url) if url else ''
            user_agent_escaped = html.escape(user_agent) if user_agent else ''

            message = MIMEMultipart()
            message['From'] = self.config['sender_email'] or ""
            message['To'] = admin_email
            message['Subject'] = f'🐛 SmartHome - Zgłoszenie błędu: {bug_title_escaped}'
            message['Reply-To'] = reporter_email

            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
                <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #e74c3c; text-align: center; margin-bottom: 30px;">🐛 Nowe zgłoszenie błędu</h2>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #f39c12; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: #856404;">Tytuł zgłoszenia</h3>
                        <p style="margin: 0; color: #333; font-size: 16px; font-weight: 600;">{bug_title_escaped}</p>
                    </div>

                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Opis problemu</h3>
                        <p style="color: #333; line-height: 1.6; white-space: pre-wrap;">{bug_description_escaped}</p>
                    </div>

                    <div style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Informacje o zgłaszającym</h3>
                        <p style="margin: 5px 0; color: #555;"><strong>Imię:</strong> {reporter_name_escaped}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>Email:</strong> <a href="mailto:{reporter_email_escaped}" style="color: #3498db;">{reporter_email_escaped}</a></p>
                    </div>

                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Szczegóły techniczne</h3>
                        <p style="margin: 5px 0; color: #555; font-size: 13px;"><strong>Data zgłoszenia:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        {f'<p style="margin: 5px 0; color: #555; font-size: 13px;"><strong>URL:</strong> {url_escaped}</p>' if url else ''}
                        {f'<p style="margin: 5px 0; color: #555; font-size: 13px;"><strong>Przeglądarka:</strong> {user_agent_escaped}</p>' if user_agent else ''}
                    </div>

                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                        <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                            Wiadomość wysłana automatycznie z systemu zgłaszania błędów SmartHome
                        </p>
                    </div>
                </div>
            </div>
            """

            message.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(smtp['server'], smtp['port']) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp['username'], smtp['password'])
                server.sendmail(self.config['sender_email'] or "", admin_email, message.as_string())

            print(f"[BUG_REPORT] ✓ Wysłano raport błędu na {admin_email}")
            return True
        except smtplib.SMTPAuthenticationError:
            print("[BUG_REPORT] ✗ Błąd autentykacji SMTP - sprawdź login i hasło SMTP w pliku .env")
            return False
        except Exception as e:
            print(f"[BUG_REPORT] ✗ Błąd wysyłania raportu błędu: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
