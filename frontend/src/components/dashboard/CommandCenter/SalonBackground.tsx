import { cn } from '@/lib/utils'

interface SalonBackgroundProps {
  className?: string
  children?: React.ReactNode
}

export function SalonBackground({
  className,
  children,
}: SalonBackgroundProps) {
  return (
    <div
      className={cn(
        'relative min-h-full w-full',
        'bg-gray-950',
        className
      )}
    >
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Top-right subtle glow */}
        <div
          className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 bg-purple-500/5 rounded-full blur-3xl"
        />
        {/* Bottom-left subtle glow */}
        <div
          className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 bg-purple-600/5 rounded-full blur-3xl"
        />
      </div>

      {/* Subtle grid pattern overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.02]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  )
}
