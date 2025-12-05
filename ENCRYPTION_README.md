# Aplikacja Kryptograficzna - Systemy Bezpieczeństwa Komputerowego

## Przegląd

Aplikacja edukacyjna stworzona na zaliczenie z przedmiotu **Bezpieczeństwo Systemów Komputerowych**. 
Zawiera implementacje klasycznych i nowoczesnych algorytmów szyfrowania, funkcje haszujące oraz kodowanie danych.

## Funkcjonalności

### 1. Szyfry Klasyczne (Classical Ciphers)

#### Szyfr Cezara (Caesar Cipher)
- **Opis**: Jeden z najprostszych szyfrów podstawieniowych
- **Metoda**: Przesuwa każdą literę o stałą liczbę pozycji w alfabecie
- **Parametry**: Przesunięcie (shift) od 1 do 25
- **Przykład**: "HELLO" z przesunięciem 3 → "KHOOR"
- **Bezpieczeństwo**: Bardzo niskie - łatwy do złamania przez analizę częstotliwości

#### Szyfr Vigenère'a (Vigenère Cipher)
- **Opis**: Ulepszenie szyfru Cezara używające klucza tekstowego
- **Metoda**: Używa różnych przesunięć dla różnych liter na podstawie klucza
- **Parametry**: Klucz tekstowy (tylko litery)
- **Przykład**: "HELLO" z kluczem "KEY" → "RIJVS"
- **Bezpieczeństwo**: Średnie - odporny na prostą analizę częstotliwości

#### Szyfr Podstawieniowy (Substitution Cipher)
- **Opis**: Każda litera alfabetu zamieniana jest na inną zgodnie z kluczem
- **Metoda**: Używa 26-literowego klucza podstawienia
- **Parametry**: 26-znakowy klucz (permutacja alfabetu)
- **Przykład**: Z kluczem "ZYXWVUTSRQPONMLKJIHGFEDCBA" - "A"→"Z", "B"→"Y", etc.
- **Bezpieczeństwo**: Średnie - podatny na analizę częstotliwości

#### Szyfr Rail Fence (Transposition Cipher)
- **Opis**: Szyfr transpozycyjny układający tekst w zygzak
- **Metoda**: Tekst zapisywany jest w formie zygzaka na wielu "szynach"
- **Parametry**: Liczba szyn (rails) od 2 do 10
- **Przykład**: "HELLO" na 3 szynach → "HOELL"
- **Bezpieczeństwo**: Niskie - łatwy do złamania przy znanej liczbie szyn

### 2. Szyfrowanie Nowoczesne (Modern Encryption)

#### AES-256 (Advanced Encryption Standard)
- **Opis**: Symetryczny algorytm szyfrowania blokowego
- **Metoda**: Używa tego samego klucza do szyfrowania i deszyfrowania
- **Parametry**: 
  - Klucz szyfrowania (dowolny tekst, haszowany do 256 bitów)
  - IV (Initialization Vector) - generowany automatycznie
- **Bezpieczeństwo**: Bardzo wysokie - standard przemysłowy
- **Zastosowania**: Szyfrowanie plików, komunikacji, baz danych

#### RSA (Rivest-Shamir-Adleman)
- **Opis**: Asymetryczny algorytm kryptografii klucza publicznego
- **Metoda**: 
  - Klucz publiczny do szyfrowania
  - Klucz prywatny do deszyfrowania
- **Parametry**: Rozmiar klucza (2048 bitów)
- **Bezpieczeństwo**: Bardzo wysokie - podstawa PKI
- **Zastosowania**: Podpisy cyfrowe, wymiana kluczy, szyfrowanie komunikacji

### 3. Funkcje Haszujące (Hashing Functions)

#### MD5 (Message Digest 5)
- **Długość**: 128 bitów (32 znaki hex)
- **Status**: Przestarzały, niezalecany do celów bezpieczeństwa
- **Zastosowania**: Sumy kontrolne (nie kryptografia)

#### SHA-1 (Secure Hash Algorithm 1)
- **Długość**: 160 bitów (40 znaków hex)
- **Status**: Przestarzały, wykryto kolizje
- **Zastosowania**: Starsze systemy (nie nowe implementacje)

