import { useState } from 'react'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { Button, Input } from '@/components/ui'
import { Building2, Clock, Bell, CreditCard, Users, Shield, Palette, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

type SettingsSection = 'salon' | 'hours' | 'notifications' | 'billing' | 'team' | 'security' | 'appearance'

interface SectionConfig {
  id: SettingsSection
  label: string
  icon: React.ElementType
  description: string
}

const sections: SectionConfig[] = [
  { id: 'salon', label: 'Salon Info', icon: Building2, description: 'Business name, address, contact' },
  { id: 'hours', label: 'Business Hours', icon: Clock, description: 'Operating hours and holidays' },
  { id: 'notifications', label: 'Notifications', icon: Bell, description: 'Email and SMS preferences' },
  { id: 'billing', label: 'Billing', icon: CreditCard, description: 'Subscription and payment' },
  { id: 'team', label: 'Team', icon: Users, description: 'Permissions and access' },
  { id: 'security', label: 'Security', icon: Shield, description: 'Password and 2FA' },
  { id: 'appearance', label: 'Appearance', icon: Palette, description: 'Theme and display' },
]

export function SettingsPage() {
  const [activeSection, setActiveSection] = useState<SettingsSection>('salon')

  return (
    <SalonBackground className="h-full">
      <div className="h-full p-6 overflow-y-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-gray-400">Manage your salon preferences</p>
        </div>

        <div className="flex gap-6">
          {/* Sidebar */}
          <div className="w-72 flex-shrink-0">
            <nav className="space-y-1">
              {sections.map((section) => {
                const Icon = section.icon
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={cn(
                      'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors',
                      activeSection === section.id
                        ? 'bg-purple-500/20 text-purple-400'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                    )}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{section.label}</div>
                      <div className="text-xs text-gray-500 truncate">{section.description}</div>
                    </div>
                    <ChevronRight className="h-4 w-4 opacity-50" />
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
              {activeSection === 'salon' && <SalonInfoSettings />}
              {activeSection === 'hours' && <BusinessHoursSettings />}
              {activeSection === 'notifications' && <NotificationSettings />}
              {activeSection === 'billing' && <BillingSettings />}
              {activeSection === 'team' && <TeamSettings />}
              {activeSection === 'security' && <SecuritySettings />}
              {activeSection === 'appearance' && <AppearanceSettings />}
            </div>
          </div>
        </div>
      </div>
    </SalonBackground>
  )
}

function SalonInfoSettings() {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-6">Salon Information</h2>
      <form className="space-y-6">
        <Input label="Salon Name" defaultValue="Style Studio" />
        <Input label="Phone" type="tel" defaultValue="(555) 123-4567" />
        <Input label="Email" type="email" defaultValue="info@stylestudio.com" />
        <Input label="Address" defaultValue="123 Main Street" />
        <div className="grid grid-cols-3 gap-4">
          <Input label="City" defaultValue="Los Angeles" />
          <Input label="State" defaultValue="CA" />
          <Input label="ZIP" defaultValue="90001" />
        </div>
        <Input label="Website" type="url" defaultValue="https://stylestudio.com" />
        <div className="flex justify-end pt-4">
          <Button variant="primary">Save Changes</Button>
        </div>
      </form>
    </div>
  )
}

function BusinessHoursSettings() {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-6">Business Hours</h2>
      <div className="space-y-4">
        {days.map((day) => (
          <div key={day} className="flex items-center gap-4">
            <div className="w-28 text-gray-300">{day}</div>
            <Input type="time" defaultValue="09:00" className="w-32" />
            <span className="text-gray-500">to</span>
            <Input type="time" defaultValue="18:00" className="w-32" />
            <label className="flex items-center gap-2 text-gray-400">
              <input type="checkbox" className="rounded bg-gray-800 border-gray-700" />
              Closed
            </label>
          </div>
        ))}
      </div>
      <div className="flex justify-end pt-6">
        <Button variant="primary">Save Hours</Button>
      </div>
    </div>
  )
}

function NotificationSettings() {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-6">Notification Preferences</h2>
      <div className="space-y-6">
        <div>
          <h3 className="text-white font-medium mb-3">Appointment Reminders</h3>
          <div className="space-y-3">
            <ToggleOption label="Email reminders to clients" defaultChecked />
            <ToggleOption label="SMS reminders to clients" defaultChecked />
            <ToggleOption label="24-hour reminder" defaultChecked />
            <ToggleOption label="2-hour reminder" defaultChecked />
          </div>
        </div>
        <div>
          <h3 className="text-white font-medium mb-3">Staff Notifications</h3>
          <div className="space-y-3">
            <ToggleOption label="New appointment notifications" defaultChecked />
            <ToggleOption label="Cancellation notifications" defaultChecked />
            <ToggleOption label="Daily schedule summary" />
          </div>
        </div>
      </div>
      <div className="flex justify-end pt-6">
        <Button variant="primary">Save Preferences</Button>
      </div>
    </div>
  )
}

function BillingSettings() {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-6">Billing & Subscription</h2>
      <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/30 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-purple-400 font-medium">Professional Plan</div>
            <div className="text-gray-400 text-sm">$49/month</div>
          </div>
          <Button variant="outline" size="sm">Upgrade</Button>
        </div>
      </div>
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-lg bg-gray-800">
          <div>
            <div className="text-white">Payment Method</div>
            <div className="text-gray-400 text-sm">Visa ending in 4242</div>
          </div>
          <Button variant="ghost" size="sm">Update</Button>
        </div>
        <div className="flex items-center justify-between p-4 rounded-lg bg-gray-800">
          <div>
            <div className="text-white">Next Billing Date</div>
            <div className="text-gray-400 text-sm">February 1, 2024</div>
          </div>
          <Button variant="ghost" size="sm">View History</Button>
        </div>
      </div>
    </div>
  )
}

