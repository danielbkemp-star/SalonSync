/**
 * Public Booking API - No authentication required
 */
import axios from 'axios'

// Create a separate axios instance for public endpoints (no auth interceptor)
const publicApi = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface PublicSalonInfo {
  id: number
  name: string
  slug: string
  address_line1: string | null
  city: string | null
  state: string | null
  zip_code: string | null
  phone: string | null
  email: string | null
  logo_url: string | null
  booking_lead_time_hours: number
  booking_window_days: number
  cancellation_policy_hours: number
}

export interface PublicServiceInfo {
  id: number
  name: string
  description: string | null
  category: string
  duration_minutes: number
  price: number
  price_max: number | null
  is_price_variable: boolean
}

export interface PublicStaffInfo {
  id: number
  first_name: string
  last_name: string
  title: string | null
  bio: string | null
  photo_url: string | null
  specialties: string[]
}

export interface TimeSlot {
  time: string
  datetime: string
  available: boolean
}

export interface AvailabilityResponse {
  date: string
  staff_id: number
  staff_name: string
  slots: TimeSlot[]
}

export interface BookingRequest {
  first_name: string
  last_name: string
  email: string
  phone: string
  service_id: number
  staff_id: number
  date: string
  time: string
  notes?: string
  sms_reminders: boolean
  email_reminders: boolean
}

export interface BookingResponse {
  appointment_id: number
  confirmation_code: string
  service_name: string
  staff_name: string
  date: string
  time: string
  duration_minutes: number
  total_price: number
  salon_name: string
  salon_address: string
  salon_phone: string
  message: string
}

export interface BookingLookupResponse {
  appointment_id: number
  status: string
  service_name: string
  staff_name: string
  date: string
  time: string
  duration_minutes: number
  salon_name: string
  salon_address: string
  can_cancel: boolean
  can_reschedule: boolean
}

// API Functions

export async function getSalonForBooking(salonSlug: string): Promise<PublicSalonInfo> {
  const response = await publicApi.get(`/book/${salonSlug}`)
  return response.data
}

export async function getBookableServices(salonSlug: string, category?: string): Promise<PublicServiceInfo[]> {
  const params = category ? { category } : {}
  const response = await publicApi.get(`/book/${salonSlug}/services`, { params })
  return response.data
}

export async function getBookableStaff(salonSlug: string, serviceId?: number): Promise<PublicStaffInfo[]> {
  const params = serviceId ? { service_id: serviceId } : {}
  const response = await publicApi.get(`/book/${salonSlug}/staff`, { params })
  return response.data
}

export async function getAvailability(
  salonSlug: string,
  serviceId: number,
  staffId?: number,
  startDate?: string,
  days?: number
): Promise<AvailabilityResponse[]> {
  const params: Record<string, unknown> = { service_id: serviceId }
  if (staffId) params.staff_id = staffId
  if (startDate) params.start_date = startDate
  if (days) params.days = days

  const response = await publicApi.get(`/book/${salonSlug}/availability`, { params })
  return response.data
}

export async function createBooking(salonSlug: string, booking: BookingRequest): Promise<BookingResponse> {
  const response = await publicApi.post(`/book/${salonSlug}`, booking)
  return response.data
}

export async function lookupBooking(
  salonSlug: string,
  email: string,
  confirmationCode: string
): Promise<BookingLookupResponse> {
  const response = await publicApi.get(`/book/${salonSlug}/lookup`, {
    params: { email, confirmation_code: confirmationCode }
  })
  return response.data
}

export async function cancelBooking(
  salonSlug: string,
  email: string,
  confirmationCode: string
): Promise<{ message: string }> {
  const response = await publicApi.post(`/book/${salonSlug}/cancel`, null, {
    params: { email, confirmation_code: confirmationCode }
  })
  return response.data
}
