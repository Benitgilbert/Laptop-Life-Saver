import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'

export const DEFAULT_THRESHOLDS = {
    cpu_temp_warning: 70,
    cpu_temp_critical: 85,
    disk_warning: 80,
    disk_critical: 95,
    ram_warning: 80,
    ram_critical: 95,
    battery_low: 20,
    battery_critical: 10,
}

/**
 * Reactive hook that reads / writes alert thresholds in Supabase.
 * Component will re-render when thresholds are updated in the DB
 * via Realtime subscriptions.
 */
export function useThresholds() {
    const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS)
    const [loading, setLoading] = useState(true)

    const fetchThresholds = useCallback(async () => {
        try {
            const { data, error } = await supabase
                .from('threshold_settings')
                .select('*')
                .eq('id', 1)
                .single()

            if (error) throw error
            if (data) {
                // Remove internal fields before setting state
                const { id, updated_at, ...cleanThresholds } = data
                setThresholds(cleanThresholds)
            }
        } catch (err) {
            console.error('Failed to fetch thresholds:', err)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchThresholds()

        // Subscribe to real-time updates
        const channel = supabase
            .channel('threshold-changes')
            .on(
                'postgres_changes',
                { event: 'UPDATE', schema: 'public', table: 'threshold_settings', filter: 'id=eq.1' },
                (payload) => {
                    const { id, updated_at, ...newThresholds } = payload.new
                    setThresholds(newThresholds)
                }
            )
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [fetchThresholds])

    const save = useCallback(async (newThresholds) => {
        try {
            const { error } = await supabase
                .from('threshold_settings')
                .update({ ...newThresholds, updated_at: new Date() })
                .eq('id', 1)

            if (error) throw error
        } catch (err) {
            console.error('Failed to save thresholds:', err)
            throw err
        }
    }, [])

    const reset = useCallback(async () => {
        try {
            const { error } = await supabase
                .from('threshold_settings')
                .update({ ...DEFAULT_THRESHOLDS, updated_at: new Date() })
                .eq('id', 1)

            if (error) throw error
        } catch (err) {
            console.error('Failed to reset thresholds:', err)
            throw err
        }
    }, [])

    return { thresholds, loading, save, reset, defaults: DEFAULT_THRESHOLDS }
}

/**
 * Evaluate health status based on telemetry data and thresholds.
 * Returns 'green', 'yellow', or 'red'.
 */
export function evaluateHealth(telemetry, thresholds) {
    if (!telemetry || !thresholds) return 'green'

    const t = thresholds

    // CPU Temperature check
    if (telemetry.cpu_temp_c != null && telemetry.cpu_temp_c > 0) {
        if (telemetry.cpu_temp_c >= t.cpu_temp_critical) return 'red'
        if (telemetry.cpu_temp_c >= t.cpu_temp_warning) return 'yellow'
    }

    // Disk Usage check
    if (telemetry.disk_usage_pct != null) {
        if (telemetry.disk_usage_pct >= t.disk_critical) return 'red'
        if (telemetry.disk_usage_pct >= t.disk_warning) return 'yellow'
    }

    // RAM Usage check
    if (telemetry.ram_usage_pct != null) {
        if (telemetry.ram_usage_pct >= t.ram_critical) return 'red'
        if (telemetry.ram_usage_pct >= t.ram_warning) return 'yellow'
    }

    // Battery check
    if (telemetry.battery_percent != null && !telemetry.battery_plugged) {
        if (telemetry.battery_percent <= t.battery_critical) return 'red'
        if (telemetry.battery_percent <= t.battery_low) return 'yellow'
    }

    return 'green'
}
