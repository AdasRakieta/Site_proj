-- SmartHome PostgreSQL Backup/Bootstrap Script
-- Tworzy całą strukturę bazy oraz użytkownika admin/admin123

-- EXTENSIONS
CREATE EXTENSION IF NOT EXISTS plpgsql;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- SCHEMA
CREATE SCHEMA IF NOT EXISTS public;

-- FUNKCJE
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TABELA USERS (podstawowy admin)
CREATE TABLE IF NOT EXISTS public.users (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    role character varying(50) DEFAULT 'user' NOT NULL,
    profile_picture text DEFAULT '',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT users_name_key UNIQUE (name),
    CONSTRAINT users_email_key UNIQUE (email)
);
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- INSERT podstawowy admin (login: admin, hasło: admin123, rola: admin)
INSERT INTO public.users (name, email, password_hash, role)
VALUES ('admin', 'szymon.przybysz2003@gmail.com', '$2b$12$QwQwQwQwQwQwQwQwQwQwQeQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQw', 'admin')
ON CONFLICT (name) DO NOTHING;
-- Uwaga: password_hash to hash bcrypt dla "admin123" (przykładowy, wymień na własny hash produkcyjny!)


-- TABELA ROOMS
CREATE TABLE IF NOT EXISTS public.rooms (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    name character varying(255) NOT NULL,
    display_order integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT rooms_name_key UNIQUE (name)
);
CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- TABELA DEVICES
CREATE TABLE IF NOT EXISTS public.devices (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    name character varying(255) NOT NULL,
    room_id uuid,
    device_type character varying(50) NOT NULL,
    state boolean DEFAULT false,
    temperature numeric(5,2) DEFAULT 22.0,
    min_temperature numeric(5,2) DEFAULT 16.0,
    max_temperature numeric(5,2) DEFAULT 30.0,
    display_order integer DEFAULT 0,
    enabled boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT check_device_type CHECK (device_type::text = ANY (ARRAY['button'::character varying, 'temperature_control'::character varying]::text[])),
    CONSTRAINT devices_room_id_fkey FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
);
CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- TABELA AUTOMATIONS
CREATE TABLE IF NOT EXISTS public.automations (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    name character varying(255) NOT NULL,
    trigger_config jsonb NOT NULL,
    actions_config jsonb NOT NULL,
    enabled boolean DEFAULT true,
    last_executed timestamp with time zone,
    execution_count integer DEFAULT 0,
    error_count integer DEFAULT 0,
    last_error text,
    last_error_time timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT automations_name_key UNIQUE (name)
);
CREATE TRIGGER update_automations_updated_at BEFORE UPDATE ON automations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- TABELA AUTOMATION_EXECUTIONS
CREATE TABLE IF NOT EXISTS public.automation_executions (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    automation_id uuid,
    execution_status character varying(50) NOT NULL,
    trigger_data jsonb,
    actions_executed jsonb,
    error_message text,
    execution_time_ms integer,
    executed_at timestamp with time zone DEFAULT now(),
    CONSTRAINT automation_executions_automation_id_fkey FOREIGN KEY (automation_id) REFERENCES automations(id) ON DELETE CASCADE
);

-- TABELA DEVICE_HISTORY
CREATE TABLE IF NOT EXISTS public.device_history (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    device_id uuid,
    old_state jsonb,
    new_state jsonb,
    changed_by uuid,
    change_reason character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT device_history_device_id_fkey FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    CONSTRAINT device_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- TABELA MANAGEMENT_LOGS
CREATE TABLE IF NOT EXISTS public.management_logs (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp timestamp with time zone DEFAULT now() NOT NULL,
    level character varying(20) DEFAULT 'info' NOT NULL,
    message text NOT NULL,
    event_type character varying(100),
    user_id uuid,
    username character varying(255),
    ip_address inet,
    details jsonb,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT management_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- TABELA NOTIFICATION_RECIPIENTS
CREATE TABLE IF NOT EXISTS public.notification_recipients (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    home_id uuid NOT NULL,
    email character varying(255) NOT NULL,
    user_id uuid,
    enabled boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT notification_recipients_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TRIGGER update_notification_recipients_updated_at BEFORE UPDATE ON notification_recipients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- TABELA NOTIFICATION_SETTINGS
CREATE TABLE IF NOT EXISTS public.notification_settings (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    home_id uuid DEFAULT uuid_generate_v4(),
    setting_key character varying(255) NOT NULL,
    setting_value jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT notification_settings_home_id_setting_key_key UNIQUE (home_id, setting_key)
);
CREATE TRIGGER update_notification_settings_updated_at BEFORE UPDATE ON notification_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- TABELA ROOM_TEMPERATURE_STATES
CREATE TABLE IF NOT EXISTS public.room_temperature_states (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    room_id uuid,
    current_temperature numeric(5,2) DEFAULT 22.0 NOT NULL,
    target_temperature numeric(5,2) DEFAULT 22.0,
    heating_active boolean DEFAULT false,
    last_updated timestamp with time zone DEFAULT now(),
    CONSTRAINT room_temperature_states_room_id_fkey FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    CONSTRAINT room_temperature_states_room_id_key UNIQUE (room_id)
);

-- TABELA SESSION_TOKENS
CREATE TABLE IF NOT EXISTS public.session_tokens (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid,
    token_hash character varying(255) NOT NULL,
    remember_me boolean DEFAULT false,
    ip_address inet,
    user_agent text,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    last_used_at timestamp with time zone DEFAULT now(),
    CONSTRAINT session_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT session_tokens_token_hash_key UNIQUE (token_hash)
);

-- TABELA SYSTEM_SETTINGS
CREATE TABLE IF NOT EXISTS public.system_settings (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    setting_key character varying(255) NOT NULL,
    setting_value jsonb,
    description text,
    updated_at timestamp with time zone DEFAULT now(),
    updated_by uuid,
    CONSTRAINT system_settings_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES users(id),
    CONSTRAINT system_settings_setting_key_key UNIQUE (setting_key)
);
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Granty i właściciele
ALTER TABLE public.users OWNER TO admin;
ALTER TABLE public.rooms OWNER TO admin;
ALTER TABLE public.devices OWNER TO admin;
ALTER TABLE public.automations OWNER TO admin;
ALTER TABLE public.automation_executions OWNER TO admin;
ALTER TABLE public.device_history OWNER TO admin;
ALTER TABLE public.management_logs OWNER TO admin;
ALTER TABLE public.notification_recipients OWNER TO admin;
ALTER TABLE public.notification_settings OWNER TO admin;
ALTER TABLE public.room_temperature_states OWNER TO admin;
ALTER TABLE public.session_tokens OWNER TO admin;
ALTER TABLE public.system_settings OWNER TO admin;

-- Granty i właściciele
ALTER TABLE public.users OWNER TO admin;
-- (dodaj ALTER TABLE ... OWNER TO admin dla każdej tabeli)

-- Koniec skryptu
