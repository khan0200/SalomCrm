import apiClient from './client'

export interface TariffOption {
  id: string
  name: string
  price: number
  created_at?: string
}

export interface GeneralOption {
  id: string
  name: string
  created_at?: string
}

export interface UniversityStatusOption {
  id: string
  name: string
  color_class: string
  created_at?: string
}

export interface CustomTag {
  name: string
  icon: string
}

export const settingsApi = {
  // Tariffs
  getTariffs: async (): Promise<TariffOption[]> => {
    const res = await apiClient.get('/tariffs/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createTariff: async (data: { name: string; price: number }): Promise<TariffOption> => {
    const res = await apiClient.post('/tariffs/', data)
    return res.data
  },
  updateTariff: async (id: string, data: { name: string; price: number }): Promise<TariffOption> => {
    const res = await apiClient.patch(`/tariffs/${id}/`, data)
    return res.data
  },
  deleteTariff: async (id: string) => {
    await apiClient.delete(`/tariffs/${id}/`)
  },

  // Education Levels
  getLevels: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/education-levels/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createLevel: async (data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.post('/education-levels/', data)
    return res.data
  },
  updateLevel: async (id: string, data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.patch(`/education-levels/${id}/`, data)
    return res.data
  },
  deleteLevel: async (id: string) => {
    await apiClient.delete(`/education-levels/${id}/`)
  },

  // Groups
  getGroups: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/student-groups/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createGroup: async (data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.post('/student-groups/', data)
    return res.data
  },
  updateGroup: async (id: string, data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.patch(`/student-groups/${id}/`, data)
    return res.data
  },
  deleteGroup: async (id: string) => {
    await apiClient.delete(`/student-groups/${id}/`)
  },

  // Leads
  getLeads: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/lead-sources/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createLead: async (data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.post('/lead-sources/', data)
    return res.data
  },
  updateLead: async (id: string, data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.patch(`/lead-sources/${id}/`, data)
    return res.data
  },
  deleteLead: async (id: string) => {
    await apiClient.delete(`/lead-sources/${id}/`)
  },

  // Coordinators
  getCoordinators: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/coordinators/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createCoordinator: async (data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.post('/coordinators/', data)
    return res.data
  },
  updateCoordinator: async (id: string, data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.patch(`/coordinators/${id}/`, data)
    return res.data
  },
  deleteCoordinator: async (id: string) => {
    await apiClient.delete(`/coordinators/${id}/`)
  },

  // Universities
  getUniversities: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/universities/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createUniversity: async (data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.post('/universities/', data)
    return res.data
  },
  updateUniversity: async (id: string, data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.patch(`/universities/${id}/`, data)
    return res.data
  },
  deleteUniversity: async (id: string) => {
    await apiClient.delete(`/universities/${id}/`)
  },

  // University Statuses
  getUniversityStatuses: async (): Promise<UniversityStatusOption[]> => {
    const res = await apiClient.get('/university-statuses/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createUniversityStatus: async (data: { name: string; color_class?: string }): Promise<UniversityStatusOption> => {
    const res = await apiClient.post('/university-statuses/', data)
    return res.data
  },
  updateUniversityStatus: async (id: string, data: { name: string; color_class?: string }): Promise<UniversityStatusOption> => {
    const res = await apiClient.patch(`/university-statuses/${id}/`, data)
    return res.data
  },
  deleteUniversityStatus: async (id: string) => {
    await apiClient.delete(`/university-statuses/${id}/`)
  },

  // Folders
  getFolders: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/folders/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createFolder: async (name: string): Promise<GeneralOption> => {
    const res = await apiClient.post('/folders/', { name })
    return res.data
  },
  deleteFolder: async (id: string) => {
    await apiClient.delete(`/folders/${id}/`)
  },

  // Payment Methods
  getPaymentMethods: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/payment-methods/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createPaymentMethod: async (data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.post('/payment-methods/', data)
    return res.data
  },
  deletePaymentMethod: async (id: string) => {
    await apiClient.delete(`/payment-methods/${id}/`)
  },

  // Payment Receivers
  getPaymentReceivers: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/payment-receivers/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createPaymentReceiver: async (data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.post('/payment-receivers/', data)
    return res.data
  },
  deletePaymentReceiver: async (id: string) => {
    await apiClient.delete(`/payment-receivers/${id}/`)
  },

  // Payment Note Templates
  getPaymentNotes: async (): Promise<GeneralOption[]> => {
    const res = await apiClient.get('/payment-notes/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },
  createPaymentNote: async (data: { name: string }): Promise<GeneralOption> => {
    const res = await apiClient.post('/payment-notes/', data)
    return res.data
  },
  deletePaymentNote: async (id: string) => {
    await apiClient.delete(`/payment-notes/${id}/`)
  },
}
