import { cn } from '@/lib/utils'
import { ReactNode } from 'react'

interface GlassCardProps {
  title?: string
  children: ReactNode
  className?: string
  headerAction?: ReactNode
  noPadding?: boolean
  glow?: 'purple' | 'plum' | 'rose' | 'gold' | 'none'
}

export function GlassCard({
  title,
  children,
  className,
  headerAction,
  noPadding = false,
  glow = 'none',
}: GlassCardProps) {
  const glowStyles = {
    purple: 'shadow-[0_0_30px_rgba(168,85,247,0.15)]',
    plum: 'shadow-[0_0_30px_rgba(139,92,246,0.15)]',
    rose: 'shadow-[0_0_30px_rgba(244,63,94,0.15)]',
    gold: 'shadow-[0_0_30px_rgba(251,191,36,0.15)]',
    none: 'shadow-[0_8px_32px_rgba(0,0,0,0.3)]',
  }

  return (
    <div
      className={cn(
        'backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl',
        glowStyles[glow],
        !noPadding && 'p-6',
        className
      )}
    >
      {title && (
        <div className={cn(
          'flex items-center justify-between',
          noPadding ? 'px-6 pt-6' : '',
          'mb-4'
        )}>
          <h3 className="text-lg font-semibold text-white/90">{title}</h3>
          {headerAction}
        </div>
      )}
      <div className={noPadding ? '' : ''}>{children}</div>
    </div>
  )
}

// Compact variant for smaller cards
export function GlassCardCompact({
  children,
  className,
  onClick,
}: {
  children: ReactNode
  className?: string
  onClick?: () => void
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-4',
        'shadow-[0_4px_16px_rgba(0,0,0,0.2)]',
        onClick && 'cursor-pointer hover:bg-white/10 transition-all duration-200',
        className
      )}
    >
      {children}
    </div>
  )
}
