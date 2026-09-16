import apiClient from './client'

export interface Contract {
  id: string
  contract_number: string
  title: string
  template_name: string
  content: string
  status: 'draft' | 'pending' | 'verified' | 'rejected' | 'sent' | 'viewed' | 'signed' | 'completed' | 'cancelled'
  version: number
  is_deleted: boolean
  is_archived: boolean
  archived_at?: string | null
  student?: string | null
  student_id?: string | null
  student_name?: string | null
  student_passport?: string | null
  student_phone?: string | null
  student_tariff?: string | null
  student_university?: string | null
  tariff_name?: string | null
  tariff_price?: number | null
  discount?: number | string | null
  email?: string | null
  passport_number?: string | null
  full_name?: string | null
  education_level?: string | null
  date_of_birth?: string | null
  office?: string | null
  tenant_office_name?: string | null
  content_snapshot?: string | null
  tariff_snapshot?: any
  phone1?: string | null
  phone2?: string | null
  signature_data?: string | null
  student_id_assigned?: string | null
  verification_code?: string | null
  verification_code_expires_at?: string | null
  verification_code_used?: boolean
  verified_at?: string | null
  rejection_reason?: string | null
  rejected_at?: string | null
  rejected_by_name?: string | null
  signed_at?: string | null
  created_at: string
  updated_at: string
  created_by_name?: string | null
  updated_by_name?: string | null
}

export interface ContractCreatePayload {
  student?: string | null
  contract_number?: string
  title: string
  template_name?: string
  content: string
  status?: string
}

export interface ContractUpdatePayload {
  student?: string | null
  contract_number?: string
  title?: string
  template_name?: string
  content?: string
  status?: string
}

export interface ContractListParams {
  search?: string
  status?: string
  student_id?: string
  include_deleted?: boolean
  // Bypasses the default is_archived=false filter - only meant for the tab-
  // counts fetch, which needs every contract (archived or not) at once.
  include_archived?: boolean
}

export const contractsApi = {
  async getContracts(params?: ContractListParams): Promise<Contract[]> {
    const { data } = await apiClient.get<Contract[]>('/contracts/', { params })
    return data
  },

  async getContract(id: string): Promise<Contract> {
    const { data } = await apiClient.get<Contract>(`/contracts/${id}/`)
    return data
  },

  async createContract(payload: ContractCreatePayload): Promise<Contract> {
    const { data } = await apiClient.post<Contract>('/contracts/', payload)
    return data
  },

  async updateContract(id: string, payload: ContractUpdatePayload): Promise<Contract> {
    const { data } = await apiClient.patch<Contract>(`/contracts/${id}/`, payload)
    return data
  },

  async deleteContract(id: string, permanent?: boolean): Promise<{ detail?: string; permanent?: boolean }> {
    const { data } = await apiClient.delete(`/contracts/${id}/`, {
      params: permanent ? { permanent: true } : undefined
    })
    return data
  },

  async duplicateContract(id: string): Promise<Contract> {
    const { data } = await apiClient.post<Contract>(`/contracts/${id}/duplicate/`)
    return data
  },

  async finalizeContract(id: string): Promise<{ detail: string; status: string }> {
    const { data } = await apiClient.post<{ detail: string; status: string }>(`/contracts/${id}/finalize/`)
    return data
  },

  async assignStudentId(id: string, studentId: string, discount?: number | string): Promise<{
    detail: string
    student_id: string
    contract_number: string
    discount?: string
    verification_code: string
    expires_at: string
  }> {
    const payload: Record<string, any> = { student_id: studentId }
    if (discount !== undefined && discount !== null && discount !== '') {
      payload.discount = discount
    }
    const { data } = await apiClient.post(`/contracts/${id}/assign-student-id/`, payload)
    return data
  },

  async regenerateCode(id: string): Promise<{
    detail: string
    student_id: string
    contract_number: string
    verification_code: string
    expires_at: string
  }> {
    const { data } = await apiClient.post(`/contracts/${id}/regenerate-code/`)
    return data
  },

  async rejectContract(id: string, reason: string): Promise<{
    detail: string
    status: string
    rejection_reason: string
  }> {
    const { data } = await apiClient.post(`/contracts/${id}/reject/`, { reason })
    return data
  },

  async archiveContract(id: string): Promise<{ detail: string; is_archived: boolean; archived_at?: string }> {
    const { data } = await apiClient.post(`/contracts/${id}/archive/`)
    return data
  },

  async unarchiveContract(id: string): Promise<{ detail: string; is_archived: boolean }> {
    const { data } = await apiClient.post(`/contracts/${id}/unarchive/`)
    return data
  },
}
