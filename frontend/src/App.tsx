import { Routes, Route } from 'react-router-dom'
import { SalonDashboard } from './components/dashboard/CommandCenter'

function App() {
  return (
    <div className="min-h-screen bg-brand-plum-900">
      <Routes>
        <Route path="/" element={<SalonDashboard />} />
        {/* Add more routes as needed */}
        <Route path="/appointments/*" element={<PlaceholderPage title="Appointments" />} />
        <Route path="/clients/*" element={<PlaceholderPage title="Clients" />} />
        <Route path="/staff/*" element={<PlaceholderPage title="Staff" />} />
        <Route path="/services/*" element={<PlaceholderPage title="Services" />} />
        <Route path="/pos/*" element={<PlaceholderPage title="Point of Sale" />} />
        <Route path="/schedule/*" element={<PlaceholderPage title="Schedule" />} />
        <Route path="/inventory/*" element={<PlaceholderPage title="Inventory" />} />
        <Route path="/reports/*" element={<PlaceholderPage title="Reports" />} />
        <Route path="/settings/*" element={<PlaceholderPage title="Settings" />} />
      </Routes>
    </div>
  )
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="min-h-screen bg-brand-plum-900 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-4">{title}</h1>
        <p className="text-white/60">This page is under construction</p>
        <a
          href="/"
          className="inline-block mt-6 px-4 py-2 bg-brand-plum-500 text-white rounded-lg hover:bg-brand-plum-400 transition-colors"
        >
          Back to Dashboard
        </a>
      </div>
    </div>
  )
}

export default App
