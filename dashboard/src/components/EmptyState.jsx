import { Inbox } from 'lucide-react'

export default function EmptyState({ icon: Icon = Inbox, title = 'No data yet', message = 'Data will appear here once the agent starts sending telemetry.' }) {
    return (
        <div className="flex flex-col items-center justify-center py-16 animate-fade-in">
            <div className="p-4 rounded-2xl bg-surface-100 mb-4">
                <Icon className="w-10 h-10 text-surface-400" />
            </div>
            <h3 className="text-lg font-semibold text-surface-700">{title}</h3>
            <p className="text-sm text-surface-400 mt-1 text-center max-w-sm">{message}</p>
        </div>
    )
}
