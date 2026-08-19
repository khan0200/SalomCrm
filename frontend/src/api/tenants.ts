import apiClient from './client'
import type { Tenant, Branch, PaginatedResponse } from '@/types'

export const tenantsApi = {
  getTenants: async (): Promise<Tenant[] | PaginatedResponse<Tenant>> => {
    const response = await apiClient.get('/tenants/')
    return response.data.results || response.data
  },

  createTenant: async (data: {
    name: string
    slug: string
    branding_color?: string
    description?: string
    admin_email: string
    admin_full_name: string
    admin_password: string
  }): Promise<Tenant> => {
    const response = await apiClient.post('/tenants/', data)
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
