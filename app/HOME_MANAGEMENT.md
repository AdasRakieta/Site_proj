# Home Management System

Osobne klasy zarządzające różnymi aspektami domów w systemie multi-home, oddzielone od ogólnych ustawień aplikacji.

## Architektura

System zarządzania domami został podzielony na osobne, wyspecjalizowane klasy:

### 1. HomeInfoManager
**Odpowiedzialność**: Zarządzanie podstawowymi informacjami o domu
- Aktualizacja nazwy i opisu domu
- Walidacja danych wejściowych
- Sprawdzanie uprawnień właściciela

**Metody**:
- `update_home_info(home_id, user_id, name, description)` - Aktualizuje podstawowe informacje
- `get_home_info(home_id, user_id)` - Pobiera informacje o domu

### 2. HomeUserManager  
**Odpowiedzialność**: Zarządzanie użytkownikami domu
- Zapraszanie nowych użytkowników
- Generowanie kodów zaproszeń
- Usuwanie użytkowników z domu
- Zarządzanie rolami i uprawnieniami

**Metody**:
- `invite_user(home_id, inviter_id, email, role)` - Zaprasza użytkownika
- `get_home_users(home_id, requester_id)` - Pobiera listę użytkowników
- `remove_user(home_id, owner_id, user_id)` - Usuwa użytkownika z domu

### 3. HomeRoomManager
**Odpowiedzialność**: Zarządzanie pokojami w domu
- Edycja pokoi (nazwa, typ)
- Usuwanie pokoi
- Sprawdzanie uprawnień administracyjnych

**Metody**:
- `get_home_rooms(home_id, user_id)` - Pobiera pokoje domu
- `update_room(home_id, user_id, room_id, name, room_type)` - Aktualizuje pokój
- `delete_room(home_id, user_id, room_id)` - Usuwa pokój

### 4. HomeDeletionManager
**Odpowiedzialność**: Zarządzanie usuwaniem domów
- Usuwanie całego domu z wszystkimi danymi
- Informacje o konsekwencjach usunięcia
- Sprawdzanie uprawnień właściciela

**Metody**:
- `delete_home(home_id, owner_id)` - Usuwa dom permanentnie
- `get_deletion_info(home_id, owner_id)` - Pobiera info o tym co zostanie usunięte

### 5. HomeSettingsManager
**Odpowiedzialność**: Główny koordynator wszystkich managerów
- Centralne zarządzanie wszystkimi aspektami domu
- Agregowanie danych dla strony ustawień
- Koordynacja między różnymi managerami

**Metody**:
- `get_home_settings_data(home_id, user_id)` - Pobiera wszystkie dane dla strony ustawień

## API Endpoints

Nowe endpoint'y zostały przeniesione do `home_settings_routes.py`:

### Strona główna
- `GET /home/<home_id>/settings` - Strona ustawień domu

### API - Informacje o domu
- `POST /api/home/<home_id>/info/update` - Aktualizacja podstawowych informacji

### API - Zarządzanie użytkownikami  
- `POST /api/home/<home_id>/users/invite` - Zaproszenie użytkownika
- `GET /api/home/<home_id>/users` - Lista użytkowników domu
- `DELETE /api/home/<home_id>/users/<user_id>/remove` - Usunięcie użytkownika

### API - Zarządzanie pokojami
- `PUT /api/home/<home_id>/rooms/<room_id>/update` - Aktualizacja pokoju
- `DELETE /api/home/<home_id>/rooms/<room_id>/delete` - Usunięcie pokoju

### API - Usuwanie domu
- `GET /api/home/<home_id>/deletion-info` - Informacje o usuwaniu
- `DELETE /api/home/<home_id>/delete` - Usunięcie domu

## Bezpieczeństwo

Każda klasa implementuje własne sprawdzanie uprawnień:
- **Właściciele** - mogą wszystko (aktualizacja, zapraszanie, usuwanie)
- **Administratorzy** - mogą zarządzać pokojami i urządzeniami
- **Użytkownicy** - mogą tylko przeglądać

## Zalety nowej architektury

1. **Separacja odpowiedzialności** - każda klasa ma jasno określone zadania
2. **Łatwość testowania** - można testować każdy aspekt osobno
3. **Skalowalność** - łatwo dodać nowe funkcje bez wpływu na istniejące
4. **Bezpieczeństwo** - każda klasa ma własną walidację uprawnień
5. **Maintainable** - kod jest lepiej zorganizowany i czytelny

## Migracja ze starych endpoint'ów

Stare endpoint'y w `multi_home_routes.py` przekierowują do nowych:
- `/api/home/<id>/update` → `/api/home/<id>/info/update`
- `/api/home/<id>/invite` → `/api/home/<id>/users/invite`

## Integracja z bazą danych

Klasy używają `MultiHomeDBManager` do operacji na bazie danych. Niektóre metody wymagają jeszcze implementacji w `MultiHomeDBManager`:

- `update_home_info()`
- `create_invitation()`
- `get_home_users()`
- `remove_user_from_home()`
- `update_room()`
- `delete_room()`
- `delete_home_completely()`

## Użycie

```python
from app.home_management import HomeSettingsManager
from utils.multi_home_db_manager import MultiHomeDBManager

# Inicjalizacja
db = MultiHomeDBManager(...)
manager = HomeSettingsManager(db)

# Aktualizacja informacji o domu
result = manager.info_manager.update_home_info(
    home_id="123",
    user_id="456", 
    name="Nowa nazwa",
    description="Nowy opis"
)

# Zaproszenie użytkownika
result = manager.user_manager.invite_user(
    home_id="123",
    inviter_id="456",
    email="user@example.com",
    role="user"
)
```