# Rozdział 2: Analiza problemu i przegląd istniejących rozwiązań

## 2.1. Definicja inteligentnego domu (Smart Home)

### 2.1.1. Koncepcja Smart Home

Inteligentny dom (ang. Smart Home) to budynek wyposażony w zaawansowane systemy automatyki, które umożliwiają monitorowanie i sterowanie różnymi urządzeniami oraz funkcjami domu za pomocą sieci komputerowej. Podstawową cechą inteligentnego domu jest możliwość:
- **Automatyzacji** - wykonywanie czynności bez interwencji użytkownika
- **Zdalnego sterowania** - kontrola urządzeń z dowolnego miejsca na świecie
- **Monitorowania** - śledzenie stanu urządzeń i parametrów środowiskowych
- **Integracji** - łączenie różnych systemów w spójną całość
- **Uczenia się** - adaptacja do zachowań i preferencji użytkowników

### 2.1.2. Kluczowe obszary funkcjonalne

Smart Home obejmuje następujące główne obszary:

1. **Oświetlenie:**
   - Zdalne włączanie/wyłączanie lamp
   - Regulacja jasności i temperatury barwowej
   - Harmonogramy czasowe
   - Scenariusze świetlne

2. **Klimatyzacja i ogrzewanie:**
   - Kontrola temperatury w poszczególnych pomieszczeniach
   - Programowalne termostaty
   - Integracja z czujnikami obecności
   - Optymalizacja zużycia energii

3. **Bezpieczeństwo:**
   - Systemy alarmowe
   - Monitoring wideo (CCTV)
   - Inteligentne zamki i domofony
   - Czujniki ruchu, dymu, zalania

4. **Multimedia:**
   - Sterowanie sprzętem audio/wideo
   - Multi-room audio
   - Inteligentne telewizory
   - Systemy home cinema

5. **Zarządzanie energią:**
   - Monitoring zużycia energii
   - Inteligentne gniazdka
   - Integracja z panelami solarnymi
   - Zarządzanie szczytowym zużyciem

### 2.1.3. Technologie IoT w Smart Home

Internet Rzeczy (IoT) stanowi fundament nowoczesnych systemów Smart Home. Kluczowe technologie to:

- **Protokoły komunikacji bezprzewodowej:**
  - Wi-Fi (IEEE 802.11)
  - Bluetooth/Bluetooth Low Energy (BLE)
  - Zigbee (IEEE 802.15.4)
  - Z-Wave
  - Thread
  - Matter (nowy standard unifikujący)

- **Protokoły aplikacyjne:**
  - MQTT (Message Queuing Telemetry Transport)
  - CoAP (Constrained Application Protocol)
  - HTTP/HTTPS
  - WebSocket

## 2.2. Przegląd istniejących systemów SmartHome

### 2.2.1. Rozwiązania komercyjne

#### Google Home
**Opis:**
- Ekosystem urządzeń i usług od Google
- Asystent głosowy Google Assistant
- Aplikacja Google Home do zarządzania

**Zalety:**
- ✅ Szeroka kompatybilność z urządzeniami różnych producentów
- ✅ Zaawansowane rozpoznawanie głosu
- ✅ Integracja z usługami Google (Kalendarz, Mapy, YouTube)
- ✅ Łatwa konfiguracja i użytkowanie

**Wady:**
- ❌ Wymaga konta Google i zgody na zbieranie danych
- ❌ Ograniczone możliwości automatyzacji
- ❌ Brak prawdziwej obsługi wielu domów (workaround przez "domy" w strukturze)
- ❌ Wymaga połączenia z chmurą Google

**Obsługa multi-home:** ⭐⭐⚪⚪⚪ (2/5)
- Możliwość tworzenia wielu "domów" w aplikacji
- Brak współdzielenia uprawnień na poziomie domu
- Przełączanie między domami niewygodne

#### Amazon Alexa / Echo
**Opis:**
- Ekosystem Amazon z asystentem głosowym Alexa
- Szeroka gama urządzeń Echo
- Aplikacja Alexa do konfiguracji

**Zalety:**
- ✅ Doskonała integracja z Amazon (zakupy, Prime Video, Music)
- ✅ Skills - rozbudowany ekosystem rozszerzeń
- ✅ Bardzo dobre rozpoznawanie głosu
- ✅ Rutyny (Routines) do automatyzacji

**Wady:**
- ❌ Silne uzależnienie od ekosystemu Amazon
- ❌ Zbieranie danych o użytkownikach
- ❌ Ograniczona obsługa wielu lokalizacji
- ❌ Wymaga chmury Amazon

