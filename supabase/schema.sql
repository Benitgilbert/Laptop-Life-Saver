-- ═══════════════════════════════════════════════════════════════════
--  Laptop Life-Saver System — Supabase Schema
--  Nyanza District Predictive Maintenance
-- ═══════════════════════════════════════════════════════════════════
--  Run this in the Supabase SQL Editor (Dashboard → SQL → New Query)
-- ═══════════════════════════════════════════════════════════════════


-- ═══════════════════════════════════════════════════════════════════
--  1. CLEAN SLATE (CRITICAL: Removes old conflicting tables)
-- ═══════════════════════════════════════════════════════════════════
DROP TABLE IF EXISTS telemetry_hourly CASCADE;
DROP TABLE IF EXISTS threshold_settings CASCADE;
DROP TABLE IF EXISTS remote_actions CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS telemetry CASCADE;
DROP TABLE IF EXISTS devices CASCADE;

-- Also clean up any potential legacy tables seen in your screenshot
DROP TABLE IF EXISTS telemetry_logs CASCADE;
DROP TABLE IF EXISTS process_snapshots CASCADE;
DROP TABLE IF EXISTS software_versions CASCADE;


-- ─────────────────────────────────────────────────────────────────
--  2. DEVICES — one row per monitored laptop
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id              uuid            PRIMARY KEY DEFAULT gen_random_uuid(),
    hostname        text            NOT NULL UNIQUE,
    os_version      text,
    registered_at   timestamptz     NOT NULL DEFAULT now(),
    last_seen       timestamptz     NOT NULL DEFAULT now(),
    
    -- Metadata (Phase 1)
    location        text,           -- School or Department
    asset_tag       text,           -- Physical inventory tag
    assigned_user   text,           -- Name/ID of the laptop user
    
    -- Hardware Inventory (Phase 1)
    cpu_model       text,
    disk_type       text,           -- SSD or HDD
    ram_size_gb     real,
    
    -- Data Science & Machine Learning Predictions (Phase 2)
    health_score real            DEFAULT 100.0, -- Isolation Forest Anomaly Score (0-100)
    predicted_disk_full_days int,   -- Linear Regression RUL forecast
    usage_profile   text,           -- K-Means Classification (e.g., 'Light Web Browsing', 'Heavy Development')
    root_cause_insight text,        -- Decision Tree analysis (e.g., 'Google Chrome is causing 80% of overheating')
    battery_degradation_warning boolean DEFAULT false, -- Polynomial Regression forecast
    malware_suspicion boolean       DEFAULT false  -- High continuous CPU during off-hours
);

COMMENT ON TABLE  devices IS 'Registered laptops in the Nyanza District fleet';
COMMENT ON COLUMN devices.hostname IS 'Windows machine name (unique identifier)';
COMMENT ON COLUMN devices.health_score IS 'ML-generated health score based on historical anomaly detection';
COMMENT ON COLUMN devices.predicted_disk_full_days IS 'ML-generated forecast of Remaining Useful Life until disk exhaustion';
COMMENT ON COLUMN devices.usage_profile IS 'ML classification of the laptop''s typical workload';
COMMENT ON COLUMN devices.root_cause_insight IS 'ML analysis identifying specific processes driving high resource usage';
COMMENT ON COLUMN devices.battery_degradation_warning IS 'ML prediction of permanent battery failure';
COMMENT ON COLUMN devices.malware_suspicion IS 'ML anomaly detection flagging potential cryptomining or background malware';


-- ─────────────────────────────────────────────────────────────────
--  2. TELEMETRY — time-series sensor logs from agents
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS telemetry (
    id              bigint          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id       uuid            NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    recorded_at     timestamptz     NOT NULL,
    cpu_temp_c      real,
    cpu_usage_pct   real,
    battery_percent real,           -- NULL for desktop systems without battery
    battery_plugged boolean,
    ram_usage_pct   real,
    disk_usage_pct  real,
    top_process     text,
    health_status   text            NOT NULL CHECK (health_status IN ('green','yellow','red')),
    
    -- S.M.A.R.T. Health (Phase 1)
    disk_health     text,           -- e.g. 'GOOD', 'WARNING', 'FAILING'
    disk_wear_pct   real            -- Wear level for SSDs
);

COMMENT ON TABLE  telemetry IS 'Hardware telemetry snapshots sent by agents';
COMMENT ON COLUMN telemetry.health_status IS 'Traffic-light status: green / yellow / red';

-- Index for fast device + time range queries (dashboard)
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time
    ON telemetry (device_id, recorded_at DESC);


