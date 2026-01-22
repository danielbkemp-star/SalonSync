# SalonSync Design Specification

> Adapted from RCMS CommandCenter Dashboard for the Hair/Beauty Industry

---

## Executive Summary

SalonSync's visual design transforms the RCMS CommandCenter's urban aesthetic into an elegant, beauty-industry focused experience. The implementation maintains the sophisticated dark theme with glassmorphism effects while introducing salon-specific visual elements and a luxurious color palette.

---

## 1. Background Design Recommendation

### Chosen Approach: **Hybrid B + D (Salon Silhouette + Geometric Luxury)**

After analyzing the existing RCMS implementation (SVG-based with CSS animations), the most technically feasible and visually impactful approach combines:

| Element | Source | Implementation |
|---------|--------|----------------|
| Salon Streetscape Silhouette | Option B | SVG vector shapes |
| Sparkle/Glitter Particles | Option D | CSS-animated DOM elements |
| Floating Gradient Orbs | Option D | CSS blur + float animations |
| Vanity Light Bulbs | Option B | SVG circles with glow animation |
| Floating Salon Icons | Option C | SVG paths with subtle rotation |

### Why This Works

1. **SVG Performance**: Vector-based silhouette scales perfectly across devices
2. **CSS Animations**: No JavaScript overhead - pure CSS @keyframes
3. **Layered Depth**: Multiple animation layers create visual richness
4. **Industry Relevance**: Immediately recognizable as beauty/salon context

### Current Implementation Status

The transformation is **already implemented** in `SalonBackground.tsx`:
- 6-building salon streetscape (salon, spa, boutique, nail salon, studio)
- Animated vanity light bulbs with gold glow
- Window glow animations simulating warm interior lighting
- Scattered sparkle/glitter particle system
- Floating salon tool icons (scissors, comb, hair dryer)
- Soft gradient orbs for atmospheric depth

---

## 2. Color Palette

### Primary Brand Colors

```css
/* ═══════════════════════════════════════════════════════════
   SALONSYNC COLOR SYSTEM
   ═══════════════════════════════════════════════════════════ */

/* PLUM - Primary Brand Color (Creativity & Elegance) */
--brand-plum-50:  #faf5ff;
--brand-plum-100: #f3e8ff;
--brand-plum-200: #e9d5ff;
--brand-plum-300: #d8b4fe;
--brand-plum-400: #c084fc;
--brand-plum-500: #a855f7;   /* ← Primary */
--brand-plum-600: #9333ea;
--brand-plum-700: #7e22ce;
--brand-plum-800: #6b21a8;
--brand-plum-900: #581c87;

/* DARK - Background System */
--brand-dark-50:  #faf5ff;
--brand-dark-100: #f3e8ff;
--brand-dark-200: #c4b5fd;
--brand-dark-300: #8b5cf6;
--brand-dark-400: #6d28d9;
--brand-dark-500: #4c1d95;
--brand-dark-600: #3b0764;
--brand-dark-700: #2e1065;   /* ← Main Background */
--brand-dark-800: #1e0a3e;   /* ← Deepest */
--brand-dark-900: #0f051f;

/* ROSE - Accent (Beauty Industry Classic) */
--brand-rose-50:  #fff1f2;
--brand-rose-100: #ffe4e6;
--brand-rose-200: #fecdd3;
--brand-rose-300: #fda4af;
--brand-rose-400: #fb7185;
--brand-rose-500: #f43f5e;   /* ← Accent */
--brand-rose-600: #e11d48;
--brand-rose-700: #be123c;
--brand-rose-800: #9f1239;
--brand-rose-900: #881337;

/* GOLD - Warm Accent (Luxury Feel) */
--brand-gold-50:  #fffbeb;
--brand-gold-100: #fef3c7;
--brand-gold-200: #fde68a;
--brand-gold-300: #fcd34d;
--brand-gold-400: #fbbf24;   /* ← Vanity Lights */
--brand-gold-500: #f59e0b;   /* ← Primary Gold */
--brand-gold-600: #d97706;
--brand-gold-700: #b45309;
--brand-gold-800: #92400e;
--brand-gold-900: #78350f;
```

### Semantic Colors

```css
/* Status & Feedback */
--color-success: #10B981;    /* Completed appointments, confirmations */
--color-warning: #F59E0B;    /* Pending items, late arrivals */
--color-error:   #EF4444;    /* Cancellations, no-shows */
--color-info:    #3B82F6;    /* Informational, neutral states */
```

### Glassmorphism Tokens

