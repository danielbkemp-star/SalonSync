import { cn } from '@/lib/utils'
import { Link } from 'react-router-dom'
import {
  CalendarPlus,
  UserPlus,
  CreditCard,
  ClipboardList,
  Clock,
  Gift,
} from 'lucide-react'

interface QuickAction {
  label: string
  icon: React.ReactNode
  href: string
  color: string
}

export function QuickActions() {
  const actions: QuickAction[] = [
    {
      label: 'New Appointment',
      icon: <CalendarPlus className="h-5 w-5" />,
      href: '/appointments/new',
      color: 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30',
    },
    {
      label: 'New Client',
      icon: <UserPlus className="h-5 w-5" />,
      href: '/clients/new',
      color: 'bg-pink-500/20 text-pink-400 hover:bg-pink-500/30',
    },
    {
      label: 'Check Out',
      icon: <CreditCard className="h-5 w-5" />,
      href: '/pos',
      color: 'bg-green-500/20 text-green-400 hover:bg-green-500/30',
    },
    {
      label: 'View Schedule',
      icon: <ClipboardList className="h-5 w-5" />,
      href: '/schedule',
      color: 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30',
    },
    {
      label: 'Walk-In',
      icon: <Clock className="h-5 w-5" />,
      href: '/appointments/walk-in',
      color: 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30',
    },
    {
      label: 'Gift Cards',
      icon: <Gift className="h-5 w-5" />,
      href: '/gift-cards',
      color: 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30',
    },
  ]

  return (
    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
      {actions.map((action) => (
        <Link
          key={action.label}
          to={action.href}
          className={cn(
            'flex flex-col items-center justify-center gap-2 p-4 rounded-xl',
            'border border-gray-700',
            'transition-all duration-200',
            action.color
          )}
        >
          {action.icon}
          <span className="text-xs text-gray-300 text-center">{action.label}</span>
        </Link>
      ))}
    </div>
  )
}
