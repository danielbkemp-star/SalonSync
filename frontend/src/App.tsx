import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { SalonDashboard } from './components/dashboard/CommandCenter'
import { LoginPage, CapturePage, SocialCreatePage, ClientsPage, AppointmentsPage, StaffPage, ServicesPage, SettingsPage, ReportsPage, BookingPage, GiftCardsPage, WaitlistPage } from './pages'
import { AppLayout } from './components/layout'
import { useAuthStore } from './stores/authStore'
import { ToastProvider } from './components/ui'
import { DollarSign, Package, Share2, Image, Gift, Wrench } from 'lucide-react'

// Protected route wrapper with layout
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore()
  const location = useLocation()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <AppLayout>{children}</AppLayout>
}

function App() {
  return (
    <ToastProvider>
    <div className="min-h-screen bg-gray-950">
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/book/:salonSlug" element={<BookingPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <SalonDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/capture"
          element={
            <ProtectedRoute>
              <CapturePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/social/create"
          element={
            <ProtectedRoute>
              <SocialCreatePage />
            </ProtectedRoute>
          }
        />

        {/* Main feature routes */}
        <Route
          path="/appointments/*"
          element={
            <ProtectedRoute>
              <AppointmentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/clients/*"
          element={
            <ProtectedRoute>
              <ClientsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/staff/*"
          element={
            <ProtectedRoute>
              <StaffPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/services/*"
          element={
            <ProtectedRoute>
              <ServicesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pos/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Point of Sale" icon="pos" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/schedule/*"
          element={
            <ProtectedRoute>
              <AppointmentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inventory/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Inventory" icon="inventory" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports/*"
          element={
            <ProtectedRoute>
              <ReportsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings/*"
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/social"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Social Media" icon="social" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portfolio"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Portfolio" icon="portfolio" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/gift-cards"
          element={
            <ProtectedRoute>
              <GiftCardsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/waitlist"
          element={
            <ProtectedRoute>
              <WaitlistPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
    </ToastProvider>
  )
}

function PlaceholderPage({ title, icon }: { title: string; icon: string }) {
  const icons: Record<string, React.ReactNode> = {
    pos: <DollarSign className="h-12 w-12 text-gray-600" />,
    inventory: <Package className="h-12 w-12 text-gray-600" />,
    social: <Share2 className="h-12 w-12 text-gray-600" />,
    portfolio: <Image className="h-12 w-12 text-gray-600" />,
    gift: <Gift className="h-12 w-12 text-gray-600" />,
  }

  return (
    <div className="h-full bg-gray-950 flex items-center justify-center p-6">
      <div className="text-center">
        <div className="w-24 h-24 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center mx-auto mb-6">
          {icons[icon]}
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">{title}</h1>
        <p className="text-gray-500 mb-6">This feature is coming soon</p>
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/10 text-purple-400 text-sm">
          <Wrench className="h-4 w-4" />
          Under Development
        </div>
      </div>
    </div>
  )
}

export default App
