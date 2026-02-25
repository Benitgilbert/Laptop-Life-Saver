/**
 * Predictive Maintenance Score Calculator
 *
 * Computes a 0–100 health score based on telemetry data, recent alerts,
 * and user-customizable thresholds from the Settings page.
 *
 * Scoring weights:
 *   CPU Temperature  30%
 *   Disk Usage       25%
 *   RAM Usage        20%
 *   Battery Health   15%
 *   Alert Frequency  10%
 */

// ── Score a single metric (0–100, higher is better) ──────────

function scoreCpuTemp(temp, thresholds) {
    if (temp == null || temp === 0) return 100   // sensor unavailable → neutral
    const warn = thresholds?.cpu_temp_warning ?? 70
    const crit = thresholds?.cpu_temp_critical ?? 85

    if (temp <= warn * 0.7) return 100           // well below warning
    if (temp <= warn) return 85                  // approaching warning
    if (temp <= (warn + crit) / 2) return 60     // between warning and critical
    if (temp <= crit) return 30                  // near critical
    return 10                                    // above critical
}

function scoreDiskUsage(pct, thresholds) {
    if (pct == null) return 100
    const warn = thresholds?.disk_warning ?? 80
    const crit = thresholds?.disk_critical ?? 95

    if (pct <= warn * 0.6) return 100
    if (pct <= warn * 0.85) return 80
    if (pct <= warn) return 50
    if (pct <= crit) return 20
    return 5
}

function scoreRamUsage(pct, thresholds) {
    if (pct == null) return 100
    const warn = thresholds?.ram_warning ?? 80
    const crit = thresholds?.ram_critical ?? 95

    if (pct <= warn * 0.75) return 100
    if (pct <= warn * 0.9) return 80
    if (pct <= warn) return 55
    if (pct <= crit) return 25
    return 10
}

function scoreBattery(percent, plugged, thresholds) {
    if (percent == null) return 100  // desktop / no battery → neutral
    if (plugged) return Math.min(100, percent + 20)  // charging is good
    const low = thresholds?.battery_low ?? 20
    const crit = thresholds?.battery_critical ?? 10

    if (percent >= low * 2.5) return 100
    if (percent >= low * 1.5) return 70
    if (percent >= low) return 40
    if (percent >= crit) return 25
    return 15  // critically low
}

function scoreAlerts(recentAlertCount) {
    if (recentAlertCount === 0) return 100
    if (recentAlertCount <= 2) return 70
    if (recentAlertCount <= 5) return 40
    return 10  // many alerts = bad
}

// ── Main calculator ──────────────────────────────────────────

const WEIGHTS = {
    cpu_temp: 0.30,
    disk: 0.25,
    ram: 0.20,
    battery: 0.15,
    alerts: 0.10,
}

/**
 * @param {Object} telemetry - Latest telemetry record
 * @param {number} alertCount - Number of alerts in last 24h for this device
 * @param {Object} [thresholds] - User-configured thresholds from Settings
 * @returns {{ score: number, label: string, color: string, breakdown: Object }}
 */
export function calculateHealthScore(telemetry, alertCount = 0, thresholds = null) {
    if (!telemetry) {
        return { score: 0, label: 'No Data', color: '#94a3b8', breakdown: {} }
    }

    const breakdown = {
        cpu_temp: scoreCpuTemp(telemetry.cpu_temp_c, thresholds),
        disk: scoreDiskUsage(telemetry.disk_usage_pct, thresholds),
        ram: scoreRamUsage(telemetry.ram_usage_pct, thresholds),
        battery: scoreBattery(telemetry.battery_percent, telemetry.battery_plugged, thresholds),
        alerts: scoreAlerts(alertCount),
    }

    const score = Math.round(
        Object.entries(WEIGHTS).reduce(
            (sum, [key, weight]) => sum + (breakdown[key] * weight),
            0
        )
    )

    return {
        score,
        label: getLabel(score),
        color: getColor(score),
        breakdown,
    }
}

function getLabel(score) {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Fair'
    if (score >= 20) return 'Poor'
    return 'Critical'
}

function getColor(score) {
    if (score >= 80) return '#10b981'  // emerald
    if (score >= 60) return '#6366f1'  // indigo
    if (score >= 40) return '#f59e0b'  // amber
    if (score >= 20) return '#f97316'  // orange
    return '#ef4444'                   // red
}

/**
 * Estimate days until maintenance may be needed.
 * Simple heuristic based on score trend.
 */
export function estimateDaysUntilMaintenance(score) {
    if (score >= 80) return '30+'
    if (score >= 60) return '14–30'
    if (score >= 40) return '7–14'
    if (score >= 20) return '3–7'
    return 'Now'
}
