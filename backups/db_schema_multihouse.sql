-- ============================================================================
-- SmartHome Multi-Home Database Schema Export
-- Database: smarthome_multihouse
-- Generated: 2025-12-02
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Users table (global system users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    profile_picture TEXT DEFAULT '',
    default_home_id UUID,
    timezone VARCHAR(100) DEFAULT 'Europe/Warsaw',
    language VARCHAR(10) DEFAULT 'pl',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Homes table (multi-home support)
CREATE TABLE IF NOT EXISTS homes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID NOT NULL,
    description TEXT,
    address TEXT,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    city VARCHAR(255),
    country VARCHAR(255),
    country_code VARCHAR(2),
    street VARCHAR(255),
    house_number VARCHAR(50),
    apartment_number VARCHAR(50),
    postal_code VARCHAR(20),
    timezone VARCHAR(100) DEFAULT 'Europe/Warsaw',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User-Home membership (many-to-many with roles)
CREATE TABLE IF NOT EXISTS user_homes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    home_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, home_id)
);

-- Rooms (belong to a home)
CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    home_id UUID,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Devices (belong to rooms and homes)
-- NOTE: Column order matches actual database structure
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_id UUID NOT NULL,
    room_id UUID,
    name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    state BOOLEAN DEFAULT FALSE,  -- NULL allowed for devices like temperature_control
    temperature NUMERIC(5,2) DEFAULT 22.0,
    min_temperature NUMERIC(5,2) DEFAULT 16.0,
    max_temperature NUMERIC(5,2) DEFAULT 30.0,
    display_order INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    settings JSONB
);

-- Home automations (per-home automation rules)
CREATE TABLE IF NOT EXISTS home_automations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    trigger_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    actions_config JSONB NOT NULL DEFAULT '[]'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    execution_count INTEGER NOT NULL DEFAULT 0,
    last_executed TIMESTAMPTZ,
    error_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(home_id, name)
);

-- Legacy single-home automations (for compatibility)
CREATE TABLE IF NOT EXISTS automations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    trigger_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    actions_config JSONB NOT NULL DEFAULT '[]'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    execution_count INTEGER NOT NULL DEFAULT 0,
    last_executed TIMESTAMPTZ,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Home invitations
CREATE TABLE IF NOT EXISTS home_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_id UUID NOT NULL,
    inviter_id UUID NOT NULL,
    invitee_email VARCHAR(255) NOT NULL,
    invitation_code VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Home security states
CREATE TABLE IF NOT EXISTS home_security_states (
    home_id UUID PRIMARY KEY,
    state VARCHAR(50) NOT NULL DEFAULT 'Wyłączony',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID
);

-- Session tokens (user sessions with home context)
CREATE TABLE IF NOT EXISTS session_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    current_home_id UUID,
    ip_address VARCHAR(45),
    user_agent TEXT,
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN DEFAULT FALSE
);

-- Management logs (audit trail with multi-home support)
CREATE TABLE IF NOT EXISTS management_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    event_type VARCHAR(100),
    user_id UUID,
    username VARCHAR(255),
    ip_address INET,
    details JSONB,
    home_id UUID REFERENCES homes(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Notification recipients (who gets notifications)
CREATE TABLE IF NOT EXISTS notification_recipients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_id UUID NOT NULL,
    email VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    added_by UUID,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(home_id, email)
);

-- Notification settings (per-home notification config)
CREATE TABLE IF NOT EXISTS notification_settings (
    home_id UUID PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    notify_on_events JSONB DEFAULT '["security_alert", "device_offline"]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Room temperature states (historical temperature data)
CREATE TABLE IF NOT EXISTS room_temperature_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL,
    temperature NUMERIC(5,2) NOT NULL,
    humidity NUMERIC(5,2),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- System settings (global key-value config)
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(255) NOT NULL UNIQUE,
    setting_value JSONB,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID
);

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

ALTER TABLE users ADD CONSTRAINT fk_users_default_home 
    FOREIGN KEY (default_home_id) REFERENCES homes(id) ON DELETE SET NULL;

ALTER TABLE homes ADD CONSTRAINT fk_homes_owner 
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE user_homes ADD CONSTRAINT fk_user_homes_user 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    
ALTER TABLE user_homes ADD CONSTRAINT fk_user_homes_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

ALTER TABLE rooms ADD CONSTRAINT fk_rooms_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

ALTER TABLE devices ADD CONSTRAINT fk_devices_room 
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL;
    
ALTER TABLE devices ADD CONSTRAINT fk_devices_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

ALTER TABLE home_automations ADD CONSTRAINT fk_home_automations_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

ALTER TABLE home_invitations ADD CONSTRAINT fk_home_invitations_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;
    
