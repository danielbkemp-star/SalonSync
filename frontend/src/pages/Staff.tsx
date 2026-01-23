import { useState } from 'react'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { DataTable, Button, Badge, Modal, Input, Select } from '@/components/ui'
import { Plus, Mail, Phone, Calendar, Star } from 'lucide-react'
import type { Column } from '@/components/ui/DataTable'

interface StaffMember {
  id: number
  name: string
  email: string
  phone: string
  title: string
  status: 'active' | 'inactive' | 'on_leave'
  rating: number
  appointmentsToday: number
  specialties: string[]
}

const mockStaff: StaffMember[] = [
  { id: 1, name: 'Jessica Martinez', email: 'jessica@salon.com', phone: '(555) 111-2222', title: 'Senior Stylist', status: 'active', rating: 4.9, appointmentsToday: 6, specialties: ['Color', 'Cuts', 'Balayage'] },
  { id: 2, name: 'Maria Garcia', email: 'maria@salon.com', phone: '(555) 222-3333', title: 'Color Specialist', status: 'active', rating: 4.8, appointmentsToday: 4, specialties: ['Color', 'Highlights', 'Ombre'] },
  { id: 3, name: 'Amy Thompson', email: 'amy@salon.com', phone: '(555) 333-4444', title: 'Nail Technician', status: 'active', rating: 4.7, appointmentsToday: 8, specialties: ['Manicure', 'Pedicure', 'Nail Art'] },
  { id: 4, name: 'David Chen', email: 'david@salon.com', phone: '(555) 444-5555', title: 'Junior Stylist', status: 'on_leave', rating: 4.5, appointmentsToday: 0, specialties: ['Cuts', 'Blowouts'] },
]

export function StaffPage() {
  const [search, setSearch] = useState('')
  const [showNewStaffModal, setShowNewStaffModal] = useState(false)
  const [staff] = useState<StaffMember[]>(mockStaff)

  const filteredStaff = staff.filter(
    (member) =>
      member.name.toLowerCase().includes(search.toLowerCase()) ||
      member.email.toLowerCase().includes(search.toLowerCase()) ||
      member.title.toLowerCase().includes(search.toLowerCase())
  )

  const columns: Column<StaffMember>[] = [
    {
      key: 'name',
      header: 'Staff Member',
      sortable: true,
      render: (member) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium">
            {member.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div>
            <div className="font-medium text-white">{member.name}</div>
            <div className="text-xs text-gray-500">{member.title}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'contact',
      header: 'Contact',
      render: (member) => (
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-gray-300 text-sm">
            <Mail className="h-3 w-3 text-gray-500" />
            {member.email}
          </div>
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <Phone className="h-3 w-3 text-gray-500" />
            {member.phone}
          </div>
        </div>
      ),
    },
    {
      key: 'rating',
      header: 'Rating',
      sortable: true,
      render: (member) => (
        <div className="flex items-center gap-1">
          <Star className="h-4 w-4 text-yellow-400 fill-yellow-400" />
          <span className="text-white font-medium">{member.rating}</span>
        </div>
      ),
    },
    {
      key: 'appointmentsToday',
      header: 'Today',
      sortable: true,
      render: (member) => (
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-gray-500" />
          <span className="text-white">{member.appointmentsToday} appointments</span>
        </div>
      ),
    },
    {
      key: 'specialties',
      header: 'Specialties',
      render: (member) => (
        <div className="flex items-center gap-1 flex-wrap">
          {member.specialties.slice(0, 2).map((specialty) => (
            <Badge key={specialty} variant="purple" size="sm">
              {specialty}
            </Badge>
          ))}
          {member.specialties.length > 2 && (
            <Badge variant="default" size="sm">+{member.specialties.length - 2}</Badge>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (member) => (
        <Badge
          variant={member.status === 'active' ? 'success' : member.status === 'on_leave' ? 'warning' : 'default'}
          dot
        >
          {member.status === 'active' ? 'Active' : member.status === 'on_leave' ? 'On Leave' : 'Inactive'}
        </Badge>
      ),
    },
  ]

  return (
    <SalonBackground className="h-full">
      <div className="h-full p-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Staff</h1>
            <p className="text-gray-400">Manage your team members</p>
          </div>
          <Button variant="primary" onClick={() => setShowNewStaffModal(true)}>
            <Plus className="h-4 w-4" />
            Add Staff
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Staff" value={staff.length} />
          <StatCard label="Active Today" value={staff.filter(s => s.status === 'active').length} />
          <StatCard label="On Leave" value={staff.filter(s => s.status === 'on_leave').length} />
          <StatCard label="Avg Rating" value="4.7" />
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredStaff}
          keyExtractor={(member) => member.id}
          searchable
          searchValue={search}
          onSearchChange={setSearch}
          searchPlaceholder="Search staff by name, email, or title..."
          emptyMessage="No staff members found"
        />

        {/* New Staff Modal */}
        <Modal
          isOpen={showNewStaffModal}
          onClose={() => setShowNewStaffModal(false)}
          title="Add Staff Member"
          size="md"
        >
          <form className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input label="First Name" placeholder="Jane" required />
              <Input label="Last Name" placeholder="Doe" required />
            </div>
            <Input label="Email" type="email" placeholder="jane@salon.com" required />
            <Input label="Phone" type="tel" placeholder="(555) 123-4567" />
            <Select
              label="Title"
              options={[
                { value: 'junior_stylist', label: 'Junior Stylist' },
                { value: 'senior_stylist', label: 'Senior Stylist' },
                { value: 'color_specialist', label: 'Color Specialist' },
                { value: 'nail_technician', label: 'Nail Technician' },
                { value: 'manager', label: 'Manager' },
              ]}
            />
            <div className="flex gap-3 justify-end pt-4">
              <Button variant="ghost" onClick={() => setShowNewStaffModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Add Staff
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </SalonBackground>
  )
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  )
}
