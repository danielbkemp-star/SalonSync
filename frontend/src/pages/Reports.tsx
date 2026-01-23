import { useState, useEffect } from 'react'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { Button, Badge } from '@/components/ui'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Calendar,
  Clock,
  Download,
  ChevronDown,
  AlertCircle,
  RefreshCw,
  BarChart3,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { analyticsApi } from '@/api/analytics'
import type {
  RevenueData,
  StaffPerformance,
  ServicePerformance,
  ClientInsights,
  DayPattern,
  RevenueComparison,
} from '@/api/analytics'

type TimeRange = '7d' | '30d' | '90d' | '1y'

const timeRangeToDays: Record<TimeRange, number> = {
  '7d': 7,
  '30d': 30,
  '90d': 90,
  '1y': 365,
}

const CHART_COLORS = ['#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']

export function ReportsPage() {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [revenueData, setRevenueData] = useState<RevenueData[]>([])
  const [staffPerformance, setStaffPerformance] = useState<StaffPerformance[]>([])
  const [servicePerformance, setServicePerformance] = useState<ServicePerformance[]>([])
  const [clientInsights, setClientInsights] = useState<ClientInsights | null>(null)
  const [dailyPatterns, setDailyPatterns] = useState<DayPattern[]>([])
  const [comparison, setComparison] = useState<RevenueComparison | null>(null)

  const days = timeRangeToDays[timeRange]

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      const [revenue, staff, services, clients, patterns, comp] = await Promise.all([
        analyticsApi.getDailyRevenue(days),
        analyticsApi.getStaffPerformance(days),
        analyticsApi.getServicePerformance(days),
        analyticsApi.getClientInsights(days),
        analyticsApi.getDailyPatterns(days),
        analyticsApi.getRevenueComparison(days),
      ])

      setRevenueData(revenue)
      setStaffPerformance(staff)
      setServicePerformance(services)
      setClientInsights(clients)
      setDailyPatterns(patterns)
      setComparison(comp)
    } catch (err) {
      console.error('Failed to fetch analytics:', err)
      setError('Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [timeRange])

  // Calculate totals for cards
  const totalRevenue = revenueData.reduce((sum, d) => sum + d.revenue, 0)
  const totalTransactions = revenueData.reduce((sum, d) => sum + d.transactions, 0)
  const avgTicket = totalTransactions > 0 ? totalRevenue / totalTransactions : 0

  if (error) {
    return (
      <SalonBackground className="h-full">
        <div className="h-full p-6 flex items-center justify-center">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl text-white mb-2">Failed to Load Analytics</h2>
            <p className="text-gray-400 mb-4">{error}</p>
            <Button variant="primary" onClick={fetchData}>
              <RefreshCw className="h-4 w-4" />
              Try Again
            </Button>
          </div>
        </div>
      </SalonBackground>
    )
  }

  return (
    <SalonBackground className="h-full">
      <div className="h-full p-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Analytics & Reports</h1>
            <p className="text-gray-400">Track your salon performance</p>
          </div>
          <div className="flex items-center gap-3">
            <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
            <Button variant="secondary" onClick={fetchData} disabled={loading}>
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="secondary">
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-purple-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Loading analytics...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <MetricCard
                label="Total Revenue"
                value={`$${totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                change={comparison?.changes.revenue_pct || 0}
                isPositive={(comparison?.changes.revenue_pct || 0) >= 0}
                icon={DollarSign}
              />
              <MetricCard
                label="Transactions"
                value={totalTransactions}
                change={comparison?.changes.transactions_pct || 0}
                isPositive={(comparison?.changes.transactions_pct || 0) >= 0}
                icon={Calendar}
              />
              <MetricCard
                label="New Clients"
                value={clientInsights?.new_clients || 0}
                change={0}
                isPositive={true}
                icon={Users}
                hideChange
              />
              <MetricCard
                label="Avg Ticket"
                value={`$${avgTicket.toFixed(2)}`}
                change={0}
                isPositive={true}
                icon={Clock}
                hideChange
              />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-2 gap-6 mb-6">
              {/* Revenue Chart */}
              <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Revenue Over Time</h3>
                  <BarChart3 className="h-5 w-5 text-gray-500" />
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={revenueData}>
                      <defs>
                        <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="date"
                        stroke="#9ca3af"
                        fontSize={12}
                        tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      />
                      <YAxis
                        stroke="#9ca3af"
                        fontSize={12}
                        tickFormatter={(v) => `$${v}`}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                        labelFormatter={(v) => new Date(v).toLocaleDateString()}
                        formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Revenue']}
                      />
                      <Area
                        type="monotone"
                        dataKey="revenue"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        fill="url(#revenueGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Appointments by Day */}
              <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Appointments by Day</h3>
                  <Calendar className="h-5 w-5 text-gray-500" />
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dailyPatterns}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="day_name"
                        stroke="#9ca3af"
                        fontSize={12}
                        tickFormatter={(v) => v.slice(0, 3)}
                      />
                      <YAxis stroke="#9ca3af" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                        formatter={(value, name) => [
                          name === 'appointment_count' ? value : `$${Number(value).toFixed(2)}`,
                          name === 'appointment_count' ? 'Appointments' : 'Revenue'
                        ]}
                      />
                      <Bar dataKey="appointment_count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Client Insights Row */}
            {clientInsights && (
              <div className="grid grid-cols-3 gap-6 mb-6">
                {/* Client Stats */}
                <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Client Overview</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Total Clients</span>
                      <span className="text-white font-semibold">{clientInsights.total_clients}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">New Clients</span>
                      <span className="text-green-400 font-semibold flex items-center gap-1">
                        <ArrowUpRight className="h-4 w-4" />
                        {clientInsights.new_clients}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Returning</span>
                      <span className="text-white font-semibold">{clientInsights.returning_clients}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Retention Rate</span>
                      <Badge variant={clientInsights.retention_rate >= 70 ? 'success' : 'warning'}>
                        {clientInsights.retention_rate}%
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Avg Visits</span>
                      <span className="text-white font-semibold">{clientInsights.avg_visits_per_client.toFixed(1)}</span>
                    </div>
                    {clientInsights.churn_risk > 0 && (
                      <div className="flex items-center justify-between pt-2 border-t border-gray-800">
                        <span className="text-amber-400">Churn Risk</span>
                        <Badge variant="warning">{clientInsights.churn_risk} clients</Badge>
                      </div>
                    )}
                  </div>
                </div>

                {/* Top Clients */}
                <div className="rounded-xl bg-gray-900 border border-gray-800 p-6 col-span-2">
                  <h3 className="text-lg font-semibold text-white mb-4">Top Clients</h3>
                  <div className="space-y-3">
                    {clientInsights.top_clients.length > 0 ? (
                      clientInsights.top_clients.map((client, index) => (
                        <div
                          key={client.id}
                          className="flex items-center justify-between p-3 rounded-lg bg-gray-800"
                        >
                          <div className="flex items-center gap-3">
                            <span className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-sm font-medium">
                              {index + 1}
                            </span>
                            <div>
                              <div className="text-white font-medium">{client.name}</div>
                              <div className="text-gray-500 text-sm">{client.visits} visits</div>
                            </div>
                          </div>
                          <div className="text-green-400 font-medium">
                            ${client.total_spent.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center text-gray-500 py-8">
                        No client data available for this period
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tables Row */}
            <div className="grid grid-cols-2 gap-6">
              {/* Top Services */}
              <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Top Services</h3>
                  <PieChart className="h-5 w-5 text-gray-500" />
                </div>
                {servicePerformance.length > 0 ? (
                  <div className="space-y-3">
                    {servicePerformance.slice(0, 5).map((service, index) => (
                      <div
                        key={service.service_id}
                        className="flex items-center justify-between p-3 rounded-lg bg-gray-800"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className="w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium"
                            style={{
                              backgroundColor: `${CHART_COLORS[index % CHART_COLORS.length]}20`,
                              color: CHART_COLORS[index % CHART_COLORS.length],
                            }}
                          >
                            {index + 1}
                          </span>
                          <div>
                            <div className="text-white font-medium">{service.service_name}</div>
                            <div className="text-gray-500 text-sm">{service.booking_count} bookings</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-green-400 font-medium">
                            ${service.revenue.toLocaleString()}
                          </div>
                          <div className={`text-xs flex items-center gap-1 justify-end ${service.growth_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {service.growth_pct >= 0 ? (
                              <ArrowUpRight className="h-3 w-3" />
                            ) : (
                              <ArrowDownRight className="h-3 w-3" />
                            )}
                            {Math.abs(service.growth_pct)}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    No service data available
                  </div>
                )}
              </div>

              {/* Top Stylists */}
              <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Top Performers</h3>
                  <Users className="h-5 w-5 text-gray-500" />
                </div>
                {staffPerformance.length > 0 ? (
                  <div className="space-y-3">
                    {staffPerformance.slice(0, 5).map((staff) => (
                      <div
                        key={staff.staff_id}
                        className="flex items-center justify-between p-3 rounded-lg bg-gray-800"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium">
                            {staff.avatar_initials}
                          </div>
                          <div>
                            <div className="text-white font-medium">{staff.staff_name}</div>
                            <div className="text-gray-500 text-sm">
                              {staff.appointment_count} appts • {staff.utilization_pct}% util
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-green-400 font-medium">
                            ${staff.total_revenue.toLocaleString()}
                          </div>
                          {staff.rating && (
                            <div className="text-yellow-400 text-sm flex items-center gap-1 justify-end">
                              <span>★</span>
                              {staff.rating.toFixed(1)}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    No staff data available
                  </div>
                )}
              </div>
            </div>

            {/* Service Distribution Pie Chart */}
            {servicePerformance.length > 0 && (
              <div className="mt-6 rounded-xl bg-gray-900 border border-gray-800 p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Revenue by Service</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie
                        data={servicePerformance.slice(0, 6)}
                        dataKey="revenue"
                        nameKey="service_name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                        labelLine={false}
                      >
                        {servicePerformance.slice(0, 6).map((_, index) => (
                          <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                        formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Revenue']}
                      />
                      <Legend
                        wrapperStyle={{ color: '#9ca3af' }}
                        formatter={(value) => <span className="text-gray-300">{value}</span>}
                      />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </SalonBackground>
  )
}

function TimeRangeSelector({ value, onChange }: { value: TimeRange; onChange: (v: TimeRange) => void }) {
  const options: { value: TimeRange; label: string }[] = [
    { value: '7d', label: 'Last 7 days' },
    { value: '30d', label: 'Last 30 days' },
    { value: '90d', label: 'Last 90 days' },
    { value: '1y', label: 'Last year' },
  ]

  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as TimeRange)}
        className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pr-10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
    </div>
  )
}

function MetricCard({
  label,
  value,
  change,
  isPositive,
  icon: Icon,
  hideChange = false,
}: {
  label: string
  value: string | number
  change: number
  isPositive: boolean
  icon: React.ElementType
  hideChange?: boolean
}) {
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="p-2 rounded-lg bg-purple-500/20">
          <Icon className="h-5 w-5 text-purple-400" />
        </div>
        {!hideChange && change !== 0 && (
          <Badge variant={isPositive ? 'success' : 'error'} size="sm">
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            <span className="ml-1">{Math.abs(change)}%</span>
          </Badge>
        )}
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  )
}