**Obsługa multi-home:** ⭐⭐⚪⚪⚪ (2/5)
- Grupy urządzeń ale nie prawdziwe "domy"
- Współdzielenie dostępu poprzez Amazon Household (do 2 dorosłych)
- Brak granularnych uprawnień

#### Apple HomeKit
**Opis:**
- Framework Apple do zarządzania Smart Home
- Integracja z iOS, iPadOS, macOS, watchOS
- Aplikacja "Dom" (Home)

**Zalety:**
- ✅ Silny nacisk na prywatność i bezpieczeństwo
- ✅ End-to-end encryption
- ✅ Lokalne przetwarzanie (Hub: Apple TV, HomePod, iPad)
- ✅ Elegancki, spójny interfejs
- ✅ Siri shortcuts

**Wady:**
- ❌ Wymagany ekosystem Apple (iPhone/iPad)
- ❌ Mniejsza liczba kompatybilnych urządzeń
- ❌ Wyższy koszt urządzeń
- ❌ Zamknięty ekosystem

**Obsługa multi-home:** ⭐⭐⭐⭐⚪ (4/5)
- **Najlepsza obsługa multi-home wśród rozwiązań komercyjnych**
- Możliwość tworzenia wielu domów
- Zapraszanie użytkowników z różnymi poziomami uprawnień
- Łatwe przełączanie między domami
- Ograniczenie: wymaga ekosystemu Apple

#### Samsung SmartThings
**Opis:**
- Platforma Samsung do zarządzania IoT
- Hub łączący różne protokoły (Zigbee, Z-Wave, Wi-Fi)
- Aplikacja SmartThings

**Zalety:**
- ✅ Obsługa wielu protokołów komunikacji
- ✅ Rozbudowane automatyzacje (Scenes, Automations)
- ✅ Otwarte API dla developerów
- ✅ Integracja z urządzeniami Samsung

**Wady:**
- ❌ Wymaga Samsung Account
- ❌ Chmura Samsung (choć hub może działać lokalnie)
- ❌ Interfejs czasami nieintuicyjny
- ❌ Problemy ze stabilnością w przeszłości

**Obsługa multi-home:** ⭐⭐⭐⚪⚪ (3/5)
- Możliwość tworzenia "Locations"
- Zapraszanie członków do lokalizacji
- Przełączanie między lokalizacjami w aplikacji

### 2.2.2. Rozwiązania open-source

#### Home Assistant
**Opis:**
- Najbardziej popularny open-source system Smart Home
- Python-based (asyncio)
- Integracje z >2000 urządzeń i usług
- Instalacja: Docker, Python venv, Home Assistant OS

**Zalety:**
- ✅ **Open source** - pełna kontrola nad kodem i danymi
- ✅ **Lokalne działanie** - nie wymaga chmury
- ✅ Ogromna liczba integracji
- ✅ Zaawansowane automatyzacje (YAML, UI, Node-RED)
- ✅ Aktywna społeczność
- ✅ Addons (MQTT broker, Zigbee2MQTT, etc.)

**Wady:**
- ❌ Wysoki próg wejścia (wymaga wiedzy technicznej)
- ❌ Czasem niestabilne integracje (community-maintained)
- ❌ UI może być przytłaczające dla początkujących
- ❌ Wymaga własnego serwera

**Obsługa multi-home:** ⭐⭐⚪⚪⚪ (2/5)
- Brak natywnej obsługi multi-home
- Możliwość instalacji wielu instancji
- Workaround: osobne instancje dla każdego domu
- Brak centralnego zarządzania wieloma domami

#### OpenHAB (Open Home Automation Bus)
**Opis:**
- Java-based open-source platforma
- Vendor-agnostic, unifikujący różne technologie
- Silny nacisk na lokalność i prywatność

**Zalety:**
- ✅ Open source
- ✅ Bardzo modularny (binding system)
- ✅ Lokalne działanie
- ✅ Zaawansowane reguły (DSL, JavaScript, Groovy)
- ✅ Długa historia (istnieje od 2010)

**Wady:**
- ❌ Wyższy próg wejścia niż Home Assistant
- ❌ Mniejsza społeczność
- ❌ UI mniej nowoczesny
- ❌ Wolniejszy rozwój w porównaniu do Home Assistant

**Obsługa multi-home:** ⭐⭐⚪⚪⚪ (2/5)
- Podobnie jak Home Assistant - brak natywnej obsługi
- Możliwość wielu instancji
- Brak centralnego panelu dla wielu domów

