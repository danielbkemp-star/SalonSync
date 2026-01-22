import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface HeroActionCardProps {
  title: string
  description?: string
  icon: LucideIcon
  gradient: string
  onClick?: () => void
  disabled?: boolean
  badge?: string
}

export function HeroActionCard({
  title,
  description,
  icon: Icon,
  gradient,
  onClick,
  disabled = false,
  badge,
}: HeroActionCardProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'group relative overflow-hidden rounded-2xl p-6',
        'backdrop-blur-xl bg-white/5 border border-white/10',
        'hover:bg-white/10 transition-all duration-300',
        'hover:scale-[1.02] hover:shadow-2xl',
        'focus:outline-none focus:ring-2 focus:ring-white/20',
        'text-left w-full',
        disabled && 'opacity-50 cursor-not-allowed hover:scale-100 hover:bg-white/5'
      )}
    >
      {/* Gradient glow on hover */}
      <div
        className={cn(
          'absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-300',
          `bg-gradient-to-br ${gradient}`,
          disabled && 'group-hover:opacity-0'
        )}
      />

      {/* Badge */}
      {badge && (
        <div className="absolute top-3 right-3">
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-white/20 text-white/80">
            {badge}
          </span>
        </div>
      )}

      <div className="relative z-10 flex flex-col items-center gap-3 text-center">
        <div
          className={cn(
            'p-4 rounded-xl bg-gradient-to-br',
            gradient,
            'shadow-lg'
          )}
        >
          <Icon className="w-8 h-8 text-white" />
        </div>
        <span className="text-white/90 font-medium">{title}</span>
        {description && (
          <span className="text-white/50 text-sm">{description}</span>
        )}
      </div>

      {/* Shine effect on hover */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -skew-x-12 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000" />
      </div>
    </button>
  )
}

// Smaller variant for secondary actions
export function ActionCard({
  title,
  icon: Icon,
  onClick,
  active = false,
  count,
}: {
  title: string
  icon: LucideIcon
  onClick?: () => void
  active?: boolean
  count?: number
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-3 p-3 rounded-xl',
        'backdrop-blur-sm border border-white/10',
        'transition-all duration-200',
        active
          ? 'bg-brand-plum-500/30 border-brand-plum-500/50'
          : 'bg-white/5 hover:bg-white/10'
      )}
    >
      <div
        className={cn(
          'p-2 rounded-lg',
          active ? 'bg-brand-plum-500' : 'bg-white/10'
        )}
      >
        <Icon className={cn('w-5 h-5', active ? 'text-white' : 'text-white/70')} />
      </div>
      <span className={cn('font-medium', active ? 'text-white' : 'text-white/80')}>
        {title}
      </span>
      {count !== undefined && (
        <span
          className={cn(
            'ml-auto px-2 py-0.5 text-xs rounded-full',
            active ? 'bg-white/20 text-white' : 'bg-white/10 text-white/60'
          )}
        >
          {count}
        </span>
      )}
    </button>
  )
}
