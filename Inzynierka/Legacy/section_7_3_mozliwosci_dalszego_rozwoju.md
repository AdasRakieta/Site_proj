## 7.3 Możliwości dalszego rozwoju

System SmartHome Multi-Home stanowi solidny fundament nadający się do rozszerzenia o zaawansowane funkcjonalności IoT. Poniżej przedstawiono kierunki dalszego rozwoju wraz z oszacowaniem nakładu pracy oraz oczekiwanych korzyści.

### Integracja fizycznych urządzeń IoT

Obecna implementacja operuje na symulowanych urządzeniach w bazie danych. Pełna funkcjonalność Smart Home wymaga integracji z rzeczywistym hardware poprzez protokoły komunikacyjne używane w branży: MQTT, Zigbee, Z-Wave oraz GPIO Raspberry Pi.

Architektura rozszerzenia zakłada dodanie warstwy Device Drivers w `utils/` (nowy moduł `device_drivers/mqtt_driver.py`, `zigbee_driver.py`, `gpio_driver.py`). Każdy driver implementuje wspólny interfejs:

```py
class DeviceDriver:
    def connect(self, config: dict) -> bool:
        ...
    def send_command(self, device_id: str, command: dict) -> bool:
        ...
    def register_callback(self, device_id: str, callback: Callable) -> None:
        ...
    def disconnect(self) -> None:
        ...
```

MQTT driver wykorzystuje bibliotekę `paho-mqtt` dla komunikacji z brokerami (Mosquitto, HiveMQ). Przykładowa implementacja `send_command` dla przełącznika Sonoff:

```py
def send_command(self, device_id, command):
    topic = f"cmnd/{device_id}/POWER"
    payload = "ON" if command.get('state') else "OFF"
    self.client.publish(topic, payload)
```

Integracja Zigbee wymaga dongle USB (np. ConBee II, Sonoff ZBDongle-E) oraz biblioteki `zigpy`. Z-Wave analogicznie wykorzystuje `python-openzwave`. GPIO na Raspberry Pi 5 obsługiwane jest przez `RPi.GPIO` z konfiguracją BCM pin numbering.

Mechanizm callback propaguje zmiany stanu z urządzeń fizycznych do aplikacji poprzez WebSocket broadcast, zachowując istniejącą architekturę real-time.

Szacowany nakład: 120–160 godzin pracy (40h MQTT + 50h Zigbee + 30h GPIO + 30h testing).

### System zaproszeń użytkowników do gospodarstw

Obecnie administratorzy dodają użytkowników do gospodarstw wyłącznie znając ich `user_id`. Funkcjonalność invite system pozwoliłaby wysyłać zaproszenia emailem z tokenem akceptacyjnym.

Schemat bazy danych zawiera już tabelę `home_invitations` (backups/db_schema_multihouse.sql):

```sql
CREATE TABLE home_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_id UUID REFERENCES homes(id) ON DELETE CASCADE,
    invited_by UUID REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Implementacja wymaga rozszerzenia `HomeUserManager` w `home_management.py` (metoda `invite_user_by_email`). Przykładowy flow:

- wygenerowanie tokena i zapis do DB
- wysłanie maila przez `AsyncMailManager` z linkiem akceptacyjnym
- endpoint `/invite/accept/<token>` weryfikuje token, tworzy konto użytkownika (jeśli nie istnieje) i dodaje do `home_users` z przypisaną rolą

Template `invite_accept.html` już istnieje, czekając na backendową implementację.

Nakład: 25–35 godzin.

### Aplikacja mobilna natywna (iOS/Android)

Interfejs webowy zapewnia responsywność poprzez Bootstrap 5, ale natywna aplikacja mobilna oferowałaby lepsze UX (push notifications, biometric auth, offline mode). Architektura zakłada:

- Backend: REST API rozszerzone o `/api/v2/` endpoints z JSON Web Tokens (PyJWT) zamiast session cookies
- Frontend: Flutter lub React Native współdzielący logikę biznesową
- Push notifications: Firebase Cloud Messaging integrowane z automation triggers

SmartHomeApp już eksponuje potrzebne endpointy (`app/routes.py`, `APIManager`), wymagające jedynie dodania JWT auth middleware.

Szacowany nakład pełnej aplikacji: 200–280 godzin (80h iOS + 80h Android + 60h backend API + 60h testing).

### Rozszerzone automatyzacje z uczeniem maszynowym

Obecny `AutomationExecutor` (`utils/automation_executor.py`) wykonuje reguły if-then statyczne. System można rozszerzyć o predykcyjne automatyzacje uczące się wzorców zachowań użytkowników:

- Czas powrotu do domu → preemptive heating
- Preferred lighting levels → auto-adjust brightness
- Energy optimization → time-series forecasting

Wymagania implementacyjne:
- Kolumna `device_state_history` dla time-series data (JSONB array lub osobna tabela)
- Biblioteka `scikit-learn` 1.3+ dla modeli ML
- Dashboard wizualizacji (Plotly/Chart.js)

Nakład: 150–200 godzin (60h data collection + 50h ML models + 40h UI + 40h validation).

### Integracja z asystentami głosowymi

Sterowanie przez Google Assistant, Amazon Alexa, Apple Siri:

- Google Home: Actions on Google + fulfillment webhook w Flask
- Alexa: Alexa Skills Kit z proxy do API (AWS Lambda)
- Siri: HomeKit HAP-python emulacja urządzeń

Każdy asystent wymaga adaptera mapującego natywne komendy na wywołania SmartHome API.

Szacowany nakład: 80–120 godzin dla pełnej triady.

(Miejsce na Rysunek 7.1: Roadmap rozwoju — timeline Q1–Q4 2026 z planowanymi features: Q1 MQTT/GPIO integration, Q2 Invitation system + Mobile app start, Q3 Mobile app release, Q4 ML automations + Voice assistants)