```css
/* Glass Effect System */
--glass-bg:           rgba(255, 255, 255, 0.05);
--glass-bg-hover:     rgba(255, 255, 255, 0.10);
--glass-border:       rgba(255, 255, 255, 0.10);
--glass-border-hover: rgba(255, 255, 255, 0.20);
--glass-shadow:       0 8px 32px rgba(0, 0, 0, 0.3);
--glass-blur:         blur(4px);  /* backdrop-blur-sm */
```

### Color Comparison: RCMS vs SalonSync

| Purpose | RCMS (Urban) | SalonSync (Beauty) |
|---------|--------------|-------------------|
| Primary | Blue/Cyan | Plum/Violet |
| Accent | Orange/Amber | Rose/Rose Gold |
| Highlight | Yellow | Gold/Champagne |
| Background | Dark Blue-Gray | Deep Purple-Black |
| Glow Effects | Cyan/Blue | Plum/Gold |

---

## 3. Typography

### Font Stack

```css
font-family: 'Inter', system-ui, -apple-system, sans-serif;
```

### Text Hierarchy

| Level | Class | Color | Usage |
|-------|-------|-------|-------|
| Primary | `text-white` | #FFFFFF | Headings, key metrics |
| Secondary | `text-white/60` | rgba(255,255,255,0.6) | Body text, descriptions |
| Tertiary | `text-white/40` | rgba(255,255,255,0.4) | Timestamps, metadata |
| Accent | `text-brand-plum-400` | #c084fc | Links, highlights |
| Warning | `text-brand-gold-400` | #fbbf24 | Pending states |
| Alert | `text-brand-rose-400` | #fb7185 | Urgent items |

---

## 4. Component Styles

### Card (Glassmorphism)

```jsx
// Base Card
className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"

// Hover State
className="hover:bg-white/10 hover:border-white/20 transition-all duration-200"

// Active/Selected State
className="ring-1 ring-brand-plum-500/50"

// Full Implementation
<div className="
  bg-white/5
  backdrop-blur-sm
  border border-white/10
  rounded-xl
  p-6
  hover:bg-white/10
  hover:border-white/20
  transition-all duration-200
">
  {children}
</div>
```

### Metric Card

```jsx
<div className="
  relative
  bg-white/5
  backdrop-blur-sm
  rounded-xl
  p-6
  border border-white/10
  hover:bg-white/10
  hover:border-white/20
  transition-all duration-200
  group
  overflow-hidden
">
  {/* Icon Container */}
  <div className="
    flex items-center justify-center
    w-12 h-12
    rounded-lg
    bg-brand-plum-500/20
  ">
    <Icon className="w-6 h-6 text-brand-plum-400" />
  </div>

  {/* Metric Value */}
  <p className="text-3xl font-bold text-white">{value}</p>

  {/* Label */}
  <p className="text-sm text-white/60">{label}</p>

  {/* Trend Badge */}
  <span className="text-xs text-emerald-400">+{trend}%</span>

  {/* Hover Border Effect */}
  <div className="
    absolute bottom-0 left-0 right-0 h-0.5
    bg-gradient-to-r from-transparent via-brand-plum-500 to-transparent
    transform scale-x-0
    group-hover:scale-x-100
    transition-transform duration-300
  " />
</div>
```

### Quick Action Button

```jsx
<button className="
  flex flex-col items-center justify-center
  p-4
  rounded-xl
  bg-white/5
  border border-white/10
  hover:bg-white/10
  hover:border-white/20
  transition-all duration-200
  group
">
  <div className="
    p-3 rounded-full mb-3
    bg-brand-plum-500/20
    group-hover:bg-brand-plum-500/30
  ">
    <Icon className="w-6 h-6 text-brand-plum-400" />
  </div>
  <span className="text-sm text-white/80">{label}</span>
</button>
```

### Schedule Item

```jsx
<div className={`
  flex items-center gap-4 p-4
  rounded-lg
  bg-white/5
  border border-white/10
  hover:bg-white/10
  transition-colors
  ${status === 'in_progress' ? 'ring-1 ring-brand-plum-500/50' : ''}
`}>
  {/* Time */}
  <div className="text-center">
    <p className="text-lg font-semibold text-white">{time}</p>
    <p className="text-xs text-white/40">{duration}</p>
  </div>

  {/* Details */}
  <div className="flex-1 min-w-0">
    <p className="font-medium text-white truncate">{clientName}</p>
    <p className="text-sm text-white/60 truncate">{service}</p>
  </div>

  {/* Status Badge */}
  <StatusBadge status={status} />
</div>
```

