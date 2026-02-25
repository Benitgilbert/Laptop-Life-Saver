import { useState } from 'react'
import { Monitor, ExternalLink, Clock, Cpu, BatteryCharging, Battery, Gauge, Search, ArrowUpDown, ChevronUp, ChevronDown, Download, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useDevices } from '../hooks/useDevices'
import { useLatestTelemetry } from '../hooks/useTelemetry'
import { exportCSV, exportPDF } from '../lib/exportUtils'
import { useThresholds, evaluateHealth } from '../hooks/useThresholds'
import StatusBadge from '../components/StatusBadge'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'

function timeAgo(dateString) {
    if (!dateString) return 'Never'
    const now = new Date()
    const date = new Date(dateString)
    const seconds = Math.floor((now - date) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
}

const HEALTH_FILTERS = [
    { key: 'all', label: 'All' },
    { key: 'green', label: 'Healthy' },
    { key: 'yellow', label: 'Warning' },
    { key: 'red', label: 'Critical' },
]

function SortableHeader({ label, sortKey, current, dir, onSort, align = 'center' }) {
    const active = current === sortKey
    const textAlign = align === 'left' ? 'text-left' : align === 'right' ? 'text-right' : 'text-center'
    return (
        <th
            className={`${textAlign} text-[11px] font-semibold text-surface-500 uppercase tracking-wider px-2 py-3 cursor-pointer select-none hover:text-surface-700 transition-colors`}
            onClick={() => onSort(sortKey)}
        >
            <span className="inline-flex items-center gap-0.5">
                {label}
                {active ? (
                    dir === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                ) : (
                    <ArrowUpDown className="w-3 h-3 opacity-30" />
                )}
            </span>
        </th>
    )
}

export default function Devices() {
    const { devices, loading: devicesLoading } = useDevices()
    const { latest } = useLatestTelemetry()
    const { thresholds, loading: thresholdsLoading } = useThresholds()

    const loading = devicesLoading || thresholdsLoading
    const [searchQuery, setSearchQuery] = useState('')
    const [healthFilter, setHealthFilter] = useState('all')
    const [sortBy, setSortBy] = useState('hostname')
    const [sortDir, setSortDir] = useState('asc')

    const handleSort = (key) => {
        if (sortBy === key) {
            setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        } else {
            setSortBy(key)
            setSortDir('asc')
        }
    }

    // ── Filter devices ────────────────────────────────
    const filteredDevices = devices.filter(device => {
        const query = searchQuery.toLowerCase()
        const matchesSearch = !query
            || device.hostname?.toLowerCase().includes(query)
            || device.os_version?.toLowerCase().includes(query)

        const t = latest.find(l => l.device_id === device.id)
        const health = evaluateHealth(t, thresholds)
        const matchesHealth = healthFilter === 'all' || health === healthFilter

        return matchesSearch && matchesHealth
    })

    // ── Sort devices ──────────────────────────────────
    const sortedDevices = [...filteredDevices].sort((a, b) => {
        const ta = latest.find(l => l.device_id === a.id) || {}
        const tb = latest.find(l => l.device_id === b.id) || {}
        let va, vb

        switch (sortBy) {
            case 'hostname': va = a.hostname || ''; vb = b.hostname || ''; break
            case 'os': va = a.os_version || ''; vb = b.os_version || ''; break
            case 'cpu': va = ta.cpu_temp_c ?? -1; vb = tb.cpu_temp_c ?? -1; break
            case 'ram': va = ta.ram_usage_pct ?? -1; vb = tb.ram_usage_pct ?? -1; break
            case 'disk': va = ta.disk_usage_pct ?? -1; vb = tb.disk_usage_pct ?? -1; break
            case 'battery': va = ta.battery_percent ?? -1; vb = tb.battery_percent ?? -1; break
            case 'last_seen': va = a.last_seen || ''; vb = b.last_seen || ''; break
            default: va = a.hostname || ''; vb = b.hostname || ''
        }

        if (typeof va === 'string') {
            const cmp = va.localeCompare(vb, undefined, { sensitivity: 'base' })
            return sortDir === 'asc' ? cmp : -cmp
        }
        return sortDir === 'asc' ? va - vb : vb - va
    })

    // ── Export helpers ────────────────────────────────
    const EXPORT_COLUMNS = ['hostname', 'os', 'health', 'cpu_temp', 'cpu_usage', 'ram', 'disk', 'battery', 'top_process', 'last_seen']
    const EXPORT_HEADERS = {
        hostname: 'Device', os: 'OS', health: 'Health', cpu_temp: 'CPU Temp (°C)',
        cpu_usage: 'CPU Usage (%)', ram: 'RAM (%)', disk: 'Disk (%)',
        battery: 'Battery (%)', top_process: 'Top Process', last_seen: 'Last Seen',
    }

    const buildExportData = () => sortedDevices.map(device => {
        const t = latest.find(l => l.device_id === device.id) || {}
        return {
            hostname: device.hostname, os: device.os_version,
            health: t.health_status || 'green', cpu_temp: t.cpu_temp_c,
            cpu_usage: t.cpu_usage_pct, ram: t.ram_usage_pct,
            disk: t.disk_usage_pct, battery: t.battery_percent,
            top_process: t.top_process, last_seen: device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never',
        }
    })

    if (loading) {
        return (
            <div className="space-y-6">
                <h1 className="text-2xl font-bold text-surface-800">Devices</h1>
                <LoadingSkeleton rows={5} type="list" />
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-surface-800 tracking-tight">Devices</h1>
                    <p className="text-surface-500 text-sm mt-1">
                        {filteredDevices.length} of {devices.length} laptop{devices.length !== 1 ? 's' : ''} shown
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => exportCSV(buildExportData(), EXPORT_COLUMNS, EXPORT_HEADERS, 'devices-report')}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-100 text-surface-600 text-xs font-semibold hover:bg-surface-200 transition-all duration-200"
                    >
                        <Download className="w-3.5 h-3.5" />
                        CSV
                    </button>
                    <button
                        onClick={() => exportPDF(buildExportData(), EXPORT_COLUMNS, EXPORT_HEADERS, 'Fleet Device Report')}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-accent-50 text-accent-700 text-xs font-semibold hover:bg-accent-100 transition-all duration-200"
                    >
                        <FileText className="w-3.5 h-3.5" />
                        PDF
                    </button>
                </div>
            </div>

            {/* ── Search & Filter bar ──────────────────── */}
            <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                    <input
                        type="text"
                        placeholder="Search by hostname or OS..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-surface-200 bg-white text-sm text-surface-700 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/30 focus:border-accent-400 transition-all duration-200"
                    />
                </div>
                <div className="flex gap-1.5">
                    {HEALTH_FILTERS.map(f => (
                        <button
                            key={f.key}
                            onClick={() => setHealthFilter(f.key)}
                            className={`px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-200 whitespace-nowrap ${healthFilter === f.key
                                ? 'bg-accent-600 text-white shadow-md'
                                : 'bg-surface-100 text-surface-500 hover:bg-surface-200'
                                }`}
                        >
                            {f.label}
                        </button>
                    ))}
                </div>
            </div>

            {sortedDevices.length === 0 ? (
                <EmptyState
                    icon={Monitor}
                    title={devices.length === 0 ? "No devices registered" : "No devices match your filters"}
                    message={devices.length === 0 ? "Start the Python agent on a laptop to register it." : "Try adjusting your search or filter."}
                />
            ) : (
                <>

                    {/* ── Desktop table ──────────────────────── */}
                    <div className="hidden md:block glass-card overflow-x-auto">
                        <table className="w-full table-auto">
                            <thead>
                                <tr className="border-b border-surface-200">
                                    <SortableHeader label="Device" sortKey="hostname" current={sortBy} dir={sortDir} onSort={handleSort} align="left" />
                                    <SortableHeader label="OS" sortKey="os" current={sortBy} dir={sortDir} onSort={handleSort} align="left" />
                                    <th className="text-center text-[11px] font-semibold text-surface-500 uppercase tracking-wider px-2 py-3">
                                        Health
                                    </th>
                                    <SortableHeader label="CPU" sortKey="cpu" current={sortBy} dir={sortDir} onSort={handleSort} />
                                    <SortableHeader label="RAM" sortKey="ram" current={sortBy} dir={sortDir} onSort={handleSort} />
                                    <SortableHeader label="Disk" sortKey="disk" current={sortBy} dir={sortDir} onSort={handleSort} />
                                    <SortableHeader label="Battery" sortKey="battery" current={sortBy} dir={sortDir} onSort={handleSort} />
                                    <th className="text-center text-[11px] font-semibold text-surface-500 uppercase tracking-wider px-2 py-3">
                                        Process
                                    </th>
                                    <SortableHeader label="Last Seen" sortKey="last_seen" current={sortBy} dir={sortDir} onSort={handleSort} align="right" />
                                    <th className="px-2 py-3" />
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-100">
                                {sortedDevices.map((device, i) => {
                                    const t = latest.find(l => l.device_id === device.id)
                                    const health = evaluateHealth(t, thresholds)
                                    return (
                                        <tr
                                            key={device.id}
                                            className="hover:bg-surface-50/80 transition-colors duration-150 animate-slide-up"
                                            style={{ animationDelay: `${i * 50}ms` }}
                                        >
                                            <td className="px-3 py-3">
                                                <div className="flex items-center gap-2">
                                                    <div className="p-1.5 rounded-lg bg-accent-50">
                                                        <Monitor className="w-3.5 h-3.5 text-accent-600" />
                                                    </div>
                                                    <span className="font-semibold text-xs text-surface-800">{device.hostname}</span>
                                                </div>
                                            </td>
                                            <td className="px-3 py-3 text-xs text-surface-500 max-w-[140px] truncate">
                                                {device.os_version || '—'}
                                            </td>
                                            <td className="px-2 py-3 text-center">
                                                <StatusBadge status={health} size="sm" />
                                            </td>
                                            <td className="px-2 py-3 text-center text-xs font-medium text-surface-600">
                                                {t?.cpu_temp_c != null ? `${t.cpu_temp_c}°C` : '—'}
                                            </td>
                                            <td className="px-2 py-3 text-center text-xs font-medium text-surface-600">
                                                {t?.ram_usage_pct != null ? `${t.ram_usage_pct}%` : '—'}
                                            </td>
                                            <td className="px-2 py-3 text-center text-xs font-medium text-surface-600">
                                                {t?.disk_usage_pct != null ? `${t.disk_usage_pct}%` : '—'}
                                            </td>
                                            <td className="px-2 py-3 text-center text-xs text-surface-600">
                                                {t?.battery_percent != null ? (
                                                    <span className="inline-flex items-center gap-1">
                                                        {t.battery_plugged ? <BatteryCharging className="w-3 h-3 text-emerald-500" /> : <Battery className="w-3 h-3 text-surface-400" />}
                                                        {t.battery_percent}%
                                                    </span>
                                                ) : <span className="text-surface-300">N/A</span>}
                                            </td>
                                            <td className="px-2 py-3 text-center text-[11px] font-medium text-surface-500 max-w-[100px] truncate">
                                                {t?.top_process || '—'}
                                            </td>
                                            <td className="px-2 py-3 text-right">
                                                <span className="text-[11px] text-surface-400 flex items-center justify-end gap-1">
                                                    <Clock className="w-3 h-3" />
                                                    {timeAgo(device.last_seen)}
                                                </span>
                                            </td>
                                            <td className="px-2 py-3 text-right">
                                                <Link
                                                    to={`/devices/${device.id}`}
                                                    className="btn-ghost text-[11px] whitespace-nowrap"
                                                >
                                                    <ExternalLink className="w-3 h-3" />
                                                    Details
                                                </Link>
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>

                    {/* ── Mobile card grid ───────────────────── */}
                    <div className="md:hidden space-y-3">
                        {sortedDevices.map((device, i) => {
                            const t = latest.find(l => l.device_id === device.id)
                            const health = evaluateHealth(t, thresholds)
                            return (
                                <Link
                                    key={device.id}
                                    to={`/devices/${device.id}`}
                                    className="glass-card p-4 flex items-center gap-4 animate-slide-up"
                                    style={{ animationDelay: `${i * 60}ms` }}
                                >
                                    <div className="p-2.5 rounded-xl bg-accent-50">
                                        <Monitor className="w-5 h-5 text-accent-600" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-semibold text-surface-800 truncate">{device.hostname}</p>
                                        <p className="text-[11px] text-surface-400 truncate">{device.os_version}</p>
                                        <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                                            {t?.cpu_temp_c != null && (
                                                <span className="text-[11px] text-surface-500">🌡 {t.cpu_temp_c}°C</span>
                                            )}
                                            {t?.ram_usage_pct != null && (
                                                <span className="text-[11px] text-surface-500">💾 {t.ram_usage_pct}%</span>
                                            )}
                                            {t?.battery_percent != null && (
                                                <span className="text-[11px] text-surface-500">{t.battery_plugged ? '⚡' : '🔋'} {t.battery_percent}%</span>
                                            )}
                                            {t?.top_process && (
                                                <span className="text-[11px] text-surface-400">⚙ {t.top_process}</span>
                                            )}
                                        </div>
                                    </div>
                                    <StatusBadge status={health} size="sm" showLabel={false} />
                                </Link>
                            )
                        })}
                    </div>
                </>
            )}
        </div>
    )
}
