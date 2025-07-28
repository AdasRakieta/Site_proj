# SmartHome Android Application

Aplikacja Android do zdalnego sterowania systemem SmartHome poprzez VPN.

## Funkcje

- **Autoryzacja użytkowników** - logowanie z użyciem istniejących kont z systemu web
- **Zarządzanie pokojami** - przegląd i nawigacja po pokojach 
- **Sterowanie urządzeniami** - włączanie/wyłączanie urządzeń w czasie rzeczywistym
- **Kontrola temperatury** - monitorowanie i ustawianie temperatury
- **System bezpieczeństwa** - podgląd statusu zabezpieczeń
- **Połączenie przez VPN** - bezpieczny dostęp do systemu domowego

## Konfiguracja VPN

### Wymagania
- Skonfigurowany serwer VPN na Raspberry Pi
- Urządzenie Android z aplikacją VPN (OpenVPN, WireGuard, itp.)
- Dostęp do lokalnej sieci przez VPN

### Instrukcja konfiguracji

1. **Konfiguracja VPN na urządzeniu**
   - Zainstaluj aplikację VPN (np. OpenVPN dla Android)
   - Zaimportuj plik konfiguracyjny VPN dla swojego systemu
   - Połącz się z serwerem VPN na Raspberry Pi

2. **Konfiguracja aplikacji SmartHome**
   - Otwórz aplikację SmartHome
   - Naciśnij "Ustawienia połączenia" na ekranie logowania
   - Wprowadź adres IP Raspberry Pi w sieci VPN (np. `192.168.1.100:5000`)
   - Zapisz ustawienia

3. **Logowanie**
   - Wprowadź swoje dane użytkownika z systemu web
   - Zaloguj się do aplikacji

## Kompilacja aplikacji

### Wymagania
- Android Studio 2023.1.1 lub nowszy
- Android SDK (API 24 lub wyższy)
- Gradle 8.4

### Kroki kompilacji

1. **Klonowanie repozytorium**
   ```bash
   git clone https://github.com/AdasRakieta/Site_proj.git
   cd Site_proj/android_app
   ```

2. **Otworzenie w Android Studio**
   - Otwórz Android Studio
   - Wybierz "Open an existing project"
   - Wskaż folder `android_app`

3. **Kompilacja**
   - Kliknij "Build" > "Make Project"
   - Lub użyj skrótu `Ctrl+F9`

4. **Instalacja na urządzeniu**
   - Podłącz urządzenie Android przez USB
   - Włącz "Debugowanie USB" w ustawieniach dewelopera
   - Kliknij "Run" > "Run 'app'"

### Kompilacja z linii poleceń

```bash
cd android_app
./gradlew assembleDebug
```

Plik APK zostanie wygenerowany w `app/build/outputs/apk/debug/`

## Struktura aplikacji

```
android_app/
├── app/
│   ├── src/main/
│   │   ├── java/com/smarthome/
│   │   │   ├── activities/          # Aktywności (ekrany)
│   │   │   ├── models/              # Modele danych
│   │   │   ├── services/            # Komunikacja z API
│   │   │   └── utils/               # Narzędzia i adaptery
│   │   ├── res/                     # Zasoby (layouty, ikony, itp.)
│   │   └── AndroidManifest.xml      # Manifest aplikacji
│   └── build.gradle                 # Konfiguracja modułu
├── gradle/                          # Pliki Gradle
└── build.gradle                     # Konfiguracja główna
```

## API Endpoints

Aplikacja komunikuje się z następującymi endpointami:

- `POST /login` - Logowanie użytkownika
- `GET /api/rooms` - Lista pokoi
- `GET /api/buttons` - Lista urządzeń
- `POST /api/buttons/{id}/toggle` - Przełączanie urządzenia
- `GET /api/temperature_controls` - Kontrola temperatury
- `GET /api/security/state` - Status bezpieczeństwa

## Bezpieczeństwo

- **Szyfrowane przechowywanie** - dane logowania są bezpiecznie przechowywane
- **HTTPS/VPN** - komunikacja przez szyfrowane połączenie
- **Sesje** - zarządzanie sesjami użytkownika
- **Network Security Config** - konfiguracja bezpieczeństwa sieci

## Rozwiązywanie problemów

### Problemy z połączeniem

1. **Sprawdź połączenie VPN**
   - Upewnij się, że VPN jest aktywny
   - Sprawdź czy masz dostęp do sieci lokalnej

2. **Sprawdź adres serwera**
   - Upewnij się, że adres IP jest poprawny
   - Sprawdź czy port 5000 jest otwarty

3. **Sprawdź logi**
   - Użyj Android Studio do podglądu logów
   - Sprawdź logi serwera SmartHome

### Problemy z logowaniem

1. **Sprawdź dane logowania**
   - Użyj tych samych danych co w aplikacji web
   - Sprawdź czy konto jest aktywne

2. **Sprawdź połączenie z bazą danych**
   - Upewnij się, że serwer ma dostęp do PostgreSQL
   - Sprawdź logi bazy danych

## Wsparcie

W przypadku problemów:
1. Sprawdź logi aplikacji w Android Studio
2. Sprawdź logi serwera SmartHome
3. Sprawdź połączenie VPN
4. Skontaktuj się z administratorem systemu