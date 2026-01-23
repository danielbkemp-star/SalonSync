import { useState } from 'react'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { Button, StatusBadge, Modal, Input, Select } from '@/components/ui'
import { Plus, ChevronLeft, ChevronRight, Clock, User, Scissors } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Appointment {
  id: number
  time: string
  endTime: string
  clientName: string
  service: string
  stylist: string
  status: 'scheduled' | 'confirmed' | 'checked_in' | 'in_progress' | 'completed' | 'cancelled'
  notes?: string
}

// Mock data
const mockAppointments: Appointment[] = [
  { id: 1, time: '09:00', endTime: '10:30', clientName: 'Sarah Johnson', service: 'Haircut & Color', stylist: 'Jessica', status: 'completed' },
  { id: 2, time: '10:30', endTime: '12:30', clientName: 'Emily Davis', service: 'Balayage', stylist: 'Maria', status: 'in_progress' },
  { id: 3, time: '12:00', endTime: '12:45', clientName: 'Lisa Chen', service: 'Manicure', stylist: 'Amy', status: 'checked_in' },
  { id: 4, time: '13:30', endTime: '14:00', clientName: 'Rachel Kim', service: 'Blowout', stylist: 'Jessica', status: 'confirmed' },
  { id: 5, time: '15:00', endTime: '17:00', clientName: 'Michelle Lee', service: 'Full Highlights', stylist: 'Maria', status: 'scheduled' },
  { id: 6, time: '16:30', endTime: '17:30', clientName: 'Amanda Brown', service: 'Haircut', stylist: 'Jessica', status: 'scheduled' },
]

const timeSlots = [
  '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
  '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
  '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
]

const stylists = ['Jessica', 'Maria', 'Amy']

