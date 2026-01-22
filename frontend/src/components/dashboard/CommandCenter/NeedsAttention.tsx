import { cn } from '@/lib/utils'
import { AlertCircle, Clock, Package, UserX } from 'lucide-react'

interface NeedsAttentionProps {
  maxItems?: number
  className?: string
}

interface AttentionItem {
  id: string
  type: 'warning' | 'info' | 'alert'
  title: string
  description: string
  icon: React.ReactNode
  actionUrl: string
}

export function NeedsAttention({ maxItems = 5, className }: NeedsAttentionProps) {
  // TODO: Fetch from API
  const items: AttentionItem[] = ([
    {
      id: '1',
      type: 'warning' as const,
      title: '2 appointments starting soon',
      description: 'Clients not checked in yet',
      icon: <Clock className="h-4 w-4" />,
      actionUrl: '/appointments',
    },
    {
      id: '2',
      type: 'info' as const,
      title: '3 products low on stock',
      description: 'Shampoo, conditioner, styling gel',
      icon: <Package className="h-4 w-4" />,
      actionUrl: '/inventory',
    },
    {
      id: '3',
      type: 'alert' as const,
      title: '1 no-show this week',
      description: 'Consider follow-up',
      icon: <UserX className="h-4 w-4" />,
      actionUrl: '/reports/no-shows',
    },
  ] as AttentionItem[]).slice(0, maxItems)

  const typeStyles = {
    warning: {
      bg: 'bg-yellow-500/10',
      border: 'border-yellow-500/30',
      icon: 'text-yellow-400',
    },
    info: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      icon: 'text-blue-400',
    },
    alert: {
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      icon: 'text-red-400',
    },
  }

  return (
    <div className={cn('rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 p-4', className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-brand-rose-400" />
          <h2 className="text-lg font-semibold text-white">Needs Attention</h2>
        </div>
        {items.length > 0 && (
          <span className="text-xs bg-brand-rose-500/20 text-brand-rose-300 px-2 py-0.5 rounded-full">
            {items.length}
          </span>
        )}
      </div>

      <div className="space-y-3">
        {items.map((item) => {
          const styles = typeStyles[item.type]
          return (
            <a
              key={item.id}
              href={item.actionUrl}
              className={cn(
                'block p-3 rounded-lg',
                styles.bg,
                'border',
                styles.border,
                'hover:bg-white/10 transition-colors'
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn('mt-0.5', styles.icon)}>
                  {item.icon}
                </div>
                <div>
                  <div className="text-white font-medium text-sm">{item.title}</div>
                  <div className="text-white/50 text-xs">{item.description}</div>
                </div>
              </div>
            </a>
          )
        })}

        {items.length === 0 && (
          <div className="text-center py-8 text-white/50">
            <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>All caught up!</p>
          </div>
        )}
      </div>
    </div>
  )
}
