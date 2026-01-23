import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button, Input } from '@/components/ui'
import {
  Calendar,
  Clock,
  User,
  Scissors,
  CheckCircle,
  ChevronRight,
  ChevronLeft,
  MapPin,
  Phone,
  Mail,
  AlertCircle,
} from 'lucide-react'
import {
  getSalonForBooking,
  getBookableServices,
  getBookableStaff,
  getAvailability,
  createBooking,
  type PublicSalonInfo,
  type PublicServiceInfo,
  type PublicStaffInfo,
  type AvailabilityResponse,
  type BookingResponse,
} from '@/api/booking'

type BookingStep = 'service' | 'staff' | 'datetime' | 'details' | 'confirmation'

export function BookingPage() {
  const { salonSlug } = useParams<{ salonSlug: string }>()
  const [searchParams] = useSearchParams()

  // State
  const [step, setStep] = useState<BookingStep>('service')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Data
  const [salon, setSalon] = useState<PublicSalonInfo | null>(null)
  const [services, setServices] = useState<PublicServiceInfo[]>([])
  const [staff, setStaff] = useState<PublicStaffInfo[]>([])
  const [availability, setAvailability] = useState<AvailabilityResponse[]>([])

  // Selections
  const [selectedService, setSelectedService] = useState<PublicServiceInfo | null>(null)
  const [selectedStaff, setSelectedStaff] = useState<PublicStaffInfo | null>(null)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [selectedTime, setSelectedTime] = useState<string | null>(null)

  // Form data
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    notes: '',
    sms_reminders: true,
    email_reminders: true,
  })

  // Booking result
  const [bookingResult, setBookingResult] = useState<BookingResponse | null>(null)

  // Load initial data
  useEffect(() => {
    if (!salonSlug) return

    const loadData = async () => {
      try {
        setLoading(true)
        setError(null)

        const [salonData, servicesData] = await Promise.all([
          getSalonForBooking(salonSlug),
          getBookableServices(salonSlug),
        ])

        setSalon(salonData)
        setServices(servicesData)

        // Check for pre-selected service from URL
        const serviceId = searchParams.get('service')
        if (serviceId) {
          const preSelectedService = servicesData.find(s => s.id === parseInt(serviceId))
          if (preSelectedService) {
            setSelectedService(preSelectedService)
            setStep('staff')
          }
        }
      } catch (err) {
        setError('Unable to load booking information. Please try again.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [salonSlug, searchParams])

  // Load staff when service is selected
  useEffect(() => {
    if (!salonSlug || !selectedService) return

    const loadStaff = async () => {
      try {
        const staffData = await getBookableStaff(salonSlug, selectedService.id)
        setStaff(staffData)
      } catch (err) {
        console.error('Failed to load staff:', err)
      }
    }

    loadStaff()
  }, [salonSlug, selectedService])

  // Load availability when staff is selected
  useEffect(() => {
    if (!salonSlug || !selectedService || !selectedStaff) return

    const loadAvailability = async () => {
      try {
        const availData = await getAvailability(salonSlug, selectedService.id, selectedStaff.id)
        setAvailability(availData)
      } catch (err) {
        console.error('Failed to load availability:', err)
      }
    }

    loadAvailability()
  }, [salonSlug, selectedService, selectedStaff])

  // Handle booking submission
  const handleSubmit = async () => {
    if (!salonSlug || !selectedService || !selectedStaff || !selectedDate || !selectedTime) return

    try {
      setSubmitting(true)
      setError(null)

      const result = await createBooking(salonSlug, {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        phone: formData.phone,
        service_id: selectedService.id,
        staff_id: selectedStaff.id,
        date: selectedDate,
        time: selectedTime,
        notes: formData.notes || undefined,
        sms_reminders: formData.sms_reminders,
        email_reminders: formData.email_reminders,
      })

      setBookingResult(result)
      setStep('confirmation')
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to book appointment'
      setError(errorMessage)
    } finally {
      setSubmitting(false)
    }
  }

  // Group services by category
  const servicesByCategory = services.reduce((acc, service) => {
    if (!acc[service.category]) {
      acc[service.category] = []
    }
    acc[service.category].push(service)
    return acc
  }, {} as Record<string, PublicServiceInfo[]>)

  // Group availability by date
  const availabilityByDate = availability.reduce((acc, item) => {
    if (!acc[item.date]) {
      acc[item.date] = []
    }
    acc[item.date].push(...item.slots)
    return acc
  }, {} as Record<string, { time: string; datetime: string; available: boolean }[]>)

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  if (error && !salon) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-white mb-2">Booking Unavailable</h1>
          <p className="text-gray-400">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center gap-4">
            {salon?.logo_url ? (
              <img src={salon.logo_url} alt={salon.name} className="h-12 w-12 rounded-xl object-cover" />
            ) : (
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Scissors className="h-6 w-6 text-white" />
              </div>
            )}
            <div>
              <h1 className="text-xl font-bold text-white">{salon?.name}</h1>
              <p className="text-gray-400 text-sm">Book an appointment</p>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      {step !== 'confirmation' && (
        <div className="bg-gray-900/50 border-b border-gray-800">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              {['service', 'staff', 'datetime', 'details'].map((s, index) => {
                const stepLabels = ['Service', 'Staff', 'Date & Time', 'Your Details']
                const isActive = s === step
                const isPast = ['service', 'staff', 'datetime', 'details'].indexOf(step) > index

                return (
                  <div key={s} className="flex items-center">
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                          isActive && 'bg-purple-500 text-white',
                          isPast && 'bg-green-500 text-white',
                          !isActive && !isPast && 'bg-gray-800 text-gray-400'
                        )}
                      >
                        {isPast ? <CheckCircle className="h-4 w-4" /> : index + 1}
                      </div>
                      <span className={cn('text-sm hidden sm:block', isActive ? 'text-white' : 'text-gray-400')}>
                        {stepLabels[index]}
                      </span>
                    </div>
                    {index < 3 && (
                      <ChevronRight className="h-4 w-4 text-gray-600 mx-2 sm:mx-4" />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Step: Select Service */}
        {step === 'service' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Select a Service</h2>
            <div className="space-y-8">
              {Object.entries(servicesByCategory).map(([category, categoryServices]) => (
                <div key={category}>
                  <h3 className="text-lg font-semibold text-gray-300 mb-3">{category}</h3>
                  <div className="grid gap-3">
                    {categoryServices.map((service) => (
                      <button
                        key={service.id}
                        onClick={() => {
                          setSelectedService(service)
                          setStep('staff')
                        }}
                        className={cn(
                          'w-full p-4 rounded-xl text-left transition-all',
                          'bg-gray-900 border border-gray-800',
                          'hover:border-purple-500/50 hover:bg-gray-800'
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-white">{service.name}</div>
                            {service.description && (
                              <div className="text-sm text-gray-400 mt-1">{service.description}</div>
                            )}
                            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                              <span className="flex items-center gap-1">
                                <Clock className="h-4 w-4" />
                                {service.duration_minutes} min
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-green-400">
                              ${service.price}
                              {service.is_price_variable && service.price_max && (
                                <span className="text-sm font-normal text-gray-400"> - ${service.price_max}</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step: Select Staff */}
        {step === 'staff' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Choose Your Stylist</h2>
              <Button variant="ghost" onClick={() => setStep('service')}>
                <ChevronLeft className="h-4 w-4" /> Back
              </Button>
            </div>

            {/* Selected service summary */}
            {selectedService && (
              <div className="mb-6 p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
                <div className="flex items-center gap-2 text-purple-400">
                  <Scissors className="h-4 w-4" />
                  <span className="font-medium">{selectedService.name}</span>
                  <span className="text-purple-300">({selectedService.duration_minutes} min, ${selectedService.price})</span>
                </div>
              </div>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              {/* Any Available option */}
              <button
                onClick={() => {
                  setSelectedStaff(staff[0]) // Select first available
                  setStep('datetime')
                }}
                className={cn(
                  'p-4 rounded-xl text-left transition-all',
                  'bg-gray-900 border border-gray-800',
                  'hover:border-purple-500/50 hover:bg-gray-800'
                )}
              >
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <User className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <div className="font-medium text-white">Any Available</div>
                    <div className="text-sm text-gray-400">First available stylist</div>
                  </div>
                </div>
              </button>

              {staff.map((member) => (
                <button
                  key={member.id}
                  onClick={() => {
                    setSelectedStaff(member)
                    setStep('datetime')
                  }}
                  className={cn(
                    'p-4 rounded-xl text-left transition-all',
                    'bg-gray-900 border border-gray-800',
                    'hover:border-purple-500/50 hover:bg-gray-800'
                  )}
                >
                  <div className="flex items-center gap-4">
                    {member.photo_url ? (
                      <img
                        src={member.photo_url}
                        alt={`${member.first_name} ${member.last_name}`}
                        className="w-14 h-14 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium text-lg">
                        {member.first_name[0]}{member.last_name[0]}
                      </div>
                    )}
                    <div>
                      <div className="font-medium text-white">{member.first_name} {member.last_name}</div>
                      {member.title && <div className="text-sm text-gray-400">{member.title}</div>}
                      {member.specialties.length > 0 && (
                        <div className="flex gap-1 mt-1">
                          {member.specialties.slice(0, 3).map((s) => (
                            <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400">
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step: Select Date & Time */}
        {step === 'datetime' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Select Date & Time</h2>
              <Button variant="ghost" onClick={() => setStep('staff')}>
                <ChevronLeft className="h-4 w-4" /> Back
              </Button>
            </div>

            {/* Selected summary */}
            <div className="mb-6 p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 space-y-2">
              {selectedService && (
                <div className="flex items-center gap-2 text-purple-400">
                  <Scissors className="h-4 w-4" />
                  <span>{selectedService.name}</span>
                </div>
              )}
              {selectedStaff && (
                <div className="flex items-center gap-2 text-purple-300">
                  <User className="h-4 w-4" />
                  <span>with {selectedStaff.first_name} {selectedStaff.last_name}</span>
                </div>
              )}
            </div>

            {/* Date selection */}
            <div className="space-y-6">
              {Object.entries(availabilityByDate).length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No available times found. Please try a different service or staff member.</p>
                </div>
              ) : (
                Object.entries(availabilityByDate).slice(0, 7).map(([date, slots]) => {
                  const dateObj = new Date(date)
                  const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' })
                  const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

                  return (
                    <div key={date}>
                      <h3 className="text-lg font-semibold text-white mb-3">
                        {dayName}, {dateStr}
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {slots.filter(s => s.available).map((slot) => (
                          <button
                            key={slot.time}
                            onClick={() => {
                              setSelectedDate(date)
                              setSelectedTime(slot.time)
                              setStep('details')
                            }}
                            className={cn(
                              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                              'bg-gray-800 text-white',
                              'hover:bg-purple-500 hover:text-white',
                              selectedDate === date && selectedTime === slot.time && 'bg-purple-500'
                            )}
                          >
                            {slot.time}
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        )}

        {/* Step: Enter Details */}
        {step === 'details' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Your Details</h2>
              <Button variant="ghost" onClick={() => setStep('datetime')}>
                <ChevronLeft className="h-4 w-4" /> Back
              </Button>
            </div>

            {/* Booking summary */}
            <div className="mb-6 p-4 rounded-xl bg-gray-900 border border-gray-800">
              <h3 className="text-lg font-semibold text-white mb-3">Booking Summary</h3>
              <div className="space-y-2 text-gray-300">
                <div className="flex items-center gap-2">
                  <Scissors className="h-4 w-4 text-purple-400" />
                  {selectedService?.name}
                </div>
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-purple-400" />
                  {selectedStaff?.first_name} {selectedStaff?.last_name}
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-purple-400" />
                  {selectedDate && new Date(selectedDate).toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric'
                  })}
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-purple-400" />
                  {selectedTime}
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-800 flex items-center justify-between">
                <span className="text-gray-400">Total</span>
                <span className="text-xl font-bold text-green-400">${selectedService?.price}</span>
              </div>
            </div>

            {/* Contact form */}
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSubmit()
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="First Name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  required
                />
                <Input
                  label="Last Name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  required
                />
              </div>
              <Input
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
              <Input
                label="Phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
              />
              <Input
                label="Notes (optional)"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Any special requests or notes for your stylist"
              />

              {/* Notification preferences */}
              <div className="space-y-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.email_reminders}
                    onChange={(e) => setFormData({ ...formData, email_reminders: e.target.checked })}
                    className="w-5 h-5 rounded bg-gray-800 border-gray-700 text-purple-500 focus:ring-purple-500"
                  />
                  <span className="text-gray-300">Send me email reminders</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.sms_reminders}
                    onChange={(e) => setFormData({ ...formData, sms_reminders: e.target.checked })}
                    className="w-5 h-5 rounded bg-gray-800 border-gray-700 text-purple-500 focus:ring-purple-500"
                  />
                  <span className="text-gray-300">Send me SMS reminders</span>
                </label>
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full mt-6"
                loading={submitting}
              >
                Confirm Booking
              </Button>
            </form>
          </div>
        )}

        {/* Step: Confirmation */}
        {step === 'confirmation' && bookingResult && (
          <div className="text-center py-8">
            <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-10 w-10 text-green-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Booking Confirmed!</h2>
            <p className="text-gray-400 mb-8">{bookingResult.message}</p>

            {/* Confirmation details */}
            <div className="max-w-md mx-auto bg-gray-900 rounded-xl border border-gray-800 p-6 text-left">
              <div className="text-center mb-4">
                <span className="text-xs text-gray-500">Confirmation Code</span>
                <div className="text-2xl font-mono font-bold text-purple-400">{bookingResult.confirmation_code}</div>
              </div>

              <div className="space-y-3 border-t border-gray-800 pt-4">
                <div className="flex items-center gap-3">
                  <Scissors className="h-5 w-5 text-purple-400" />
                  <div>
                    <div className="text-white">{bookingResult.service_name}</div>
                    <div className="text-sm text-gray-400">{bookingResult.duration_minutes} minutes</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <User className="h-5 w-5 text-purple-400" />
                  <div className="text-white">{bookingResult.staff_name}</div>
                </div>
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-purple-400" />
                  <div className="text-white">
                    {new Date(bookingResult.date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Clock className="h-5 w-5 text-purple-400" />
                  <div className="text-white">{bookingResult.time}</div>
                </div>
                <div className="flex items-center gap-3">
                  <MapPin className="h-5 w-5 text-purple-400" />
                  <div>
                    <div className="text-white">{bookingResult.salon_name}</div>
                    <div className="text-sm text-gray-400">{bookingResult.salon_address}</div>
                  </div>
                </div>
                {bookingResult.salon_phone && (
                  <div className="flex items-center gap-3">
                    <Phone className="h-5 w-5 text-purple-400" />
                    <div className="text-white">{bookingResult.salon_phone}</div>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-800 flex items-center justify-between">
                <span className="text-gray-400">Total</span>
                <span className="text-xl font-bold text-green-400">${bookingResult.total_price}</span>
              </div>
            </div>

            <p className="text-gray-500 text-sm mt-6">
              <Mail className="h-4 w-4 inline mr-1" />
              A confirmation email has been sent to your email address
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 border-t border-gray-800 mt-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 text-center">
          <p className="text-gray-500 text-sm">
            Powered by <span className="text-purple-400">SalonSync</span>
          </p>
        </div>
      </footer>
    </div>
  )
}
