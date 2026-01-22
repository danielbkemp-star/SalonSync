import { cn } from '@/lib/utils'

interface SalonBackgroundProps {
  className?: string
  children?: React.ReactNode
  showSalonscape?: boolean
}

export function SalonBackground({
  className,
  children,
  showSalonscape = true,
}: SalonBackgroundProps) {
  return (
    <div
      className={cn(
        'relative min-h-full w-full',
        'bg-gradient-to-br from-brand-dark-800 via-brand-dark-700 to-brand-plum-900',
        className
      )}
    >
      {/* Animated gradient orbs for depth */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Top-right glow - rose gold */}
        <div
          className={cn(
            'absolute -top-1/4 -right-1/4 w-1/2 h-1/2',
            'bg-brand-rose-500/10 rounded-full blur-3xl',
            'animate-float-subtle'
          )}
        />
        {/* Bottom-left glow - purple */}
        <div
          className={cn(
            'absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2',
            'bg-brand-plum-500/20 rounded-full blur-3xl',
            'animate-float-subtle',
            '[animation-delay:2s]'
          )}
        />
        {/* Center accent - gold */}
        <div
          className={cn(
            'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
            'w-3/4 h-3/4',
            'bg-brand-gold-500/5 rounded-full blur-3xl'
          )}
        />
      </div>

      {/* Floating Sparkles/Glitter */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Row 1 */}
        <div className="absolute bottom-[20%] left-[5%] w-1 h-1 bg-brand-gold-300 rounded-full animate-twinkle-1" />
        <div className="absolute bottom-[25%] left-[12%] w-1.5 h-1.5 bg-white rounded-full animate-twinkle-2" />
        <div className="absolute bottom-[22%] left-[20%] w-1 h-1 bg-brand-rose-300 rounded-full animate-twinkle-3 [animation-delay:0.5s]" />
        <div className="absolute bottom-[28%] left-[30%] w-1 h-1 bg-brand-gold-200 rounded-full animate-twinkle-1 [animation-delay:1.2s]" />
        <div className="absolute bottom-[24%] left-[42%] w-1 h-1 bg-white rounded-full animate-twinkle-2 [animation-delay:0.3s]" />
        <div className="absolute bottom-[26%] left-[55%] w-1.5 h-1.5 bg-brand-plum-300 rounded-full animate-twinkle-3 [animation-delay:1.8s]" />
        <div className="absolute bottom-[23%] left-[68%] w-1 h-1 bg-brand-gold-300 rounded-full animate-twinkle-1 [animation-delay:0.7s]" />
        <div className="absolute bottom-[27%] left-[80%] w-1 h-1 bg-white rounded-full animate-twinkle-2 [animation-delay:2.1s]" />
        <div className="absolute bottom-[21%] left-[92%] w-1 h-1 bg-brand-rose-200 rounded-full animate-twinkle-3 [animation-delay:0.4s]" />

        {/* Row 2 */}
        <div className="absolute bottom-[32%] left-[8%] w-1 h-1 bg-white rounded-full animate-twinkle-2 [animation-delay:0.9s]" />
        <div className="absolute bottom-[35%] left-[18%] w-1.5 h-1.5 bg-brand-gold-200 rounded-full animate-twinkle-3 [animation-delay:1.6s]" />
        <div className="absolute bottom-[33%] left-[35%] w-1 h-1 bg-brand-rose-300 rounded-full animate-twinkle-1 [animation-delay:0.2s]" />
        <div className="absolute bottom-[36%] left-[50%] w-1 h-1 bg-white rounded-full animate-twinkle-2 [animation-delay:2.3s]" />
        <div className="absolute bottom-[31%] left-[65%] w-1 h-1 bg-brand-plum-300 rounded-full animate-twinkle-3 [animation-delay:0.6s]" />
        <div className="absolute bottom-[34%] left-[78%] w-1.5 h-1.5 bg-brand-gold-300 rounded-full animate-twinkle-1 [animation-delay:1.1s]" />
        <div className="absolute bottom-[37%] left-[88%] w-1 h-1 bg-white rounded-full animate-twinkle-2 [animation-delay:1.9s]" />

        {/* Larger sparkle stars */}
        <div className="absolute bottom-[30%] left-[25%] animate-sparkle-pulse">
          <div className="relative w-3 h-3">
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-gold-300 to-transparent w-0.5 h-full left-1/2 -translate-x-1/2" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-brand-gold-300 to-transparent h-0.5 w-full top-1/2 -translate-y-1/2" />
          </div>
        </div>
        <div className="absolute bottom-[35%] left-[60%] animate-sparkle-pulse [animation-delay:0.7s]">
          <div className="relative w-2.5 h-2.5">
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white to-transparent w-0.5 h-full left-1/2 -translate-x-1/2" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent h-0.5 w-full top-1/2 -translate-y-1/2" />
          </div>
        </div>

        {/* Floating salon icons */}
        <div className="absolute bottom-[40%] left-[10%] opacity-20 animate-float-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-brand-gold-300">
            {/* Scissors icon */}
            <path d="M6.5 3C8.43 3 10 4.57 10 6.5c0 1.05-.46 1.99-1.19 2.63l2.19 2.37 2.19-2.37C12.46 8.49 12 7.55 12 6.5 12 4.57 13.57 3 15.5 3S19 4.57 19 6.5c0 1.05-.46 1.99-1.19 2.63L12 16.5l-5.81-7.37C5.46 8.49 5 7.55 5 6.5 5 4.57 6.57 3 8.5 3m0 2C7.67 5 7 5.67 7 6.5S7.67 8 8.5 8 10 7.33 10 6.5 9.33 5 8.5 5m7 0c-.83 0-1.5.67-1.5 1.5S14.67 8 15.5 8 17 7.33 17 6.5 16.33 5 15.5 5"/>
          </svg>
        </div>
        <div className="absolute bottom-[45%] right-[15%] opacity-20 animate-float-icon [animation-delay:2s]">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="text-brand-rose-300">
            {/* Comb icon */}
            <path d="M4 2v20h2V2H4m4 0v20h2V2H8m4 0v12h2V2h-2m4 0v8h2V2h-2m4 0v4h2V2h-2"/>
          </svg>
        </div>
        <div className="absolute bottom-[50%] left-[50%] opacity-15 animate-float-icon [animation-delay:3s]">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" className="text-brand-plum-300 animate-styling-tool">
            {/* Hair dryer icon */}
            <path d="M22 9a4.32 4.32 0 0 1-2.22-.55A3.4 3.4 0 0 0 18 8V7a1 1 0 0 0-1-1h-2a1 1 0 0 0-1 1v1a3.4 3.4 0 0 0-1.78.45A4.32 4.32 0 0 1 10 9a5 5 0 0 0 0 10 4.32 4.32 0 0 1 2.22.55A3.4 3.4 0 0 0 14 20v1a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1v-1a3.4 3.4 0 0 0 1.78-.45A4.32 4.32 0 0 1 22 19a5 5 0 0 0 0-10zm-6 9a4 4 0 1 1 0-8 4 4 0 0 1 0 8z"/>
          </svg>
        </div>
      </div>

      {/* Subtle grid pattern overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Salon silhouette at bottom */}
      {showSalonscape && (
        <div className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none overflow-hidden">
          <svg
            viewBox="0 0 1200 140"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="absolute bottom-0 w-full h-full opacity-25"
            preserveAspectRatio="xMidYMax slice"
          >
            {/* Salon/spa building silhouette */}
            <g className="text-brand-dark-900">
              {/* Left storefront with large window */}
              <rect x="0" y="50" width="150" height="90" fill="currentColor" />
              <rect x="10" y="60" width="60" height="50" fill="rgba(168,85,247,0.15)" className="animate-window-glow" />
              <rect x="80" y="60" width="60" height="50" fill="rgba(168,85,247,0.1)" className="animate-window-glow [animation-delay:1s]" />
              {/* Door */}
              <rect x="55" y="90" width="40" height="50" fill="rgba(0,0,0,0.3)" />

              {/* Main salon building with awning */}
              <rect x="160" y="30" width="250" height="110" fill="currentColor" />
              {/* Awning */}
              <polygon points="160,30 285,15 410,30 410,40 160,40" fill="rgba(168,85,247,0.3)" />
              {/* Large front windows */}
              <rect x="175" y="50" width="80" height="60" fill="rgba(253,224,71,0.15)" className="animate-window-glow [animation-delay:0.5s]" />
              <rect x="270" y="50" width="80" height="60" fill="rgba(253,224,71,0.12)" className="animate-window-glow [animation-delay:1.5s]" />
              {/* Salon chairs visible through window (silhouette) */}
              <ellipse cx="215" cy="95" rx="15" ry="10" fill="rgba(0,0,0,0.2)" />
              <ellipse cx="310" cy="95" rx="15" ry="10" fill="rgba(0,0,0,0.2)" />
              {/* Door */}
              <rect x="360" y="80" width="35" height="60" fill="rgba(0,0,0,0.3)" />

              {/* Spa building with arched windows */}
              <rect x="420" y="40" width="180" height="100" fill="currentColor" />
              {/* Arched window frames */}
              <path d="M440 50 L440 100 L490 100 L490 50 Q465 35 440 50" fill="rgba(244,63,94,0.1)" className="animate-window-glow [animation-delay:2s]" />
              <path d="M510 50 L510 100 L560 100 L560 50 Q535 35 510 50" fill="rgba(244,63,94,0.08)" className="animate-window-glow" />
              {/* Door */}
              <rect x="570" y="85" width="25" height="55" fill="rgba(0,0,0,0.3)" />

              {/* Boutique shop */}
              <rect x="610" y="55" width="120" height="85" fill="currentColor" />
              <rect x="620" y="65" width="45" height="40" fill="rgba(168,85,247,0.12)" className="animate-window-glow [animation-delay:0.7s]" />
              <rect x="675" y="65" width="45" height="40" fill="rgba(168,85,247,0.1)" className="animate-window-glow [animation-delay:1.3s]" />
              {/* Door */}
              <rect x="655" y="95" width="30" height="45" fill="rgba(0,0,0,0.3)" />

              {/* Nail salon with vanity lights */}
              <rect x="740" y="45" width="160" height="95" fill="currentColor" />
              <rect x="755" y="55" width="55" height="45" fill="rgba(253,224,71,0.1)" className="animate-window-glow [animation-delay:1s]" />
              <rect x="825" y="55" width="55" height="45" fill="rgba(253,224,71,0.08)" className="animate-window-glow [animation-delay:2s]" />
              {/* Door */}
              <rect x="870" y="90" width="25" height="50" fill="rgba(0,0,0,0.3)" />

              {/* Hair studio building */}
              <rect x="910" y="35" width="180" height="105" fill="currentColor" />
              {/* Modern angular window */}
              <polygon points="930,50 1010,45 1010,95 930,95" fill="rgba(168,85,247,0.12)" className="animate-window-glow [animation-delay:0.3s]" />
              <polygon points="1020,50 1080,45 1080,95 1020,95" fill="rgba(168,85,247,0.08)" className="animate-window-glow [animation-delay:1.7s]" />
              {/* Door */}
              <rect x="1050" y="85" width="30" height="55" fill="rgba(0,0,0,0.3)" />

              {/* Far right boutique */}
              <rect x="1100" y="50" width="100" height="90" fill="currentColor" />
              <rect x="1110" y="60" width="35" height="45" fill="rgba(244,63,94,0.1)" className="animate-window-glow [animation-delay:1.2s]" />
              <rect x="1155" y="60" width="35" height="45" fill="rgba(244,63,94,0.08)" className="animate-window-glow [animation-delay:0.8s]" />
            </g>

            {/* Vanity light bulbs on main salon */}
            <g className="text-brand-gold-300">
              <circle cx="190" cy="45" r="3" fill="currentColor" className="animate-vanity-light" />
              <circle cx="210" cy="45" r="3" fill="currentColor" className="animate-vanity-light-delayed" />
              <circle cx="230" cy="45" r="3" fill="currentColor" className="animate-vanity-light-delayed-2" />
              <circle cx="250" cy="45" r="3" fill="currentColor" className="animate-vanity-light" />
              <circle cx="270" cy="45" r="3" fill="currentColor" className="animate-vanity-light-delayed" />
              <circle cx="290" cy="45" r="3" fill="currentColor" className="animate-vanity-light-delayed-2" />
              <circle cx="310" cy="45" r="3" fill="currentColor" className="animate-vanity-light" />
              <circle cx="330" cy="45" r="3" fill="currentColor" className="animate-vanity-light-delayed" />
              <circle cx="350" cy="45" r="3" fill="currentColor" className="animate-vanity-light-delayed-2" />
            </g>

            {/* Salon signs (neon-style glow) */}
            <text x="285" y="27" fill="rgba(168,85,247,0.6)" fontSize="12" fontFamily="sans-serif" textAnchor="middle" className="animate-glow-pulse">SALON</text>
            <text x="510" y="38" fill="rgba(244,63,94,0.5)" fontSize="10" fontFamily="sans-serif" textAnchor="middle">SPA</text>
            <text x="990" y="33" fill="rgba(168,85,247,0.5)" fontSize="10" fontFamily="sans-serif" textAnchor="middle">STUDIO</text>
          </svg>

          {/* Soft ambient glow from windows */}
          <div className="absolute bottom-[50%] left-[20%] w-32 h-16 bg-brand-gold-500/10 rounded-full blur-xl animate-soft-glow" />
          <div className="absolute bottom-[50%] left-[40%] w-24 h-12 bg-brand-rose-500/10 rounded-full blur-xl animate-soft-glow [animation-delay:1s]" />
          <div className="absolute bottom-[50%] left-[70%] w-28 h-14 bg-brand-plum-500/10 rounded-full blur-xl animate-soft-glow [animation-delay:2s]" />
        </div>
      )}

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  )
}