function TeamSettings() {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-6">Team & Permissions</h2>
      <p className="text-gray-400 mb-6">Manage who has access to your SalonSync account and what they can do.</p>
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-lg bg-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-500 flex items-center justify-center text-white font-medium">JD</div>
            <div>
              <div className="text-white">Jane Doe (You)</div>
              <div className="text-gray-400 text-sm">Owner</div>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between p-4 rounded-lg bg-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-pink-500 flex items-center justify-center text-white font-medium">JM</div>
            <div>
              <div className="text-white">Jessica Martinez</div>
              <div className="text-gray-400 text-sm">Manager</div>
            </div>
          </div>
          <Button variant="ghost" size="sm">Edit</Button>
        </div>
      </div>
      <div className="flex justify-end pt-6">
        <Button variant="primary">Invite Team Member</Button>
      </div>
    </div>
  )
}

function SecuritySettings() {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-6">Security Settings</h2>
      <div className="space-y-6">
        <div>
          <h3 className="text-white font-medium mb-3">Change Password</h3>
          <div className="space-y-4 max-w-md">
            <Input label="Current Password" type="password" />
            <Input label="New Password" type="password" />
            <Input label="Confirm New Password" type="password" />
            <Button variant="primary">Update Password</Button>
          </div>
        </div>
        <div className="pt-4 border-t border-gray-800">
          <h3 className="text-white font-medium mb-3">Two-Factor Authentication</h3>
          <div className="flex items-center justify-between p-4 rounded-lg bg-gray-800">
            <div>
              <div className="text-white">Status: Not Enabled</div>
              <div className="text-gray-400 text-sm">Add an extra layer of security to your account</div>
            </div>
            <Button variant="outline">Enable 2FA</Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function AppearanceSettings() {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-6">Appearance</h2>
      <div className="space-y-6">
        <div>
          <h3 className="text-white font-medium mb-3">Theme</h3>
          <div className="flex gap-4">
            <button className="p-4 rounded-lg bg-gray-800 border-2 border-purple-500 text-white">
              <div className="w-20 h-12 rounded bg-gray-900 mb-2" />
              <span className="text-sm">Dark</span>
            </button>
            <button className="p-4 rounded-lg bg-gray-800 border-2 border-transparent text-gray-400 hover:border-gray-600">
              <div className="w-20 h-12 rounded bg-white mb-2" />
              <span className="text-sm">Light</span>
            </button>
          </div>
        </div>
        <div>
          <h3 className="text-white font-medium mb-3">Accent Color</h3>
          <div className="flex gap-3">
            {['bg-purple-500', 'bg-pink-500', 'bg-blue-500', 'bg-green-500', 'bg-orange-500'].map((color) => (
              <button
                key={color}
                className={cn(
                  'w-10 h-10 rounded-full',
                  color,
                  color === 'bg-purple-500' && 'ring-2 ring-white ring-offset-2 ring-offset-gray-900'
                )}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function ToggleOption({ label, defaultChecked }: { label: string; defaultChecked?: boolean }) {
  return (
    <label className="flex items-center justify-between p-3 rounded-lg bg-gray-800 cursor-pointer hover:bg-gray-750 transition-colors">
      <span className="text-gray-300">{label}</span>
      <input
        type="checkbox"
        defaultChecked={defaultChecked}
        className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-900"
      />
    </label>
  )
}
