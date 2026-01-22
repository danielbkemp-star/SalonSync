import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { GlassCard } from '@/components/ui'
import { Button } from '@/components/ui'
import { Input } from '@/components/ui'
import { useAuthStore } from '@/stores/authStore'
import { Scissors } from 'lucide-react'

export function LoginPage() {
  const navigate = useNavigate()
  const { login, isLoading, error, clearError } = useAuthStore()
  const [isRegister, setIsRegister] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()

    try {
      if (isRegister) {
        // Registration would go here
        await login({ username: formData.email, password: formData.password })
      } else {
        await login({ username: formData.email, password: formData.password })
      }
      navigate('/')
    } catch {
      // Error is handled by the store
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      <SalonBackground />

      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-plum-500 to-brand-rose-500 mb-4">
              <Scissors className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">SalonSync</h1>
            <p className="text-white/60 mt-2">Your salon management companion</p>
          </div>

          {/* Login Card */}
          <GlassCard glow="plum">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-xl font-semibold text-white">
                  {isRegister ? 'Create Account' : 'Welcome Back'}
                </h2>
                <p className="text-white/60 text-sm mt-1">
                  {isRegister
                    ? 'Sign up to get started'
                    : 'Sign in to your account'}
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-sm">
                  {error}
                </div>
              )}

              {isRegister && (
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="First Name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    placeholder="Jane"
                    required
                  />
                  <Input
                    label="Last Name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    placeholder="Doe"
                    required
                  />
                </div>
              )}

              <Input
                label="Email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="you@salon.com"
                required
              />

              <Input
                label="Password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                required
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading
                  ? 'Please wait...'
                  : isRegister
                  ? 'Create Account'
                  : 'Sign In'}
              </Button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setIsRegister(!isRegister)
                    clearError()
                  }}
                  className="text-brand-plum-400 hover:text-brand-plum-300 text-sm transition-colors"
                >
                  {isRegister
                    ? 'Already have an account? Sign in'
                    : "Don't have an account? Sign up"}
                </button>
              </div>
            </form>
          </GlassCard>

          {/* Demo credentials hint */}
          <p className="text-center text-white/40 text-xs mt-6">
            Demo: demo@salon.com / demo123
          </p>
        </div>
      </div>
    </div>
  )
}
