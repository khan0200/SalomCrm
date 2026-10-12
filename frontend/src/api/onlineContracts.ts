import apiClient from './client'

export type IdentityVerificationStatus =
  | 'NOT_STARTED'
  | 'IN_PROGRESS'
  | 'PENDING_REVIEW'
  | 'VERIFIED'
  | 'DECLINED'
  | 'ABANDONED'

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
  canvas_source?: string
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

// ─── Staff-prefilled, token-based signing link flow (contract_sign_views.py) ───
// No account/login - the sign_token in the URL is the sole access key.

export type ContractSignReason = 'ok' | 'not_found' | 'expired' | 'used' | 'locked'

export interface ContractSignStatusResponse {
  reason: ContractSignReason
  detail?: string
  contract_number?: string
  title?: string
  tariff_name?: string
  tariff_price?: number
  discount?: number
  full_name?: string
  office?: string
  education_level?: string
  is_minor_hint?: boolean
  identity_confirmed?: boolean
  kyc_status?: IdentityVerificationStatus
  has_signature?: boolean
  content?: string
  // Already visible verbatim inside `content`'s rendered text - returned
  // again here so canvas_source's {{tokens}} (full_name/office/education_level
  // above resolve the same way) can be fully resolved for the preview.
  passport_number?: string
  date_of_birth?: string
  phone1?: string
  phone2?: string
  // Original canvas-contract JSON (unresolved {{tokens}}), when the tariff
  // was built in the A4 canvas editor - see Contract.canvas_source on the
  // backend. Used for a correctly paginated, true-to-size preview/PDF.
  canvas_source?: string
  verification_code?: string
  guardian_contract_text?: string
  tenant?: {
    id: string
    name: string
    slug: string
    logo_url?: string
    branding_color?: string
  }
}

export interface ConfirmSignIdentityPayload {
  date_of_birth: string
  passport_number: string
}

export interface SubmitSignedContractPayload {
  signature_data: string
  declarations: {
    read_full_contract: boolean
    data_correct: boolean
    informed: boolean
    esignature_consent: boolean
  }
  guardian_full_name?: string
  guardian_passport_number?: string
  guardian_relation?: string
  guardian_phone?: string
  guardian_address?: string
  guardian_signature_data?: string
  guardian_declarations?: {
    read_full_contract: boolean
    data_correct: boolean
    informed: boolean
    esignature_consent: boolean
  }
}

export const onlineContractsApi = {
  // Public verification by code (no auth) - QR code / "check authenticity" link
  async verifyPublicContract(code: string): Promise<PublicContractVerifyResponse> {
    const { data } = await apiClient.get<PublicContractVerifyResponse>(`/contracts/public/${encodeURIComponent(code)}/`)
    return data
  },

  // Staff-prefilled signing link - no auth, token in the URL is the access key.
  async getSignableContract(token: string): Promise<ContractSignStatusResponse> {
    const { data } = await apiClient.get<ContractSignStatusResponse>(`/contracts/sign/${encodeURIComponent(token)}/`)
    return data
  },

  async confirmSignIdentity(token: string, payload: ConfirmSignIdentityPayload): Promise<{ detail: string; identity_confirmed: boolean; attempts_remaining?: number }> {
    const { data } = await apiClient.post(`/contracts/sign/${encodeURIComponent(token)}/confirm-identity/`, payload)
    return data
  },

  async startSignKyc(token: string, documentType: 'PASSPORT' | 'ID_CARD' = 'PASSPORT'): Promise<VerificationStartResponse> {
    const { data } = await apiClient.post(`/contracts/sign/${encodeURIComponent(token)}/kyc/start/`, { document_type: documentType })
    return data
  },

  async getSignKycStatus(token: string): Promise<VerificationStatusResponse> {
    const { data } = await apiClient.get(`/contracts/sign/${encodeURIComponent(token)}/kyc/status/`)
    return data
  },

  async confirmSignKyc(token: string, payload: { full_name: string; document_number: string; date_of_birth: string }): Promise<{ detail: string; status: IdentityVerificationStatus }> {
    const { data } = await apiClient.post(`/contracts/sign/${encodeURIComponent(token)}/kyc/confirm/`, payload)
    return data
  },

  async submitSignedContract(token: string, payload: SubmitSignedContractPayload): Promise<{ detail: string; contract_id: string; status: string; verification_code?: string }> {
    const { data } = await apiClient.post(`/contracts/sign/${encodeURIComponent(token)}/submit/`, payload)
    return data
  },
}
