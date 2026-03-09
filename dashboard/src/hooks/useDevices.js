import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export function useDevices() {
    const [devices, setDevices] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchDevices = async () => {
        try {
            setLoading(true)
            const { data, error: err } = await supabase
                .from('devices')
                .select('*')
                .order('last_seen', { ascending: false })

            if (err) throw err
            setDevices(data || [])
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchDevices()

        // Real-time subscription
        const channel = supabase
            .channel('devices-changes')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'devices' }, (payload) => {
                if (payload.eventType === 'INSERT') {
                    setDevices(prev => [payload.new, ...prev])
                } else if (payload.eventType === 'UPDATE') {
                    setDevices(prev => prev.map(d => d.id === payload.new.id ? payload.new : d))
                } else if (payload.eventType === 'DELETE') {
                    setDevices(prev => prev.filter(d => d.id === payload.old.id))
                }
            })
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [])

    return { devices, loading, error, refetch: fetchDevices }
}