#### SHA-256 (Secure Hash Algorithm 256)
- **Długość**: 256 bitów (64 znaki hex)
- **Status**: Aktualny, bezpieczny
- **Zastosowania**: Podpisy cyfrowe, blockchain, certyfikaty

#### SHA-512 (Secure Hash Algorithm 512)
- **Długość**: 512 bitów (128 znaków hex)
- **Status**: Aktualny, bardzo bezpieczny
- **Zastosowania**: Aplikacje wymagające maksymalnego bezpieczeństwa

### 4. Kodowanie (Encoding)

#### Base64
- **Opis**: Kodowanie binarne do tekstu ASCII
- **Uwaga**: To NIE jest szyfrowanie - nie zapewnia bezpieczeństwa!
- **Zastosowania**: Przesyłanie danych binarnych w tekstowych protokołach

#### Hexadecimal (Hex)
- **Opis**: Reprezentacja szesnastkowa danych
- **Uwaga**: To NIE jest szyfrowanie - tylko zmiana reprezentacji!
- **Zastosowania**: Debugowanie, wyświetlanie danych binarnych

## Struktura Projektu

```
Site_proj/
├── utils/
│   └── encryption_algorithms.py    # Implementacje algorytmów
├── app/
│   └── encryption_routes.py        # Endpointy API
├── templates/
│   └── encryption.html             # Interfejs użytkownika
└── test_encryption.py              # Testy funkcjonalności
```

## Moduły Kodu

### `utils/encryption_algorithms.py`

#### Klasy:
1. **ClassicalCiphers**: Szyfry klasyczne
   - `caesar_encrypt(text, shift)`
   - `caesar_decrypt(text, shift)`
   - `vigenere_encrypt(text, key)`
   - `vigenere_decrypt(text, key)`
   - `substitution_encrypt(text, key)`
   - `substitution_decrypt(text, key)`
   - `rail_fence_encrypt(text, rails)`
   - `rail_fence_decrypt(text, rails)`

2. **ModernEncryption**: Szyfrowanie nowoczesne
   - `aes_encrypt(plaintext, key)` → {ciphertext, iv}
   - `aes_decrypt(ciphertext, key, iv)` → plaintext
   - `generate_rsa_keypair(key_size)` → {public_key, private_key}
   - `rsa_encrypt(plaintext, public_key)` → ciphertext
   - `rsa_decrypt(ciphertext, private_key)` → plaintext

3. **HashingFunctions**: Funkcje haszujące
   - `md5_hash(text)` → hash
   - `sha1_hash(text)` → hash
   - `sha256_hash(text)` → hash
   - `sha512_hash(text)` → hash
   - `all_hashes(text)` → {md5, sha1, sha256, sha512}

4. **EncodingFunctions**: Kodowanie
   - `base64_encode(text)` → encoded
   - `base64_decode(encoded)` → text
   - `hex_encode(text)` → encoded
   - `hex_decode(hex_text)` → text

## API Endpoints

Wszystkie endpointy znajdują się pod `/encryption/api/`:

### Szyfry Klasyczne
- `POST /encryption/api/caesar` - Szyfr Cezara
- `POST /encryption/api/vigenere` - Szyfr Vigenère'a
- `POST /encryption/api/substitution` - Szyfr podstawieniowy
- `POST /encryption/api/railfence` - Szyfr Rail Fence

### Szyfrowanie Nowoczesne
- `POST /encryption/api/aes` - Szyfrowanie AES-256
- `POST /encryption/api/rsa/generate` - Generowanie kluczy RSA
- `POST /encryption/api/rsa` - Szyfrowanie/deszyfrowanie RSA

### Funkcje Haszujące
- `POST /encryption/api/hash` - Obliczanie hashów

### Kodowanie
- `POST /encryption/api/encode` - Kodowanie/dekodowanie

## Instalacja i Uruchomienie

### Wymagania
```bash
pip install -r requirements.txt
```

