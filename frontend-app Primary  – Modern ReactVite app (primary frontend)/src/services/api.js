import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const refreshToken = localStorage.getItem('refresh_token')
          if (refreshToken) {
            try {
              const response = await this.client.post('/auth/refresh', {}, {
                headers: { Authorization: `Bearer ${refreshToken}` }
              })
              const { access_token } = response.data
              localStorage.setItem('access_token', access_token)
              this.setAuthToken(access_token)
              
              return this.client.request(error.config)
            } catch (refreshError) {
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              window.location.href = '/login'
            }
          } else {
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }

  setAuthToken(token) {
    if (token) {
      this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete this.client.defaults.headers.common['Authorization']
    }
  }

  get(url, config = {}) {
    return this.client.get(url, config)
  }

  post(url, data = {}, config = {}) {
    return this.client.post(url, data, config)
  }

  put(url, data = {}, config = {}) {
    return this.client.put(url, data, config)
  }

  delete(url, config = {}) {
    return this.client.delete(url, config)
  }
}

export const apiService = new ApiService()
