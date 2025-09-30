-- Migration: Add multihouse support to existing database
-- This adds the missing tables and columns needed for the multihouse system

-- First, create homes table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.homes (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    name character varying(255) NOT NULL,
    description text DEFAULT '',
    owner_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT homes_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add trigger for homes
CREATE TRIGGER IF NOT EXISTS update_homes_updated_at 
    BEFORE UPDATE ON homes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create user_homes junction table for user-home relationships
CREATE TABLE IF NOT EXISTS public.user_homes (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid NOT NULL,
    home_id uuid NOT NULL,
    role character varying(50) DEFAULT 'member' NOT NULL, -- owner, admin, member, guest
    joined_at timestamp with time zone DEFAULT now(),
    CONSTRAINT user_homes_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT user_homes_home_id_fkey FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE,
    CONSTRAINT user_homes_user_home_unique UNIQUE (user_id, home_id)
);

-- Add home_id to existing tables that need it
ALTER TABLE public.rooms 
ADD COLUMN IF NOT EXISTS home_id uuid;

ALTER TABLE public.devices 
ADD COLUMN IF NOT EXISTS home_id uuid;

ALTER TABLE public.management_logs 
ADD COLUMN IF NOT EXISTS home_id uuid;

-- Create default home if none exists
INSERT INTO public.homes (name, description, owner_id)
SELECT 'Default Home', 'Automatically created default home', u.id
FROM public.users u 
WHERE u.role = 'admin' 
AND NOT EXISTS (SELECT 1 FROM public.homes)
LIMIT 1;

-- Get the default home ID for updates
DO $$
DECLARE
    default_home_id uuid;
BEGIN
    SELECT id INTO default_home_id FROM public.homes ORDER BY created_at ASC LIMIT 1;
    
    IF default_home_id IS NOT NULL THEN
        -- Update existing rooms to belong to default home
        UPDATE public.rooms SET home_id = default_home_id WHERE home_id IS NULL;
        
        -- Update existing devices to belong to default home  
        UPDATE public.devices SET home_id = default_home_id WHERE home_id IS NULL;
        
        -- Update existing logs to belong to default home
        UPDATE public.management_logs SET home_id = default_home_id WHERE home_id IS NULL;
        
        -- Add all existing users to default home
        INSERT INTO public.user_homes (user_id, home_id, role)
        SELECT u.id, default_home_id, 
               CASE 
                   WHEN u.role = 'admin' THEN 'owner'
                   ELSE 'member'
               END
        FROM public.users u
        WHERE NOT EXISTS (
            SELECT 1 FROM public.user_homes uh 
            WHERE uh.user_id = u.id AND uh.home_id = default_home_id
        );
    END IF;
END $$;

-- Add foreign key constraints after data migration
ALTER TABLE public.rooms 
ADD CONSTRAINT IF NOT EXISTS rooms_home_id_fkey 
FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

ALTER TABLE public.devices 
ADD CONSTRAINT IF NOT EXISTS devices_home_id_fkey 
FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE;

-- Update unique constraints to include home_id
ALTER TABLE public.rooms 
DROP CONSTRAINT IF EXISTS rooms_name_key;

ALTER TABLE public.rooms 
ADD CONSTRAINT IF NOT EXISTS rooms_name_home_unique 
UNIQUE (name, home_id);

COMMIT;