Kluczowe zależności:
- `cryptography>=44.0.0` - Biblioteka kryptograficzna
- `flask>=3.1.0` - Framework webowy
- `flask-socketio>=5.5.0` - WebSocket support

### Uruchomienie
```bash
python app_db.py
```

Aplikacja będzie dostępna pod adresem: `http://localhost:5000/encryption`

### Testowanie
```bash
python test_encryption.py
```

## Użytkowanie

### Interfejs Web
1. Uruchom aplikację
2. Zaloguj się do systemu SmartHome
3. W menu nawigacyjnym wybierz "🔐 Kryptografia"
4. Wybierz kategorię algorytmów (zakładki na górze)
5. Wprowadź tekst i parametry
6. Kliknij przycisk szyfrowania/deszyfrowania
7. Wynik pojawi się poniżej z opcją kopiowania

### Przykłady Użycia w Kodzie

#### Caesar Cipher
```python
from utils.encryption_algorithms import ClassicalCiphers

text = "Hello World"
encrypted = ClassicalCiphers.caesar_encrypt(text, 3)
decrypted = ClassicalCiphers.caesar_decrypt(encrypted, 3)
```

#### AES-256
```python
from utils.encryption_algorithms import ModernEncryption

plaintext = "Secret Message"
key = "MySecretKey"

# Szyfrowanie
result = ModernEncryption.aes_encrypt(plaintext, key)
ciphertext = result['ciphertext']
iv = result['iv']

# Deszyfrowanie
decrypted = ModernEncryption.aes_decrypt(ciphertext, key, iv)
```

#### Haszowanie
```python
from utils.encryption_algorithms import HashingFunctions

text = "Password123"
hashes = HashingFunctions.all_hashes(text)
print(hashes['sha256'])
```

## Aspekty Bezpieczeństwa

### Dobre Praktyki
1. **Szyfry klasyczne** - tylko do celów edukacyjnych, NIE używać w produkcji
2. **AES-256** - bezpieczny do ochrony danych, używaj silnych kluczy
3. **RSA-2048** - bezpieczny do wymiany kluczy i podpisów cyfrowych
4. **SHA-256/512** - bezpieczne do haszowania haseł (z salt) i sum kontrolnych
5. **MD5/SHA-1** - NIE używać do celów bezpieczeństwa

### Zagrożenia
- **Analiza częstotliwości** - zagrożenie dla szyfrów klasycznych
- **Brute force** - zagrożenie dla słabych kluczy
- **Man-in-the-middle** - wymaga bezpiecznej wymiany kluczy
- **Kolizje hashów** - problem MD5 i SHA-1

### Zalecenia
- Używaj długich, losowych kluczy
- Nigdy nie przechowuj kluczy prywatnych w kodzie
- Używaj HTTPS do przesyłania zaszyfrowanych danych
- Regularnie aktualizuj biblioteki kryptograficzne
- W produkcji używaj tylko aktualnych standardów (AES, RSA, SHA-256/512)

## Cele Edukacyjne

Aplikacja demonstruje:
1. ✓ Ewolucję kryptografii od klasycznej do nowoczesnej
2. ✓ Różnice między szyfrowaniem symetrycznym a asymetrycznym
3. ✓ Zastosowanie funkcji jednokierunkowych (hashy)
4. ✓ Różnicę między szyfrowaniem a kodowaniem
5. ✓ Praktyczne implementacje standardów przemysłowych
6. ✓ Integrację kryptografii z aplikacjami webowymi

## Licencja i Autorstwo

Projekt edukacyjny - Bezpieczeństwo Systemów Komputerowych
Utworzony: Grudzień 2024

## Dalszy Rozwój

Możliwe rozszerzenia:
- [ ] Dodanie analizy statystycznej tekstu
- [ ] Implementacja łamania prostych szyfrów
- [ ] Wizualizacja procesu szyfrowania
- [ ] Porównanie wydajności algorytmów
- [ ] Dodanie więcej algorytmów (Blowfish, Twofish, etc.)
- [ ] Szyfrowanie plików
- [ ] Podpisy cyfrowe
- [ ] Certyfikaty X.509
