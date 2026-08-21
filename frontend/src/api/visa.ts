import apiClient from './client'

export type VisaType = 'Embassy' | 'E-Visa' | 'Regional'

export interface VisaRecord {
  application_date: string
  status: string
  status_korean: string
  entry_date: string
  entry_purpose: string
  rejection_reason: string
}

export interface VisaCheckResult {
  found: boolean
  records: VisaRecord[]
  result_count: number
  latest_status: string
  latest_status_korean: string
  latest_date: string
  entry_date: string
  entry_purpose: string
  rejection_reason: string
  visa_expiry: string
  visa_kind: string
  status_of_residence: string
  inviting_company: string
  pdf_url: string
  ccvi_appl_no?: string
  ccvi_seq?: string
  ev_seq?: string
  inv_seq?: string
  appl_no?: string
}

export interface VisaCheckParams {
  passport: string
  full_name: string
  birth_date: string
  visa_type: VisaType
  application_no?: string
}

export interface VisaStudent {
  id?: string
  student_id?: string
  full_name: string
  passport: string
  birthday?: string
  visa_type: VisaType
  application_no?: string
  status: string
  application_date?: string
  status_date?: string
  last_checked?: string
  rejection_reason?: string
  pdf_url?: string
  api_response?: any
  tariff?: string
  university?: string
  coordinator?: string
  b2b?: string
  flag?: boolean
  refund_application?: boolean
  pinned?: boolean
  batch_selected?: boolean
  is_deleted?: boolean
  created_at?: string
  updated_at?: string
}

export interface LookupStudentResult {
  found: boolean
  student?: {
    id: string
    full_name: string
    passport: string
    birthday: string
    tariff: string
    university: string
    coordinator: string
    phone1?: string
  }
}

export interface VisaOptions {
  tariffs: { name: string }[]
  universities: { name: string }[]
  coordinators: { name: string }[]
  b2b: { name: string }[]
}

export const visaApi = {
  getVisaStudents: async (params: { search?: string; status?: string; sort_by?: string } = {}): Promise<{ count: number; results: VisaStudent[] }> => {
    const queryParams = new URLSearchParams()
    if (params.search) queryParams.set('search', params.search)
    if (params.status) queryParams.set('status', params.status)
    if (params.sort_by) queryParams.set('sort_by', params.sort_by)
    const response = await apiClient.get<{ count: number; results: VisaStudent[] }>(`/students/visa/students/?${queryParams.toString()}`)
    return response.data
  },

  createVisaStudent: async (data: Partial<VisaStudent>): Promise<VisaStudent> => {
    const response = await apiClient.post<VisaStudent>('/students/visa/students/', data)
    return response.data
  },

  updateVisaStudent: async (passport: string, data: Partial<VisaStudent>): Promise<VisaStudent> => {
    const response = await apiClient.patch<VisaStudent>(`/students/visa/students/${encodeURIComponent(passport)}/`, data)
    return response.data
  },

  deleteVisaStudent: async (passport: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/students/visa/students/${encodeURIComponent(passport)}/`)
    return response.data
  },

  bulkDeleteVisaStudents: async (passports: string[]): Promise<{ deleted_count: number; message: string }> => {
    const response = await apiClient.post<{ deleted_count: number; message: string }>('/students/visa/students/bulk-delete/', { passports })
    return response.data
  },

  lookupMainDatabase: async (passport: string): Promise<LookupStudentResult> => {
    const response = await apiClient.get<LookupStudentResult>(`/students/visa/lookup/?passport=${encodeURIComponent(passport)}`)
    return response.data
  },

  getVisaOptions: async (): Promise<VisaOptions> => {
    const response = await apiClient.get<VisaOptions>('/students/visa/options/')
    return response.data
  },

  checkVisa: async (params: VisaCheckParams): Promise<VisaCheckResult> => {
    const response = await apiClient.post<VisaCheckResult>('/students/visa/check/', params)
    return response.data
  },

  downloadPdf: async (params: VisaCheckParams & { pdf_url?: string }): Promise<Blob> => {
    const response = await apiClient.post('/students/visa/download-pdf/', params, {
      responseType: 'blob'
    })
    return response.data
  }
}
