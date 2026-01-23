import { useState } from 'react'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { Button, Input, Badge, Modal, DataTable } from '@/components/ui'
import {
  Plus,
  Clock,
  Bell,
  CheckCircle,
  Calendar,
  User,
  Phone,
  Mail,
  Filter,
  RefreshCw,
  Send,
  Trash2,
} from 'lucide-react'
import type { Column } from '@/components/ui/DataTable'
import { cn } from '@/lib/utils'

interface WaitlistEntry {
  id: number
  client_name: string
  client_email: string | null
  client_phone: string | null
  service_name: string | null
  staff_name: string | null
  preferred_date: string
  preferred_time_start: string | null
  preferred_time_end: string | null
  flexible_dates: boolean
  flexible_staff: boolean
  status: 'pending' | 'notified' | 'booked' | 'expired' | 'cancelled'
  priority: 'low' | 'normal' | 'high' | 'vip'
  notes: string | null
  notification_count: number
  last_notified_at: string | null
  created_at: string
  is_active: boolean
}

// Mock data
const mockWaitlist: WaitlistEntry[] = [
  {
    id: 1,
    client_name: 'Sarah Johnson',
    client_email: 'sarah@email.com',
    client_phone: '(555) 123-4567',
    service_name: 'Balayage',
    staff_name: 'Jessica Martinez',
    preferred_date: '2024-02-15',
    preferred_time_start: '10:00',
    preferred_time_end: '14:00',
    flexible_dates: true,
    flexible_staff: false,
    status: 'pending',
    priority: 'high',
    notes: 'Prefers morning appointments',
    notification_count: 0,
    last_notified_at: null,
    created_at: '2024-01-20T10:30:00Z',
    is_active: true,
  },
  {
    id: 2,
    client_name: 'Emily Davis',
    client_email: 'emily@email.com',
    client_phone: '(555) 234-5678',
    service_name: 'Full Highlights',
    staff_name: null,
    preferred_date: '2024-02-14',
    preferred_time_start: null,
    preferred_time_end: null,
    flexible_dates: true,
    flexible_staff: true,
    status: 'notified',
    priority: 'normal',
    notes: null,
    notification_count: 1,
    last_notified_at: '2024-01-22T14:00:00Z',
    created_at: '2024-01-18T09:15:00Z',
    is_active: true,
  },
  {
    id: 3,
    client_name: 'Lisa Chen',
    client_email: 'lisa@email.com',
    client_phone: null,
    service_name: 'Haircut & Color',
    staff_name: 'Maria Garcia',
    preferred_date: '2024-02-10',
    preferred_time_start: '15:00',
    preferred_time_end: '18:00',
    flexible_dates: false,
    flexible_staff: true,
    status: 'booked',
    priority: 'vip',
    notes: 'VIP client - always prioritize',
    notification_count: 1,
    last_notified_at: '2024-01-21T11:00:00Z',
    created_at: '2024-01-15T16:45:00Z',
    is_active: false,
  },
]

