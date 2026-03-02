-- ═══════════════════════════════════════════════════════════════════
--  FORCE RESET: ALERTING BRAIN
--  Run this in the Supabase SQL Editor for project `kyiqysaniixjofwvqwvv`
-- ═══════════════════════════════════════════════════════════════════

-- 1. Re-create the threshold table with clean defaults
CREATE TABLE IF NOT EXISTS threshold_settings (
    id                  int             PRIMARY KEY CHECK (id = 1),
    cpu_temp_warning    real            NOT NULL DEFAULT 70,
    cpu_temp_critical   real            NOT NULL DEFAULT 85,
    disk_warning        real            NOT NULL DEFAULT 80,
    disk_critical       real            NOT NULL DEFAULT 95,
    ram_warning         real            NOT NULL DEFAULT 80,
    ram_critical        real            NOT NULL DEFAULT 95,
    battery_low         real            NOT NULL DEFAULT 20,
    battery_critical    real            NOT NULL DEFAULT 10,
    updated_at          timestamptz     NOT NULL DEFAULT now()
);

-- Ensure the sync row exists
INSERT INTO threshold_settings (id) VALUES (1) ON CONFLICT DO NOTHING;

-- 2. Drop the old trigger so we can start fresh
DROP TRIGGER IF EXISTS on_telemetry_insert ON telemetry;

-- 3. The logic (with safety checks for NULLs)
CREATE OR REPLACE FUNCTION handle_telemetry_alert()
RETURNS TRIGGER AS $$
DECLARE
    t threshold_settings%ROWTYPE;
    last_alert_time timestamptz;
    cooldown interval := interval '1 hour';
BEGIN
    -- Update 'last_seen'
    UPDATE devices SET last_seen = NEW.recorded_at WHERE id = NEW.device_id;

    -- Get thresholds
    SELECT * INTO t FROM threshold_settings WHERE id = 1;

    -- Safety: If thresholds are missing, use hardcoded defaults
    IF t.id IS NULL THEN
        RAISE WARNING 'Threshold settings missing (ID=1). Using defaults.';
        t.cpu_temp_warning := 70; t.disk_warning := 80; t.ram_warning := 80;
    END IF;

    -- RAM Alert
    IF COALESCE(NEW.ram_usage_pct, 0) >= t.ram_warning THEN
        SELECT created_at INTO last_alert_time FROM alerts 
        WHERE device_id = NEW.device_id AND alert_type = 'high_ram' 
        ORDER BY created_at DESC LIMIT 1;

        IF last_alert_time IS NULL OR (now() - last_alert_time) > cooldown THEN
            INSERT INTO alerts (device_id, alert_type, severity, message)
            VALUES (
                NEW.device_id, 'high_ram', 
                CASE WHEN NEW.ram_usage_pct >= t.ram_critical THEN 'critical' ELSE 'warning' END,
                format('RAM usage is high: %s%%', round(NEW.ram_usage_pct::numeric, 1))
            );
        END IF;
    END IF;

    -- Disk Alert
    IF COALESCE(NEW.disk_usage_pct, 0) >= t.disk_warning THEN
        SELECT created_at INTO last_alert_time FROM alerts 
        WHERE device_id = NEW.device_id AND alert_type = 'high_disk' 
        ORDER BY created_at DESC LIMIT 1;

        IF last_alert_time IS NULL OR (now() - last_alert_time) > cooldown THEN
            INSERT INTO alerts (device_id, alert_type, severity, message)
            VALUES (
                NEW.device_id, 'high_disk', 
                CASE WHEN NEW.disk_usage_pct >= t.disk_critical THEN 'critical' ELSE 'warning' END,
                format('Disk usage is high: %s%%', round(NEW.disk_usage_pct::numeric, 1))
            );
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Re-attach trigger
CREATE TRIGGER on_telemetry_insert
    AFTER INSERT ON telemetry
    FOR EACH ROW
    EXECUTE FUNCTION handle_telemetry_alert();

-- 5. TEST: Insert a manual alert just to see if the table works
INSERT INTO alerts (device_id, alert_type, severity, message)
SELECT id, 'system_test', 'warning', 'Manual system test — if you see this, the Alerts table is working!'
FROM devices LIMIT 1;