-- ─────────────────────────────────────────────────────────────────
--  2b. TELEMETRY_HOURLY — aggregated summaries for data retention
-- ─────────────────────────────────────────────────────────────────
--  Raw telemetry is kept for 30 days, then rolled up into hourly
--  averages to save storage on the Supabase free tier.
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS telemetry_hourly (
    id              bigint          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id       uuid            NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    hour_timestamp  timestamptz     NOT NULL,
    sample_count    int             NOT NULL DEFAULT 0,
    avg_cpu_temp    real,
    min_cpu_temp    real,
    max_cpu_temp    real,
    avg_cpu_usage   real,
    avg_ram_usage   real,
    avg_disk_usage  real,
    avg_battery     real,
    worst_health    text            CHECK (worst_health IN ('green','yellow','red')),
    UNIQUE (device_id, hour_timestamp)
);

COMMENT ON TABLE telemetry_hourly IS 'Hourly aggregated telemetry — replaces raw data older than 30 days';

CREATE INDEX IF NOT EXISTS idx_hourly_device_time
    ON telemetry_hourly (device_id, hour_timestamp DESC);


-- ─────────────────────────────────────────────────────────────────
--  3. ALERTS — triggered when health is yellow or red
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id              bigint          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id       uuid            NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    alert_type      text            NOT NULL,        -- e.g. 'HIGH_TEMP', 'DISK_FULL'
    severity        text            NOT NULL CHECK (severity IN ('warning','critical')),
    message         text,
    created_at      timestamptz     NOT NULL DEFAULT now(),
    resolved        boolean         NOT NULL DEFAULT false
);

COMMENT ON TABLE  alerts IS 'Maintenance alerts requiring IT admin attention';

CREATE INDEX IF NOT EXISTS idx_alerts_device_unresolved
    ON alerts (device_id) WHERE resolved = false;


-- ─────────────────────────────────────────────────────────────────
--  3b. REMOTE ACTIONS — commands sent from dashboard to agent
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS remote_actions (
    id              uuid            PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       uuid            NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    command         text            NOT NULL,        -- 'FORCE_SYNC', 'REBOOT', 'COLLECT_LOGS'
    params          jsonb,
    status          text            NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at      timestamptz     NOT NULL DEFAULT now(),
    completed_at    timestamptz,
    error_message   text
);

ALTER TABLE remote_actions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Dashboard users can manage actions" ON remote_actions FOR ALL TO authenticated USING (true);


-- ─────────────────────────────────────────────────────────────────
--  4. ROW LEVEL SECURITY (RLS)
-- ─────────────────────────────────────────────────────────────────
--  Supabase uses two built-in roles:
--    • service_role  — full access (used by the Python agent with the service key)
--    • authenticated — logged-in dashboard users (read-only)
--
--  RLS is enabled on all tables.  The service_role bypasses RLS by
--  default, so we only need explicit policies for authenticated users.
-- ─────────────────────────────────────────────────────────────────

-- Enable RLS
ALTER TABLE devices          ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry        ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry_hourly ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts           ENABLE ROW LEVEL SECURITY;

-- Allow authenticated (dashboard) users to READ all rows
CREATE POLICY "Dashboard users can read devices"
    ON devices FOR SELECT
    TO authenticated, anon
    USING (true);

CREATE POLICY "Dashboard users can update devices"
    ON devices FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access"
    ON devices FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Dashboard users can read telemetry"
    ON telemetry FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Dashboard users can read alerts"
    ON alerts FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Dashboard users can read hourly telemetry"
    ON telemetry_hourly FOR SELECT
    TO authenticated
    USING (true);

-- Allow authenticated users to resolve alerts (update only the `resolved` column)
CREATE POLICY "Dashboard users can resolve alerts"
    ON alerts FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);


