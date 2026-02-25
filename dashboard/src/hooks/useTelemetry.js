import { useState, useEffect } from 'react'
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

    return { telemetry, loading, error }
}

export function useLatestTelemetry() {
    const [latest, setLatest] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchLatest = async () => {
            try {
                setLoading(true)
                // Get the latest telemetry record per device
                const { data, error } = await supabase
                    .from('telemetry')
                    .select('*')
                    .order('recorded_at', { ascending: false })
                    .limit(100)

                if (error) throw error

                // Group by device_id and take the latest
                const byDevice = {}
                for (const row of (data || [])) {
                    if (!byDevice[row.device_id]) {
                        byDevice[row.device_id] = row
                    }
                }
                setLatest(Object.values(byDevice))
            } catch (err) {
                console.error('Failed to fetch latest telemetry:', err)
            } finally {
                setLoading(false)
            }
        }

        fetchLatest()
        const interval = setInterval(fetchLatest, 30000) // refresh every 30s
        return () => clearInterval(interval)
    }, [])

    return { latest, loading }
}
