import apiClient from './client'
import type { Student, Folder, PaginatedResponse } from '@/types'

export interface StudentFilterParams {
  page?: number
  page_size?: number
  search?: string
  search_mode?: 'all' | 'id'
  folder?: string
  tariff?: string[]
  level?: string[]
  group?: string[]
  cert?: string[]
  lead_by?: string[]
  office?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  include_archive?: boolean
}

export const studentsApi = {
  getStudents: async (params: StudentFilterParams = {}): Promise<PaginatedResponse<Student>> => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))
    if (params.search) queryParams.set('search', params.search)
    if (params.search_mode) queryParams.set('search_mode', params.search_mode)
    if (params.folder) queryParams.set('folder', params.folder)
    if (params.sort_by) queryParams.set('sort_by', params.sort_by)
    if (params.sort_order) queryParams.set('sort_order', params.sort_order)
    if (params.office) queryParams.set('office', params.office)
    if (params.include_archive) queryParams.set('include_archive', 'true')

    if (params.tariff?.length) params.tariff.forEach(t => queryParams.append('tariff', t))
    if (params.level?.length) params.level.forEach(l => queryParams.append('level', l))
    if (params.group?.length) params.group.forEach(g => queryParams.append('group', g))
    if (params.cert?.length) params.cert.forEach(c => queryParams.append('cert', c))
    if (params.lead_by?.length) params.lead_by.forEach(lb => queryParams.append('lead_by', lb))

    const response = await apiClient.get(`/students/?${queryParams.toString()}`)
    return response.data
  },

  getStudentDetail: async (id: string): Promise<Student> => {
    const response = await apiClient.get(`/students/${id}/`)
    return response.data
  },

  createStudent: async (data: Partial<Student>): Promise<Student> => {
    const response = await apiClient.post('/students/', data)
    return response.data
  },

  updateStudent: async (id: string, data: Partial<Student>): Promise<Student> => {
    const response = await apiClient.patch(`/students/${id}/`, data)
    return response.data
  },

  archiveStudent: async (id: string) => {
    const response = await apiClient.post(`/students/${id}/archive/`)
    return response.data
  },

  restoreStudent: async (id: string) => {
    const response = await apiClient.post(`/students/${id}/restore/`)
    return response.data
  },

  permanentDeleteStudent: async (id: string) => {
    const response = await apiClient.delete(`/students/${id}/permanent_delete/`)
    return response.data
  },

  setColor: async (id: string, colors: { row_color?: string | null; status_row_color?: string | null }) => {
    const response = await apiClient.post(`/students/${id}/set_color/`, colors)
    return response.data
  },

  setFolders: async (id: string, folderIds: string[]) => {
    const response = await apiClient.post(`/students/${id}/set_folders/`, { folder_ids: folderIds })
    return response.data
  },

  getFolders: async (): Promise<Folder[]> => {
    const response = await apiClient.get('/folders/')
    return response.data.results || response.data
  },

  createFolder: async (name: string): Promise<Folder> => {
    const response = await apiClient.post('/folders/', { name })
    return response.data
  },

  deleteFolder: async (id: string) => {
    const response = await apiClient.delete(`/folders/${id}/`)
    return response.data
  },

  getOptions: async () => {
    const response = await apiClient.get('/student-options/')
    return response.data
  },
}
