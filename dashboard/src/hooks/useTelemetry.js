import { useState, useEffect, useMemo } from 'react'
import { supabase } from '../lib/supabase'

const TIME_RANGES = {
    '1h': 60 * 60 * 1000,
    '6h': 6 * 60 * 60 * 1000,
    '24h': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
}

export function useTelemetry(deviceId, range = '24h') {
    const [telemetry, setTelemetry] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!deviceId) return

        const fetchTelemetry = async () => {
            try {
                setLoading(true)
                const since = new Date(Date.now() - TIME_RANGES[range]).toISOString()

                const { data, error: err } = await supabase
                    .from('telemetry')
                    .select('*')
                    .eq('device_id', deviceId)
                    .gte('recorded_at', since)
                    .order('recorded_at', { ascending: true })

                if (err) throw err
                setTelemetry(data || [])
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }

        fetchTelemetry()

        // Refresh on new telemetry
        const channel = supabase
            .channel(`telemetry-${deviceId}`)
            .on('postgres_changes',
                { event: 'INSERT', schema: 'public', table: 'telemetry', filter: `device_id=eq.${deviceId}` },
                (payload) => {
                    setTelemetry(prev => [...prev, payload.new])
                }
            )
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [deviceId, range])

    const memoizedTelemetry = useMemo(() => telemetry, [telemetry])
    return { telemetry: memoizedTelemetry, loading, error }
}

export function useLatestTelemetry() {
    const [latest, setLatest] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchLatest = async () => {
            try {
                setLoading(true)
                const { data, error } = await supabase
                    .from('telemetry')
                    .select('*')
                    .order('recorded_at', { ascending: false })
                    .limit(200)

                if (error) throw error
                setLatest(data || [])
            } catch (err) {
                console.error('Failed to fetch latest telemetry:', err)
            } finally {
                setLoading(false)
            }
        }

        fetchLatest()

        // Real-time subscription for automatic updates
        const channel = supabase
            .channel('latest-telemetry-changes')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'telemetry' }, (payload) => {
                setLatest(prev => [payload.new, ...prev].slice(0, 200))
            })
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [])

    const memoizedLatest = useMemo(() => {
        const byDevice = {}
        for (const row of latest) {
            if (!byDevice[row.device_id]) {
                byDevice[row.device_id] = row
            }
        }
        return Object.values(byDevice)
    }, [latest])

    return { latest: memoizedLatest, loading }
}
