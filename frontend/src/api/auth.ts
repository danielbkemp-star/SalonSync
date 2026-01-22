import { api } from './client'

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
}

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  role: string
  is_active: boolean
  is_verified: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  register: async (data: RegisterData): Promise<TokenResponse> => {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  me: async (): Promise<User> => {
    const response = await api.get('/auth/me')
    return response.data
  },

  refresh: async (): Promise<{ access_token: string }> => {
    const response = await api.post('/auth/refresh')
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
    localStorage.removeItem('access_token')
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },
}