ALTER TABLE home_invitations ADD CONSTRAINT fk_home_invitations_inviter 
    FOREIGN KEY (inviter_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE home_security_states ADD CONSTRAINT fk_home_security_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;
    
ALTER TABLE home_security_states ADD CONSTRAINT fk_home_security_updated_by 
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE session_tokens ADD CONSTRAINT fk_session_tokens_user 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    
ALTER TABLE session_tokens ADD CONSTRAINT fk_session_tokens_home 
    FOREIGN KEY (current_home_id) REFERENCES homes(id) ON DELETE SET NULL;

ALTER TABLE management_logs ADD CONSTRAINT fk_management_logs_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;
    
ALTER TABLE management_logs ADD CONSTRAINT fk_management_logs_user 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE notification_recipients ADD CONSTRAINT fk_notification_recipients_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;
    
ALTER TABLE notification_recipients ADD CONSTRAINT fk_notification_recipients_added_by 
    FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE notification_settings ADD CONSTRAINT fk_notification_settings_home 
    FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

ALTER TABLE room_temperature_states ADD CONSTRAINT fk_room_temperature_room 
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE;

ALTER TABLE system_settings ADD CONSTRAINT fk_system_settings_updated_by 
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);

CREATE INDEX IF NOT EXISTS idx_homes_owner ON homes(owner_id);

CREATE INDEX IF NOT EXISTS idx_user_homes_user ON user_homes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_homes_home ON user_homes(home_id);

CREATE INDEX IF NOT EXISTS idx_rooms_home ON rooms(home_id);
CREATE INDEX IF NOT EXISTS idx_rooms_display ON rooms(display_order);

CREATE INDEX IF NOT EXISTS idx_devices_room ON devices(room_id);
CREATE INDEX IF NOT EXISTS idx_devices_home ON devices(home_id);

CREATE INDEX IF NOT EXISTS idx_home_automations_home ON home_automations(home_id);
CREATE INDEX IF NOT EXISTS idx_home_automations_enabled ON home_automations(enabled);

CREATE INDEX IF NOT EXISTS idx_automations_name ON automations(name);

CREATE INDEX IF NOT EXISTS idx_invitations_code ON home_invitations(invitation_code);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON home_invitations(invitee_email);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON home_invitations(status);

CREATE INDEX IF NOT EXISTS idx_session_tokens_user ON session_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_session_tokens_token ON session_tokens(token);
CREATE INDEX IF NOT EXISTS idx_session_tokens_expires ON session_tokens(expires_at);

CREATE INDEX IF NOT EXISTS idx_management_logs_home ON management_logs(home_id);
CREATE INDEX IF NOT EXISTS idx_management_logs_user ON management_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_management_logs_event ON management_logs(event_type);

CREATE INDEX IF NOT EXISTS idx_notification_recipients_home ON notification_recipients(home_id);

CREATE INDEX IF NOT EXISTS idx_room_temperature_room ON room_temperature_states(room_id);
CREATE INDEX IF NOT EXISTS idx_room_temperature_recorded ON room_temperature_states(recorded_at);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMPS
-- ============================================================================

CREATE TRIGGER users_update_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER homes_update_updated_at BEFORE UPDATE ON homes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER rooms_update_updated_at BEFORE UPDATE ON rooms 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER devices_update_updated_at BEFORE UPDATE ON devices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER home_automations_update_updated_at BEFORE UPDATE ON home_automations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER automations_update_updated_at BEFORE UPDATE ON automations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER notification_settings_update_updated_at BEFORE UPDATE ON notification_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER system_settings_update_updated_at BEFORE UPDATE ON system_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA (Run once during setup)
-- ============================================================================

-- Create sys-admin user (password: Qwuizzy123.)
-- Run only if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'szymon.przybysz2003@gmail.com') THEN
        INSERT INTO users (id, name, email, password_hash, role, created_at, updated_at)
        VALUES (
            uuid_generate_v4(),
            'sysadmin',
            'szymon.przybysz2003@gmail.com',
            '$2a$12$fdlMw8XjO0F1ZKKV3OvjA.kPnTXVI0eC2UzzajHL2lWNfjYcmLKje',
            'sys-admin',
            NOW(),
            NOW()
        );
    END IF;
END $$;

-- Create default home for sys-admin
DO $$
DECLARE
    v_user_id UUID;
    v_home_id UUID;
BEGIN
    SELECT id INTO v_user_id FROM users WHERE email = 'szymon.przybysz2003@gmail.com';
    
    IF v_user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM homes WHERE owner_id = v_user_id) THEN
        v_home_id := uuid_generate_v4();
        
        INSERT INTO homes (id, name, owner_id, description, created_at, updated_at)
        VALUES (v_home_id, 'SysAdmin Home', v_user_id, 'Dom podstawowy sys-admin', NOW(), NOW());
        
        INSERT INTO user_homes (user_id, home_id, role, permissions, joined_at)
        VALUES (v_user_id, v_home_id, 'owner', '["full_control"]'::jsonb, NOW());
        
        UPDATE users SET default_home_id = v_home_id WHERE id = v_user_id;
    END IF;
END $$;

-- ============================================================================
-- SCHEMA VERSION INFO
-- ============================================================================

INSERT INTO system_settings (setting_key, setting_value, description, updated_at)
VALUES ('schema_version', '"1.0.0"'::jsonb, 'Database schema version', NOW())
ON CONFLICT (setting_key) DO UPDATE 
    SET setting_value = '"1.0.0"'::jsonb, updated_at = NOW();

-- END OF SCHEMA
