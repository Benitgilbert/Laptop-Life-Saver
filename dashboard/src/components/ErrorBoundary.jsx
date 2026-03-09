import React from 'react'
import { AlertTriangle, RefreshCcw } from 'lucide-react'

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, errorInfo) {
        console.error("Dashboard Error:", error, errorInfo)
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center p-6 bg-surface-50">
                    <div className="glass-card p-8 max-w-md w-full text-center border-t-4 border-t-rose-500">
                        <div className="w-16 h-16 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-6">
                            <AlertTriangle className="w-8 h-8" />
                        </div>
                        <h1 className="text-2xl font-bold text-surface-900 mb-2">Something went wrong</h1>
                        <p className="text-surface-600 mb-8">
                            The dashboard encountered an unexpected error. Don't worry, your data is safe.
                        </p>
                        <button
                            onClick={() => window.location.reload()}
                            className="btn-accent w-full flex items-center justify-center gap-2 py-3"
                        >
                            <RefreshCcw className="w-4 h-4" />
                            Reload Dashboard
                        </button>
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary
