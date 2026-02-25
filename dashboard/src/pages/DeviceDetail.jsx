import { useParams, Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { ArrowLeft, Monitor, Thermometer, MemoryStick, HardDrive, Battery, BatteryCharging, Clock, Cpu, Plug, ZapOff, Gauge, ShieldCheck } from 'lucide-react'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from 'recharts'
import { supabase } from '../lib/supabase'
import { useTelemetry } from '../hooks/useTelemetry'
import { useAlerts } from '../hooks/useAlerts'
import { useThresholds, evaluateHealth } from '../hooks/useThresholds'
import { calculateHealthScore, estimateDaysUntilMaintenance } from '../lib/predictiveScore'
import StatusBadge from '../components/StatusBadge'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'
import HealthTimeline from '../components/HealthTimeline'

const TIME_RANGES = ['1h', '6h', '24h', '7d']

function formatTime(isoString) {
    const d = new Date(isoString)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function ChartCard({ title, icon: Icon, children, color = '#6366f1' }) {
    return (
        <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
                <Icon className="w-4 h-4" style={{ color }} />
                <h3 className="text-sm font-semibold text-surface-700">{title}</h3>
            </div>
            {children}
        </div>
    )
}

const tooltipStyle = {
    contentStyle: {
        borderRadius: '12px',
        border: 'none',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        fontSize: '12px',
        padding: '8px 12px',
    },
}

export default function DeviceDetail() {
    const { deviceId } = useParams()
    const [range, setRange] = useState('24h')
    const [device, setDevice] = useState(null)
    const [deviceLoading, setDeviceLoading] = useState(true)
    const { thresholds, loading: thresholdsLoading } = useThresholds()
    const { telemetry, loading: telemetryLoading } = useTelemetry(deviceId, range)

    const loading = deviceLoading || telemetryLoading || thresholdsLoading

    useEffect(() => {
        const fetchDevice = async () => {
            setDeviceLoading(true)
            const { data } = await supabase
                .from('devices')
                .select('*')
                .eq('id', deviceId)
                .single()
            setDevice(data)
            setDeviceLoading(false)
        }
        if (deviceId) fetchDevice()
    }, [deviceId])

    const chartData = telemetry.map(t => ({
        time: formatTime(t.recorded_at),
        cpu_temp: t.cpu_temp_c,
        ram: t.ram_usage_pct,
        disk: t.disk_usage_pct,
        battery: t.battery_percent,
        cpu_usage: t.cpu_usage_pct,
        top_process: t.top_process,
        health: t.health_status,
    }))

    const latestRecord = telemetry.length > 0 ? telemetry[telemetry.length - 1] : null

    // Predictive maintenance score (using custom thresholds)
    const { alerts: deviceAlerts } = useAlerts('active')
    const alertCount = deviceAlerts.filter(a => a.device_id === deviceId).length
    const healthScore = calculateHealthScore(latestRecord, alertCount, thresholds)
    const daysEstimate = estimateDaysUntilMaintenance(healthScore.score)

    if (loading) {
        return (
            <div className="space-y-6">
                <LoadingSkeleton rows={1} type="card" />
                <LoadingSkeleton rows={1} type="chart" />
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Back + Header */}
            <div>
                <Link to="/devices" className="btn-ghost text-xs mb-4 inline-flex">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Devices
                </Link>

                <div className="glass-card p-6 flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-accent-500 to-accent-700 shadow-lg">
                        <Monitor className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                        <h1 className="text-xl font-bold text-surface-800">{device?.hostname || 'Unknown'}</h1>
                        <p className="text-sm text-surface-500">{device?.os_version}</p>
                        <p className="text-xs text-surface-400 mt-1 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Registered: {device?.registered_at ? new Date(device.registered_at).toLocaleDateString() : '—'}
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* Predictive score badge */}
                        <div className="flex flex-col items-center gap-1">
                            <div
                                className="w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg"
                                style={{ backgroundColor: healthScore.color }}
                            >
                                {healthScore.score}
                            </div>
                            <span className="text-[10px] font-semibold" style={{ color: healthScore.color }}>
                                {healthScore.label}
                            </span>
                            <span className="text-[9px] text-surface-400">
                                ~{daysEstimate} days
                            </span>
                        </div>
                        {latestRecord && (
                            <StatusBadge status={evaluateHealth(latestRecord, thresholds)} size="md" glow />
                        )}
                    </div>
                </div>
            </div>

            {/* Live stats panel */}
            {latestRecord && (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    <div className="glass-card p-4 text-center">
                        <Thermometer className="w-4 h-4 text-amber-500 mx-auto mb-1" />
                        <p className="text-lg font-bold text-surface-800">{latestRecord.cpu_temp_c ?? '—'}°C</p>
                        <p className="text-[10px] text-surface-400">CPU Temp</p>
                    </div>
                    <div className="glass-card p-4 text-center">
                        <Gauge className="w-4 h-4 text-orange-500 mx-auto mb-1" />
                        <p className="text-lg font-bold text-surface-800">{latestRecord.cpu_usage_pct ?? '—'}%</p>
                        <p className="text-[10px] text-surface-400">CPU Usage</p>
                    </div>
                    <div className="glass-card p-4 text-center">
                        <MemoryStick className="w-4 h-4 text-accent-500 mx-auto mb-1" />
                        <p className="text-lg font-bold text-surface-800">{latestRecord.ram_usage_pct ?? '—'}%</p>
                        <p className="text-[10px] text-surface-400">RAM Usage</p>
                    </div>
                    <div className="glass-card p-4 text-center">
                        <HardDrive className="w-4 h-4 text-blue-500 mx-auto mb-1" />
                        <p className="text-lg font-bold text-surface-800">{latestRecord.disk_usage_pct ?? '—'}%</p>
                        <p className="text-[10px] text-surface-400">Disk Usage</p>
                    </div>
                    <div className="glass-card p-4 text-center">
                        {latestRecord.battery_plugged ? (
                            <BatteryCharging className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
                        ) : (
                            <Battery className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
                        )}
                        <p className="text-lg font-bold text-surface-800">
                            {latestRecord.battery_percent != null ? `${latestRecord.battery_percent}%` : 'N/A'}
                        </p>
                        <p className="text-[10px] text-surface-400">
                            {latestRecord.battery_plugged == null ? 'No Battery' : latestRecord.battery_plugged ? '⚡ Charging' : '🔋 On Battery'}
                        </p>
                    </div>
                    <div className="glass-card p-4 text-center">
                        <Cpu className="w-4 h-4 text-rose-500 mx-auto mb-1" />
                        <p className="text-sm font-bold text-surface-800 truncate" title={latestRecord.top_process}>
                            {latestRecord.top_process || 'N/A'}
                        </p>
                        <p className="text-[10px] text-surface-400">Top Process</p>
                    </div>
                    <div className="glass-card p-4 text-center">
                        <Clock className="w-4 h-4 text-surface-400 mx-auto mb-1" />
                        <p className="text-sm font-bold text-surface-800">
                            {latestRecord.recorded_at ? formatTime(latestRecord.recorded_at) : '—'}
                        </p>
                        <p className="text-[10px] text-surface-400">Last Reading</p>
                    </div>
                </div>
            )}

            {/* Time range selector */}
            <div className="flex gap-2">
                {TIME_RANGES.map(r => (
                    <button
                        key={r}
                        onClick={() => setRange(r)}
                        className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${range === r
                            ? 'bg-accent-600 text-white shadow-md'
                            : 'bg-surface-100 text-surface-500 hover:bg-surface-200'
                            }`}
                    >
                        {r}
                    </button>
                ))}
            </div>

            {/* Charts */}
            {telemetryLoading ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <LoadingSkeleton type="chart" />
                    <LoadingSkeleton type="chart" />
                </div>
            ) : chartData.length === 0 ? (
                <EmptyState
                    icon={Thermometer}
                    title="No telemetry data"
                    message={`No readings found for the last ${range}. Make sure the agent is running.`}
                />
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* CPU Temperature */}
                    <ChartCard title="CPU Temperature" icon={Thermometer} color="#f59e0b">
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.02} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} unit="°C" />
                                <Tooltip {...tooltipStyle} />
                                <Area type="monotone" dataKey="cpu_temp" stroke="#f59e0b" strokeWidth={2} fill="url(#tempGrad)" name="CPU Temp (°C)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </ChartCard>

                    {/* CPU Usage */}
                    <ChartCard title="CPU Usage" icon={Gauge} color="#ea580c">
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#ea580c" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#ea580c" stopOpacity={0.02} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} unit="%" domain={[0, 100]} />
                                <Tooltip {...tooltipStyle} />
                                <Area type="monotone" dataKey="cpu_usage" stroke="#ea580c" strokeWidth={2} fill="url(#cpuGrad)" name="CPU Usage (%)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </ChartCard>

                    {/* RAM Usage */}
                    <ChartCard title="RAM Usage" icon={MemoryStick} color="#6366f1">
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="ramGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#6366f1" stopOpacity={0.02} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} unit="%" domain={[0, 100]} />
                                <Tooltip {...tooltipStyle} />
                                <Area type="monotone" dataKey="ram" stroke="#6366f1" strokeWidth={2} fill="url(#ramGrad)" name="RAM (%)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </ChartCard>

                    {/* Disk Usage */}
                    <ChartCard title="Disk Usage" icon={HardDrive} color="#3b82f6">
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="diskGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} unit="%" domain={[0, 100]} />
                                <Tooltip {...tooltipStyle} />
                                <Area type="monotone" dataKey="disk" stroke="#3b82f6" strokeWidth={2} fill="url(#diskGrad)" name="Disk (%)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </ChartCard>

                    {/* Battery (only if data exists) */}
                    {chartData.some(d => d.battery != null) && (
                        <ChartCard title="Battery Level" icon={Battery} color="#10b981">
                            <ResponsiveContainer width="100%" height={220}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="battGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                                            <stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                    <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                    <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} unit="%" domain={[0, 100]} />
                                    <Tooltip {...tooltipStyle} />
                                    <Area type="monotone" dataKey="battery" stroke="#10b981" strokeWidth={2} fill="url(#battGrad)" name="Battery (%)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </ChartCard>
                    )}
                </div>
            )}

            {/* ── Health Timeline ────────────────────────── */}
            {telemetry.length > 0 && (
                <div className="glass-card p-6">
                    <h2 className="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-4 flex items-center gap-2">
                        <Clock className="w-4 h-4 text-surface-400" />
                        Health Timeline
                    </h2>
                    <HealthTimeline telemetry={telemetry} thresholds={thresholds} />
                </div>
            )}
        </div>
    )
}
