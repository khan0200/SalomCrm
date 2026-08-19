import apiClient from './client'
import type { Student, PaginatedResponse } from '@/types'

export interface StatusFilterParams {
  page?: number
  page_size?: number
  search?: string
  folder?: string
  sort_by?: 'id' | 'left'
  sort_order?: 'asc' | 'desc'
  show_hidden?: boolean
}

export const statusApi = {
  getStatusStudents: async (params: StatusFilterParams = {}): Promise<PaginatedResponse<Student>> => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))
    if (params.search) queryParams.set('search', params.search)
    if (params.folder) queryParams.set('folder', params.folder)
    if (params.sort_by) queryParams.set('sort_by', params.sort_by)
    if (params.sort_order) queryParams.set('sort_order', params.sort_order)
    if (params.show_hidden) queryParams.set('show_hidden', 'true')

    const response = await apiClient.get(`/status/?${queryParams.toString()}`)
    return response.data
  },

  quickUpdate: async (id: string, data: {
    invoice?: string | null
    coa?: string | null
    kdb_put_date?: string | null
    kdb_take_date?: string | null
    embassy?: string | null
    status_hidden?: boolean
    status_row_color?: string | null
  }): Promise<Student> => {
    const response = await apiClient.patch(`/status/${id}/quick_update/`, data)
    return response.data
  },

  updateEmbassyDrawer: async (id: string, data: {
    embassy_father_docs?: string[]
    embassy_mother_docs?: string[]
    embassy_sponsor_notes?: string | null
    embassy?: string | null
    status_hidden?: boolean
  }): Promise<Student> => {
    const response = await apiClient.patch(`/status/${id}/embassy_drawer/`, data)
    return response.data
  },
}
