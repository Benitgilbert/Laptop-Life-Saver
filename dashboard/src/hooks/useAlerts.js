import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export function useAlerts(filter = 'all') {
    const [alerts, setAlerts] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchAlerts = async () => {
        try {
            setLoading(true)
            let query = supabase
                .from('alerts')
                .select('*, devices(hostname)')
                .order('created_at', { ascending: false })
                .limit(50)

            if (filter === 'active') {
                query = query.eq('resolved', false)
            } else if (filter === 'resolved') {
                query = query.eq('resolved', true)
            }

            const { data, error: err } = await query
            if (err) throw err
            setAlerts(data || [])
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const resolveAlert = async (alertId) => {
        try {
            const { error: err } = await supabase
                .from('alerts')
                .update({ resolved: true })
                .eq('id', alertId)

            if (err) throw err
            // Refresh the list
            await fetchAlerts()
            return true
        } catch (err) {
            setError(err.message)
            return false
        }
    }

    useEffect(() => {
        fetchAlerts()

        const channel = supabase
            .channel('alerts-changes')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'alerts' }, () => {
                fetchAlerts()
            })
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [filter])

    return { alerts, loading, error, resolveAlert, refetch: fetchAlerts }
}
