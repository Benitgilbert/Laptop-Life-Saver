import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Thermometer, HardDrive, MemoryStick, Battery, Save, RotateCcw, Moon, Sun, Bell, BellOff } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useNotifications } from '../hooks/useNotifications'
import { useThresholds } from '../hooks/useThresholds'

export default function Settings() {
    const { dark, toggle } = useTheme()
    const { permission, requestPermission } = useNotifications()
    const { thresholds: storedThresholds, loading, save: saveThresholds, reset: resetThresholds, defaults } = useThresholds()
    const [localThresholds, setLocalThresholds] = useState(defaults)
    const [saved, setSaved] = useState(false)
    const [hasChanges, setHasChanges] = useState(false)

    // Sync local state when server data arrives or changes via Realtime
    useEffect(() => {
        if (!loading && storedThresholds) {
            setLocalThresholds(storedThresholds)
        }
    }, [loading, storedThresholds])

    const update = (key, value) => {
        setLocalThresholds(prev => ({ ...prev, [key]: Number(value) || 0 }))
        setSaved(false)
        setHasChanges(true)
    }

    const handleSave = async () => {
        try {
            await saveThresholds(localThresholds)
            setSaved(true)
            setHasChanges(false)
            setTimeout(() => setSaved(false), 2000)
        } catch (err) {
            alert('Failed to save thresholds. Please check your connection.')
        }
    }

    const handleReset = async () => {
        try {
            await resetThresholds()
            setSaved(false)
            setHasChanges(false)
        } catch (err) {
            alert('Failed to reset thresholds.')
        }
    }

    if (loading) {
        return (
            <div className="space-y-6 animate-pulse">
                <div className="h-8 w-48 bg-surface-200 dark:bg-surface-700 rounded-lg mb-8" />
                <div className="glass-card p-6 h-32" />
                <div className="glass-card p-6 h-32" />
                <div className="glass-card p-6 h-64" />
            </div>
        )
    }

    return (
        <div className="space-y-8 animate-fade-in max-w-3xl">
            {/* Header */}
            <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-surface-800 dark:text-white tracking-tight">Settings</h1>
                <p className="text-surface-500 text-sm mt-1">Configure alert thresholds and preferences</p>
            </div>

            {/* ── Appearance ─────────────────────────────── */}
            <div className="glass-card p-6">
                <h2 className="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-4 flex items-center gap-2">
                    {dark ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                    Appearance
                </h2>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-surface-700 dark:text-surface-300">Dark Mode</p>
                        <p className="text-xs text-surface-400">Switch between light and dark themes</p>
                    </div>
                    <button
                        onClick={toggle}
                        className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${dark ? 'bg-accent-600' : 'bg-surface-300'}`}
                    >
                        <span
                            className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-md transform transition-transform duration-300 ${dark ? 'translate-x-6' : 'translate-x-0'}`}
                        />
                    </button>
                </div>
            </div>

            {/* ── Notifications ──────────────────────────── */}
            <div className="glass-card p-6">
                <h2 className="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-4 flex items-center gap-2">
                    {permission === 'granted' ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
                    Notifications
                </h2>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-surface-700 dark:text-surface-300">Browser Notifications</p>
                        <p className="text-xs text-surface-400">
                            {permission === 'granted' ? 'Enabled — you will receive alerts' :
                                permission === 'denied' ? 'Blocked — check browser settings' :
                                    'Not enabled'}
                        </p>
                    </div>
                    {permission !== 'granted' && permission !== 'denied' && (
                        <button
                            onClick={requestPermission}
                            className="px-4 py-2 rounded-xl bg-accent-600 text-white text-xs font-semibold hover:bg-accent-500 transition-all duration-200"
                        >
                            Enable
                        </button>
                    )}
                    {permission === 'granted' && (
                        <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-xl">
                            ✓ Active
                        </span>
                    )}
                </div>
            </div>

            {/* ── Alert Thresholds ───────────────────────── */}
            <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-sm font-semibold text-surface-700 dark:text-surface-300 flex items-center gap-2">
                        <SettingsIcon className="w-4 h-4" />
                        Alert Thresholds
                    </h2>
                    {hasChanges && (
                        <span className="text-[11px] text-amber-500 font-semibold animate-pulse-soft">
                            Unsaved changes
                        </span>
                    )}
                </div>
                <p className="text-xs text-surface-400 mb-4 -mt-2">
                    These thresholds control how health status is evaluated across the dashboard.
                    Changes take effect immediately after saving.
                </p>

                <div className="space-y-6">
                    {/* CPU Temperature */}
                    <ThresholdGroup
                        icon={Thermometer}
                        label="CPU Temperature"
                        unit="°C"
                        warningKey="cpu_temp_warning"
                        criticalKey="cpu_temp_critical"
                        values={localThresholds}
                        defaults={defaults}
                        onChange={update}
                        warningMax={120}
                    />

                    {/* Disk Usage */}
                    <ThresholdGroup
                        icon={HardDrive}
                        label="Disk Usage"
                        unit="%"
                        warningKey="disk_warning"
                        criticalKey="disk_critical"
                        values={localThresholds}
                        defaults={defaults}
                        onChange={update}
                        warningMax={100}
                    />

                    {/* RAM Usage */}
                    <ThresholdGroup
                        icon={MemoryStick}
                        label="RAM Usage"
                        unit="%"
                        warningKey="ram_warning"
                        criticalKey="ram_critical"
                        values={localThresholds}
                        defaults={defaults}
                        onChange={update}
                        warningMax={100}
                    />

                    {/* Battery */}
                    <ThresholdGroup
                        icon={Battery}
                        label="Battery Level"
                        unit="%"
                        warningKey="battery_low"
                        criticalKey="battery_critical"
                        values={localThresholds}
                        defaults={defaults}
                        onChange={update}
                        warningMax={100}
                        inverted
                    />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 mt-8 pt-6 border-t border-surface-200 dark:border-surface-700">
                    <button
                        onClick={handleSave}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-white text-xs font-semibold shadow-md hover:shadow-lg transition-all duration-200 ${saved ? 'bg-emerald-500' : 'bg-accent-600 hover:bg-accent-500'
                            }`}
                    >
                        <Save className="w-3.5 h-3.5" />
                        {saved ? 'Saved ✓' : 'Save Changes'}
                    </button>
                    <button
                        onClick={handleReset}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-100 text-surface-600 text-xs font-semibold hover:bg-surface-200 transition-all duration-200"
                    >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Reset to Defaults
                    </button>
                </div>
            </div>
        </div>
    )
}

function ThresholdGroup({ icon: Icon, label, unit, warningKey, criticalKey, values, defaults, onChange, warningMax = 100, inverted }) {
    const isModified = values[warningKey] !== defaults[warningKey] || values[criticalKey] !== defaults[criticalKey]

    return (
        <div className={`p-4 rounded-xl border transition-all duration-200 ${isModified
            ? 'bg-accent-50/50 dark:bg-accent-900/10 border-accent-200 dark:border-accent-700'
            : 'bg-surface-50 dark:bg-surface-800/50 border-surface-100 dark:border-surface-700'
            }`}>
            <div className="flex items-center gap-2 mb-3">
                <Icon className="w-4 h-4 text-surface-500" />
                <span className="text-sm font-medium text-surface-700 dark:text-surface-300">{label}</span>
                {isModified && (
                    <span className="text-[10px] text-accent-500 font-semibold bg-accent-50 dark:bg-accent-900/30 px-1.5 py-0.5 rounded">
                        Modified
                    </span>
                )}
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-[11px] text-amber-600 font-semibold mb-1">
                        {inverted ? 'Low' : 'Warning'} ({unit})
                        <span className="text-surface-300 font-normal ml-1">(default: {defaults[warningKey]})</span>
                    </label>
                    <input
                        type="number"
                        min="0"
                        max={warningMax}
                        value={values[warningKey]}
                        onChange={e => onChange(warningKey, e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-800 text-sm text-surface-700 dark:text-surface-300 focus:outline-none focus:ring-2 focus:ring-accent-500/30 transition-all duration-200"
                    />
                </div>
                <div>
                    <label className="block text-[11px] text-red-500 font-semibold mb-1">
                        Critical ({unit})
                        <span className="text-surface-300 font-normal ml-1">(default: {defaults[criticalKey]})</span>
                    </label>
                    <input
                        type="number"
                        min="0"
                        max={warningMax}
                        value={values[criticalKey]}
                        onChange={e => onChange(criticalKey, e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-800 text-sm text-surface-700 dark:text-surface-300 focus:outline-none focus:ring-2 focus:ring-accent-500/30 transition-all duration-200"
                    />
                </div>
            </div>
        </div>
    )
}
