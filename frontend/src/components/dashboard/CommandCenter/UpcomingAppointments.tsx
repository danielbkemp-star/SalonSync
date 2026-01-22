import { cn } from '@/lib/utils'
import { Clock, User, Scissors } from 'lucide-react'

interface UpcomingAppointmentsProps {
  maxItems?: number
  className?: string
}

export function UpcomingAppointments({ maxItems = 5, className }: UpcomingAppointmentsProps) {
  // TODO: Fetch from API
  const appointments = [
    {
      id: 1,
      clientName: 'Lisa Chen',
      time: '12:00 PM',
      service: 'Manicure',
      duration: 45,
      status: 'checked_in',
    },
    {
      id: 2,
      clientName: 'Rachel Kim',
      time: '1:30 PM',
      service: 'Blowout',
      duration: 30,
      status: 'confirmed',
    },
    {
      id: 3,
      clientName: 'Michelle Lee',
      time: '3:00 PM',
      service: 'Full Highlights',
      duration: 120,
      status: 'scheduled',
    },
  ].slice(0, maxItems)

  return (
    <div className={cn('rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 p-4', className)}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Upcoming</h2>
        <a href="/appointments" className="text-sm text-brand-plum-400 hover:text-brand-plum-300">
          View all
        </a>
      </div>

      <div className="space-y-3">
        {appointments.map((apt) => (
          <div
            key={apt.id}
            className={cn(
              'p-3 rounded-lg',
              'bg-white/5 border border-white/10',
              'hover:bg-white/10 transition-colors cursor-pointer'
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-brand-plum-400" />
                <span className="text-white font-medium">{apt.time}</span>
              </div>
              <span className="text-xs text-white/50">{apt.duration} min</span>
            </div>
            <div className="flex items-center gap-2 mb-1">
              <User className="h-4 w-4 text-white/40" />
              <span className="text-white/90">{apt.clientName}</span>
            </div>
            <div className="flex items-center gap-2">
              <Scissors className="h-4 w-4 text-white/40" />
              <span className="text-white/60 text-sm">{apt.service}</span>
            </div>
          </div>
        ))}

        {appointments.length === 0 && (
          <div className="text-center py-8 text-white/50">
            No upcoming appointments
          </div>
        )}
      </div>
    </div>
  )
}
