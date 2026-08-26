export type UserRole = 'SUPER_ADMIN' | 'HEAD_MANAGER' | 'MANAGER' | 'STAFF'

export interface Tenant {
  id: string
  name: string
  slug: string
  is_active: boolean
  logo_url?: string | null
  description?: string | null
  settings?: {
    telegram_bot_token?: string
    telegram_chat_id?: string
    [key: string]: unknown
  } | null
  user_count?: number
  student_count?: number
  created_at: string
}

export interface Branch {
  id: string
  name: string
  code?: string | null
  address?: string | null
  phone?: string | null
  is_active: boolean
}

export interface UserProfile {
  id: string
  email: string
  full_name: string
  role: UserRole
  avatar_url?: string | null
  phone?: string | null
  telegram_id?: string | null
  telegram_username?: string | null
  is_superuser: boolean
  tenant?: Tenant | null
  branch?: Branch | null
}

export type StudentLevel = 'COLLEGE' | 'BACHELOR' | 'MASTERS' | 'MASTER NO CERTIFICATE' | 'LANGUAGE COURSE'
export type StudentTariff = 'STANDART' | 'PREMIUM' | 'VISA PLUS' | 'E-VISA' | 'REGIONAL VISA' | 'ZERO RISK'
export type StudentLanguageCertificate = 'TOPIK' | 'IELTS' | 'TOEFL' | 'CEFR' | 'SAT' | 'SKA' | 'NO CERTIFICATE'

export interface Folder {
  id: string
  name: string
  student_count?: number
  created_at?: string
}

export interface Student {
  id: string
  full_name: string
  korean_name?: string | null
  passport?: string | null
  passport_issue_date?: string | null
  passport_expire_date?: string | null
  gender?: 'MALE' | 'FEMALE' | null
  birthday?: string | null
  phone1?: string | null
  phone2?: string | null
  father_name?: string | null
  father_phone?: string | null
  father_job?: string | null
  mother_name?: string | null
  mother_phone?: string | null
  mother_job?: string | null
  email?: string | null
  address?: string | null

  // Education
  level?: StudentLevel | null
  level2?: StudentLevel | null
  educational_background?: string | null
  major?: string | null
  final_school_name?: string | null
  gpa?: string | null
  gpa_system?: string | null
  degree_no?: string | null
  date_of_entry?: string | null
  date_of_graduation?: string | null
  graduation_expected?: boolean
  school_address?: string | null
  school_website?: string | null
  school_phone?: string | null
  school_email?: string | null
  tariff?: StudentTariff | string | null

  // Language Certificates
  language_certificate?: StudentLanguageCertificate | string | null
  certificate_score?: string | null
  certificate_test_date?: string | null
  certificate_valid_date?: string | null

  language_certificate_2?: StudentLanguageCertificate | string | null
  certificate_score_2?: string | null
  certificate_2_test_date?: string | null
  certificate_2_valid_date?: string | null

  language_certificate_3?: StudentLanguageCertificate | string | null
  certificate_score_3?: string | null
  certificate_3_test_date?: string | null
  certificate_3_valid_date?: string | null

  // Universities (1 to 5)
  university_1?: string | null
  university_1_status?: string
  university_1_major?: string | null
  university_2?: string | null
  university_2_status?: string | null
  university_2_major?: string | null
  university_3?: string | null
  university_3_status?: string | null
  university_3_major?: string | null
  university_4?: string | null
  university_4_status?: string | null
  university_4_major?: string | null
  university_5?: string | null
  university_5_status?: string | null
  university_5_major?: string | null

  // Financial
  balance: number
  discount: number
  invoice_sum?: number
  payments_sum?: number

  // Documents Checklist & Hand counts
  pick_needed?: string[]
  has_mc?: boolean
  bc_hand_count?: number
  mc_hand_count?: number
  apos_hand_count?: number
  pic_hand_count?: number

  // Status board & Embassy
  invoice?: string | null
  invoice_university?: string | null
  coa?: string | null
  embassy?: string | null
  embassy_documents?: string[]
  status_hidden?: boolean
  kdb_put_date?: string | null
  kdb_take_date?: string | null
  days_left?: number | null
  urgency?: 'OVERDUE' | 'CRITICAL' | 'URGENT' | 'NORMAL' | null
  embassy_father_docs?: string[]
  embassy_mother_docs?: string[]
  embassy_sponsor_notes?: string | null
  status_row_color?: string | null
  folders?: { id: string; name: string }[]
  folder_names?: string[]

  // Management Metadata
  office?: string | null
  student_group?: string | null
  lead_by?: string | null
  coordinator?: string | null
  notes?: string | null
  is_deleted?: boolean
  row_color?: string | null
  task_tags?: string[]
  my_row_color?: string | null
  my_task_tags?: string[]
  folder_ids?: string[]
  google_drive_url?: string | null
  google_drive_folder_id?: string | null
  created_at?: string
  updated_at?: string
  creator_name?: string | null
}

export interface Payment {
  id: string
  student_id?: string | null
  student_full_name?: string | null
  student_name?: string | null
  amount: number
  method: string
  received_by: string
  notes?: string | null
  is_discount: boolean
  is_withdrawal: boolean
  created_by_name?: string | null
  created_at: string
}

export interface PaginatedResponse<T> {
  count: number
  total_pages: number
  current_page: number
  page_size: number
  next: string | null
  previous: string | null
  results: T[]
}

export const ROW_COLOR_MAP: Record<string, { bg: string; ball: string; name: string }> = {
  BLUE: { bg: '#86bcf6', ball: '#2563EB', name: 'Blue' },
  EMERALD: { bg: '#58d39f', ball: '#10B981', name: 'Emerald' },
  RED: { bg: '#fa8c8c', ball: '#EF4444', name: 'Red' },
  VIOLET: { bg: '#b79df8', ball: '#8B5CF6', name: 'Violet' },
  ORANGE: { bg: '#fba557', ball: '#F97316', name: 'Orange' },
  YELLOW: { bg: '#fad338', ball: '#EAB308', name: 'Yellow' },
  CYAN: { bg: '#5ecef8', ball: '#06B6D4', name: 'Cyan' },
  SLATE: { bg: '#b2c0d2', ball: '#64748B', name: 'Slate' }
}
