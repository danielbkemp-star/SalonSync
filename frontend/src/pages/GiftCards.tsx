import { useState } from 'react'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { Button, Input, Badge, Modal, DataTable } from '@/components/ui'
import { Plus, Gift, CreditCard, Mail, Search, Copy, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Column } from '@/components/ui/DataTable'

interface GiftCard {
  id: number
  code: string
  initial_value: number
  current_balance: number
  status: 'active' | 'redeemed' | 'expired' | 'cancelled'
  card_type: 'digital' | 'physical'
  purchaser_name: string | null
  recipient_name: string | null
  recipient_email: string | null
  purchased_at: string
  expires_at: string | null
  last_used_at: string | null
}

// Mock data
const mockGiftCards: GiftCard[] = [
  { id: 1, code: 'GIFT-ABCD-1234', initial_value: 100, current_balance: 100, status: 'active', card_type: 'digital', purchaser_name: 'John Smith', recipient_name: 'Jane Doe', recipient_email: 'jane@email.com', purchased_at: '2024-01-15T10:30:00Z', expires_at: null, last_used_at: null },
  { id: 2, code: 'GIFT-EFGH-5678', initial_value: 50, current_balance: 25.50, status: 'active', card_type: 'digital', purchaser_name: 'Sarah Johnson', recipient_name: 'Emily Davis', recipient_email: 'emily@email.com', purchased_at: '2024-01-10T14:00:00Z', expires_at: '2025-01-10T14:00:00Z', last_used_at: '2024-01-12T16:30:00Z' },
  { id: 3, code: 'GIFT-IJKL-9012', initial_value: 200, current_balance: 0, status: 'redeemed', card_type: 'physical', purchaser_name: 'Mike Wilson', recipient_name: 'Lisa Chen', recipient_email: null, purchased_at: '2023-12-20T09:00:00Z', expires_at: null, last_used_at: '2024-01-08T11:15:00Z' },
  { id: 4, code: 'GIFT-MNOP-3456', initial_value: 75, current_balance: 75, status: 'expired', card_type: 'digital', purchaser_name: 'Anna Brown', recipient_name: 'Tom Miller', recipient_email: 'tom@email.com', purchased_at: '2023-06-15T12:00:00Z', expires_at: '2023-12-15T12:00:00Z', last_used_at: null },
]