#### Domoticz
**Opis:**
- Lekki system automatyki domowej (C++)
- Prosty, szybki, niskie wymagania sprzętowe
- Darmowy i open-source

**Zalety:**
- ✅ Bardzo lekki (działa na Raspberry Pi Zero)
- ✅ Szybki i stabilny
- ✅ Prosta konfiguracja
- ✅ Lokalne działanie

**Wady:**
- ❌ Przestarzały interfejs
- ❌ Mniej integracji niż Home Assistant
- ❌ Mniejsza społeczność
- ❌ Ograniczone funkcje automatyzacji

**Obsługa multi-home:** ⭐⚪⚪⚪⚪ (1/5)
- Brak obsługi wielu domów
- System zaprojektowany dla jednej lokalizacji

### 2.2.3. Analiza porównawcza

| Kryterium | Google Home | Amazon Alexa | Apple HomeKit | Samsung SmartThings | Home Assistant | OpenHAB |
|-----------|-------------|--------------|---------------|---------------------|----------------|---------|
| **Multi-home** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Prywatność** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Łatwość użycia** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Automatyzacje** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Integracje** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Koszt** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Kontrola lokalna** | ❌ | ❌ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 2.3. Problem zarządzania wieloma gospodarstwami domowymi

### 2.3.1. Identyfikacja problemu

**Scenariusze użycia:**

1. **Właściciel wielu nieruchomości:**
   - Osoba posiadająca dom główny i domek letniskowy
   - Problem: Konieczność przełączania między aplikacjami lub kontami
   - Oczekiwanie: Jeden interfejs do zarządzania wszystkimi domami

2. **Rodzina współdzieląca dostęp:**
   - Dom rodzinny współdzielony przez dorosłe dzieci
   - Problem: Brak mechanizmu delegowania uprawnień
   - Oczekiwanie: Różne poziomy dostępu dla różnych członków rodziny

3. **Zarządca nieruchomości:**
   - Osoba zarządzająca wieloma wynajmowanymi mieszkaniami
   - Problem: Chaos w zarządzaniu wieloma lokalizacjami
   - Oczekiwanie: Centralne zarządzanie z możliwością szybkiego przełączania

4. **Administrator IT:**
   - Firma instalująca systemy Smart Home
   - Problem: Brak dostępu serwisowego do domów klientów
   - Oczekiwanie: Tymczasowy dostęp z możliwością audytu

### 2.3.2. Luki w istniejących rozwiązaniach

**Rozwiązania komercyjne:**
- ❌ Brak prawdziwego multi-tenancy (każdy dom = osobne konto)
- ❌ Ograniczone możliwości współdzielenia (max 2-3 użytkowników)
- ❌ Brak granularnych uprawnień (albo admin, albo użytkownik)
- ❌ Uzależnienie od chmury (brak kontroli nad danymi)
- ❌ Vendor lock-in (zamknięte ekosystemy)

**Rozwiązania open-source:**
- ❌ Wymaga oddzielnych instancji dla każdego domu
- ❌ Brak centralnego panelu zarządzania
- ❌ Wysoki próg wejścia techniczny
- ❌ Brak intuicyjnego UI do zarządzania uprawnieniami
- ❌ Wymaga wiedzy technicznej do konfiguracji

### 2.3.3. Wymagania dla rozwiązania problemu

**Funkcjonalne:**
1. Możliwość tworzenia wielu "domów" w ramach jednego konta
2. Zapraszanie użytkowników do domów z różnymi rolami
3. Szybkie przełączanie się między domami
4. Izolacja danych między domami
5. Współdzielenie automatyzacji w ramach domu
6. Historia zmian z informacją "kto co zrobił"

**Niefunkcjonalne:**
1. Bezpieczeństwo - silna izolacja między domami
2. Wydajność - szybkie ładowanie nawet przy wielu domach
3. Skalowalność - obsługa setek domów na użytkownika
4. Użyteczność - intuicyjny interfejs
5. Prywatność - możliwość self-hosting

## 2.4. Wymagania funkcjonalne i niefunkcjonalne

### 2.4.1. Wymagania funkcjonalne (FR - Functional Requirements)

**FR1: Zarządzanie użytkownikami**
- FR1.1: Rejestracja nowego użytkownika z weryfikacją email
- FR1.2: Logowanie z użyciem email/hasło
- FR1.3: Reset hasła przez email
- FR1.4: Edycja profilu użytkownika (nazwa, email, zdjęcie)
- FR1.5: Zmiana hasła

