import { useMemo } from 'react'
import { Clock, ArrowRight } from 'lucide-react'
import { evaluateHealth } from '../hooks/useThresholds'

const STATUS_CONFIG = {
    green: { label: 'Healthy', color: '#10b981', bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-700 dark:text-emerald-400', dot: 'bg-emerald-500' },
    yellow: { label: 'Warning', color: '#f59e0b', bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-400', dot: 'bg-amber-500' },
    red: { label: 'Critical', color: '#ef4444', bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-400', dot: 'bg-red-500' },
}

/**
 * Shows timeline of health status transitions.
 * Each node represents a change in health_status.
 */
export default function HealthTimeline({ telemetry, thresholds }) {
    // Compute transitions: only show when health CHANGES
    const transitions = useMemo(() => {
        if (!telemetry || telemetry.length === 0) return []

        const result = []
        let prevStatus = null

        for (const record of telemetry) {
            const status = evaluateHealth(record, thresholds)
            if (status !== prevStatus) {
                result.push({
                    status,
                    time: record.recorded_at,
                    cpu_temp: record.cpu_temp_c,
                    ram: record.ram_usage_pct,
                    disk: record.disk_usage_pct,
                    battery: record.battery_percent,
                })
                prevStatus = status
            }
        }

        return result.reverse() // newest first
    }, [telemetry])

    if (transitions.length === 0) {
        return (
            <div className="text-center py-8 text-surface-400 text-sm">
                No health transitions recorded
            </div>
        )
    }

    return (
        <div className="space-y-0">
            {transitions.map((t, i) => {
                const config = STATUS_CONFIG[t.status] || STATUS_CONFIG.green
                const time = new Date(t.time)
                const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                const dateStr = time.toLocaleDateString([], { month: 'short', day: 'numeric' })
                const isFirst = i === 0
                const isLast = i === transitions.length - 1

                return (
                    <div key={i} className="flex gap-4">
                        {/* Timeline column */}
                        <div className="flex flex-col items-center w-8">
                            <div className={`w-3 h-3 rounded-full ${config.dot} ring-4 ring-white dark:ring-gray-800 z-10 ${isFirst ? 'animate-pulse-soft' : ''}`} />
                            {!isLast && (
                                <div className="w-0.5 flex-1 bg-surface-200 dark:bg-gray-700 min-h-[40px]" />
                            )}
                        </div>

                        {/* Content */}
                        <div className={`flex-1 ${config.bg} rounded-xl p-3 mb-3 border border-surface-100 dark:border-gray-700`}>
                            <div className="flex items-center justify-between mb-1">
                                <span className={`text-xs font-bold ${config.text}`}>
                                    {config.label}
                                    {isFirst && <span className="ml-1.5 text-[10px] opacity-70">(current)</span>}
                                </span>
                                <span className="text-[10px] text-surface-400 flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {dateStr} {timeStr}
                                </span>
                            </div>
                            <div className="flex gap-3 text-[11px] text-surface-500 dark:text-surface-400">
                                {t.cpu_temp != null && <span>CPU: {t.cpu_temp}°C</span>}
                                {t.ram != null && <span>RAM: {t.ram}%</span>}
                                {t.disk != null && <span>Disk: {t.disk}%</span>}
                                {t.battery != null && <span>Battery: {t.battery}%</span>}
                            </div>
                        </div>
                    </div>
                )
            })}
        </div>
    )
}