export function AppointmentsPage() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [showNewAppointmentModal, setShowNewAppointmentModal] = useState(false)
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)
  const [viewMode, setViewMode] = useState<'day' | 'week'>('day')

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const navigateDate = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate)
    if (viewMode === 'day') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1))
    } else {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7))
    }
    setCurrentDate(newDate)
  }

  const getAppointmentForSlot = (time: string, stylist: string) => {
    return mockAppointments.find(
      (apt) => apt.time === time && apt.stylist === stylist
    )
  }

  const getAppointmentHeight = (apt: Appointment) => {
    const startParts = apt.time.split(':').map(Number)
    const endParts = apt.endTime.split(':').map(Number)
    const startMinutes = startParts[0] * 60 + startParts[1]
    const endMinutes = endParts[0] * 60 + endParts[1]
    const duration = endMinutes - startMinutes
    return Math.max(1, duration / 30) // Each slot is 30 min
  }

  return (
    <SalonBackground className="h-full">
      <div className="h-full flex flex-col p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Appointments</h1>
            <p className="text-gray-400">Manage your salon schedule</p>
          </div>
          <Button variant="primary" onClick={() => setShowNewAppointmentModal(true)}>
            <Plus className="h-4 w-4" />
            New Appointment
          </Button>
        </div>

        {/* Calendar Controls */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigateDate('prev')}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={() => setCurrentDate(new Date())}
              className="px-4 py-2 rounded-lg hover:bg-gray-800 text-white transition-colors"
            >
              Today
            </button>
            <button
              onClick={() => navigateDate('next')}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
            <span className="ml-4 text-lg font-medium text-white">{formatDate(currentDate)}</span>
          </div>

          <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('day')}
              className={cn(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                viewMode === 'day' ? 'bg-purple-500 text-white' : 'text-gray-400 hover:text-white'
              )}
            >
              Day
            </button>
            <button
              onClick={() => setViewMode('week')}
              className={cn(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                viewMode === 'week' ? 'bg-purple-500 text-white' : 'text-gray-400 hover:text-white'
              )}
            >
              Week
            </button>
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="flex-1 rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
          <div className="flex h-full">
            {/* Time Column */}
            <div className="w-20 flex-shrink-0 border-r border-gray-800">
              <div className="h-12 border-b border-gray-800" /> {/* Header spacer */}
              {timeSlots.map((time) => (
                <div
                  key={time}
                  className="h-16 flex items-start justify-end pr-3 pt-1 text-xs text-gray-500"
                >
                  {time}
                </div>
              ))}
            </div>

            {/* Stylist Columns */}
            <div className="flex-1 flex overflow-x-auto">
              {stylists.map((stylist) => (
                <div key={stylist} className="flex-1 min-w-[200px] border-r border-gray-800 last:border-0">
                  {/* Stylist Header */}
                  <div className="h-12 flex items-center justify-center border-b border-gray-800 bg-gray-800/50">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-sm font-medium">
                        {stylist[0]}
                      </div>
                      <span className="text-white font-medium">{stylist}</span>
                    </div>
                  </div>

                  {/* Time Slots */}
                  <div className="relative">
                    {timeSlots.map((time) => {
                      const apt = getAppointmentForSlot(time, stylist)
                      return (
                        <div
                          key={time}
                          className="h-16 border-b border-gray-800/50 relative"
                        >
                          {apt && (
                            <button
                              onClick={() => setSelectedAppointment(apt)}
                              className={cn(
                                'absolute inset-x-1 top-1 rounded-lg p-2 text-left transition-all hover:ring-2 hover:ring-purple-500',
                                apt.status === 'completed' && 'bg-green-500/20 border border-green-500/30',
                                apt.status === 'in_progress' && 'bg-purple-500/20 border border-purple-500/30',
                                apt.status === 'checked_in' && 'bg-yellow-500/20 border border-yellow-500/30',
                                apt.status === 'confirmed' && 'bg-blue-500/20 border border-blue-500/30',
                                apt.status === 'scheduled' && 'bg-gray-700 border border-gray-600',
                                apt.status === 'cancelled' && 'bg-red-500/20 border border-red-500/30 opacity-50'
                              )}
                              style={{ height: `${getAppointmentHeight(apt) * 64 - 8}px` }}
                            >
                              <div className="text-white text-sm font-medium truncate">{apt.clientName}</div>
                              <div className="text-gray-400 text-xs truncate">{apt.service}</div>
                              <div className="text-gray-500 text-xs">{apt.time} - {apt.endTime}</div>
                            </button>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* New Appointment Modal */}
        <Modal
          isOpen={showNewAppointmentModal}
          onClose={() => setShowNewAppointmentModal(false)}
          title="New Appointment"
          size="md"
        >
          <form className="space-y-4">
            <Input label="Client Name" placeholder="Search or enter client name" />
            <Select
              label="Service"
              options={[
                { value: 'haircut', label: 'Haircut' },
                { value: 'color', label: 'Color' },
                { value: 'balayage', label: 'Balayage' },
                { value: 'highlights', label: 'Highlights' },
                { value: 'blowout', label: 'Blowout' },
                { value: 'manicure', label: 'Manicure' },
              ]}
            />
            <Select
              label="Stylist"
              options={stylists.map(s => ({ value: s.toLowerCase(), label: s }))}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Date" type="date" />
              <Input label="Time" type="time" />
            </div>
            <div className="flex gap-3 justify-end pt-4">
              <Button variant="ghost" onClick={() => setShowNewAppointmentModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Book Appointment
              </Button>
            </div>
          </form>
        </Modal>

        {/* Appointment Detail Modal */}
        <Modal
          isOpen={!!selectedAppointment}
          onClose={() => setSelectedAppointment(null)}
          title="Appointment Details"
          size="md"
        >
          {selectedAppointment && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium">
                    {selectedAppointment.clientName.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <div className="text-lg font-medium text-white">{selectedAppointment.clientName}</div>
                    <StatusBadge status={selectedAppointment.status} />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 p-4 rounded-lg bg-gray-800">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-gray-400">Time</div>
                    <div className="text-white">{selectedAppointment.time} - {selectedAppointment.endTime}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Scissors className="h-4 w-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-gray-400">Service</div>
                    <div className="text-white">{selectedAppointment.service}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-gray-400">Stylist</div>
                    <div className="text-white">{selectedAppointment.stylist}</div>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                {selectedAppointment.status === 'scheduled' && (
                  <Button variant="primary" className="flex-1">Confirm</Button>
                )}
                {selectedAppointment.status === 'confirmed' && (
                  <Button variant="primary" className="flex-1">Check In</Button>
                )}
                {selectedAppointment.status === 'checked_in' && (
                  <Button variant="primary" className="flex-1">Start Service</Button>
                )}
                {selectedAppointment.status === 'in_progress' && (
                  <Button variant="primary" className="flex-1">Complete</Button>
                )}
                <Button variant="ghost">Reschedule</Button>
                <Button variant="danger">Cancel</Button>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </SalonBackground>
  )
}
