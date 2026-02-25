export default function LoadingSkeleton({ rows = 3, type = 'card' }) {
    if (type === 'card') {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {Array.from({ length: rows }).map((_, i) => (
                    <div key={i} className="glass-card p-5 animate-pulse">
                        <div className="flex items-start gap-4">
                            <div className="w-11 h-11 rounded-xl bg-surface-200" />
                            <div className="flex-1 space-y-2">
                                <div className="h-3 bg-surface-200 rounded w-20" />
                                <div className="h-6 bg-surface-200 rounded w-16" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        )
    }

    if (type === 'list') {
        return (
            <div className="space-y-3">
                {Array.from({ length: rows }).map((_, i) => (
                    <div key={i} className="glass-card p-4 animate-pulse flex items-center gap-4">
                        <div className="w-16 h-6 rounded-full bg-surface-200" />
                        <div className="flex-1 space-y-2">
                            <div className="h-4 bg-surface-200 rounded w-40" />
                            <div className="h-3 bg-surface-200 rounded w-60" />
                        </div>
                        <div className="w-20 h-8 rounded-xl bg-surface-200" />
                    </div>
                ))}
            </div>
        )
    }

    // type === 'chart'
    return (
        <div className="glass-card p-6 animate-pulse">
            <div className="h-4 bg-surface-200 rounded w-32 mb-6" />
            <div className="h-64 bg-surface-100 rounded-xl" />
        </div>
    )
}