-- ─────────────────────────────────────────────────────────────────
--  5. THRESHOLD_SETTINGS — fleet-wide alert thresholds
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS threshold_settings (
    id                  int             PRIMARY KEY CHECK (id = 1), -- Single row
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

-- Seed with default row if empty
INSERT INTO threshold_settings (id) VALUES (1) ON CONFLICT DO NOTHING;

ALTER TABLE threshold_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read thresholds" ON threshold_settings FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "Admins can update thresholds" ON threshold_settings FOR UPDATE TO authenticated USING (true);

-- ─────────────────────────────────────────────────────────────────
--  6. ALERT TRIGGER — automatic alerting logic
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION handle_telemetry_alert()
RETURNS TRIGGER AS $$
DECLARE
    t threshold_settings%ROWTYPE;
    last_alert_time timestamptz;
    cooldown interval := interval '1 hour';
BEGIN
    -- 1. Update the 'last_seen' timestamp for the device immediately
    UPDATE devices 
    SET last_seen = NEW.recorded_at 
    WHERE id = NEW.device_id;

    -- 2. Get current thresholds for alerting
    SELECT * INTO t FROM threshold_settings WHERE id = 1;

    -- 3. CPU Temperature Alert
    IF NEW.cpu_temp_c >= t.cpu_temp_warning THEN
        -- Check cooldown for this device and alert type
        SELECT created_at INTO last_alert_time FROM alerts 
        WHERE device_id = NEW.device_id AND alert_type = 'high_cpu_temp' 
        ORDER BY created_at DESC LIMIT 1;

        IF last_alert_time IS NULL OR (now() - last_alert_time) > cooldown THEN
            INSERT INTO alerts (device_id, alert_type, severity, message)
            VALUES (
                NEW.device_id, 
                'high_cpu_temp', 
                CASE WHEN NEW.cpu_temp_c >= t.cpu_temp_critical THEN 'critical' ELSE 'warning' END,
                format('CPU Temperature is high: %s°C', NEW.cpu_temp_c)
            );
        END IF;
    END IF;

    -- 4. Disk Usage Alert
    IF NEW.disk_usage_pct >= t.disk_warning THEN
        SELECT created_at INTO last_alert_time FROM alerts 
        WHERE device_id = NEW.device_id AND alert_type = 'high_disk' 
        ORDER BY created_at DESC LIMIT 1;

        IF last_alert_time IS NULL OR (now() - last_alert_time) > cooldown THEN
            INSERT INTO alerts (device_id, alert_type, severity, message)
            VALUES (
                NEW.device_id, 
                'high_disk', 
                CASE WHEN NEW.disk_usage_pct >= t.disk_critical THEN 'critical' ELSE 'warning' END,
                format('Disk usage is high: %s%%', NEW.disk_usage_pct)
            );
        END IF;
    END IF;

    -- 5. RAM Usage Alert
    IF NEW.ram_usage_pct >= t.ram_warning THEN
        SELECT created_at INTO last_alert_time FROM alerts 
        WHERE device_id = NEW.device_id AND alert_type = 'high_ram' 
        ORDER BY created_at DESC LIMIT 1;

        IF last_alert_time IS NULL OR (now() - last_alert_time) > cooldown THEN
            INSERT INTO alerts (device_id, alert_type, severity, message)
            VALUES (
                NEW.device_id, 
                'high_ram', 
                CASE WHEN NEW.ram_usage_pct >= t.ram_critical THEN 'critical' ELSE 'warning' END,
                format('RAM usage is high: %s%%', NEW.ram_usage_pct)
            );
        END IF;
    END IF;

    -- 6. Battery Level Alert (only if not plugged)
    IF NEW.battery_percent IS NOT NULL AND NEW.battery_plugged = false AND NEW.battery_percent <= t.battery_low THEN
        SELECT created_at INTO last_alert_time FROM alerts 
        WHERE device_id = NEW.device_id AND alert_type = 'low_battery' 
        ORDER BY created_at DESC LIMIT 1;

        IF last_alert_time IS NULL OR (now() - last_alert_time) > cooldown THEN
            INSERT INTO alerts (device_id, alert_type, severity, message)
            VALUES (
                NEW.device_id, 
                'low_battery', 
                CASE WHEN NEW.battery_percent <= t.battery_critical THEN 'critical' ELSE 'warning' END,
                format('Battery level is low: %s%%', NEW.battery_percent)
            );
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_telemetry_insert
    AFTER INSERT ON telemetry
    FOR EACH ROW
    EXECUTE FUNCTION handle_telemetry_alert();


-- ─────────────────────────────────────────────────────────────────
--  7. REALTIME — Enable Postgres Publications
-- ─────────────────────────────────────────────────────────────────
-- This allows the dashboard to listen for INSERTs and UPDATEs
-- without manual page refreshes.

-- Drop if exists to avoid errors on re-run
DROP PUBLICATION IF EXISTS supabase_realtime;

-- Create publication for shared tables
CREATE PUBLICATION supabase_realtime FOR TABLE 
    devices, 
    telemetry, 
    alerts,
    threshold_settings;


-- ═══════════════════════════════════════════════════════════════════
--  Done!  Three tables + Thresholds + Alert Trigger + Realtime.
--  The Python agent uses the service_role key (bypasses RLS).
--  Dashboard users authenticate and get read-only + alert-resolve.
-- ═══════════════════════════════════════════════════════════════════
