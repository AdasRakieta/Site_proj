-- ========================================================================
-- MULTI-HOME SYSTEM DATABASE MIGRATION
-- ========================================================================
-- This migration adds support for multiple homes in the SmartHome system
-- Each home can have its own rooms, devices, automations, and users
-- ========================================================================

-- 1. CREATE HOMES TABLE
-- ========================================================================
CREATE TABLE IF NOT EXISTS "public"."homes" (
    id uuid DEFAULT uuid_generate_v4() NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    address text,
    timezone character varying(50) DEFAULT 'UTC',
    owner_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT homes_pkey PRIMARY KEY (id),
    CONSTRAINT homes_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add trigger for updated_at
CREATE TRIGGER update_homes_updated_at 
    BEFORE UPDATE ON homes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 2. CREATE USER-HOME RELATIONSHIP TABLE
-- ========================================================================
CREATE TABLE IF NOT EXISTS "public"."user_homes" (
    id uuid DEFAULT uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    home_id uuid NOT NULL,
    role character varying(50) DEFAULT 'member',  -- owner, admin, member, guest
    invited_by uuid,
    joined_at timestamp with time zone DEFAULT now(),
    permissions jsonb DEFAULT '{}',
    CONSTRAINT user_homes_pkey PRIMARY KEY (id),
    CONSTRAINT user_homes_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT user_homes_home_id_fkey FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE,
    CONSTRAINT user_homes_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT user_homes_user_home_unique UNIQUE (user_id, home_id)
);

-- 3. ADD HOME_ID TO EXISTING TABLES
-- ========================================================================

-- Add home_id to rooms
ALTER TABLE "public"."rooms" 
ADD COLUMN IF NOT EXISTS home_id uuid;

-- Add foreign key constraint for rooms.home_id
ALTER TABLE "public"."rooms" 
ADD CONSTRAINT rooms_home_id_fkey 
FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

-- Update unique constraint for rooms (name unique per home)
ALTER TABLE "public"."rooms" 
DROP CONSTRAINT IF EXISTS rooms_name_key;

ALTER TABLE "public"."rooms" 
ADD CONSTRAINT rooms_name_home_unique UNIQUE (name, home_id);

-- Add home_id to automations
ALTER TABLE "public"."automations" 
ADD COLUMN IF NOT EXISTS home_id uuid;

-- Add foreign key constraint for automations.home_id
ALTER TABLE "public"."automations" 
ADD CONSTRAINT automations_home_id_fkey 
FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

-- Update unique constraint for automations (name unique per home)
ALTER TABLE "public"."automations" 
DROP CONSTRAINT IF EXISTS automations_name_key;

ALTER TABLE "public"."automations" 
ADD CONSTRAINT automations_name_home_unique UNIQUE (name, home_id);

-- Add home_id to management_logs
ALTER TABLE "public"."management_logs" 
ADD COLUMN IF NOT EXISTS home_id uuid;

-- Add foreign key constraint for management_logs.home_id
ALTER TABLE "public"."management_logs" 
ADD CONSTRAINT management_logs_home_id_fkey 
FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE SET NULL;

-- 4. UPDATE NOTIFICATION TABLES
-- ========================================================================

-- Update notification_settings to have proper home_id foreign key
ALTER TABLE "public"."notification_settings" 
ADD CONSTRAINT notification_settings_home_id_fkey 
FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

-- Update notification_recipients to have proper home_id foreign key  
ALTER TABLE "public"."notification_recipients" 
ADD CONSTRAINT notification_recipients_home_id_fkey 
FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

-- 5. CREATE DEFAULT HOME FOR EXISTING DATA
-- ========================================================================

-- Insert default home (will be updated with actual data)
INSERT INTO homes (id, name, description, owner_id) 
SELECT 
    uuid_generate_v4(),
    'Default Home',
    'Automatically created during multi-home migration',
    u.id
FROM users u 
WHERE u.role = 'admin' 
LIMIT 1
ON CONFLICT DO NOTHING;

-- Get the default home ID for updates
DO $$
DECLARE
    default_home_id uuid;
    admin_user_id uuid;
BEGIN
    -- Get admin user
    SELECT id INTO admin_user_id FROM users WHERE role = 'admin' LIMIT 1;
    
    -- Get or create default home
    SELECT id INTO default_home_id FROM homes WHERE name = 'Default Home' LIMIT 1;
    
    IF default_home_id IS NULL THEN
        INSERT INTO homes (name, description, owner_id) 
        VALUES ('Default Home', 'Automatically created during multi-home migration', admin_user_id)
        RETURNING id INTO default_home_id;
    END IF;
    
    -- Update existing rooms with default home_id
    UPDATE rooms SET home_id = default_home_id WHERE home_id IS NULL;
    
    -- Update existing automations with default home_id
    UPDATE automations SET home_id = default_home_id WHERE home_id IS NULL;
    
    -- Update existing management_logs with default home_id (optional)
    UPDATE management_logs SET home_id = default_home_id WHERE home_id IS NULL;
    
    -- Update existing notification_settings with default home_id
    UPDATE notification_settings SET home_id = default_home_id WHERE home_id IS NULL;
    
    -- Update existing notification_recipients with default home_id
    UPDATE notification_recipients SET home_id = default_home_id WHERE home_id IS NULL;
    
    -- Add all existing users to default home
    INSERT INTO user_homes (user_id, home_id, role, joined_at)
    SELECT u.id, default_home_id, 
           CASE WHEN u.role = 'admin' THEN 'owner' ELSE 'member' END,
           u.created_at
    FROM users u
    ON CONFLICT (user_id, home_id) DO NOTHING;
    
END $$;

-- 6. MAKE HOME_ID REQUIRED FOR CRITICAL TABLES
-- ========================================================================

-- Make home_id NOT NULL for rooms (after data migration)
ALTER TABLE "public"."rooms" 
ALTER COLUMN home_id SET NOT NULL;

-- Make home_id NOT NULL for automations (after data migration)
ALTER TABLE "public"."automations" 
ALTER COLUMN home_id SET NOT NULL;

-- 7. CREATE INDEXES FOR PERFORMANCE
-- ========================================================================

CREATE INDEX IF NOT EXISTS idx_rooms_home_id ON rooms(home_id);
CREATE INDEX IF NOT EXISTS idx_devices_room_id ON devices(room_id);
CREATE INDEX IF NOT EXISTS idx_automations_home_id ON automations(home_id);
CREATE INDEX IF NOT EXISTS idx_user_homes_user_id ON user_homes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_homes_home_id ON user_homes(home_id);
CREATE INDEX IF NOT EXISTS idx_management_logs_home_id ON management_logs(home_id);

-- 8. CREATE HELPER VIEWS
-- ========================================================================

-- View for complete device information with home context
CREATE OR REPLACE VIEW device_details AS
SELECT 
    d.id as device_id,
    d.name as device_name,
    d.device_type,
    d.state,
    d.temperature,
    d.enabled,
    r.id as room_id,
    r.name as room_name,
    h.id as home_id,
    h.name as home_name,
    d.created_at,
    d.updated_at
FROM devices d
JOIN rooms r ON d.room_id = r.id
JOIN homes h ON r.home_id = h.id;

-- View for user permissions per home
CREATE OR REPLACE VIEW user_home_permissions AS
SELECT 
    u.id as user_id,
    u.name as username,
    u.email,
    h.id as home_id,
    h.name as home_name,
    uh.role as home_role,
    uh.permissions,
    uh.joined_at
FROM users u
JOIN user_homes uh ON u.id = uh.user_id
JOIN homes h ON uh.home_id = h.id;

-- ========================================================================
-- MIGRATION COMPLETE
-- ========================================================================
-- The database now supports multiple homes with:
-- - Isolated rooms, devices, and automations per home
-- - User-home relationships with roles and permissions
-- - Proper foreign key constraints and indexes
-- - Backward compatibility with existing data
-- ========================================================================