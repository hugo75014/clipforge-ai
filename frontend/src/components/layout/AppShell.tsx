import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Plus,
  Film,
  Scissors,
  Wand2,
  Palette,
  Settings2,
  Download,
  Settings,
  Shield,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Sparkles,
  Menu,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'

import { useAuthStore } from '@/store/auth'
import { useUIStore } from '@/store/ui'
import { cn } from '@/lib/utils'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/new', label: 'New Project', icon: Plus, end: false },
  { to: '/projects', label: 'My Projects', icon: Film, end: false },
  { to: '/clips', label: 'Clips', icon: Scissors, end: false },
  { to: '/templates', label: 'Templates', icon: Wand2, end: false },
  { to: '/brand-kit', label: 'Brand Kit', icon: Palette, end: false },
  { to: '/ai-settings', label: 'AI Settings', icon: Settings2, end: false },
  { to: '/exports', label: 'Export History', icon: Download, end: false },
  { to: '/settings', label: 'Settings', icon: Settings, end: false },
] as const

export default function AppShell() {
  const { user, logout } = useAuthStore()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="min-h-screen flex bg-ink-950 text-ink-100">
      {/* Sidebar */}
      <aside
        className={cn(
          'hidden lg:flex flex-col border-r border-white/5 bg-ink-950/80 backdrop-blur transition-all duration-200 sticky top-0 h-screen z-30',
          sidebarOpen ? 'w-64' : 'w-[72px]'
        )}
      >
        <div className="h-16 flex items-center gap-2 px-4 border-b border-white/5">
          <div className="size-9 rounded-xl bg-gradient-to-br from-brand-500 to-pink-500 grid place-items-center shadow-glow">
            <Sparkles className="size-5 text-white" />
          </div>
          {sidebarOpen && (
            <div className="leading-tight">
              <div className="font-semibold tracking-tight">ClipForge</div>
              <div className="text-[10px] uppercase tracking-wider text-ink-400">AI Studio</div>
            </div>
          )}
        </div>

        <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all',
                  isActive
                    ? 'bg-gradient-to-r from-brand-500/20 to-pink-500/10 text-white border border-brand-500/20'
                    : 'text-ink-300 hover:bg-white/5 hover:text-white'
                )
              }
            >
              <item.icon className="size-4 shrink-0" />
              {sidebarOpen && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}

          {user?.role === 'admin' && (
            <div className="pt-3 mt-3 border-t border-white/5">
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all',
                    isActive
                      ? 'bg-gradient-to-r from-amber-500/20 to-pink-500/10 text-white border border-amber-500/20'
                      : 'text-amber-300/80 hover:bg-white/5'
                  )
                }
              >
                <Shield className="size-4 shrink-0" />
                {sidebarOpen && <span>Admin</span>}
              </NavLink>
            </div>
          )}
        </nav>

        <div className="border-t border-white/5 p-3">
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center justify-center rounded-lg p-2 text-ink-400 hover:bg-white/5 hover:text-ink-200 transition"
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? <ChevronLeft className="size-4" /> : <ChevronRight className="size-4" />}
          </button>
        </div>
      </aside>

      {/* Mobile sidebar */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'tween', duration: 0.2 }}
              className="fixed inset-y-0 left-0 w-72 bg-ink-950 border-r border-white/5 z-50 lg:hidden flex flex-col"
            >
              <div className="h-16 flex items-center justify-between px-4 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <div className="size-9 rounded-xl bg-gradient-to-br from-brand-500 to-pink-500 grid place-items-center">
                    <Sparkles className="size-5 text-white" />
                  </div>
                  <div className="font-semibold tracking-tight">ClipForge AI</div>
                </div>
                <button onClick={() => setMobileOpen(false)} className="p-2">
                  <ChevronLeft className="size-4" />
                </button>
              </div>
              <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
                {NAV.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    onClick={() => setMobileOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 rounded-xl px-3 py-2 text-sm',
                        isActive
                          ? 'bg-brand-500/15 text-white border border-brand-500/20'
                          : 'text-ink-300 hover:bg-white/5'
                      )
                    }
                  >
                    <item.icon className="size-4" />
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-16 sticky top-0 z-20 bg-ink-950/70 backdrop-blur-xl border-b border-white/5 px-4 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="p-2 -ml-2 lg:hidden text-ink-300 hover:text-white"
              aria-label="Open menu"
            >
              <Menu className="size-5" />
            </button>
            <h1 className="text-sm text-ink-400 hidden sm:block">Welcome back, {user?.name || 'creator'}.</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/new')}
              className="hidden sm:inline-flex btn-primary"
            >
              <Plus className="size-4" />
              <span>New project</span>
            </button>
            <div className="flex items-center gap-2 pl-3 border-l border-white/5">
              <div className="size-8 rounded-full bg-gradient-to-br from-brand-500 to-pink-500 grid place-items-center text-xs font-semibold">
                {(user?.name?.[0] || user?.email?.[0] || '?').toUpperCase()}
              </div>
              <div className="hidden sm:block leading-tight">
                <div className="text-xs font-medium">{user?.name || user?.email}</div>
                <div className="text-[10px] text-ink-400 uppercase tracking-wider">{user?.role}</div>
              </div>
              <button
                onClick={() => {
                  logout()
                  navigate('/login')
                }}
                className="p-2 text-ink-400 hover:text-white"
                aria-label="Sign out"
                title="Sign out"
              >
                <LogOut className="size-4" />
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
