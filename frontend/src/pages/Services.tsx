import { useState } from 'react'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { Button, Badge, Modal, Input } from '@/components/ui'
import { Plus, Clock, DollarSign, Edit2, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Service {
  id: number
  name: string
  description: string
  duration: number
  price: number
  category: string
  isActive: boolean
}

const mockServices: Service[] = [
  { id: 1, name: 'Haircut', description: 'Classic cut and style', duration: 45, price: 50, category: 'Hair', isActive: true },
  { id: 2, name: 'Color', description: 'Single process color', duration: 90, price: 120, category: 'Hair', isActive: true },
  { id: 3, name: 'Balayage', description: 'Hand-painted highlights', duration: 150, price: 250, category: 'Hair', isActive: true },
  { id: 4, name: 'Full Highlights', description: 'Full head foil highlights', duration: 120, price: 180, category: 'Hair', isActive: true },
  { id: 5, name: 'Blowout', description: 'Wash, dry, and style', duration: 30, price: 45, category: 'Hair', isActive: true },
  { id: 6, name: 'Manicure', description: 'Classic manicure', duration: 30, price: 35, category: 'Nails', isActive: true },
  { id: 7, name: 'Pedicure', description: 'Classic pedicure', duration: 45, price: 50, category: 'Nails', isActive: true },
  { id: 8, name: 'Gel Manicure', description: 'Long-lasting gel polish', duration: 45, price: 55, category: 'Nails', isActive: true },
  { id: 9, name: 'Deep Conditioning', description: 'Intensive hair treatment', duration: 30, price: 40, category: 'Treatments', isActive: true },
  { id: 10, name: 'Keratin Treatment', description: 'Smoothing keratin service', duration: 180, price: 300, category: 'Treatments', isActive: false },
]

const categories = ['All', 'Hair', 'Nails', 'Treatments']

export function ServicesPage() {
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [showNewServiceModal, setShowNewServiceModal] = useState(false)
  const [services] = useState<Service[]>(mockServices)

  const filteredServices = selectedCategory === 'All'
    ? services
    : services.filter((s) => s.category === selectedCategory)

  const groupedServices = filteredServices.reduce((acc, service) => {
    if (!acc[service.category]) {
      acc[service.category] = []
    }
    acc[service.category].push(service)
    return acc
  }, {} as Record<string, Service[]>)

  return (
    <SalonBackground className="h-full">
      <div className="h-full p-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Services</h1>
            <p className="text-gray-400">Manage your service menu</p>
          </div>
          <Button variant="primary" onClick={() => setShowNewServiceModal(true)}>
            <Plus className="h-4 w-4" />
            Add Service
          </Button>
        </div>

        {/* Category Filter */}
        <div className="flex items-center gap-2 mb-6">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                selectedCategory === category
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
              )}
            >
              {category}
            </button>
          ))}
        </div>

        {/* Services Grid */}
        <div className="space-y-8">
          {Object.entries(groupedServices).map(([category, categoryServices]) => (
            <div key={category}>
              <h2 className="text-lg font-semibold text-white mb-4">{category}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categoryServices.map((service) => (
                  <ServiceCard key={service.id} service={service} />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* New Service Modal */}
        <Modal
          isOpen={showNewServiceModal}
          onClose={() => setShowNewServiceModal(false)}
          title="Add New Service"
          size="md"
        >
          <form className="space-y-4">
            <Input label="Service Name" placeholder="e.g., Haircut" required />
            <Input label="Description" placeholder="Brief description of the service" />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Duration (min)" type="number" placeholder="45" required />
              <Input label="Price ($)" type="number" placeholder="50" required />
            </div>
            <Input label="Category" placeholder="e.g., Hair, Nails, Treatments" />
            <div className="flex gap-3 justify-end pt-4">
              <Button variant="ghost" onClick={() => setShowNewServiceModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Add Service
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </SalonBackground>
  )
}

function ServiceCard({ service }: { service: Service }) {
  return (
    <div
      className={cn(
        'rounded-xl bg-gray-900 border border-gray-800 p-4',
        'hover:border-gray-700 transition-colors',
        !service.isActive && 'opacity-50'
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-medium text-white">{service.name}</h3>
          <p className="text-sm text-gray-400">{service.description}</p>
        </div>
        <div className="flex items-center gap-1">
          <button className="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-white transition-colors">
            <Edit2 className="h-4 w-4" />
          </button>
          <button className="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-red-400 transition-colors">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-gray-400">
            <Clock className="h-4 w-4" />
            <span className="text-sm">{service.duration} min</span>
          </div>
          <div className="flex items-center gap-1.5 text-green-400">
            <DollarSign className="h-4 w-4" />
            <span className="text-sm font-medium">${service.price}</span>
          </div>
        </div>
        <Badge variant={service.isActive ? 'success' : 'default'} size="sm">
          {service.isActive ? 'Active' : 'Inactive'}
        </Badge>
      </div>
    </div>
  )
}
