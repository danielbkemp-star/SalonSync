import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'purple'
  | 'pink'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  icon?: LucideIcon
  dot?: boolean
  className?: string
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  icon: Icon,
  dot = false,
  className,
}: BadgeProps) {
  const variants = {
    default: 'bg-gray-700 text-gray-300',
    success: 'bg-green-500/20 text-green-400',
    warning: 'bg-yellow-500/20 text-yellow-400',
    error: 'bg-red-500/20 text-red-400',
    info: 'bg-blue-500/20 text-blue-400',
    purple: 'bg-purple-500/20 text-purple-400',
    pink: 'bg-pink-500/20 text-pink-400',
  }

  const sizes = {
    sm: 'text-[10px] px-1.5 py-0.5',
    md: 'text-xs px-2 py-0.5',
  }

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-3.5 w-3.5',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium rounded-full',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {dot && (
        <span
          className={cn(
            'rounded-full',
            size === 'sm' ? 'h-1.5 w-1.5' : 'h-2 w-2',
            variant === 'default' ? 'bg-gray-400' :
            variant === 'success' ? 'bg-green-400' :
            variant === 'warning' ? 'bg-yellow-400' :
            variant === 'error' ? 'bg-red-400' :
            variant === 'info' ? 'bg-blue-400' :
            variant === 'purple' ? 'bg-purple-400' :
            'bg-pink-400'
          )}
        />
      )}
      {Icon && <Icon className={iconSizes[size]} />}
      {children}
    </span>
  )
}

// Status badge specifically for appointments
type AppointmentStatus = 'scheduled' | 'confirmed' | 'checked_in' | 'in_progress' | 'completed' | 'cancelled' | 'no_show'

interface StatusBadgeProps {
  status: AppointmentStatus
  size?: 'sm' | 'md'
  showDot?: boolean
}

export function StatusBadge({ status, size = 'md', showDot = true }: StatusBadgeProps) {
  const statusConfig: Record<AppointmentStatus, { label: string; variant: BadgeVariant }> = {
    scheduled: { label: 'Scheduled', variant: 'default' },
    confirmed: { label: 'Confirmed', variant: 'info' },
    checked_in: { label: 'Checked In', variant: 'warning' },
    in_progress: { label: 'In Progress', variant: 'purple' },
    completed: { label: 'Completed', variant: 'success' },
    cancelled: { label: 'Cancelled', variant: 'error' },
    no_show: { label: 'No Show', variant: 'error' },
  }

  const config = statusConfig[status]

  return (
    <Badge variant={config.variant} size={size} dot={showDot}>
      {config.label}
    </Badge>
  )
}
