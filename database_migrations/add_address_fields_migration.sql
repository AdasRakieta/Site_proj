-- Migration: Add detailed address fields to homes table
-- Date: 2025-10-16
-- Description: Adds street, house_number, apartment_number, and postal_code fields

-- Add new address fields to homes table
ALTER TABLE homes 
ADD COLUMN IF NOT EXISTS street VARCHAR(255),
ADD COLUMN IF NOT EXISTS house_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS apartment_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS postal_code VARCHAR(10);

-- Add comments for documentation
COMMENT ON COLUMN homes.street IS 'Street name';
COMMENT ON COLUMN homes.house_number IS 'House number (can include building number)';
COMMENT ON COLUMN homes.apartment_number IS 'Apartment/flat number (optional)';
COMMENT ON COLUMN homes.postal_code IS 'Postal code (format: XX-XXX for Poland)';

-- Create index for faster address-based queries
CREATE INDEX IF NOT EXISTS idx_homes_postal_code ON homes(postal_code);
CREATE INDEX IF NOT EXISTS idx_homes_city ON homes(city);

-- Update the address column comment to indicate it's deprecated in favor of structured fields
COMMENT ON COLUMN homes.address IS 'Full address text (legacy - prefer using structured fields: street, house_number, apartment_number, postal_code)';

COMMIT;
