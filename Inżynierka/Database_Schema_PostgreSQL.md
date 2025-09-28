# Schemat Bazy Danych PostgreSQL 17.5 - System SmartHome

## Przegląd

System SmartHome wykorzystuje bazę danych PostgreSQL 17.5 z 12 głównymi tabelami, zaawansowanym systemem indeksów i automatycznymi triggerami. Baza zapewnia pełną integralnośc referencyjną, audyt zmian oraz efektywne przechowywanie danych JSONB.

## Struktura Tabel

### 1. Tabele Główne

#### 1.1 Users - Zarządzanie Użytkownikami
```sql
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    profile_picture TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indeksy wydajnościowe
CREATE INDEX idx_users_name ON users (name);
CREATE INDEX idx_users_email ON users (email);
```

**Opis**: Przechowuje dane użytkowników systemu z systemem ról (admin/user).

#### 1.2 Rooms - Pokoje
```sql
CREATE TABLE rooms (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_rooms_order ON rooms (display_order);
```

**Opis**: Definiuje pokoje w domu z możliwością sortowania.

#### 1.3 Devices - Urządzenia IoT
```sql
CREATE TABLE devices (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    device_type VARCHAR(50) NOT NULL,
    state BOOLEAN DEFAULT false,
    temperature NUMERIC(5,2) DEFAULT 22.0,
    min_temperature NUMERIC(5,2) DEFAULT 16.0,
    max_temperature NUMERIC(5,2) DEFAULT 30.0,
    display_order INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT check_device_type 
        CHECK (device_type IN ('button', 'temperature_control'))
);

-- Indeksy optymalizujące zapytania
CREATE INDEX idx_devices_room ON devices (room_id);
CREATE INDEX idx_devices_type ON devices (device_type);
CREATE INDEX idx_devices_order ON devices (room_id, display_order);
```

**Opis**: Główna tabela urządzeń IoT z obsługą przełączników i termostatów.

#### 1.4 Room_Temperature_States - Stany Temperaturowe Pokojów
```sql
CREATE TABLE room_temperature_states (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    room_id UUID UNIQUE REFERENCES rooms(id) ON DELETE CASCADE,
    current_temperature NUMERIC(5,2) DEFAULT 22.0 NOT NULL,
    target_temperature NUMERIC(5,2) DEFAULT 22.0,
    heating_active BOOLEAN DEFAULT false,
    last_updated TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_temp_states_room ON room_temperature_states (room_id);
```

**Opis**: Przechowuje aktualne stany temperaturowe dla każdego pokoju.

### 2. System Automatyzacji

#### 2.1 Automations - Definicje Automatyzacji
```sql
CREATE TABLE automations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    trigger_config JSONB NOT NULL,
    actions_config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT true,
    last_executed TIMESTAMPTZ,
    execution_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    last_error_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_automations_enabled ON automations (enabled);
CREATE INDEX idx_automations_name ON automations (name);
```

**Opis**: Definicje automatyzacji z konfiguracją w formacie JSONB.

#### 2.2 Automation_Executions - Historia Wykonań
```sql
CREATE TABLE automation_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    automation_id UUID REFERENCES automations(id) ON DELETE CASCADE,
    execution_status VARCHAR(50) NOT NULL,
    trigger_data JSONB,
    actions_executed JSONB,
    error_message TEXT,
    execution_time_ms INTEGER,
    executed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_auto_exec_automation ON automation_executions (automation_id);
CREATE INDEX idx_auto_exec_time ON automation_executions (executed_at DESC);
CREATE INDEX idx_auto_exec_status ON automation_executions (execution_status);
```

**Opis**: Rejestr wszystkich wykonań automatyzacji z metrykami wydajności.

### 3. Audyt i Historia

#### 3.1 Device_History - Historia Zmian Urządzeń
```sql
CREATE TABLE device_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    old_state JSONB,
    new_state JSONB,
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    change_reason VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_device_history_device ON device_history (device_id);
CREATE INDEX idx_device_history_time ON device_history (created_at DESC);
```

**Opis**: Kompletna historia zmian stanów urządzeń z informacją o autorze zmiany.

#### 3.2 Management_Logs - Logi Administracyjne
```sql
CREATE TABLE management_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT now() NOT NULL,
    level VARCHAR(20) DEFAULT 'info' NOT NULL,
    message TEXT NOT NULL,
    event_type VARCHAR(100),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(255),
    ip_address INET,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_logs_timestamp ON management_logs (timestamp DESC);
CREATE INDEX idx_logs_level ON management_logs (level);
CREATE INDEX idx_logs_event_type ON management_logs (event_type);
CREATE INDEX idx_logs_user ON management_logs (user_id);
```

