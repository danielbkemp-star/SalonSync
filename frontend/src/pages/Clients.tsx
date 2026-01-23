import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { DataTable, Button, Badge, Modal, Input } from '@/components/ui'
import { Plus, Phone, Mail, Calendar, Tag } from 'lucide-react'
import type { Column } from '@/components/ui/DataTable'

interface Client {
  id: number
  name: string
  email: string
  phone: string
  visits: number
  lastVisit: string
  tags: string[]
  status: 'active' | 'inactive' | 'vip'
}

// Mock data - would come from API
const mockClients: Client[] = [
  { id: 1, name: 'Sarah Johnson', email: 'sarah@email.com', phone: '(555) 123-4567', visits: 24, lastVisit: '2024-01-15', tags: ['VIP', 'Color'], status: 'vip' },
  { id: 2, name: 'Emily Davis', email: 'emily@email.com', phone: '(555) 234-5678', visits: 12, lastVisit: '2024-01-14', tags: ['Regular'], status: 'active' },
  { id: 3, name: 'Lisa Chen', email: 'lisa@email.com', phone: '(555) 345-6789', visits: 8, lastVisit: '2024-01-10', tags: ['New'], status: 'active' },
  { id: 4, name: 'Rachel Kim', email: 'rachel@email.com', phone: '(555) 456-7890', visits: 15, lastVisit: '2024-01-12', tags: ['VIP'], status: 'vip' },
  { id: 5, name: 'Michelle Lee', email: 'michelle@email.com', phone: '(555) 567-8901', visits: 3, lastVisit: '2023-12-20', tags: [], status: 'inactive' },
  { id: 6, name: 'Amanda Brown', email: 'amanda@email.com', phone: '(555) 678-9012', visits: 18, lastVisit: '2024-01-13', tags: ['Loyal'], status: 'active' },
]

export function ClientsPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [showNewClientModal, setShowNewClientModal] = useState(false)
  const [clients] = useState<Client[]>(mockClients)

  const filteredClients = clients.filter(
    (client) =>
      client.name.toLowerCase().includes(search.toLowerCase()) ||
      client.email.toLowerCase().includes(search.toLowerCase()) ||
      client.phone.includes(search)
  )

  const columns: Column<Client>[] = [
    {
      key: 'name',
      header: 'Client',
      sortable: true,
      render: (client) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium">
            {client.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div>
            <div className="font-medium text-white">{client.name}</div>
            <div className="text-xs text-gray-500 flex items-center gap-1">
              <Mail className="h-3 w-3" />
              {client.email}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'phone',
      header: 'Phone',
      render: (client) => (
        <div className="flex items-center gap-2 text-gray-300">
          <Phone className="h-4 w-4 text-gray-500" />
          {client.phone}
        </div>
      ),
    },
    {
      key: 'visits',
      header: 'Visits',
      sortable: true,
      render: (client) => (
        <span className="text-white font-medium">{client.visits}</span>
      ),
    },
    {
      key: 'lastVisit',
      header: 'Last Visit',
      sortable: true,
      render: (client) => (
        <div className="flex items-center gap-2 text-gray-400">
          <Calendar className="h-4 w-4" />
          {new Date(client.lastVisit).toLocaleDateString()}
        </div>
      ),
    },
    {
      key: 'tags',
      header: 'Tags',
      render: (client) => (
        <div className="flex items-center gap-1 flex-wrap">
          {client.tags.length > 0 ? (
            client.tags.map((tag) => (
              <Badge key={tag} variant={tag === 'VIP' ? 'purple' : 'default'} size="sm">
                {tag}
              </Badge>
            ))
          ) : (
            <span className="text-gray-600 text-sm">-</span>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (client) => (
        <Badge
          variant={client.status === 'vip' ? 'purple' : client.status === 'active' ? 'success' : 'default'}
          dot
        >
          {client.status === 'vip' ? 'VIP' : client.status === 'active' ? 'Active' : 'Inactive'}
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
            <h1 className="text-2xl font-bold text-white">Clients</h1>
            <p className="text-gray-400">Manage your client database</p>
          </div>
          <Button variant="primary" onClick={() => setShowNewClientModal(true)}>
            <Plus className="h-4 w-4" />
            Add Client
          </Button>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Clients" value={clients.length} />
          <StatCard label="Active" value={clients.filter(c => c.status === 'active' || c.status === 'vip').length} />
          <StatCard label="VIP Clients" value={clients.filter(c => c.status === 'vip').length} />
          <StatCard label="New This Month" value={2} />
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredClients}
          keyExtractor={(client) => client.id}
          onRowClick={(client) => navigate(`/clients/${client.id}`)}
          searchable
          searchValue={search}
          onSearchChange={setSearch}
          searchPlaceholder="Search clients by name, email, or phone..."
          emptyMessage="No clients found"
        />

        {/* New Client Modal */}
        <Modal
          isOpen={showNewClientModal}
          onClose={() => setShowNewClientModal(false)}
          title="Add New Client"
          description="Enter the client's information below"
          size="md"
        >
          <form className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input label="First Name" placeholder="Jane" required />
              <Input label="Last Name" placeholder="Doe" required />
            </div>
            <Input label="Email" type="email" placeholder="jane@example.com" />
            <Input label="Phone" type="tel" placeholder="(555) 123-4567" />
            <div className="flex items-center gap-2 pt-2">
              <Tag className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-400">Tags can be added after creation</span>
            </div>
            <div className="flex gap-3 justify-end pt-4">
              <Button variant="ghost" onClick={() => setShowNewClientModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Add Client
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </SalonBackground>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  )
}
