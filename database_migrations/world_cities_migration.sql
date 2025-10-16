-- ========================================================================
-- GLOBAL CITIES CACHE TABLE MIGRATION
-- ========================================================================
-- This migration creates the world_cities table for global city autocomplete
-- Used by the home location feature to cache cities from API Ninjas
-- ========================================================================

-- Create world_cities table
CREATE TABLE IF NOT EXISTS "public"."world_cities" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    population INTEGER,
    country VARCHAR(100),
    country_code VARCHAR(2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_world_cities_name ON world_cities(name);
CREATE INDEX IF NOT EXISTS idx_world_cities_country_code ON world_cities(country_code);
CREATE INDEX IF NOT EXISTS idx_world_cities_population ON world_cities(population DESC);
CREATE INDEX IF NOT EXISTS idx_world_cities_coords ON world_cities(latitude, longitude);

-- Add location columns to homes table if they don't exist
ALTER TABLE "public"."homes" 
ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 6),
ADD COLUMN IF NOT EXISTS longitude DECIMAL(10, 6),
ADD COLUMN IF NOT EXISTS city VARCHAR(255),
ADD COLUMN IF NOT EXISTS country VARCHAR(100),
ADD COLUMN IF NOT EXISTS country_code VARCHAR(2);

-- Create update trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger for world_cities updated_at
DROP TRIGGER IF EXISTS update_world_cities_updated_at ON world_cities;
CREATE TRIGGER update_world_cities_updated_at 
    BEFORE UPDATE ON world_cities 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE world_cities IS 'Global cities cache from API Ninjas, updated weekly on Mondays at 22:00';
