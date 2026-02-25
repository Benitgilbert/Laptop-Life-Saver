export default function StatCard({ icon: Icon, label, value, sub, color = 'accent', delay = 0 }) {
    const colorMap = {
        accent: 'from-accent-500 to-accent-600',
        green: 'from-emerald-500 to-emerald-600',
        yellow: 'from-amber-500 to-amber-600',
        red: 'from-red-500 to-red-600',
        blue: 'from-blue-500 to-blue-600',
    }

    return (
        <div
            className="glass-card p-5 flex items-start gap-4 animate-slide-up"
            style={{ animationDelay: `${delay}ms` }}
        >
            <div className={`p-3 rounded-xl bg-gradient-to-br ${colorMap[color]} shadow-lg`}>
                <Icon className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-sm text-surface-500 font-medium">{label}</p>
                <p className="text-2xl font-bold text-surface-800 mt-0.5 tracking-tight">{value}</p>
                {sub && <p className="text-xs text-surface-400 mt-1">{sub}</p>}
            </div>
        </div>
    )
}
