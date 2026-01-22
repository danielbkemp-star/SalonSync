import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { SalonDashboard } from './components/dashboard/CommandCenter'
import { LoginPage, CapturePage, SocialCreatePage } from './pages'
import { useAuthStore } from './stores/authStore'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore()
  const location = useLocation()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-brand-plum-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <div className="min-h-screen bg-brand-plum-900">
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

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

        {/* Placeholder routes */}
        <Route
          path="/appointments/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Appointments" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/clients/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Clients" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/staff/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Staff" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/services/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Services" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pos/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Point of Sale" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/schedule/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Schedule" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inventory/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Inventory" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Reports" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings/*"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Settings" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/social"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Social Media" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portfolio"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Portfolio" />
            </ProtectedRoute>
          }
        />
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
