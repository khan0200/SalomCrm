import apiClient from './client'
import type { Tenant, Branch, PaginatedResponse } from '@/types'

export interface TenantAdmin {
  id: string
  email: string
  full_name: string
  is_active: boolean
}

export const tenantsApi = {
  getTenants: async (): Promise<Tenant[] | PaginatedResponse<Tenant>> => {
    const response = await apiClient.get('/tenants/')
    return response.data.results || response.data
  },

  createTenant: async (data: {
    name: string
    slug: string
    description?: string
    admin_email: string
    admin_full_name: string
    admin_password: string
  }): Promise<Tenant> => {
    const response = await apiClient.post('/tenants/', data)
    return response.data
  },

  updateTenant: async (id: string, data: {
    name?: string
    description?: string
    settings?: {
      telegram_bot_token?: string
      telegram_chat_id?: string
    }
  }): Promise<Tenant> => {
    const response = await apiClient.patch(`/tenants/${id}/`, data)
    return response.data
  },

  deleteTenant: async (id: string) => {
    const response = await apiClient.delete(`/tenants/${id}/`)
    return response.data
  },

  getTenantAdmins: async (id: string): Promise<TenantAdmin[]> => {
    const response = await apiClient.get(`/tenants/${id}/admins/`)
    return response.data
  },

  updateTenantAdminCredentials: async (id: string, data: {
    user_id: string
    email?: string
    full_name?: string
    password?: string
  }) => {
    const response = await apiClient.post(`/tenants/${id}/admin-credentials/`, data)
    return response.data
  },

  deactivateTenant: async (id: string) => {
    const response = await apiClient.post(`/tenants/${id}/deactivate/`)
    return response.data
  },

  activateTenant: async (id: string) => {
    const response = await apiClient.post(`/tenants/${id}/activate/`)
    return response.data
  },

  getBranches: async (): Promise<Branch[]> => {
    const response = await apiClient.get('/branches/')
    return response.data.results || response.data
  },
}
