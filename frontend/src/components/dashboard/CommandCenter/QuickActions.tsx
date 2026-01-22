import { cn } from '@/lib/utils'
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
      color: 'bg-brand-plum-500/20 text-brand-plum-400 hover:bg-brand-plum-500/30',
    },
    {
      label: 'New Client',
      icon: <UserPlus className="h-5 w-5" />,
      href: '/clients/new',
      color: 'bg-brand-rose-500/20 text-brand-rose-400 hover:bg-brand-rose-500/30',
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
      color: 'bg-brand-gold-500/20 text-brand-gold-400 hover:bg-brand-gold-500/30',
    },
  ]

  return (
    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
      {actions.map((action) => (
        <a
          key={action.label}
          href={action.href}
          className={cn(
            'flex flex-col items-center justify-center gap-2 p-4 rounded-xl',
            'border border-white/10',
            'transition-all duration-200',
            action.color
          )}
        >
          {action.icon}
          <span className="text-xs text-white/80 text-center">{action.label}</span>
        </a>
      ))}
    </div>
  )
}
