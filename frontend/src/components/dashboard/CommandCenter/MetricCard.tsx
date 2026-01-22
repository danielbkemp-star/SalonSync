import { Link } from 'react-router-dom'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  value: string | number
  label: string
  sublabel?: string
  icon: LucideIcon
  href: string
  trend?: {
    value: number
    isPositive: boolean
  }
  loading?: boolean
  compact?: boolean
  className?: string
}

export function MetricCard({
  value,
  label,
  sublabel,
  icon: Icon,
  href,
  trend,
  loading = false,
  compact = false,
  className,
}: MetricCardProps) {
  if (loading) {
    return <MetricCardSkeleton className={className} compact={compact} />
  }

  return (
    <Link
      to={href}
      className={cn(
        'group relative flex flex-col rounded-xl',
        'bg-white/5 backdrop-blur-sm',
        'border border-white/10',
        'hover:bg-white/10 hover:border-white/20',
        'transition-all duration-200',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-plum-500',
        compact ? 'p-2.5' : 'p-4',
        className
      )}
    >
      <div className={cn('flex items-center justify-between', compact ? 'mb-1.5' : 'mb-2')}>
        <div className={cn('rounded-lg bg-brand-plum-500/20', compact ? 'p-1.5' : 'p-2')}>
          <Icon className={cn('text-brand-plum-400', compact ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
        </div>
        {trend && (
          <span
            className={cn(
              'text-xs font-medium px-1.5 py-0.5 rounded',
              trend.isPositive
                ? 'text-emerald-400 bg-emerald-500/20'
                : 'text-rose-400 bg-rose-500/20'
            )}
          >
            {trend.isPositive ? '+' : ''}{trend.value}%
          </span>
        )}
      </div>
      <span className={cn('font-bold text-white tracking-tight', compact ? 'text-xl' : 'text-2xl')}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </span>
      <div className="flex items-baseline gap-1 mt-0.5">
        <span className={cn('text-white/60 leading-tight', compact ? 'text-xs' : 'text-sm')}>{label}</span>
        {sublabel && (
          <span className={cn('text-white/40', compact ? 'text-[10px]' : 'text-xs')}>({sublabel})</span>
        )}
      </div>

      {/* Hover indicator */}
      <div className="absolute inset-x-0 bottom-0 h-0.5 bg-brand-plum-500 scale-x-0 group-hover:scale-x-100 transition-transform rounded-b-xl" />
    </Link>
  )
}

export function MetricCardSkeleton({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <div
      className={cn(
        'flex flex-col rounded-xl',
        'bg-white/5 backdrop-blur-sm',
        'border border-white/10',
        'animate-pulse',
        compact ? 'p-2.5' : 'p-4',
        className
      )}
    >
      <div className={cn('flex items-center justify-between', compact ? 'mb-1.5' : 'mb-2')}>
        <div className={cn('bg-white/10 rounded-lg', compact ? 'h-6 w-6' : 'h-8 w-8')} />
      </div>
      <div className={cn('bg-white/10 rounded mb-1', compact ? 'h-5 w-12' : 'h-7 w-16')} />
      <div className={cn('bg-white/5 rounded', compact ? 'h-3 w-16' : 'h-4 w-24')} />
    </div>
  )
}