export function GiftCardsPage() {
  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showRedeemModal, setShowRedeemModal] = useState(false)
  const [giftCards] = useState<GiftCard[]>(mockGiftCards)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  // Form state for new gift card
  const [newGiftCard, setNewGiftCard] = useState({
    amount: '',
    recipientName: '',
    recipientEmail: '',
    purchaserName: '',
    message: '',
    sendToRecipient: true,
  })

  // Form state for redeem
  const [redeemForm, setRedeemForm] = useState({
    code: '',
    amount: '',
  })

  const filteredGiftCards = giftCards.filter(
    (card) =>
      card.code.toLowerCase().includes(search.toLowerCase()) ||
      card.recipient_name?.toLowerCase().includes(search.toLowerCase()) ||
      card.purchaser_name?.toLowerCase().includes(search.toLowerCase())
  )

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(code)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const statusVariant = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'active': return 'success'
      case 'redeemed': return 'default'
      case 'expired': return 'warning'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  const columns: Column<GiftCard>[] = [
    {
      key: 'code',
      header: 'Gift Card',
      render: (card) => (
        <div className="flex items-center gap-3">
          <div className={cn(
            'w-10 h-10 rounded-lg flex items-center justify-center',
            card.card_type === 'digital' ? 'bg-purple-500/20' : 'bg-pink-500/20'
          )}>
            {card.card_type === 'digital' ? (
              <Mail className="h-5 w-5 text-purple-400" />
            ) : (
              <CreditCard className="h-5 w-5 text-pink-400" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-white font-medium">{card.code}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  copyCode(card.code)
                }}
                className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
              >
                {copiedCode === card.code ? (
                  <CheckCircle className="h-4 w-4 text-green-400" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
            <div className="text-xs text-gray-500 capitalize">{card.card_type}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'value',
      header: 'Value',
      render: (card) => (
        <div>
          <div className="text-white font-medium">${card.current_balance.toFixed(2)}</div>
          {card.current_balance !== card.initial_value && (
            <div className="text-xs text-gray-500">of ${card.initial_value.toFixed(2)}</div>
          )}
        </div>
      ),
    },
    {
      key: 'recipient',
      header: 'Recipient',
      render: (card) => (
        <div>
          <div className="text-white">{card.recipient_name || '-'}</div>
          {card.recipient_email && (
            <div className="text-xs text-gray-500">{card.recipient_email}</div>
          )}
        </div>
      ),
    },
    {
      key: 'purchaser_name',
      header: 'Purchased By',
      render: (card) => (
        <div className="text-gray-300">{card.purchaser_name || '-'}</div>
      ),
    },
    {
      key: 'purchased_at',
      header: 'Date',
      render: (card) => (
        <div className="text-gray-400">
          {new Date(card.purchased_at).toLocaleDateString()}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (card) => (
        <Badge variant={statusVariant(card.status)} dot>
          {card.status.charAt(0).toUpperCase() + card.status.slice(1)}
        </Badge>
      ),
    },
  ]

  // Calculate stats
  const stats = {
    totalActive: giftCards.filter(c => c.status === 'active').length,
    totalValue: giftCards.filter(c => c.status === 'active').reduce((sum, c) => sum + c.current_balance, 0),
    soldThisMonth: giftCards.filter(c => {
      const date = new Date(c.purchased_at)
      const now = new Date()
      return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear()
    }).length,
    redeemedThisMonth: giftCards.filter(c => c.status === 'redeemed' && c.last_used_at).length,
  }

  return (
    <SalonBackground className="h-full">
      <div className="h-full p-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Gift Cards</h1>
            <p className="text-gray-400">Manage gift card sales and redemptions</p>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setShowRedeemModal(true)}>
              <Search className="h-4 w-4" />
              Redeem
            </Button>
            <Button variant="primary" onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4" />
              Create Gift Card
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard
            icon={<Gift className="h-5 w-5 text-purple-400" />}
            label="Active Cards"
            value={stats.totalActive}
          />
          <StatCard
            icon={<CreditCard className="h-5 w-5 text-green-400" />}
            label="Outstanding Value"
            value={`$${stats.totalValue.toFixed(2)}`}
          />
          <StatCard
            icon={<Plus className="h-5 w-5 text-blue-400" />}
            label="Sold This Month"
            value={stats.soldThisMonth}
          />
          <StatCard
            icon={<CheckCircle className="h-5 w-5 text-pink-400" />}
            label="Redeemed This Month"
            value={stats.redeemedThisMonth}
          />
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredGiftCards}
          keyExtractor={(card) => card.id}
          searchable
          searchValue={search}
          onSearchChange={setSearch}
          searchPlaceholder="Search by code, recipient, or purchaser..."
          emptyMessage="No gift cards found"
        />

        {/* Create Gift Card Modal */}
        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create Gift Card"
          description="Issue a new gift card"
          size="md"
        >
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Amount</label>
              <div className="grid grid-cols-4 gap-2 mb-2">
                {[25, 50, 100, 200].map((amount) => (
                  <button
                    key={amount}
                    type="button"
                    onClick={() => setNewGiftCard({ ...newGiftCard, amount: amount.toString() })}
                    className={cn(
                      'py-2 rounded-lg font-medium transition-colors',
                      newGiftCard.amount === amount.toString()
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    )}
                  >
                    ${amount}
                  </button>
                ))}
              </div>
              <Input
                placeholder="Or enter custom amount"
                value={newGiftCard.amount}
                onChange={(e) => setNewGiftCard({ ...newGiftCard, amount: e.target.value })}
                type="number"
              />
            </div>

            <div className="border-t border-gray-800 pt-4">
              <h4 className="text-white font-medium mb-3">Recipient</h4>
              <div className="space-y-3">
                <Input
                  label="Name"
                  value={newGiftCard.recipientName}
                  onChange={(e) => setNewGiftCard({ ...newGiftCard, recipientName: e.target.value })}
                  placeholder="Recipient's name"
                />
                <Input
                  label="Email"
                  type="email"
                  value={newGiftCard.recipientEmail}
                  onChange={(e) => setNewGiftCard({ ...newGiftCard, recipientEmail: e.target.value })}
                  placeholder="recipient@email.com"
                />
              </div>
            </div>

            <div className="border-t border-gray-800 pt-4">
              <h4 className="text-white font-medium mb-3">From</h4>
              <Input
                label="Purchaser Name"
                value={newGiftCard.purchaserName}
                onChange={(e) => setNewGiftCard({ ...newGiftCard, purchaserName: e.target.value })}
                placeholder="Your name"
              />
            </div>

            <Input
              label="Personal Message (optional)"
              value={newGiftCard.message}
              onChange={(e) => setNewGiftCard({ ...newGiftCard, message: e.target.value })}
              placeholder="Add a message for the recipient"
            />

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={newGiftCard.sendToRecipient}
                onChange={(e) => setNewGiftCard({ ...newGiftCard, sendToRecipient: e.target.checked })}
                className="w-5 h-5 rounded bg-gray-800 border-gray-700 text-purple-500 focus:ring-purple-500"
              />
              <span className="text-gray-300">Email gift card to recipient</span>
            </label>

            <div className="flex gap-3 justify-end pt-4">
              <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Create Gift Card
              </Button>
            </div>
          </form>
        </Modal>

        {/* Redeem Gift Card Modal */}
        <Modal
          isOpen={showRedeemModal}
          onClose={() => setShowRedeemModal(false)}
          title="Redeem Gift Card"
          description="Apply a gift card to a purchase"
          size="sm"
        >
          <form className="space-y-4">
            <Input
              label="Gift Card Code"
              value={redeemForm.code}
              onChange={(e) => setRedeemForm({ ...redeemForm, code: e.target.value.toUpperCase() })}
              placeholder="XXXX-XXXX-XXXX"
              className="font-mono"
            />
            <Input
              label="Amount to Redeem"
              type="number"
              value={redeemForm.amount}
              onChange={(e) => setRedeemForm({ ...redeemForm, amount: e.target.value })}
              placeholder="0.00"
            />
            <div className="flex gap-3 justify-end pt-4">
              <Button variant="ghost" onClick={() => setShowRedeemModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Check & Redeem
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </SalonBackground>
  )
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-lg bg-gray-800">
          {icon}
        </div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  )
}
