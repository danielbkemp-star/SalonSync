import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, User, LoginCredentials, RegisterData } from '@/api/auth'

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.login(credentials)
          localStorage.setItem('access_token', response.access_token)
          set({
            user: response.user,
            accessToken: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: any) {
          const message = error.response?.data?.detail || 'Login failed'
          set({ error: message, isLoading: false })
          throw error
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.register(data)
          localStorage.setItem('access_token', response.access_token)
          set({
            user: response.user,
            accessToken: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: any) {
          const message = error.response?.data?.detail || 'Registration failed'
          set({ error: message, isLoading: false })
          throw error
        }
      },

      logout: async () => {
        try {
          await authApi.logout()
        } catch {
          // Continue with logout even if API call fails
        }
        localStorage.removeItem('access_token')
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
        })
      },

      checkAuth: async () => {
        const token = localStorage.getItem('access_token')
        if (!token) {
          set({ isAuthenticated: false, user: null })
          return
        }

        set({ isLoading: true })
        try {
          const user = await authApi.me()
          set({
            user,
            accessToken: token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch {
          localStorage.removeItem('access_token')
          set({
            user: null,
            accessToken: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
      }),
    }
  )
)
