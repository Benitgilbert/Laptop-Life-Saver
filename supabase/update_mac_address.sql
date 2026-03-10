-- ═══════════════════════════════════════════════════════════════════
--  Laptop Life-Saver — Schema Update (MAC Address Support)
-- ═══════════════════════════════════════════════════════════════════
--  Run this in the Supabase SQL Editor to support the new agent version.
-- ═══════════════════════════════════════════════════════════════════

-- 1. Add mac_address to devices table
ALTER TABLE devices ADD COLUMN IF NOT EXISTS mac_address text;

-- 2. Create a unique constraint on mac_address (essential for the agent upsert)
CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_mac_address ON devices (mac_address);

-- 3. Add mac_address to telemetry for easier debugging
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS mac_address text;