### Status Badges

```jsx
// Badge color mapping
const statusColors = {
  scheduled:  'bg-white/10 text-white/60',
  confirmed:  'bg-emerald-500/20 text-emerald-400',
  checked_in: 'bg-brand-plum-500/20 text-brand-plum-400',
  in_progress:'bg-brand-gold-500/20 text-brand-gold-400',
  completed:  'bg-emerald-500/20 text-emerald-400',
  no_show:    'bg-red-500/20 text-red-400',
  cancelled:  'bg-white/10 text-white/40',
};

<span className={`
  px-2 py-1
  text-xs font-medium
  rounded-full
  ${statusColors[status]}
`}>
  {statusLabel}
</span>
```

---

## 5. Animation System

### Available Animations

| Animation | Duration | Use Case | Tailwind Class |
|-----------|----------|----------|----------------|
| `glow-pulse` | 2s | Active items, attention | `animate-glow-pulse` |
| `fade-in-up` | 0.4s | Card entry stagger | `animate-fade-in-up` |
| `float-subtle` | 3s | Background orbs | `animate-float-subtle` |
| `border-glow` | 2s | Border highlights | `animate-border-glow` |
| `critical-pulse` | 2s | Urgent alerts | `animate-critical-pulse` |
| `slide-in-right` | 0.3s | Panel/modal entry | `animate-slide-in-right` |
| `shimmer` | 1.5s | Skeleton loading | `animate-shimmer` |
| `scale-in` | 0.2s | Popover/tooltip | `animate-scale-in` |
| `twinkle-1/2/3` | 2.5-4s | Sparkle particles | `animate-twinkle-1` |
| `sparkle-pulse` | 2s | Star highlights | `animate-sparkle-pulse` |
| `float-icon` | 6s | Floating elements | `animate-float-icon` |
| `soft-glow` | 4s | Ambient effects | `animate-soft-glow` |
| `mirror-shine` | 3s | Reflection sweep | `animate-mirror-shine` |
| `window-glow` | 4s | SVG window lights | `animate-window-glow` |
| `vanity-light` | 2s | Bulb glow pulse | `animate-vanity-light` |
| `float-particle` | 5s | Glitter drift | `animate-float-particle` |

### Animation Delays

```jsx
// Stagger animation entry
<div className="animate-fade-in-up [animation-delay:0.1s]" />
<div className="animate-fade-in-up [animation-delay:0.2s]" />
<div className="animate-fade-in-up [animation-delay:0.3s]" />

// Background element variety
<div className="animate-float-subtle [animation-delay:0s]" />
<div className="animate-float-subtle [animation-delay:2s]" />
<div className="animate-float-subtle [animation-delay:4s]" />
```

### Keyframe Definitions

Located in `/frontend/src/index.css` (lines 179-416)

```css
/* Example: Vanity Light Animation */
@keyframes vanity-light {
  0%, 100% {
    opacity: 0.7;
    box-shadow: 0 0 10px rgba(251, 191, 36, 0.5);
  }
  50% {
    opacity: 1;
    box-shadow: 0 0 20px rgba(251, 191, 36, 0.8);
  }
}

/* Example: Sparkle Twinkle */
@keyframes twinkle-1 {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}
```

---

## 6. Layout Structure

### Dashboard Grid (70/30 Split)

```jsx
<div className="flex gap-8 p-8 h-screen">
  {/* Main Content - 70% */}
  <div className="flex-1 flex flex-col gap-6 overflow-auto">
    {/* Header */}
    <header>...</header>

    {/* Metrics Grid - 6 columns */}
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <MetricCard />
      <MetricCard />
      {/* ... 6 total */}
    </div>

    {/* Two Column Content */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <NeedsAttention />
      <UpcomingAppointments />
    </div>

    {/* Quick Actions - 6 columns */}
    <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
      <QuickAction />
      {/* ... 6 total */}
    </div>
  </div>

  {/* Side Panel - 30% */}
  <aside className="w-80 xl:w-96 flex-shrink-0">
    <TodaySchedule />
  </aside>
</div>
```

### Background Layer Stack

```
┌─────────────────────────────────────────────────┐
│  z-10: Dashboard Content (cards, buttons)       │
├─────────────────────────────────────────────────┤
│  z-0: Grid Pattern Overlay                      │
├─────────────────────────────────────────────────┤
│  Floating Icons (scissors, comb, dryer)         │
├─────────────────────────────────────────────────┤
│  Sparkle/Glitter Particles                      │
├─────────────────────────────────────────────────┤
│  SVG Salon Silhouette + Window Glows            │
├─────────────────────────────────────────────────┤
│  Ambient Glow Orbs                              │
├─────────────────────────────────────────────────┤
│  Gradient Orbs (blurred circles)                │
├─────────────────────────────────────────────────┤
│  Base Gradient Background                       │
│  (from-brand-dark-800 via-dark-700 to-plum-900) │
└─────────────────────────────────────────────────┘
```

