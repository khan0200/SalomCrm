import apiClient from './client'

export interface OnlineTariff {
  id: number | string
  name: string
  price: number
  contract_text?: string
}

export interface OnlineOffice {
  id: number | string
  name: string
  icon?: string
}

export interface OnlineEducationLevel {
  id: number | string
  name: string
}

export interface TenantInfoResponse {
  active: boolean
  id: string
  name: string
  slug: string
  logo_url?: string
  branding_color?: string
  description?: string
  tariffs: OnlineTariff[]
  offices: OnlineOffice[]
  education_levels: OnlineEducationLevel[]
  detail?: string
  guardian_contract_text?: string
}

export interface StudentAuthResponse {
  access: string
  refresh: string
  user: {
    id: string
    email: string
    full_name: string
    role: string
    tenant?: {
      id: string
      name: string
      slug: string
      logo_url?: string
    }
  }
  profile?: {
    passport_number?: string
    date_of_birth?: string
    phone1?: string
    phone2?: string
    education_level?: string
    office?: string
  }
}

export interface OnlineContractSummary {
  id: string
  contract_number: string
  title: string
  status: 'draft' | 'pending' | 'verified' | 'rejected' | 'completed' | 'cancelled'
  tariff_name: string
  tariff_price: number
  discount?: number
  student_id_assigned?: string
  created_at?: string
  signed_at?: string
  verified_at?: string
  rejection_reason?: string
  has_verification_code: boolean
  verification_code_expires_at?: string
  is_code_expired?: boolean
  has_signature: boolean
}

export type IdentityVerificationStatus =
  | 'NOT_STARTED'
  | 'IN_PROGRESS'
  | 'PENDING_REVIEW'
  | 'VERIFIED'
  | 'DECLINED'
  | 'ABANDONED'

export interface StudentProfileResponse {
  user: {
    id: string
    email: string
    full_name: string
  }
  profile: {
    passport_number: string
    date_of_birth: string
    phone1: string
    phone2: string
    education_level: string
    office: string
  }
  contracts: OnlineContractSummary[]
  is_identity_verified: boolean
  verification_status: IdentityVerificationStatus
}

export interface VerificationStartResponse {
  session_id: string
  url: string
  status: IdentityVerificationStatus
}

export interface VerificationStatusResponse {
  status: IdentityVerificationStatus
  document_type?: 'PASSPORT' | 'ID_CARD'
  extracted?: {
    full_name: string
    document_number: string
    date_of_birth: string
  }
}

export interface SubmitContractPayload {
  tariff_id: number | string
  passport_number: string
  full_name: string
  education_level: string
  date_of_birth: string
  office: string
  phone1: string
  phone2: string
  email?: string
  signature_data: string
  declarations: {
    read_full_contract: boolean
    voluntary_sign: boolean
    confirmation_code_meaning: boolean
  }
  password: string
  // Required only when the student is under 18 at signing time (Fuqarolik
  // kodeksi 27-modda) - omitted entirely for adult students.
  guardian_full_name?: string
  guardian_passport_number?: string
  guardian_relation?: string
  guardian_phone?: string
  guardian_address?: string
  guardian_signature_data?: string
}

export interface PublicContractVerifyResponse {
  status: 'draft' | 'pending' | 'verified' | 'rejected' | 'completed' | 'cancelled'
  contract_number: string
  title: string
  tariff_name: string
  tariff_price: number
  discount?: number
  full_name: string
  passport_number: string
  education_level: string
  date_of_birth: string
  office: string
  phone1: string
  phone2: string
  signature_data: string
  is_minor?: boolean
  guardian_full_name?: string
  guardian_passport_number?: string
  guardian_relation?: string
  guardian_phone?: string
  guardian_address?: string
  guardian_signature_data?: string
  guardian_contract_text?: string
  content: string
  verification_code: string
  verified_at?: string
  signed_at?: string
  created_at?: string
  contract_hash?: string
  tenant: {
    id: string
    name: string
    slug: string
    logo_url?: string
  }
}

export interface ContractDetailOnlineResponse {
  id: string
  contract_number: string
  title: string
  status: 'draft' | 'pending' | 'verified' | 'rejected' | 'completed' | 'cancelled'
  tariff_id?: number | string
  tariff_name: string
  tariff_price: number
  discount?: number
  email?: string
  passport_number: string
  full_name: string
  education_level: string
  date_of_birth: string
  office: string
  phone1: string
  phone2: string
  signature_data: string
  is_minor?: boolean
  guardian_full_name?: string
  guardian_passport_number?: string
  guardian_relation?: string
  guardian_phone?: string
  guardian_address?: string
  guardian_signature_data?: string
  guardian_contract_text?: string
  content: string
  student_id_assigned?: string
  has_verification_code: boolean
  verification_code?: string
  verification_code_expires_at?: string
  verified_at?: string
  rejection_reason?: string
  created_at?: string
  signed_at?: string
  contract_hash?: string
  tenant: {
    id: string
    name: string
    slug: string
    logo_url?: string
  }
}

