# SmartHome Android Application

Aplikacja Android do zdalnego sterowania systemem SmartHome poprzez VPN.

## ⚠️ Status: Gradle Configuration Fixed

**Problem**: Gradle 8.13 wymaga Java 11+, ale projekt używa Java 8
**Rozwiązanie**: Downgrade do Gradle 8.0.2 (kompatybilne z Java 8)

### Co zostało naprawione:
- ✅ `build.gradle`: Android Gradle Plugin downgrade z 8.11.1 → 8.0.2
- ✅ `gradle/wrapper/gradle-wrapper.properties`: Gradle wrapper downgrade z 8.13 → 8.0.2
- ✅ `gradlew.bat`: Utworzony brakujący Windows wrapper script

### Wymagania do pełnego działania:
- Pobranie `gradle-wrapper.jar` (brakujący plik)
- Alternatywnie: Użyj Android Studio do regeneracji Gradle wrapper

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

## Build Instructions

### Metoda 1: Android Studio (Zalecana)

1. **Klonowanie repozytorium**
   ```bash
   git clone https://github.com/AdasRakieta/Site_proj.git
   cd Site_proj/android_app
   ```

2. **Otworzenie w Android Studio**
   - Otwórz Android Studio
   - Wybierz "Open an existing project"
   - Wskaż folder `android_app`
   - Android Studio automatycznie regeneruje Gradle wrapper

3. **Kompilacja**
   - Kliknij "Build" > "Make Project"
   - Lub użyj skrótu `Ctrl+F9`

4. **Instalacja na urządzeniu**
   - Podłącz urządzenie Android przez USB
   - Włącz "Debugowanie USB" w ustawieniach dewelopera
   - Kliknij "Run" > "Run 'app'"

### Metoda 2: Command Line (Wymaga gradle-wrapper.jar)

```bash
# Pobierz brakujący gradle-wrapper.jar
# Alternatywnie: regeneruj przez Android Studio

# Następnie:
./gradlew build           # Linux/macOS
gradlew.bat build         # Windows
```

### Troubleshooting

**Problem**: `Could not find or load main class org.gradle.wrapper.GradleWrapperMain`
**Rozwiązanie**: Brakuje `gradle/wrapper/gradle-wrapper.jar` - użyj Android Studio aby go wygenerować

**Problem**: `JVM runtime version 11 required`  
**Rozwiązanie**: ✅ Już naprawione - używamy Gradle 8.0.2 kompatybilne z Java 8

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