**FR2: Zarządzanie domami (Multi-Home)**
- FR2.1: Tworzenie nowego domu przez użytkownika
- FR2.2: Edycja ustawień domu (nazwa, opis)
- FR2.3: Usuwanie domu (tylko właściciel)
- FR2.4: Przełączanie się między domami
- FR2.5: Lista wszystkich domów użytkownika

**FR3: Zarządzanie uprawnieniami**
- FR3.1: Zapraszanie użytkowników do domu (przez email)
- FR3.2: Akceptacja/odrzucenie zaproszenia
- FR3.3: Przypisywanie ról (Owner, Admin, User)
- FR3.4: Usuwanie użytkownika z domu
- FR3.5: Lista członków domu z rolami

**FR4: Zarządzanie urządzeniami**
- FR4.1: Dodawanie urządzenia (przycisk/kontroler temperatury)
- FR4.2: Edycja urządzenia (nazwa, pokój)
- FR4.3: Usuwanie urządzenia
- FR4.4: Włączanie/wyłączanie urządzenia
- FR4.5: Ustawianie temperatury
- FR4.6: Historia zmian stanu urządzenia

**FR5: Zarządzanie pokojami**
- FR5.1: Tworzenie pokoju
- FR5.2: Edycja nazwy pokoju
- FR5.3: Usuwanie pokoju (wraz z przypisanymi urządzeniami)
- FR5.4: Sortowanie pokojów (drag & drop)

**FR6: Automatyzacje**
- FR6.1: Tworzenie automatyzacji z triggerem i akcjami
- FR6.2: Edycja automatyzacji
- FR6.3: Włączanie/wyłączanie automatyzacji
- FR6.4: Usuwanie automatyzacji
- FR6.5: Logi wykonania automatyzacji
- FR6.6: Obsługa triggerów czasowych
- FR6.7: Obsługa triggerów urządzeniowych
- FR6.8: Obsługa triggerów sensorowych

**FR7: Panel administratora domu**
- FR7.1: Dashboard z kluczowymi metrykami
- FR7.2: Zarządzanie użytkownikami domu
- FR7.3: Przegląd logów zarządzania
- FR7.4: Statystyki użycia urządzeń

**FR8: Powiadomienia**
- FR8.1: Powiadomienia email o zmianach bezpieczeństwa
- FR8.2: Powiadomienia o zaproszeniach do domu
- FR8.3: Powiadomienia o błędach automatyzacji
- FR8.4: Konfiguracja preferencji powiadomień

### 2.4.2. Wymagania niefunkcjonalne (NFR - Non-Functional Requirements)

**NFR1: Wydajność**
- NFR1.1: Czas odpowiedzi API < 200ms (95th percentile)
- NFR1.2: Czas propagacji zmian przez WebSocket < 100ms
- NFR1.3: Obsługa min. 1000 concurrent connections
- NFR1.4: Czas ładowania strony < 2s (3G connection)

**NFR2: Bezpieczeństwo**
- NFR2.1: Haszowanie haseł algorytmem bcrypt (cost factor ≥ 12)
- NFR2.2: Sesje z timeout 24h
- NFR2.3: HTTPS wymuszony dla całej komunikacji
- NFR2.4: CSRF protection dla wszystkich formularzy
- NFR2.5: SQL injection prevention (prepared statements)
- NFR2.6: XSS protection (input sanitization)
- NFR2.7: Rate limiting dla API (100 req/min per user)

**NFR3: Skalowalność**
- NFR3.1: Architektura umożliwiająca horizontal scaling
- NFR3.2: Database connection pooling
- NFR3.3: Cache layer (Redis) dla często używanych danych
- NFR3.4: Lazy loading dla dużych list

**NFR4: Dostępność (Availability)**
- NFR4.1: Uptime ≥ 99.5% (cel: 99.9%)
- NFR4.2: Graceful degradation przy awarii Redis
- NFR4.3: Health check endpoints
- NFR4.4: Automatic restart on failure (Docker restart policy)

**NFR5: Użyteczność (Usability)**
- NFR5.1: Responsive design (mobile, tablet, desktop)
- NFR5.2: Interfejs w języku polskim
- NFR5.3: Intuicyjna nawigacja (max 3 kliknięcia do funkcji)
- NFR5.4: Feedback użytkownikowi (loading states, error messages)
- NFR5.5: Accessibility (WCAG 2.1 Level A minimum)

