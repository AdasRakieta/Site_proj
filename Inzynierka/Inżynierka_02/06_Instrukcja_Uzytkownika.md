# 6. Instrukcja użytkownika

6.1 Uruchomienie lokalne
1. Utwórz wirtualne środowisko Python i zainstaluj zależności:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Utwórz plik `.env` na podstawie `.env.example` i ustaw zmienne: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`.
3. Uruchom aplikację:

```powershell
python app_db.py
```

6.2 Użycie funkcjonalne
- Tworzenie domu: panel `Home Create` w UI.
- Zapraszanie użytkownika: w ustawieniach domu wybierz `Invite` i podaj e-mail.
- Sterowanie urządzeniami: przełączniki i kontrola temperatury dostępne w panelu sterowania; zmiany propagowane w czasie rzeczywistym.
