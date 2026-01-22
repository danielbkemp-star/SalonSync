import { SalonBackground } from './SalonBackground'
import { MetricCard } from './MetricCard'
import { UpcomingAppointments } from './UpcomingAppointments'
import { NeedsAttention } from './NeedsAttention'
import { QuickActions } from './QuickActions'
import { cn } from '@/lib/utils'
import { Calendar, DollarSign, Users, Scissors, TrendingUp, Clock } from 'lucide-react'

interface SalonDashboardProps {
  className?: string
}

export function SalonDashboard({ className }: SalonDashboardProps) {
  // TODO: Fetch from API
  const metrics = {
    todayAppointments: 12,
    todayRevenue: 1450.00,
    weekRevenue: 8750.00,
    newClients: 8,
    upcomingCount: 3,
    completedToday: 6,
  }

  return (
    <SalonBackground
      className={cn('min-h-full h-full', className)}
      showSalonscape={true}
    >
      <div className="h-full p-4 lg:p-6">
        {/* Two-panel layout: Main (70%) + Side Panel (30%) */}
        <div className="h-full flex flex-col lg:flex-row gap-6">
          {/* Main Content Area - Left Side */}
          <main
            className="flex-1 lg:w-[70%] overflow-y-auto space-y-6"
            role="main"
            aria-label="Dashboard Main Area"
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white">Good morning!</h1>
                <p className="text-white/60">Here's what's happening at your salon today</p>
              </div>
              <div className="text-right text-white/60 text-sm">
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric',
                })}
              </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
              <MetricCard
                value={metrics.todayAppointments}
                label="Appointments"
                sublabel="Today"
                icon={Calendar}
                href="/appointments"
                compact
              />
              <MetricCard
                value={`$${metrics.todayRevenue.toLocaleString()}`}
                label="Revenue"
                sublabel="Today"
                icon={DollarSign}
                href="/sales"
                trend={{ value: 12, isPositive: true }}
                compact
              />
              <MetricCard
                value={`$${metrics.weekRevenue.toLocaleString()}`}
                label="Revenue"
                sublabel="This Week"
                icon={TrendingUp}
                href="/reports"
                compact
              />
              <MetricCard
                value={metrics.newClients}
                label="New Clients"
                sublabel="This Month"
                icon={Users}
                href="/clients"
                compact
              />
              <MetricCard
                value={metrics.upcomingCount}
                label="Upcoming"
                sublabel="Next 2 Hours"
                icon={Clock}
                href="/appointments"
                compact
              />
              <MetricCard
                value={metrics.completedToday}
                label="Completed"
                sublabel="Today"
                icon={Scissors}
                href="/appointments"
                compact
              />
            </div>

            {/* Two-column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <NeedsAttention maxItems={4} />
              <UpcomingAppointments maxItems={4} />
            </div>

            {/* Quick Actions */}
            <div className="rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 p-4">
              <h2 className="text-lg font-semibold text-white mb-3">Quick Actions</h2>
              <QuickActions />
            </div>
          </main>

          {/* Side Panel - Today's Schedule */}
          <aside
            className="w-full lg:w-[30%] lg:min-w-[320px] lg:max-w-[400px]"
            role="complementary"
            aria-label="Today's Schedule"
          >
            <div className="h-full rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Today's Schedule</h2>
              <div className="space-y-3">
                {/* Placeholder for schedule items */}
                <ScheduleItem
                  time="9:00 AM"
                  clientName="Sarah Johnson"
                  service="Haircut & Color"
                  stylist="Jessica"
                  status="completed"
                />
                <ScheduleItem
                  time="10:30 AM"
                  clientName="Emily Davis"
                  service="Balayage"
                  stylist="Maria"
                  status="in_progress"
                />
                <ScheduleItem
                  time="12:00 PM"
                  clientName="Lisa Chen"
                  service="Manicure"
                  stylist="Amy"
                  status="checked_in"
                />
                <ScheduleItem
                  time="1:30 PM"
                  clientName="Rachel Kim"
                  service="Blowout"
                  stylist="Jessica"
                  status="scheduled"
                />
                <ScheduleItem
                  time="3:00 PM"
                  clientName="Michelle Lee"
                  service="Full Highlights"
                  stylist="Maria"
                  status="scheduled"
                />
                <ScheduleItem
                  time="4:30 PM"
                  clientName="Amanda Brown"
                  service="Haircut"
                  stylist="Jessica"
                  status="scheduled"
                />
              </div>
            </div>
          </aside>
        </div>
      </div>
    </SalonBackground>
  )
}

interface ScheduleItemProps {
  time: string
  clientName: string
  service: string
  stylist: string
  status: 'scheduled' | 'confirmed' | 'checked_in' | 'in_progress' | 'completed' | 'cancelled'
}

function ScheduleItem({ time, clientName, service, stylist, status }: ScheduleItemProps) {
  const statusColors = {
    scheduled: 'bg-gray-400/20 text-gray-300',
    confirmed: 'bg-blue-400/20 text-blue-300',
    checked_in: 'bg-yellow-400/20 text-yellow-300',
    in_progress: 'bg-brand-plum-400/20 text-brand-plum-300',
    completed: 'bg-green-400/20 text-green-300',
    cancelled: 'bg-red-400/20 text-red-300',
  }

  const statusLabels = {
    scheduled: 'Scheduled',
    confirmed: 'Confirmed',
    checked_in: 'Checked In',
    in_progress: 'In Progress',
    completed: 'Done',
    cancelled: 'Cancelled',
  }

  return (
    <div className={cn(
      'p-3 rounded-lg',
      'bg-white/5 border border-white/10',
      'hover:bg-white/10 transition-colors cursor-pointer',
      status === 'in_progress' && 'ring-1 ring-brand-plum-500/50'
    )}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-white">{time}</span>
        <span className={cn('text-xs px-2 py-0.5 rounded-full', statusColors[status])}>
          {statusLabels[status]}
        </span>
      </div>
      <div className="text-white/90 font-medium">{clientName}</div>
      <div className="text-white/50 text-sm">{service} with {stylist}</div>
    </div>
  )
}

export default SalonDashboard
