import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Monitor, Bell, Activity, LogOut, Settings, Moon, Sun } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'

const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/devices', label: 'Devices', icon: Monitor },
    { to: '/alerts', label: 'Alerts', icon: Bell },
    { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout() {
    const { user, signOut } = useAuth()
    const { dark, toggle } = useTheme()

    return (
        <div className="min-h-screen flex flex-col lg:flex-row bg-surface-50 dark:bg-gray-900 transition-colors duration-300">
            {/* ── Sidebar (desktop) ─────────────────────────── */}
            <aside className="hidden lg:flex flex-col w-64 border-r border-surface-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm p-4">
                {/* Brand */}
                <div className="flex items-center gap-3 px-3 mb-8 mt-2">
                    <div className="p-2 rounded-xl bg-gradient-to-br from-accent-500 to-accent-700 shadow-lg">
                        <Activity className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                        <h1 className="text-sm font-bold text-surface-800 dark:text-white tracking-tight">
                            Laptop Life-Saver
                        </h1>
                        <p className="text-[11px] text-surface-400">Nyanza District</p>
                    </div>
                    <button
                        onClick={toggle}
                        className="p-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-gray-700 transition-colors"
                        title={dark ? 'Light mode' : 'Dark mode'}
                    >
                        {dark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-surface-400" />}
                    </button>
                </div>

                {/* Nav */}
                <nav className="flex-1 space-y-1">
                    {navItems.map(({ to, label, icon: Icon }) => (
                        <NavLink
                            key={to}
                            to={to}
                            end={to === '/'}
                            className={({ isActive }) =>
                                `nav-link ${isActive ? 'active' : ''}`
                            }
                        >
                            <Icon className="w-4.5 h-4.5" />
                            {label}
                        </NavLink>
                    ))}
                </nav>

                {/* User + Logout */}
                <div className="px-3 py-3 border-t border-surface-200 mt-4 space-y-2">
                    {user && (
                        <p className="text-[11px] text-surface-500 truncate" title={user.email}>
                            {user.email}
                        </p>
                    )}
                    <button
                        onClick={signOut}
                        className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-xs font-medium text-surface-500 hover:text-red-600 hover:bg-red-50 transition-all duration-200"
                    >
                        <LogOut className="w-3.5 h-3.5" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* ── Main content ──────────────────────────────── */}
            <main className="flex-1 min-h-screen pb-20 lg:pb-0">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
                    <Outlet />
                </div>
            </main>

            {/* ── Bottom nav (mobile) ───────────────────────── */}
            <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-md border-t border-surface-200 flex justify-around items-center py-2 px-4 z-50">
                {navItems.map(({ to, label, icon: Icon }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === '/'}
                        className={({ isActive }) =>
                            `flex flex-col items-center gap-1 px-3 py-1.5 rounded-xl text-[11px] font-medium transition-colors duration-200 ${isActive
                                ? 'text-accent-600'
                                : 'text-surface-400 hover:text-surface-600'
                            }`
                        }
                    >
                        <Icon className="w-5 h-5" />
                        {label}
                    </NavLink>
                ))}
            </nav>
        </div>
    )
}