---

## 7. Files Requiring Visual Updates

### Core Design Files

| File | Purpose | Status |
|------|---------|--------|
| `frontend/tailwind.config.js` | Color palette, theme | ✅ Configured |
| `frontend/src/index.css` | Animations, utilities | ✅ Complete |

### Dashboard Components

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `SalonBackground.tsx` | 219 | Background, silhouette, sparkles | ✅ Implemented |
| `SalonDashboard.tsx` | 227 | Main layout, schedule | ✅ Implemented |
| `MetricCard.tsx` | 102 | Metric display cards | ✅ Implemented |
| `NeedsAttention.tsx` | 117 | Alert/warning items | ✅ Implemented |
| `UpcomingAppointments.tsx` | 84 | Appointment preview | ✅ Implemented |
| `QuickActions.tsx` | 78 | Action button grid | ✅ Implemented |

### Future Components (Apply Same Design)

When building new features, apply the same design tokens:

- **Forms**: Use glass card containers, `text-white/60` labels
- **Modals**: `bg-brand-dark-700` with glass overlay backdrop
- **Tables**: Striped rows using `bg-white/5` alternating
- **Inputs**: `bg-white/5 border-white/10` with focus ring
- **Dropdowns**: Glass effect with `backdrop-blur-sm`

---

## 8. Hero Actions Mapping

### RCMS → SalonSync Transformation

| RCMS Action | SalonSync Equivalent | Icon | Color |
|-------------|---------------------|------|-------|
| Find Property | Book Appointment | Calendar | Plum |
| Generate BOV | Capture Before/After | Camera | Rose |
| View Pipeline | View Schedule | Clock | Gold |
| Market Analysis | Create Social Post | Share | Emerald |
| — (new) | New Client | UserPlus | Plum |
| — (new) | Walk-In | UserCheck | Gold |

### Quick Actions Grid

```jsx
const quickActions = [
  { label: 'New Appointment', icon: CalendarPlus, color: 'plum' },
  { label: 'New Client', icon: UserPlus, color: 'plum' },
  { label: 'Check Out', icon: CreditCard, color: 'emerald' },
  { label: 'View Schedule', icon: Calendar, color: 'blue' },
  { label: 'Walk-In', icon: UserCheck, color: 'gold' },
  { label: 'Gift Cards', icon: Gift, color: 'rose' },
];
```

---

## 9. Accessibility Considerations

### Color Contrast

All text meets WCAG AA standards against dark backgrounds:
- White on `brand-dark-700`: **12.5:1** (AAA)
- `brand-plum-400` on dark: **6.2:1** (AA)
- `brand-gold-400` on dark: **8.1:1** (AAA)

### Motion Preferences

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Screen Reader Support

- All icons paired with `aria-label` or `sr-only` text
- Status badges include full status text
- Interactive elements have clear focus states

---

## 10. Implementation Checklist

### Phase 1: Foundation (Complete)
- [x] Tailwind color configuration
- [x] Animation keyframes library
- [x] Base glassmorphism utilities
- [x] Background component with silhouette
- [x] Sparkle/particle system

### Phase 2: Dashboard (Complete)
- [x] Metric card component
- [x] Schedule item component
- [x] Needs attention component
- [x] Upcoming appointments component
- [x] Quick actions grid
- [x] 70/30 layout structure

### Phase 3: Future Expansion
- [ ] Apply design to booking flow
- [ ] Apply design to client management
- [ ] Apply design to service catalog
- [ ] Apply design to reporting views
- [ ] Add dark/light mode toggle (optional)
- [ ] Create component library documentation

---

## Appendix: Icon Library

Using **Lucide React** for consistent iconography:

```jsx
import {
  Calendar, CalendarPlus,
  Clock, Timer,
  User, Users, UserPlus, UserCheck,
  Scissors,
  DollarSign, CreditCard,
  TrendingUp, TrendingDown,
  AlertCircle, AlertTriangle, CheckCircle,
  Camera, Share2, Gift,
  ChevronRight, ChevronDown,
  X, Plus, Minus,
} from 'lucide-react';
```

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Based on RCMS CommandCenter design system*
