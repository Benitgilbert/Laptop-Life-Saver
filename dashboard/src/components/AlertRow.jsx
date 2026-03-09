import { Link } from 'react-router-dom'
import { CheckCircle2, Clock } from 'lucide-react'

function formatDate(dateString) {
    const d = new Date(dateString)
    return d.toLocaleString([], {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}

function timeAgo(dateString) {
    const now = new Date()
    const date = new Date(dateString)
    const seconds = Math.floor((now - date) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
}

export default function AlertRow({ alert, onResolve }) {
    const severityStyles = {
        warning: {
            bg: 'bg-health-yellow-bg',
            text: 'text-amber-700',
            border: 'border-amber-200',
        },
        critical: {
            bg: 'bg-health-red-bg',
            text: 'text-red-700',
            border: 'border-red-200',
        },
    }

    const style = severityStyles[alert.severity] || severityStyles.warning

    return (
        <div className={`flex items-center gap-4 p-4 rounded-xl border ${style.border} ${style.bg} transition-all duration-300 hover:scale-[1.01]`}>
            {/* Severity badge */}
            <span className={`badge ${style.bg} ${style.text} uppercase tracking-wider`}>
                {alert.severity}
            </span>

            {/* Info */}
            <Link
                to={`/devices/${alert.device_id}`}
                className="flex-1 min-w-0 group cursor-pointer"
            >
                <p className="text-sm font-semibold text-surface-800 truncate group-hover:text-accent-600 transition-colors">
                    {alert.alert_type?.replace(/_/g, ' ')}
                </p>
                <p className="text-xs text-surface-500 mt-0.5 truncate">{alert.message}</p>
                <div className="flex items-center gap-3 mt-1">
                    <span className="text-[11px] text-surface-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {timeAgo(alert.created_at)}
                        <span className="opacity-60 ml-1">• {formatDate(alert.created_at)}</span>
                    </span>
                    {alert.devices?.hostname && (
                        <span className="text-[11px] text-surface-400 flex items-center gap-1">
                            <span>📟</span>
                            <span className="group-hover:underline">{alert.devices.hostname}</span>
                        </span>
                    )}
                </div>
            </Link>

            {/* Resolve button */}
            {!alert.resolved ? (
                <button
                    onClick={() => onResolve?.(alert.id)}
                    className="btn-ghost text-emerald-600 hover:bg-emerald-50 text-xs"
                >
                    <CheckCircle2 className="w-4 h-4" />
                    Resolve
                </button>
            ) : (
                <span className="badge bg-surface-100 text-surface-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Resolved
                </span>
            )}
        </div>
    )
}