**NFR6: Maintainability**
- NFR6.1: Kod zgodny z PEP 8 (Python)
- NFR6.2: Pokrycie testami ≥ 70%
- NFR6.3: Dokumentacja API (OpenAPI/Swagger)
- NFR6.4: Dokumentacja użytkownika
- NFR6.5: Logs w formacie JSON dla łatwego parsowania

**NFR7: Przenośność (Portability)**
- NFR7.1: Konteneryzacja (Docker)
- NFR7.2: Deployment na Linux, Windows Server
- NFR7.3: Konfiguracja przez zmienne środowiskowe
- NFR7.4: Brak hard-coded paths

## 2.5. Wybór stosu technologicznego

### 2.5.1. Backend: Flask (Python)

**Uzasadnienie:**
- ✅ Lekki i elastyczny framework
- ✅ Łatwa integracja z PostgreSQL (psycopg2)
- ✅ Flask-SocketIO dla WebSocket
- ✅ Duża społeczność i dokumentacja
- ✅ Python - język ogólnego przeznaczenia (łatwo dodać ML w przyszłości)

**Alternatywy rozważane:**
- Django - zbyt ciężki dla tego projektu
- FastAPI - brak wbudowanego wsparcia dla szablonów (wymaga osobnego frontendu)
- Node.js/Express - preferuję Python dla logiki biznesowej

### 2.5.2. Baza danych: PostgreSQL

**Uzasadnienie:**
- ✅ Relacyjna struktura (naturalna dla multi-home)
- ✅ ACID compliance
- ✅ Zaawansowane funkcje (JSON columns, UUID)
- ✅ Dobre wsparcie dla concurrent access
- ✅ Open source, darmowy

**Alternatywy:**
- MySQL - gorsze wsparcie dla UUID i JSON
- MongoDB - NoSQL nieodpowiedni dla relacyjnych danych
- SQLite - brak obsługi concurrent writes

### 2.5.3. Cache: Redis

**Uzasadnienie:**
- ✅ In-memory - bardzo szybki
- ✅ Proste key-value store
- ✅ Wsparcie dla TTL (Time To Live)
- ✅ Opcjonalny (graceful fallback do SimpleCache)

### 2.5.4. Real-time: Socket.IO

**Uzasadnienie:**
- ✅ Dwukierunkowa komunikacja
- ✅ Automatic reconnection
- ✅ Fallback do long-polling
- ✅ Room support (dla multi-home)
- ✅ Flask-SocketIO - łatwa integracja

### 2.5.5. Frontend: Vanilla JS + Jinja2

**Uzasadnienie:**
- ✅ Server-side rendering (szybsze initial load)
- ✅ Brak złożoności SPA frameworks
- ✅ Progressive enhancement
- ✅ Mniejszy bundle size

**Alternatywy:**
- React/Vue - dodatkowa złożoność, overkill dla projektu
- HTMX - rozważany, ale Socket.IO wymaga custom JS

### 2.5.6. Deployment: Docker + Nginx

**Uzasadnienie:**
- ✅ Docker - izolacja, reprodukowalność
- ✅ Nginx - reverse proxy, SSL termination, static files
- ✅ Docker Compose - łatwy multi-container setup
- ✅ GitHub Actions - automatyczny build i push

---

**Podsumowanie rozdziału:**

W tym rozdziale przeprowadzono szczegółową analizę istniejących rozwiązań Smart Home, identyfikując kluczowe luki w obsłudze wielu gospodarstw domowych. Porównano rozwiązania komercyjne (Google Home, Amazon Alexa, Apple HomeKit, Samsung SmartThings) oraz open-source (Home Assistant, OpenHAB, Domoticz), wykazując że **żadne z nich nie oferuje w pełni satysfakcjonującej obsługi multi-home z granularnymi uprawnieniami**. 

Apple HomeKit oferuje najlepszą obsługę wielu domów, ale jest zamknięty w ekosystemie Apple. Home Assistant, mimo ogromnej funkcjonalności, wymaga oddzielnych instancji dla każdego domu.

Zdefiniowano szczegółowe wymagania funkcjonalne (8 grup, 50+ wymagań) oraz niefunkcjonalne (7 kategorii), które stanowią podstawę dla projektowania systemu. Wybrano stos technologiczny oparty na Flask, PostgreSQL, Redis, Socket.IO i Docker, uzasadniając każdą decyzję technologiczną.

W kolejnym rozdziale zostaną przedstawione podstawy teoretyczne zastosowanych technologii.
