import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Activity, Mail, Lock, AlertCircle, Loader2 } from 'lucide-react'

export default function Login() {
    const { user, signIn } = useAuth()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    if (user) return <Navigate to="/" replace />

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            await signIn(email, password)
        } catch (err) {
            setError(err.message || 'Invalid credentials')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center px-4"
            style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f97316 100%)',
            }}
        >
            <div className="w-full max-w-md">
                {/* Brand */}
                <div className="text-center mb-8">
                    <div className="inline-flex p-4 rounded-2xl bg-white/20 backdrop-blur-sm shadow-xl mb-4">
                        <Activity className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">
                        Laptop Life-Saver
                    </h1>
                    <p className="text-white/70 text-sm mt-1">Nyanza District • Admin Dashboard</p>
                </div>

                {/* Login card */}
                <form
                    onSubmit={handleSubmit}
                    className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 space-y-5"
                >
                    <div className="text-center">
                        <h2 className="text-xl font-bold text-surface-800">Welcome Back</h2>
                        <p className="text-sm text-surface-500 mt-1">Sign in to access the dashboard</p>
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 p-3 rounded-xl bg-red-50 text-red-600 text-sm">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            {error}
                        </div>
                    )}

                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-semibold text-surface-600 mb-1.5">
                                Email Address
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    placeholder="admin@nyanza.rw"
                                    required
                                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-surface-200 bg-white text-sm text-surface-700 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/30 focus:border-accent-400 transition-all duration-200"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-semibold text-surface-600 mb-1.5">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-surface-200 bg-white text-sm text-surface-700 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/30 focus:border-accent-400 transition-all duration-200"
                                />
                            </div>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-accent-600 to-accent-700 text-white font-semibold text-sm shadow-lg hover:shadow-xl hover:from-accent-500 hover:to-accent-600 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Signing in...
                            </>
                        ) : (
                            'Sign In'
                        )}
                    </button>

                   <p className="text-center text-[11px] leading-relaxed text-surface-400">
  <strong>A Data-Driven Approach to Predictive Maintenance of Nyanza District IT Assets</strong> <br />
  Developed by BYIRINGIRO Benit Gilbert (Reg No: 22247/2023) <br />
  Final Year Project
</p>
                </form>
            </div>
        </div>
    )
}
