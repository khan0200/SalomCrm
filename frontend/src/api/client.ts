import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach access token and tenant ID
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  const activeTenantId = localStorage.getItem('active_tenant_id')
  if (activeTenantId) {
    config.headers['X-Tenant-ID'] = activeTenantId
  }

  const aiSettings = localStorage.getItem('ai_settings')
  if (aiSettings) {
    try {
      config.headers['X-AI-Settings'] = encodeURIComponent(aiSettings)
    } catch {
      // ignore
    }
  }

  return config
})

// Response interceptor: handle 401 token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')

      const handleLogoutRedirect = () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_profile')
        const path = window.location.pathname
        const match = path.match(/^\/contracts\/online\/([^/]+)/)
        if (match && match[1]) {
          window.location.href = `/contracts/online/${match[1]}/sign-in`
        } else {
          window.location.href = '/login'
        }
      }

      if (refreshToken) {
        try {
          const res = await axios.post('/api/auth/refresh/', { refresh: refreshToken })
          if (res.data.access) {
            localStorage.setItem('access_token', res.data.access)
            originalRequest.headers.Authorization = `Bearer ${res.data.access}`
            return apiClient(originalRequest)
          }
        } catch (refreshErr) {
          handleLogoutRedirect()
        }
      } else {
        handleLogoutRedirect()
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
