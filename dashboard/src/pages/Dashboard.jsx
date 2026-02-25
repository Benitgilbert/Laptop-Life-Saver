import { useEffect, useRef } from 'react'
import { Monitor, AlertTriangle, Activity, Thermometer, HardDrive, MemoryStick, Bell, BellRing, ShieldCheck, Wrench } from 'lucide-react'
import { useDevices } from '../hooks/useDevices'
import { useAlerts } from '../hooks/useAlerts'
import { useLatestTelemetry } from '../hooks/useTelemetry'
import { useNotifications } from '../hooks/useNotifications'
import { useThresholds, evaluateHealth } from '../hooks/useThresholds'
import { calculateHealthScore, estimateDaysUntilMaintenance } from '../lib/predictiveScore'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'
import AlertRow from '../components/AlertRow'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'
import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const HEALTH_COLORS = {
    green: '#10b981',
    yellow: '#f59e0b',
    red: '#ef4444',
}

export default function Dashboard() {
    const { devices, loading: devicesLoading } = useDevices()
    const { alerts, loading: alertsLoading, resolveAlert } = useAlerts('active')
    const { latest, loading: telemetryLoading } = useLatestTelemetry()
    const { permission, requestPermission, notify } = useNotifications()
    const { thresholds, loading: thresholdsLoading } = useThresholds()
    const seenAlertIds = useRef(new Set())

    const loading = devicesLoading || alertsLoading || telemetryLoading || thresholdsLoading

    // ── Real-time alert notifications ─────────────────
    useEffect(() => {
        // Seed already-seen alert IDs so we only notify on NEW ones
        alerts.forEach(a => seenAlertIds.current.add(a.id))
    }, [alerts])

    useEffect(() => {
        const channel = supabase
            .channel('dashboard-alert-notifications')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'alerts' }, (payload) => {
                const alert = payload.new
                if (seenAlertIds.current.has(alert.id)) return
                seenAlertIds.current.add(alert.id)

                // Fire browser notification
                notify(
                    `⚠️ ${alert.alert_type === 'high_cpu_temp' ? 'High CPU Temperature' :
                        alert.alert_type === 'low_battery' ? 'Low Battery' :
                            alert.alert_type === 'high_disk' ? 'High Disk Usage' :
                                alert.alert_type === 'high_ram' ? 'High RAM Usage' : 'Alert'}`,
                    alert.message || 'A device needs attention',
                    { tag: `alert-${alert.id}` }
                )
            })
            .subscribe()

        return () => supabase.removeChannel(channel)
    }, [notify])

    // ── Compute stats ───────────────────────────────
    const totalDevices = devices.length
    const activeAlerts = alerts.filter(a => !a.resolved).length

    // Health distribution — use custom thresholds instead of agent-side health_status
    const healthCounts = { green: 0, yellow: 0, red: 0 }
    latest.forEach(t => {
        const health = evaluateHealth(t, thresholds)
        healthCounts[health]++
    })

    const healthData = [
        { name: 'Healthy', value: healthCounts.green, color: HEALTH_COLORS.green },
        { name: 'Warning', value: healthCounts.yellow, color: HEALTH_COLORS.yellow },
        { name: 'Critical', value: healthCounts.red, color: HEALTH_COLORS.red },
    ].filter(d => d.value > 0)

    // Average temps
    const avgTemp = latest.length > 0
        ? (latest.reduce((sum, t) => sum + (t.cpu_temp_c || 0), 0) / latest.length).toFixed(1)
        : '—'

    const avgDisk = latest.length > 0
        ? (latest.reduce((sum, t) => sum + (t.disk_usage_pct || 0), 0) / latest.length).toFixed(1)
        : '—'

    const avgRam = latest.length > 0
        ? (latest.reduce((sum, t) => sum + (t.ram_usage_pct || 0), 0) / latest.length).toFixed(1)
        : '—'

    // ── Predictive scores per device (using custom thresholds) ──
    const deviceScores = devices.map(device => {
        const telemetry = latest.find(t => t.device_id === device.id)
        const deviceAlerts = alerts.filter(a => a.device_id === device.id).length
        const result = calculateHealthScore(telemetry, deviceAlerts, thresholds)
        return { device, telemetry, ...result }
    }).sort((a, b) => a.score - b.score) // worst first

    const needsAttention = deviceScores.filter(d => d.score < 80)

    if (loading) {
        return (
            <div className="space-y-6">
                <h1 className="text-2xl font-bold text-surface-800">Dashboard</h1>
                <LoadingSkeleton rows={4} type="card" />
                <LoadingSkeleton rows={1} type="chart" />
                <LoadingSkeleton rows={3} type="list" />
            </div>
        )
    }

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-surface-800 tracking-tight">
                        Fleet Overview
                    </h1>
                    <p className="text-surface-500 text-sm mt-1">
                        Real-time health monitoring for Nyanza District laptops
                    </p>
                </div>

                {/* Notification permission button */}
                {permission !== 'granted' && (
                    <button
                        onClick={requestPermission}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-50 text-accent-700 text-xs font-semibold hover:bg-accent-100 transition-all duration-200"
                    >
                        <BellRing className="w-4 h-4" />
                        Enable Notifications
                    </button>
                )}
            </div>

            {/* ── Summary cards ──────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    icon={Monitor}
                    label="Total Devices"
                    value={totalDevices}
                    sub={`${latest.length} reporting`}
                    color="accent"
                    delay={0}
                />
                <StatCard
                    icon={AlertTriangle}
                    label="Active Alerts"
                    value={activeAlerts}
                    sub={activeAlerts === 0 ? 'All clear ✓' : 'Needs attention'}
                    color={activeAlerts > 0 ? 'red' : 'green'}
                    delay={80}
                />
                <StatCard
                    icon={Thermometer}
                    label="Avg CPU Temp"
                    value={`${avgTemp}°C`}
                    sub="Across all devices"
                    color="yellow"
                    delay={160}
                />
                <StatCard
                    icon={HardDrive}
                    label="Avg Disk Usage"
                    value={`${avgDisk}%`}
                    sub="Across all devices"
                    color="blue"
                    delay={240}
                />
            </div>

            {/* ── Middle row: Health chart + Device status ── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Health distribution pie */}
                <div className="glass-card p-6 lg:col-span-1">
                    <h2 className="text-sm font-semibold text-surface-700 mb-4">Health Distribution</h2>
                    {healthData.length > 0 ? (
                        <div className="flex items-center justify-center">
                            <ResponsiveContainer width="100%" height={180}>
                                <PieChart>
                                    <Pie
                                        data={healthData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={50}
                                        outerRadius={75}
                                        paddingAngle={4}
                                        dataKey="value"
                                        stroke="none"
                                    >
                                        {healthData.map((entry, index) => (
                                            <Cell key={index} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{
                                            borderRadius: '12px',
                                            border: 'none',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                            fontSize: '12px',
                                        }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-44 text-surface-400 text-sm">
                            No telemetry data yet
                        </div>
                    )}
                    {/* Legend */}
                    <div className="flex justify-center gap-4 mt-2">
                        {[
                            { label: 'Healthy', color: 'bg-health-green', count: healthCounts.green },
                            { label: 'Warning', color: 'bg-health-yellow', count: healthCounts.yellow },
                            { label: 'Critical', color: 'bg-health-red', count: healthCounts.red },
                        ].map(h => (
                            <div key={h.label} className="flex items-center gap-1.5 text-xs text-surface-500">
                                <span className={`w-2 h-2 rounded-full ${h.color}`} />
                                {h.label} ({h.count})
                            </div>
                        ))}
                    </div>
                </div>

                {/* Device quick-status grid */}
                <div className="glass-card p-6 lg:col-span-2">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-sm font-semibold text-surface-700">Device Status</h2>
                        <Link to="/devices" className="text-xs text-accent-600 hover:text-accent-700 font-medium">
                            View all →
                        </Link>
                    </div>
                    {devices.length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {devices.map(device => {
                                const deviceTelemetry = latest.find(t => t.device_id === device.id)
                                const health = deviceTelemetry?.health_status || 'green'
                                return (
                                    <Link
                                        key={device.id}
                                        to={`/devices/${device.id}`}
                                        className="flex items-center gap-3 p-3 rounded-xl bg-surface-50 hover:bg-surface-100 transition-colors duration-200 border border-surface-100 hover:border-surface-200"
                                    >
                                        <div className="p-2 rounded-lg bg-surface-200/50">
                                            <Monitor className="w-4 h-4 text-surface-500" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-surface-700 truncate">{device.hostname}</p>
                                            <p className="text-[11px] text-surface-400 truncate">{device.os_version}</p>
                                        </div>
                                        <StatusBadge status={health} size="xs" showLabel={false} />
                                    </Link>
                                )
                            })}
                        </div>
                    ) : (
                        <EmptyState title="No devices" message="Run the agent on a laptop to register it." />
                    )}
                </div>
            </div>

            {/* ── Needs Attention (Predictive) ────────────── */}
            {needsAttention.length > 0 && (
                <div className="glass-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Wrench className="w-4 h-4 text-amber-500" />
                        <h2 className="text-sm font-semibold text-surface-700">Needs Attention</h2>
                        <span className="ml-auto text-[11px] text-surface-400">Sorted by risk (worst first)</span>
                    </div>
                    <div className="space-y-3">
                        {needsAttention.map(({ device, score, label, color }) => (
                            <Link
                                key={device.id}
                                to={`/devices/${device.id}`}
                                className="flex items-center gap-4 p-3 rounded-xl bg-surface-50 hover:bg-surface-100 transition-colors duration-200 border border-surface-100 hover:border-surface-200"
                            >
                                <div className="p-2 rounded-lg bg-surface-200/50">
                                    <Monitor className="w-4 h-4 text-surface-500" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-surface-700">{device.hostname}</p>
                                    <p className="text-[11px] text-surface-400">
                                        Maintenance in ~{estimateDaysUntilMaintenance(score)} days
                                    </p>
                                </div>
                                {/* Score badge */}
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-md"
                                        style={{ backgroundColor: color }}
                                    >
                                        {score}
                                    </div>
                                    <span className="text-xs font-semibold" style={{ color }}>
                                        {label}
                                    </span>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* All OK message */}
            {needsAttention.length === 0 && devices.length > 0 && (
                <div className="glass-card p-6 flex items-center gap-3">
                    <ShieldCheck className="w-5 h-5 text-emerald-500" />
                    <div>
                        <p className="text-sm font-semibold text-surface-700">All devices healthy</p>
                        <p className="text-[11px] text-surface-400">Every device has a health score of 80 or above</p>
                    </div>
                </div>
            )}

            {/* ── Recent alerts ─────────────────────────── */}
            <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-semibold text-surface-700">Recent Alerts</h2>
                    <Link to="/alerts" className="text-xs text-accent-600 hover:text-accent-700 font-medium">
                        View all →
                    </Link>
                </div>
                {alerts.length > 0 ? (
                    <div className="space-y-3">
                        {alerts.slice(0, 5).map(alert => (
                            <AlertRow key={alert.id} alert={alert} onResolve={resolveAlert} />
                        ))}
                    </div>
                ) : (
                    <EmptyState
                        icon={Activity}
                        title="No active alerts"
                        message="All systems are running smoothly. Alerts will appear here when issues are detected."
                    />
                )}
            </div>
        </div>
    )
}
