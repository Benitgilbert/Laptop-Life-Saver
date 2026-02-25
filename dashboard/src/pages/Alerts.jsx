import { useState } from 'react'
import { Bell, Filter } from 'lucide-react'
import { useAlerts } from '../hooks/useAlerts'
import AlertRow from '../components/AlertRow'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'

const FILTERS = [
    { key: 'all', label: 'All' },
    { key: 'active', label: 'Active' },
    { key: 'resolved', label: 'Resolved' },
]

export default function Alerts() {
    const [filter, setFilter] = useState('all')
    const { alerts, loading, resolveAlert } = useAlerts(filter)

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-surface-800 tracking-tight">Alerts</h1>
                    <p className="text-surface-500 text-sm mt-1">
                        {alerts.length} alert{alerts.length !== 1 ? 's' : ''} found
                    </p>
                </div>

                {/* Filter pills */}
                <div className="flex gap-2">
                    {FILTERS.map(f => (
                        <button
                            key={f.key}
                            onClick={() => setFilter(f.key)}
                            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${filter === f.key
                                    ? 'bg-accent-600 text-white shadow-md'
                                    : 'bg-surface-100 text-surface-500 hover:bg-surface-200'
                                }`}
                        >
                            {f.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Alert list */}
            {loading ? (
                <LoadingSkeleton rows={4} type="list" />
            ) : alerts.length === 0 ? (
                <EmptyState
                    icon={Bell}
                    title={filter === 'active' ? 'No active alerts' : filter === 'resolved' ? 'No resolved alerts' : 'No alerts yet'}
                    message={
                        filter === 'active'
                            ? 'All systems are healthy. Alerts appear when the agent detects issues.'
                            : 'Alerts will appear here once the agent reports warning or critical conditions.'
                    }
                />
            ) : (
                <div className="space-y-3">
                    {alerts.map((alert, i) => (
                        <div
                            key={alert.id}
                            className="animate-slide-up"
                            style={{ animationDelay: `${i * 40}ms` }}
                        >
                            <AlertRow alert={alert} onResolve={resolveAlert} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
