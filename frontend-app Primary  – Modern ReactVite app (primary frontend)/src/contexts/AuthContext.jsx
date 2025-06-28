import { createContext, useContext, useState, useEffect } from 'react'
import { apiService } from '../services/api'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      apiService.setAuthToken(token)
      fetchProfile()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await apiService.get('/auth/profile')
      setUser(response.data)
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      apiService.setAuthToken(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      const response = await apiService.post('/auth/login', { email, password })
      const { user, access_token, refresh_token } = response.data
      
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      apiService.setAuthToken(access_token)
      setUser(user)
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed' 
      }
    }
  }

  const register = async (userData) => {
    try {
      const response = await apiService.post('/auth/register', userData)
      const { user, access_token, refresh_token } = response.data
      
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      apiService.setAuthToken(access_token)
      setUser(user)
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Registration failed' 
      }
    }
  }

  const logout = async () => {
    try {
      await apiService.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      apiService.setAuthToken(null)
      setUser(null)
    }
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    fetchProfile
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
