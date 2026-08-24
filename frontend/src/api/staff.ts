import apiClient from './client'
import type { UserProfile, UserRole } from '@/types'

export interface StaffCreatePayload {
  full_name: string
  email: string
  role: UserRole
  password?: string
}

export const staffApi = {
  getStaff: async (): Promise<UserProfile[]> => {
    const response = await apiClient.get('/users/')
    return response.data.results || response.data
  },

  // The backend forces tenant = request.user.tenant in perform_create,
  // so the tenant is never sent from the client.
  createStaff: async (data: StaffCreatePayload): Promise<UserProfile> => {
    const response = await apiClient.post('/users/', data)
    return response.data
  },

  updateStaff: async (id: string, data: Partial<StaffCreatePayload> & { is_active?: boolean }): Promise<UserProfile> => {
    const response = await apiClient.patch(`/users/${id}/`, data)
    return response.data
  },

  deleteStaff: async (id: string) => {
    const response = await apiClient.delete(`/users/${id}/`)
    return response.data
  },
}
