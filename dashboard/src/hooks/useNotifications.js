import { useState, useCallback, useEffect } from 'react'

/**
 * Hook for browser push notifications.
 * Requests permission and provides a `notify()` function.
 */
export function useNotifications() {
    const [permission, setPermission] = useState(
        typeof Notification !== 'undefined' ? Notification.permission : 'denied'
    )

    const requestPermission = useCallback(async () => {
        if (typeof Notification === 'undefined') return 'denied'
        const result = await Notification.requestPermission()
        setPermission(result)
        return result
    }, [])

    const notify = useCallback((title, body, options = {}) => {
        if (permission !== 'granted') return null
        try {
            return new Notification(title, {
                body,
                icon: '/vite.svg',
                badge: '/vite.svg',
                tag: options.tag || 'alert',
                ...options,
            })
        } catch {
            return null
        }
    }, [permission])

    return { permission, requestPermission, notify }
}
