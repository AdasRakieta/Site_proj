# Site_proj - Przewodnik Szybkiego Startu

## 🚀 Szybkie Odniesienie Optymalizacji Wydajności

### Minifikacja CSS/JS

#### Dla Rozwoju (Auto-obserwacja zmian)
```bash
python utils/asset_manager.py --watch
```

#### Dla Produkcji (Jednorazowa minifikacja)
```bash
python utils/asset_manager.py
```

#### Wyczyść i Odbuduj Wszystkie Zasoby
```bash
python utils/asset_manager.py --clean
```

### Workflow Edycji Plików

1. **Edytuj oryginalne pliki**: `static/css/style.css`, `static/js/app.js`, itp.
2. **Uruchom minifikację**: `python utils/asset_manager.py`
3. **Aplikacja automatycznie serwuje** zminifikowane wersje

**NIE edytuj ręcznie plików .min.css lub .min.js** - są auto-generowane!

### Uruchamianie Aplikacji

```bash
python app.py
```

Aplikacja automatycznie:
- ✅ Serwuje zminifikowane CSS/JS gdy dostępne (fallback do oryginałów)
- ✅ Używa lokalnego cachowania dla poprawy wydajności
- ✅ Wysyła emaile asynchronicznie (nieblokujące UI)
- ✅ Przetwarza zadania w tle

### Struktura Plików

```
Site_proj/
├── app.py                          # Główna aplikacja
├── utils/                          # 🆕 Zorganizowane narzędzia
│   ├── cache_manager.py           # Funkcjonalność cachowania
│   ├── async_manager.py           # Operacje async
│   └── asset_manager.py           # Minifikacja CSS/JS
├── deprecated/                     # Stare pliki (do odniesienia)
├── static/
│   ├── css/
│   │   ├── style.css              # ✏️ Edytuj te pliki
│   │   └── min/                   # 🤖 Folder z plikami zminifikowanymi
│   │       └── style.min.css      # Auto-generowane
│   └── js/
│       ├── app.js                 # ✏️ Edytuj te pliki
│       └── min/                   # 🤖 Folder z plikami zminifikowanymi
│           └── app.min.js         # Auto-generowane
└── PERFORMANCE_OPTIMIZATION.md    # 📖 Szczegółowa dokumentacja
```

### Korzyści Wydajnościowe

- **36.1% mniejsze** pliki CSS/JS
- **~50ms szybsze** odpowiedzi API (cachowanie)
- **Nieblokujące** wysyłanie emaili
- **Poprawione** doświadczenie użytkownika

### Monitoring

Sprawdź logi aplikacji dla:
- Statystyki trafień/chybień cache
- Status kolejki async emaili
- Informacje serwowania zasobów

---

📖 **Dla szczegółowej dokumentacji**: Zobacz `PERFORMANCE_OPTIMIZATION.md`