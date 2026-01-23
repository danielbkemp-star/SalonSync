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
    <SalonBackground className={cn('h-full', className)}>
      <div className="h-full p-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Good morning!</h1>
            <p className="text-gray-400">Here's what's happening at your salon today</p>
          </div>
          <div className="text-right text-gray-400 text-sm">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              month: 'long',
              day: 'numeric',
            })}
          </div>
        </div>

        {/* Metrics Row */}
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
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
            href="/pos"
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

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - 2/3 width */}
          <div className="lg:col-span-2 space-y-6">
            {/* Two-column layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <NeedsAttention maxItems={4} />
              <UpcomingAppointments maxItems={4} />
            </div>

            {/* Quick Actions */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h2 className="text-lg font-semibold text-white mb-3">Quick Actions</h2>
              <QuickActions />
            </div>
          </div>

          {/* Right Column - Today's Schedule */}
          <div className="lg:col-span-1">
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 h-fit">
              <h2 className="text-lg font-semibold text-white mb-4">Today's Schedule</h2>
              <div className="space-y-3">
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
          </div>
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
    scheduled: 'bg-gray-700 text-gray-300',
    confirmed: 'bg-blue-500/20 text-blue-400',
    checked_in: 'bg-yellow-500/20 text-yellow-400',
    in_progress: 'bg-purple-500/20 text-purple-400',
    completed: 'bg-green-500/20 text-green-400',
    cancelled: 'bg-red-500/20 text-red-400',
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
      'bg-gray-800 border border-gray-700',
      'hover:bg-gray-750 transition-colors cursor-pointer',
      status === 'in_progress' && 'ring-1 ring-purple-500/50'
    )}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-white">{time}</span>
        <span className={cn('text-xs px-2 py-0.5 rounded-full', statusColors[status])}>
          {statusLabels[status]}
        </span>
      </div>
      <div className="text-white font-medium">{clientName}</div>
      <div className="text-gray-400 text-sm">{service} with {stylist}</div>
    </div>
  )
}

export default SalonDashboard