export function WaitlistPage() {
  const [waitlist, setWaitlist] = useState<WaitlistEntry[]>(mockWaitlist)
  const [search, setSearch] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [showNotifyModal, setShowNotifyModal] = useState(false)
  const [selectedEntry, setSelectedEntry] = useState<WaitlistEntry | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('active')
  const [loading, setLoading] = useState(false)

  // Form state
  const [newEntry, setNewEntry] = useState({
    client_name: '',
    client_email: '',
    client_phone: '',
    service_id: '',
    staff_id: '',
    preferred_date: '',
    preferred_time_start: '',
    preferred_time_end: '',
    flexible_dates: false,
    flexible_staff: true,
    notes: '',
    priority: 'normal',
  })

  const [notifyMessage, setNotifyMessage] = useState('')

  const filteredWaitlist = waitlist.filter((entry) => {
    const matchesSearch =
      entry.client_name.toLowerCase().includes(search.toLowerCase()) ||
      entry.client_email?.toLowerCase().includes(search.toLowerCase()) ||
      entry.service_name?.toLowerCase().includes(search.toLowerCase())

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && entry.is_active) ||
      statusFilter === entry.status

    return matchesSearch && matchesStatus
  })

  const statusVariant = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'pending':
        return 'warning'
      case 'notified':
        return 'default'
      case 'booked':
        return 'success'
      case 'expired':
      case 'cancelled':
        return 'error'
      default:
        return 'default'
    }
  }

  const handleNotify = async () => {
    if (!selectedEntry) return
    setLoading(true)
    // Simulate API call
    await new Promise((r) => setTimeout(r, 1000))
    setWaitlist((prev) =>
      prev.map((e) =>
        e.id === selectedEntry.id
          ? {
              ...e,
              status: 'notified' as const,
              notification_count: e.notification_count + 1,
              last_notified_at: new Date().toISOString(),
            }
          : e
      )
    )
    setLoading(false)
    setShowNotifyModal(false)
    setSelectedEntry(null)
    setNotifyMessage('')
  }

  const handleRemove = (entry: WaitlistEntry) => {
    setWaitlist((prev) =>
      prev.map((e) =>
        e.id === entry.id ? { ...e, status: 'cancelled' as const, is_active: false } : e
      )
    )
  }

  const handleAddEntry = () => {
    const entry: WaitlistEntry = {
      id: Date.now(),
      client_name: newEntry.client_name,
      client_email: newEntry.client_email || null,
      client_phone: newEntry.client_phone || null,
      service_name: 'Selected Service',
      staff_name: newEntry.staff_id ? 'Selected Staff' : null,
      preferred_date: newEntry.preferred_date,
      preferred_time_start: newEntry.preferred_time_start || null,
      preferred_time_end: newEntry.preferred_time_end || null,
      flexible_dates: newEntry.flexible_dates,
      flexible_staff: newEntry.flexible_staff,
      status: 'pending',
      priority: newEntry.priority as 'low' | 'normal' | 'high' | 'vip',
      notes: newEntry.notes || null,
      notification_count: 0,
      last_notified_at: null,
      created_at: new Date().toISOString(),
      is_active: true,
    }
    setWaitlist((prev) => [entry, ...prev])
    setShowAddModal(false)
    setNewEntry({
      client_name: '',
      client_email: '',
      client_phone: '',
      service_id: '',
      staff_id: '',
      preferred_date: '',
      preferred_time_start: '',
      preferred_time_end: '',
      flexible_dates: false,
      flexible_staff: true,
      notes: '',
      priority: 'normal',
    })
  }

  const columns: Column<WaitlistEntry>[] = [
    {
      key: 'client',
      header: 'Client',
      render: (entry) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium">
            {entry.client_name
              .split(' ')
              .map((n) => n[0])
              .join('')}
          </div>
          <div>
            <div className="text-white font-medium flex items-center gap-2">
              {entry.client_name}
              {entry.priority === 'vip' && (
                <Badge variant="success" size="sm">VIP</Badge>
              )}
              {entry.priority === 'high' && (
                <Badge variant="warning" size="sm">High</Badge>
              )}
            </div>
            <div className="text-xs text-gray-500 flex items-center gap-2">
              {entry.client_email && (
                <span className="flex items-center gap-1">
                  <Mail className="h-3 w-3" />
                  {entry.client_email}
                </span>
              )}
              {entry.client_phone && (
                <span className="flex items-center gap-1">
                  <Phone className="h-3 w-3" />
                  {entry.client_phone}
                </span>
              )}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'service',
      header: 'Service',
      render: (entry) => (
        <div>
          <div className="text-white">{entry.service_name || 'Any service'}</div>
          {entry.staff_name && (
            <div className="text-xs text-gray-500">with {entry.staff_name}</div>
          )}
          {entry.flexible_staff && !entry.staff_name && (
            <div className="text-xs text-gray-500">Any available staff</div>
          )}
        </div>
      ),
    },
    {
      key: 'preferred_date',
      header: 'Preferred Date',
      render: (entry) => (
        <div>
          <div className="text-white flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-500" />
            {new Date(entry.preferred_date).toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            })}
          </div>
          {entry.preferred_time_start && (
            <div className="text-xs text-gray-500 flex items-center gap-1 mt-1">
              <Clock className="h-3 w-3" />
              {entry.preferred_time_start}
              {entry.preferred_time_end && ` - ${entry.preferred_time_end}`}
            </div>
          )}
          <div className="flex gap-1 mt-1">
            {entry.flexible_dates && (
              <span className="text-xs text-purple-400">Flexible dates</span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (entry) => (
        <div className="space-y-1">
          <Badge variant={statusVariant(entry.status)} dot>
            {entry.status.charAt(0).toUpperCase() + entry.status.slice(1)}
          </Badge>
          {entry.notification_count > 0 && (
            <div className="text-xs text-gray-500">
              Notified {entry.notification_count}x
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'created_at',
      header: 'Added',
      render: (entry) => (
        <div className="text-gray-400 text-sm">
          {new Date(entry.created_at).toLocaleDateString()}
        </div>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (entry) => (
        <div className="flex items-center gap-2">
          {entry.is_active && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedEntry(entry)
                  setShowNotifyModal(true)
                }}
                title="Notify client"
              >
                <Send className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  handleRemove(entry)
                }}
                title="Remove from waitlist"
              >
                <Trash2 className="h-4 w-4 text-red-400" />
              </Button>
            </>
          )}
        </div>
      ),
    },
  ]

  // Stats
  const stats = {
    pending: waitlist.filter((e) => e.status === 'pending').length,
    notified: waitlist.filter((e) => e.status === 'notified').length,
    booked: waitlist.filter((e) => e.status === 'booked').length,
    total: waitlist.filter((e) => e.is_active).length,
  }

  return (
    <SalonBackground className="h-full">
      <div className="h-full p-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Waitlist</h1>
            <p className="text-gray-400">Manage clients waiting for appointments</p>
          </div>
          <Button variant="primary" onClick={() => setShowAddModal(true)}>
            <Plus className="h-4 w-4" />
            Add to Waitlist
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard
            icon={<Clock className="h-5 w-5 text-yellow-400" />}
            label="Pending"
            value={stats.pending}
            color="yellow"
          />
          <StatCard
            icon={<Bell className="h-5 w-5 text-blue-400" />}
            label="Notified"
            value={stats.notified}
            color="blue"
          />
          <StatCard
            icon={<CheckCircle className="h-5 w-5 text-green-400" />}
            label="Booked"
            value={stats.booked}
            color="green"
          />
          <StatCard
            icon={<User className="h-5 w-5 text-purple-400" />}
            label="Active"
            value={stats.total}
            color="purple"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-4">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="active">Active entries</option>
            <option value="pending">Pending only</option>
            <option value="notified">Notified only</option>
            <option value="booked">Booked</option>
            <option value="all">All entries</option>
          </select>
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredWaitlist}
          keyExtractor={(entry) => entry.id}
          searchable
          searchValue={search}
          onSearchChange={setSearch}
          searchPlaceholder="Search by name, email, or service..."
          emptyMessage="No waitlist entries found"
        />

        {/* Add Entry Modal */}
        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Add to Waitlist"
          description="Add a client to the appointment waitlist"
          size="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleAddEntry()
            }}
            className="space-y-4"
          >
            <Input
              label="Client Name"
              value={newEntry.client_name}
              onChange={(e) => setNewEntry({ ...newEntry, client_name: e.target.value })}
              placeholder="Enter client name"
              required
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Email"
                type="email"
                value={newEntry.client_email}
                onChange={(e) => setNewEntry({ ...newEntry, client_email: e.target.value })}
                placeholder="client@email.com"
              />
              <Input
                label="Phone"
                type="tel"
                value={newEntry.client_phone}
                onChange={(e) => setNewEntry({ ...newEntry, client_phone: e.target.value })}
                placeholder="(555) 123-4567"
              />
            </div>

            <Input
              label="Preferred Date"
              type="date"
              value={newEntry.preferred_date}
              onChange={(e) => setNewEntry({ ...newEntry, preferred_date: e.target.value })}
              required
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Earliest Time"
                type="time"
                value={newEntry.preferred_time_start}
                onChange={(e) =>
                  setNewEntry({ ...newEntry, preferred_time_start: e.target.value })
                }
              />
              <Input
                label="Latest Time"
                type="time"
                value={newEntry.preferred_time_end}
                onChange={(e) =>
                  setNewEntry({ ...newEntry, preferred_time_end: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newEntry.flexible_dates}
                  onChange={(e) =>
                    setNewEntry({ ...newEntry, flexible_dates: e.target.checked })
                  }
                  className="w-5 h-5 rounded bg-gray-800 border-gray-700 text-purple-500 focus:ring-purple-500"
                />
                <span className="text-gray-300">Flexible on dates (nearby days OK)</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newEntry.flexible_staff}
                  onChange={(e) =>
                    setNewEntry({ ...newEntry, flexible_staff: e.target.checked })
                  }
                  className="w-5 h-5 rounded bg-gray-800 border-gray-700 text-purple-500 focus:ring-purple-500"
                />
                <span className="text-gray-300">Any available staff</span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Priority</label>
              <select
                value={newEntry.priority}
                onChange={(e) => setNewEntry({ ...newEntry, priority: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="vip">VIP</option>
              </select>
            </div>

            <Input
              label="Notes (optional)"
              value={newEntry.notes}
              onChange={(e) => setNewEntry({ ...newEntry, notes: e.target.value })}
              placeholder="Any special requests or notes"
            />

            <div className="flex gap-3 justify-end pt-4">
              <Button variant="ghost" onClick={() => setShowAddModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Add to Waitlist
              </Button>
            </div>
          </form>
        </Modal>

        {/* Notify Modal */}
        <Modal
          isOpen={showNotifyModal}
          onClose={() => {
            setShowNotifyModal(false)
            setSelectedEntry(null)
            setNotifyMessage('')
          }}
          title="Notify Client"
          description={`Send availability notification to ${selectedEntry?.client_name}`}
          size="sm"
        >
          <div className="space-y-4">
            {selectedEntry && (
              <div className="p-3 rounded-lg bg-gray-800 space-y-2">
                <div className="text-white font-medium">{selectedEntry.client_name}</div>
                <div className="text-sm text-gray-400">
                  Waiting for: {selectedEntry.service_name}
                </div>
                <div className="text-sm text-gray-400">
                  Preferred: {new Date(selectedEntry.preferred_date).toLocaleDateString()}
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Custom Message (optional)
              </label>
              <textarea
                value={notifyMessage}
                onChange={(e) => setNotifyMessage(e.target.value)}
                placeholder="An appointment slot has opened up! Contact us to book..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 h-24 resize-none"
              />
            </div>

            <div className="flex gap-3 justify-end pt-4">
              <Button
                variant="ghost"
                onClick={() => {
                  setShowNotifyModal(false)
                  setSelectedEntry(null)
                }}
              >
                Cancel
              </Button>
              <Button variant="primary" onClick={handleNotify} disabled={loading}>
                {loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                Send Notification
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </SalonBackground>
  )
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode
  label: string
  value: number
  color: 'yellow' | 'blue' | 'green' | 'purple'
}) {
  const bgColors = {
    yellow: 'bg-yellow-500/10',
    blue: 'bg-blue-500/10',
    green: 'bg-green-500/10',
    purple: 'bg-purple-500/10',
  }

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className={cn('p-2 rounded-lg', bgColors[color])}>{icon}</div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  )
}
