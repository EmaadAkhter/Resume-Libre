import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { FileText, FileSearch, LogOut, Menu, X } from 'lucide-react'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'My Resumes', Icon: FileText },
  { to: '/ats-check', label: 'ATS Check', Icon: FileSearch },
]

function navLinkClass({ isActive }) {
  return `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
    isActive
      ? 'bg-primary-50 text-primary-700 font-medium'
      : 'text-gray-600 hover:bg-gray-50'
  }`
}

function SidebarContent({ user, profile, logout, onNavigate }) {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-4">
        <Link to="/dashboard" onClick={onNavigate}>
          <img
            src="/logo.png"
            alt="ResumeLibre"
            className="h-12 w-auto"
            style={{ viewTransitionName: 'site-logo' }}
          />
        </Link>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map(({ to, label, Icon }) => (
          <NavLink key={to} to={to} className={navLinkClass} onClick={onNavigate}>
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-gray-200">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-gray-600 truncate">
            {profile?.email || user?.email}
          </span>
          {profile?.role === 'admin' && (
            <span className="shrink-0 px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded font-medium">
              Admin
            </span>
          )}
        </div>
        <button
          onClick={() => {
            logout()
            navigate('/login')
          }}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </div>
  )
}

export default function AppShell({ user, profile, logout, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop sidebar */}
      <aside className="hidden md:block fixed inset-y-0 left-0 w-60 bg-white border-r border-gray-200 z-30">
        <SidebarContent user={user} profile={profile} logout={logout} />
      </aside>

      {/* Mobile top bar */}
      <header className="md:hidden sticky top-0 z-30 bg-white border-b border-gray-200 flex items-center justify-between px-4 py-3">
        <Link to="/dashboard">
          <img src="/logo.png" alt="ResumeLibre" className="h-11 w-auto" />
        </Link>
        <button
          onClick={() => setSidebarOpen(true)}
          className="text-gray-600 hover:text-gray-900"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>
      </header>

      {/* Mobile slide-over sidebar */}
      {sidebarOpen && (
        <div className="md:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 w-60 bg-white border-r border-gray-200 shadow-xl">
            <button
              onClick={() => setSidebarOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
            <SidebarContent
              user={user}
              profile={profile}
              logout={logout}
              onNavigate={() => setSidebarOpen(false)}
            />
          </aside>
        </div>
      )}

      <main className="md:pl-60">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">{children}</div>
      </main>
    </div>
  )
}
