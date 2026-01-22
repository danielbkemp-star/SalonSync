import { cn } from '@/lib/utils'
import { ButtonHTMLAttributes, forwardRef } from 'react'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  gradient?: string
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      loading = false,
      gradient,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = cn(
      'inline-flex items-center justify-center gap-2 rounded-xl font-medium',
      'transition-all duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    )

    const variants = {
      primary: gradient
        ? `bg-gradient-to-r ${gradient} text-white hover:opacity-90 focus:ring-purple-500`
        : 'bg-brand-plum-500 text-white hover:bg-brand-plum-600 focus:ring-brand-plum-500',
      secondary:
        'bg-white/10 text-white border border-white/20 hover:bg-white/20 focus:ring-white/30',
      ghost: 'text-white/80 hover:bg-white/10 hover:text-white focus:ring-white/20',
      danger: 'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500',
      outline:
        'border-2 border-brand-plum-500 text-brand-plum-400 hover:bg-brand-plum-500/20 focus:ring-brand-plum-500',
    }

    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2.5 text-sm',
      lg: 'px-6 py-3 text-base',
    }

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {loading && <Loader2 className="w-4 h-4 animate-spin" />}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

// Icon button variant
export function IconButton({
  icon: Icon,
  onClick,
  className,
  size = 'md',
  variant = 'ghost',
  ...props
}: {
  icon: React.ComponentType<{ className?: string }>
  onClick?: () => void
  className?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'ghost' | 'outline'
} & ButtonHTMLAttributes<HTMLButtonElement>) {
  const sizes = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3',
  }

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  }

  const variants = {
    ghost: 'text-white/70 hover:bg-white/10 hover:text-white',
    outline: 'border border-white/20 text-white/70 hover:bg-white/10 hover:text-white',
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-white/20',
        sizes[size],
        variants[variant],
        className
      )}
      {...props}
    >
      <Icon className={iconSizes[size]} />
    </button>
  )
}
