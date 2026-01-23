/**
 * Analytics API client for SalonSync
 */

import { api } from './client'

export interface DashboardMetrics {
  today_appointments: number
  today_revenue: number
  week_revenue: number
  month_revenue: number
  new_clients_this_month: number
  total_active_clients: number
  upcoming_appointments: number
  cancelled_today: number
}

export interface RevenueData {
  date: string
  revenue: number
  transactions: number
}

export interface StaffPerformance {
  staff_id: number
  staff_name: string
  avatar_initials: string
  total_revenue: number
  appointment_count: number
  avg_ticket: number
  utilization_pct: number
  rating: number | null
  return_client_pct: number
}

export interface ServicePerformance {
  service_id: number
  service_name: string
  category: string | null
  revenue: number
  booking_count: number
  avg_price: number
  growth_pct: number
}

export interface ClientInsights {
  total_clients: number
  new_clients: number
  returning_clients: number
  retention_rate: number
  avg_visits_per_client: number
  top_clients: Array<{
    id: number
    name: string
    visits: number
    total_spent: number
  }>
  churn_risk: number
}

export interface HourlyPattern {
  hour: number
  appointment_count: number
  revenue: number
}

export interface DayPattern {
  day: number
  day_name: string
  appointment_count: number
  revenue: number
}

export interface StatusBreakdown {
  status: string
  count: number
}

export interface RevenueComparison {
  current_period: {
    revenue: number
    transactions: number
    avg_ticket: number
  }
  previous_period: {
    revenue: number
    transactions: number
    avg_ticket: number
  }
  changes: {
    revenue_pct: number
    transactions_pct: number
  }
}

export const analyticsApi = {
  // Dashboard metrics
  getMetrics: async (): Promise<DashboardMetrics> => {
    const { data } = await api.get('/api/dashboard/metrics')
    return data
  },

  // Revenue data
  getDailyRevenue: async (days: number = 30): Promise<RevenueData[]> => {
    const { data } = await api.get(`/api/dashboard/revenue/daily?days=${days}`)
    return data
  },

  // Staff performance
  getStaffPerformance: async (days: number = 30): Promise<StaffPerformance[]> => {
    const { data } = await api.get(`/api/dashboard/analytics/staff-performance?days=${days}`)
    return data
  },

  // Service performance
  getServicePerformance: async (days: number = 30): Promise<ServicePerformance[]> => {
    const { data } = await api.get(`/api/dashboard/analytics/service-performance?days=${days}`)
    return data
  },

  // Client insights
  getClientInsights: async (days: number = 30): Promise<ClientInsights> => {
    const { data } = await api.get(`/api/dashboard/analytics/client-insights?days=${days}`)
    return data
  },

  // Hourly patterns
  getHourlyPatterns: async (days: number = 30): Promise<HourlyPattern[]> => {
    const { data } = await api.get(`/api/dashboard/analytics/hourly-patterns?days=${days}`)
    return data
  },

  // Daily patterns
  getDailyPatterns: async (days: number = 30): Promise<DayPattern[]> => {
    const { data } = await api.get(`/api/dashboard/analytics/daily-patterns?days=${days}`)
    return data
  },

  // Status breakdown
  getStatusBreakdown: async (days: number = 30): Promise<StatusBreakdown[]> => {
    const { data } = await api.get(`/api/dashboard/analytics/appointments/by-status?days=${days}`)
    return data
  },

  // Revenue comparison
  getRevenueComparison: async (days: number = 30): Promise<RevenueComparison> => {
    const { data } = await api.get(`/api/dashboard/analytics/revenue-comparison?days=${days}`)
    return data
  },
}
