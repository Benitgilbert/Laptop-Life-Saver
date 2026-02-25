import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react'

const config = {
    green: {
        label: 'Healthy',
        bg: 'bg-health-green-bg',
        text: 'text-emerald-700',
        dot: 'bg-health-green',
        shadow: 'shadow-glow-green',
        icon: ShieldCheck,
    },
    yellow: {
        label: 'Warning',
        bg: 'bg-health-yellow-bg',
        text: 'text-amber-700',
        dot: 'bg-health-yellow',
        shadow: 'shadow-glow-yellow',
        icon: Shield,
    },
    red: {
        label: 'Critical',
        bg: 'bg-health-red-bg',
        text: 'text-red-700',
        dot: 'bg-health-red',
        shadow: 'shadow-glow-red',
        icon: ShieldAlert,
    },
}

export default function StatusBadge({ status, size = 'sm', showLabel = true, glow = false }) {
    const s = config[status] || config.green
    const Icon = s.icon

    const sizes = {
        xs: 'px-2 py-0.5 text-[10px]',
        sm: 'px-2.5 py-1 text-xs',
        md: 'px-3 py-1.5 text-sm',
        lg: 'px-4 py-2 text-base',
    }

    return (
        <span className={`badge ${s.bg} ${s.text} ${sizes[size]} ${glow ? s.shadow : ''}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${s.dot} animate-pulse-soft`} />
            {size !== 'xs' && <Icon className="w-3.5 h-3.5" />}
            {showLabel && <span>{s.label}</span>}
        </span>
    )
}
