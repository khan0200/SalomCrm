import apiClient from './client'
import type { UserProfile } from '@/types'

export const authApi = {
  login: async (credentials: { email: string; password: string }) => {
    const response = await apiClient.post('/auth/login/', credentials)
    return response.data
  },
  getMe: async (): Promise<UserProfile> => {
    const response = await apiClient.get('/auth/me/')
    return response.data
  },
}