**Opis**: Centralne logowanie wszystkich akcji administracyjnych w systemie.

### 4. Zarządzanie Sesjami i Bezpieczeństwo

#### 4.1 Session_Tokens - Tokeny Sesji
```sql
CREATE TABLE session_tokens (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    remember_me BOOLEAN DEFAULT false,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_session_user ON session_tokens (user_id);
CREATE INDEX idx_session_token ON session_tokens (token_hash);
CREATE INDEX idx_session_expires ON session_tokens (expires_at);
```

**Opis**: Zaawansowane zarządzanie sesjami użytkowników z obsługą "Zapamiętaj mnie".

### 5. Konfiguracja Systemu

#### 5.1 System_Settings - Ustawienia Systemowe
```sql
CREATE TABLE system_settings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value JSONB,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_system_settings_key ON system_settings (setting_key);
```

**Opis**: Elastyczne przechowywanie ustawień systemowych w formacie JSONB.

### 6. System Powiadomień

#### 6.1 Notification_Settings - Ustawienia Powiadomień
```sql
CREATE TABLE notification_settings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    home_id UUID DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(255) NOT NULL,
    setting_value JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(home_id, setting_key)
);

CREATE INDEX idx_notif_settings_home ON notification_settings (home_id);
```

#### 6.2 Notification_Recipients - Odbiorcy powiadomień
```sql
CREATE TABLE notification_recipients (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    home_id UUID NOT NULL,
    email VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_notif_recipients_home ON notification_recipients (home_id);
CREATE INDEX idx_notif_recipients_enabled ON notification_recipients (enabled);
```

## Triggery i Funkcje

### Automatyczna Aktualizacja Timestampów
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Zastosowanie triggerów
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_devices_updated_at 
    BEFORE UPDATE ON devices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at 
    BEFORE UPDATE ON rooms 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_automations_updated_at 
    BEFORE UPDATE ON automations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_settings_updated_at 
    BEFORE UPDATE ON notification_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_recipients_updated_at 
    BEFORE UPDATE ON notification_recipients 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at 
    BEFORE UPDATE ON system_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Rozszerzenia PostgreSQL

System wykorzystuje następujące rozszerzenia:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- Generacja UUID
CREATE EXTENSION IF NOT EXISTS plpgsql;      -- Procedury składowane
```

## Statystyki Bazy

- **Liczba tabel**: 12
- **Liczba indeksów**: 25+ (optymalizacja wydajności)
- **Liczba triggerów**: 7 (automatyczne timestampy)
- **Liczba foreign keys**: 15 (integralność referencyjna)
- **Obsługa JSONB**: 8 kolumn (elastyczne przechowywanie danych)

## Wzorce Projektowe Zastosowane

1. **UUID jako Primary Keys** - Unikalne identyfikatory globally unique
2. **TIMESTAMPTZ** - Wszystkie czasy z informacją o strefie czasowej
3. **JSONB** - Elastyczne przechowywanie konfiguracji i metadanych
4. **CASCADE/SET NULL** - Przemyślane zarządzanie integralności referencyjnej
5. **Indeksy kompozytowe** - Optymalizacja złożonych zapytań
6. **Triggery automatyczne** - Spójność danych bez interwencji aplikacji

## Przykłady Zapytań

### Pobranie wszystkich urządzeń w pokoju z historią
```sql
SELECT 
    d.*,
    dh.old_state,
    dh.new_state,
    dh.created_at as last_change
FROM devices d
LEFT JOIN device_history dh ON d.id = dh.device_id
WHERE d.room_id = $1
ORDER BY d.display_order, dh.created_at DESC;
```

### Statystyki wykonań automatyzacji
```sql
SELECT 
    a.name,
    a.execution_count,
    a.error_count,
    COUNT(ae.id) as recent_executions,
    AVG(ae.execution_time_ms) as avg_execution_time
FROM automations a
LEFT JOIN automation_executions ae ON a.id = ae.automation_id
WHERE ae.executed_at > NOW() - INTERVAL '24 hours'
GROUP BY a.id, a.name, a.execution_count, a.error_count;
```

### Czyszczenie wygasłych sesji
```sql
DELETE FROM session_tokens 
WHERE expires_at < NOW();
```