# System Lokalizacji Domu - Polski Miasta

## Przegląd
System lokalizacji umożliwia właścicielom domów ustawienie lokalizacji z wykorzystaniem bazy 184 polskich miast.

## Baza Danych

### Tabela: `polish_cities`
```sql
CREATE TABLE polish_cities (
    id SERIAL PRIMARY KEY,
    city VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    admin_name VARCHAR(255),  -- Województwo
    population INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Dane:**
- 184 miasta polskie
- Źródło: `pl.json`
- Załadowane przez: `load_polish_cities.py`

**Indeksy:**
- `idx_polish_cities_name` - wyszukiwanie po nazwie
- `idx_polish_cities_admin` - filtrowanie po województwie
- `idx_polish_cities_coords` - spatial queries

### Tabela: `homes` (kolumny lokalizacji)
```sql
ALTER TABLE homes ADD COLUMN:
- latitude DECIMAL(10, 6)
- longitude DECIMAL(10, 6)
- city VARCHAR(255)
- country VARCHAR(100)
- country_code VARCHAR(2)
- address TEXT
```

## Funkcjonalności

### 1. Autocomplete Miast
**Endpoint:** `GET /api/cities/search?q={search_term}&limit={limit}`

**Przykład:**
```
GET /api/cities/search?q=War&limit=10
```

**Odpowiedź:**
```json
{
  "success": true,
  "cities": [
    {
      "name": "Warsaw",
      "latitude": 52.23,
      "longitude": 21.0111,
      "admin_name": "Mazowieckie",
      "population": 1860281,
      "country": "Poland",
      "country_code": "PL"
    }
  ],
  "count": 1
}
```

**Wyszukiwanie:**
- Po nazwie miasta (prefix match)
- Po nazwie województwa
- Sortowanie: populacja DESC, potem alfabetycznie

### 2. Geolokalizacja
**Przycisk:** "📍 Użyj mojej lokalizacji"

**Proces:**
1. Przeglądarka pobiera współrzędne GPS użytkownika
2. **Walidacja:** Sprawdza czy lokalizacja jest w granicach Polski
   - Szerokość: 49.0° - 54.9°N
   - Długość: 14.1° - 24.2°E
3. Jeśli tak → znajduje najbliższe miasto z bazy
4. Automatycznie wypełnia formularz

**Walidacja:**
- Frontend: JavaScript w `home_settings.js`
- Backend: Python w `home_management.py`

### 3. Zapisywanie Lokalizacji
**Endpoint:** `POST /api/home/{home_id}/location/update`

**Body:**
```json
{
  "city": "Warsaw",
  "address": "ul. Marszałkowska 1",
  "latitude": 52.23,
  "longitude": 21.0111,
  "country": "Poland"
}
```

**Walidacja Backend:**
- Tylko właściciel może zmieniać lokalizację
- Współrzędne muszą być w Polsce
- Zwraca błąd jeśli poza granicami

## Pliki

### Backend
- `app/home_settings_routes.py` - Endpoint `/api/cities/search`
- `app/home_management.py` - Business logic + walidacja
- `utils/multi_home_db_manager.py` - Database queries
- `load_polish_cities.py` - Ładowanie miast z JSON

### Frontend
- `templates/home_settings.html` - Formularz lokalizacji
- `static/js/home_settings.js` - Autocomplete + geolokalizacja
- `static/css/home_settings.css` - Style

### Dane
- `pl.json` - 184 miast polskich (źródło danych)

## Użycie

### Dla Użytkowników
1. Wejdź w **Ustawienia domu**
2. Przewiń do sekcji **📍 Lokalizacja domu**
3. **Opcja A:** Zacznij pisać nazwę miasta → wybierz z listy
4. **Opcja B:** Kliknij "📍 Użyj mojej lokalizacji"
5. Opcjonalnie: Dodaj dokładny adres
6. Kliknij **Zapisz lokalizację**

### Dla Deweloperów

**Załadowanie miast do bazy:**
```bash
python load_polish_cities.py
```

**Test wyszukiwania:**
```sql
SELECT city, admin_name, population 
FROM polish_cities 
WHERE LOWER(city) LIKE 'war%'
ORDER BY population DESC;
```

**Sprawdzenie lokalizacji domu:**
```sql
SELECT name, city, admin_name, latitude, longitude 
FROM homes 
WHERE city IS NOT NULL;
```

## Granice Polski (Walidacja)
```javascript
const POLAND_BOUNDS = {
  minLat: 49.0,   // Najdalej na południe
  maxLat: 54.9,   // Najdalej na północ
  minLon: 14.1,   // Najdalej na zachód
  maxLon: 24.2    // Najdalej na wschód
};
```

## Przyszłe Rozszerzenia
1. **Mapa** - Wyświetlanie pinezki na mapie strony głównej
2. **Pogoda** - Integracja z API pogodowym dla danego miasta
3. **Więcej miast** - Mniejsze miejscowości (< 10k mieszkańców)
4. **Geokodowanie** - Automatyczne uzupełnianie adresu na podstawie współrzędnych

## Troubleshooting

**Problem:** Geolokalizacja nie działa
- **Rozwiązanie:** Sprawdź czy przeglądarka ma pozwolenie na dostęp do lokalizacji

**Problem:** "Twoja lokalizacja jest poza Polską"
- **Rozwiązanie:** To normalne jeśli jesteś poza Polską - wpisz miasto ręcznie

**Problem:** Brak miast w autocomplete
- **Rozwiązanie:** Uruchom `python load_polish_cities.py`

**Problem:** Błąd "Failed to update location"
- **Rozwiązanie:** Sprawdź czy współrzędne są w granicach Polski (49-54.9°N, 14.1-24.2°E)
