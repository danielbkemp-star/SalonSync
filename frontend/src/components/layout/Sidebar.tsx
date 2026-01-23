import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Calendar,
  Users,
  UserCircle,
  Scissors,
  DollarSign,
  Camera,
  Share2,
  Image,
  BarChart3,
  Settings,
  LogOut,
  ChevronLeft,
  Menu,
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '@/stores/authStore'

interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: number
}

const mainNavItems: NavItem[] = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'Appointments', href: '/appointments', icon: Calendar },
  { label: 'Clients', href: '/clients', icon: Users },
  { label: 'Staff', href: '/staff', icon: UserCircle },
  { label: 'Services', href: '/services', icon: Scissors },
  { label: 'Point of Sale', href: '/pos', icon: DollarSign },
]

const contentNavItems: NavItem[] = [
  { label: 'Capture', href: '/capture', icon: Camera },
  { label: 'Social Media', href: '/social', icon: Share2 },
  { label: 'Portfolio', href: '/portfolio', icon: Image },
]

const systemNavItems: NavItem[] = [
  { label: 'Reports', href: '/reports', icon: BarChart3 },
  { label: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const { logout, user } = useAuthStore()

  const isActive = (href: string) => {
    if (href === '/') return location.pathname === '/'
    return location.pathname.startsWith(href)
  }

  return (
    <aside
      className={cn(
        'h-screen bg-gray-900 border-r border-gray-800 flex flex-col transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Scissors className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-white">SalonSync</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
        >
          {collapsed ? <Menu className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        {/* Main Navigation */}
        <div className="px-3 mb-6">
          {!collapsed && (
            <p className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Main
            </p>
          )}
          <ul className="space-y-1">
            {mainNavItems.map((item) => (
              <NavLink key={item.href} item={item} isActive={isActive(item.href)} collapsed={collapsed} />
            ))}
          </ul>
        </div>

        {/* Content Navigation */}
        <div className="px-3 mb-6">
          {!collapsed && (
            <p className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Content
            </p>
          )}
          <ul className="space-y-1">
            {contentNavItems.map((item) => (
              <NavLink key={item.href} item={item} isActive={isActive(item.href)} collapsed={collapsed} />
            ))}
          </ul>
        </div>

        {/* System Navigation */}
        <div className="px-3">
          {!collapsed && (
            <p className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              System
            </p>
          )}
          <ul className="space-y-1">
            {systemNavItems.map((item) => (
              <NavLink key={item.href} item={item} isActive={isActive(item.href)} collapsed={collapsed} />
            ))}
          </ul>
        </div>
      </nav>

      {/* User Section */}
      <div className="border-t border-gray-800 p-4">
        {!collapsed ? (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium">
              {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.first_name ? `${user.first_name} ${user.last_name || ''}` : user?.email}
              </p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
            <button
              onClick={() => logout()}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-red-400 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => logout()}
            className="w-full p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-red-400 transition-colors flex justify-center"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        )}
      </div>
    </aside>
  )
}

interface NavLinkProps {
  item: NavItem
  isActive: boolean
  collapsed: boolean
}

function NavLink({ item, isActive, collapsed }: NavLinkProps) {
  const Icon = item.icon

  return (
    <li>
      <Link
        to={item.href}
        className={cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
          isActive
            ? 'bg-purple-500/20 text-purple-400'
            : 'text-gray-400 hover:bg-gray-800 hover:text-white',
          collapsed && 'justify-center'
        )}
        title={collapsed ? item.label : undefined}
      >
        <Icon className="w-5 h-5 flex-shrink-0" />
        {!collapsed && (
          <>
            <span className="flex-1">{item.label}</span>
            {item.badge && (
              <span className="px-2 py-0.5 text-xs bg-purple-500 text-white rounded-full">
                {item.badge}
              </span>
            )}
          </>
        )}
      </Link>
    </li>
  )
}

export default Sidebar