export const onlineContractsApi = {
  // 1. Get Tenant Public Info & Catalog
  async getTenantInfo(slug: string): Promise<TenantInfoResponse> {
    const { data } = await apiClient.get<TenantInfoResponse>(`/contracts/online/tenant-info/${slug}/`)
    return data
  },

  // 1b. Get one tariff's full contract text, on demand (deliberately not
  // included in getTenantInfo's tariff list - see backend TenantInfoView).
  async getTariffContractText(tariffId: string | number): Promise<{ id: number; contract_text: string }> {
    const { data } = await apiClient.get(`/contracts/online/tariff-contract-text/${tariffId}/`)
    return data
  },

  // 2. Request Email OTP
  async sendOtp(email: string, tenant_slug: string): Promise<{ detail: string; expires_in_seconds: number }> {
    const { data } = await apiClient.post('/contracts/online/send-otp/', { email, tenant_slug })
    return data
  },

  // 3. Verify OTP & Complete Sign Up
  async signUp(payload: { full_name: string; email: string; password: string; code: string; tenant_slug: string }): Promise<StudentAuthResponse> {
    const { data } = await apiClient.post<StudentAuthResponse>('/contracts/online/sign-up/', payload)
    return data
  },

  // 4. Student Sign In
  async signIn(payload: { email: string; password: string; tenant_slug?: string }): Promise<StudentAuthResponse> {
    const { data } = await apiClient.post<StudentAuthResponse>('/contracts/online/sign-in/', payload)
    return data
  },

  // 5. Get Student Profile & Shartnomalarim
  async getProfile(): Promise<StudentProfileResponse> {
    const { data } = await apiClient.get<StudentProfileResponse>('/contracts/online/profile/')
    return data
  },

  // 6. Update Student Profile
  async updateProfile(payload: Partial<StudentProfileResponse['profile']> & { full_name?: string }): Promise<any> {
    const { data } = await apiClient.patch('/contracts/online/profile/', payload)
    return data
  },

  // 6b. Identity Verification (Didit KYC) - required before a student's
  // first contract can be created.
  async startVerification(documentType: 'PASSPORT' | 'ID_CARD'): Promise<VerificationStartResponse> {
    const { data } = await apiClient.post('/contracts/online/verification/start/', { document_type: documentType })
    return data
  },

  async getVerificationStatus(): Promise<VerificationStatusResponse> {
    const { data } = await apiClient.get('/contracts/online/verification/status/')
    return data
  },

  async confirmVerification(payload: { full_name: string; document_number: string; date_of_birth: string }): Promise<{ detail: string; status: IdentityVerificationStatus }> {
    const { data } = await apiClient.post('/contracts/online/verification/confirm/', payload)
    return data
  },

  // 6c. Permanently delete the student's own login account. Submitted
  // contracts are unaffected - see DeleteProfileView docstring.
  async deleteProfile(payload: { full_name: string; password: string }): Promise<{ detail: string }> {
    const { data } = await apiClient.post('/contracts/online/profile/delete/', payload)
    return data
  },

  // 7. Submit & Sign Contract
  async submitContract(payload: SubmitContractPayload): Promise<{
    detail: string
    contract_id: string
    contract_number: string
    status: string
    created_at: string
  }> {
    const { data } = await apiClient.post('/contracts/online/submit-contract/', payload)
    return data
  },

  // 8. Get Detailed Contract for Student View/Sign
  async getContractDetail(contractId: string): Promise<ContractDetailOnlineResponse> {
    const { data } = await apiClient.get<ContractDetailOnlineResponse>(`/contracts/online/${contractId}/detail/`)
    return data
  },

  // 9. Student Final Verification
  async verifyContract(contractId: string, payload: { code: string; password: string }): Promise<{
    detail: string
    status: string
    contract_number: string
    student_id: string
    verified_at: string
  }> {
    const { data } = await apiClient.post(`/contracts/online/${contractId}/verify-code/`, payload)
    return data
  },

  // 10. Resubmit Rejected Contract
  async resubmitContract(contractId: string, payload: any): Promise<{ detail: string; status: string }> {
    const { data } = await apiClient.post(`/contracts/online/${contractId}/resubmit/`, payload)
    return data
  },

  // 11. Audit log full contract viewed
  async logContractViewAudit(contractId: string): Promise<void> {
    await apiClient.post(`/contracts/online/${contractId}/audit-view/`)
  },

  // 12. Cancel pending contract
  async cancelContract(contractId: string, reason?: string): Promise<{ detail: string; status: string }> {
    const { data } = await apiClient.post(`/contracts/online/${contractId}/cancel/`, { reason })
    return data
  },

  // 13. Public verification by code (no auth) - QR code / "check authenticity" link
  async verifyPublicContract(code: string): Promise<PublicContractVerifyResponse> {
    const { data } = await apiClient.get<PublicContractVerifyResponse>(`/contracts/public/${encodeURIComponent(code)}/`)
    return data
  },
}
