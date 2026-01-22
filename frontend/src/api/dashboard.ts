import api from './client'

export interface DashboardMetrics {
  today_appointments: number
  week_revenue: number
  month_new_clients: number
  today_services: number
  products_sold: number
  staff_utilization: number
  trends: {
    appointments: number
    revenue: number
    clients: number
  }
}

export interface Appointment {
  id: number
  client_name: string
  service_name: string
  staff_name: string
  start_time: string
  end_time: string
  status: 'scheduled' | 'confirmed' | 'checked_in' | 'in_progress' | 'completed' | 'no_show' | 'cancelled'
  duration_mins: number
}

export interface AttentionItem {
  id: string
  type: 'warning' | 'info' | 'alert'
  title: string
  description: string
  action_url: string
}

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  const response = await api.get('/dashboard/metrics')
  return response.data
}

export async function getUpcomingAppointments(limit: number = 5): Promise<Appointment[]> {
  const response = await api.get('/dashboard/upcoming-appointments', { params: { limit } })
  return response.data
}

export async function getNeedsAttention(): Promise<AttentionItem[]> {
  const response = await api.get('/dashboard/needs-attention')
  return response.data
}
