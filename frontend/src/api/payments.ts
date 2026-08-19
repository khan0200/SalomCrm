import apiClient from './client'
import type { Payment, Student, PaginatedResponse } from '@/types'

export interface PaymentFilterParams {
  page?: number
  page_size?: number
  search?: string
  student_id?: string
  method?: string
  received_by?: string
  is_discount?: boolean
  is_withdrawal?: boolean
}

export interface PaymentOverviewFilterParams {
  page?: number
  page_size?: number
  status?: string
  search?: string
  tariff?: string[]
  group?: string[]
  balance?: string[]
}

export const paymentsApi = {
  getPaymentHistory: async (params: PaymentFilterParams = {}): Promise<PaginatedResponse<Payment>> => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))
    if (params.search) queryParams.set('search', params.search)
    if (params.student_id) queryParams.set('student_id', params.student_id)
    if (params.method && params.method !== 'all') queryParams.set('method', params.method)
    if (params.received_by && params.received_by !== 'all') queryParams.set('received_by', params.received_by)
    if (params.is_discount !== undefined) queryParams.set('is_discount', String(params.is_discount))
    if (params.is_withdrawal !== undefined) queryParams.set('is_withdrawal', String(params.is_withdrawal))

    const response = await apiClient.get(`/payments/?${queryParams.toString()}`)
    return response.data
  },

  getPaymentOverview: async (params: PaymentOverviewFilterParams = {}): Promise<PaginatedResponse<Student>> => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))
    if (params.status) queryParams.set('status', params.status)
    if (params.search) queryParams.set('search', params.search)

    if (params.tariff?.length) params.tariff.forEach(t => queryParams.append('tariff', t))
    if (params.group?.length) params.group.forEach(g => queryParams.append('group', g))
    if (params.balance?.length) params.balance.forEach(b => queryParams.append('balance', b))

    const response = await apiClient.get(`/payment-overview/?${queryParams.toString()}`)
    return response.data
  },

  createPayment: async (data: {
    student_id?: string | null
    amount: number
    method: string
    received_by: string
    notes?: string
    is_discount?: boolean
  }): Promise<Payment> => {
    const response = await apiClient.post('/payments/', data)
    return response.data
  },

  createWithdrawal: async (data: {
    student_id?: string | null
    amount: number
    reason: string
  }): Promise<Payment> => {
    const response = await apiClient.post('/payments/withdraw/', data)
    return response.data
  },

  updatePayment: async (id: string, data: {
    amount: number
    method: string
    received_by: string
    notes?: string
  }): Promise<Payment> => {
    const response = await apiClient.put(`/payments/${id}/`, data)
    return response.data
  },

  deletePayment: async (id: string) => {
    const response = await apiClient.delete(`/payments/${id}/`)
    return response.data
  },

  exportExcel: async () => {
    const response = await apiClient.get('/payments/export/excel/', {
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'salom_crm_payment_history.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
  },
}
