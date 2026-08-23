<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { settingsApi } from '@/api/settings'
import { paymentsApi } from '@/api/payments'
import { getTariffPrice } from '@/utils/tariff'
import type { Student, Payment } from '@/types'
import { useCurrency } from '@/composables/useCurrency'
import { useUniversityStatuses } from '@/composables/useUniversityStatuses'
import { UNIVERSITY_SUGGESTIONS, BUILTIN_SCHOOL_DIRECTORY, UZ_MAJOR_SUGGESTIONS, type SchoolEntry } from '@/data/schoolsData'
import {
  User, Mail, Calendar, GraduationCap, Layers, Landmark,
  Tag, Building2, CheckSquare, Plus, Pencil, CheckCircle2,
  Trash2, RefreshCw, X, Maximize2, Minimize2, Copy,
  Check, ChevronDown, Folder, ExternalLink, AlertTriangle, AlertCircle,
  BookOpen, ArrowLeft, FileText, Eraser, Loader2, ArrowDownCircle
} from 'lucide-vue-next'

const router = useRouter()

const props = defineProps<{
  isOpen: boolean
  student: Student | null
  options?: any
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update-student', data: Partial<Student>): void
  (e: 'archive'): void
  (e: 'restore'): void
  (e: 'permanent-delete'): void
  (e: 'open-add-payment', studentId: string): void
}>()

const navigateToExtract = () => {
  if (props.student) {
    router.push(`/students/${props.student.id}/extract`)
  }
}

const { formatCurrency } = useCurrency()

// Drawer fullscreen state - Expanded by default
const isExpanded = ref(true)
const copiedField = ref<string | null>(null)

// Name Language Mode
const nameLanguage = ref<'EN' | 'KR'>('EN')

// Accordion Collapsible States - matching UniApp2
const expandedSection = ref<'contact' | 'education' | null>(null)
const contactExpanded = computed(() => expandedSection.value === 'contact')
const eduExpanded = computed(() => expandedSection.value === 'education')

const toggleSection = (sec: 'contact' | 'education') => {
  expandedSection.value = expandedSection.value === sec ? null : sec
}

// Slot Visibility States
const showLevel2 = ref(false)
const showCert2 = ref(false)
const showCert3 = ref(false)
const showUni2 = ref(false)
const showUni3 = ref(false)
const showUni4 = ref(false)
const showUni5 = ref(false)

// Inline Editing State
const editingField = ref<string | null>(null)
const editValue = ref<any>('')

// University Status Dropdown Popover state
const activeStatusDropdown = ref<number | null>(null)

// Major Editing Modal State (Write Selected Major)
const isMajorModalOpen = ref(false)
const majorModalSlot = ref<number>(1)
const tempMajorValue = ref('')
const savingMajor = ref(false)

// University Edit Modal State
const isUniModalOpen = ref(false)
const uniModalSlot = ref<number>(1)
const tempUniName = ref('')
const tempUniStatus = ref('')
const tempUniMajor = ref('')

// School Modal State
const isSchoolModalOpen = ref(false)
const schoolForm = ref<Record<string, any>>({})

// Certificate Modal State
const isCertModalOpen = ref(false)
const certModalSlot = ref<1 | 2 | 3>(1)
const certForm = ref({
  type: '',
  score: '',
  test_date: '',
  valid_date: ''
})

// Google Drive Modal State
const isDriveModalOpen = ref(false)
const driveUrlInput = ref('')

// Permanent Delete Confirm State
const isPermanentConfirmOpen = ref(false)

// Phone & Passport Formatters
const phoneFields = new Set(['phone1', 'phone2', 'father_phone', 'mother_phone', 'school_phone'])

const formatPhoneValue = (value?: string | null) => {
  if (!value) return ''
  const digits = value.replace(/\D/g, '').slice(0, 9)
  const first = digits.slice(0, 2)
  const second = digits.slice(2, 5)
  const third = digits.slice(5, 7)
  const fourth = digits.slice(7, 9)
  return [first, second, third, fourth].filter(Boolean).join('-')
}

const formatSchoolPhone = (value?: string | null): string => {
  if (!value) return ''
  const trimmed = value.trim()
  if (!trimmed) return ''

  // If already starts with '+'
  if (trimmed.startsWith('+')) {
    // If it starts with +998 and is 12 continuous digits, format with clean spaces
    const digitsOnly = trimmed.replace(/\D/g, '')
    if (digitsOnly.startsWith('998') && digitsOnly.length === 12 && !trimmed.includes(' ')) {
      return `+998 ${digitsOnly.slice(3, 5)} ${digitsOnly.slice(5, 8)} ${digitsOnly.slice(8, 10)} ${digitsOnly.slice(10, 12)}`
    }
    return trimmed
  }

  // Strip all non-digit characters
  const digits = trimmed.replace(/\D/g, '')
  if (!digits) return trimmed

  // 12 digits starting with 998: e.g. 998742000025 -> +998 74 200 00 25
  if (digits.startsWith('998') && digits.length === 12) {
    return `+998 ${digits.slice(3, 5)} ${digits.slice(5, 8)} ${digits.slice(8, 10)} ${digits.slice(10, 12)}`
  }

  // 9 digits (Uzbek local number): e.g. 742000025 -> +998 74 200 00 25
  if (digits.length === 9) {
    return `+998 ${digits.slice(0, 2)} ${digits.slice(2, 5)} ${digits.slice(5, 7)} ${digits.slice(7, 9)}`
  }

  // If it starts with 998 but unexpected length: +998...
  if (digits.startsWith('998')) {
    return `+${digits}`
  }

  // Otherwise prefix with +998
  return `+998 ${trimmed}`
}

const formatPassportValue = (value?: string | null) => {
  if (!value) return ''
  const clean = value.toUpperCase().replace(/[^A-Z0-9]/g, '')
  const letters = clean.replace(/[^A-Z]/g, '').slice(0, 2)
  const digits = clean.replace(/\D/g, '').slice(0, 7)
  return `${letters}${digits}`
}

const formatEditValueForField = (field: string, value: string) => {
  if (phoneFields.has(field)) return formatPhoneValue(value)
  if (field === 'passport') return formatPassportValue(value)
  return value
}

const onInlineInput = (field: string, event: Event) => {
  const target = event.target as HTMLInputElement
  if (target) {
    editValue.value = formatEditValueForField(field, target.value)
  }
}

// Major Suggestions List (from UniApp2)
const MAJOR_SUGGESTIONS = [
  "Business Administration",
  "International Business",
  "Economics",
  "Accounting",
  "Finance",
  "Marketing",
  "Hospitality & Tourism Management",
  "Hotel Management",
  "Tourism Management",
  "Global Business",
  "International Trade",
  "International Studies",
  "Korean Language & Literature",
  "Korean Language Education",
  "Media & Communication",
  "Journalism",
  "Artificial Intelligence",
  "Computer Science",
  "Software Engineering",
  "Computer Engineering",
  "Information Technology (IT)",
  "Data Science",
  "Cyber Security",
  "Electrical Engineering",
  "Electronic Engineering",
  "Mechanical Engineering",
  "Civil Engineering",
  "Industrial Engineering",
  "Automotive Engineering",
  "Naval Architecture & Marine Engineering",
  "SHIP BUILDING",
  "Marine Power Machinery Engineering",
  "Architecture",
  "Biotechnology",
  "Biomedical Engineering",
  "Nursing",
  "Pharmacy",
  "Fashion Design",
  "Beauty & Cosmetology",
  "Animation & Game Design",
  "Visual Design",
  "Music & Performing Arts",
  "Korean Tourism Service Department"
]

const showUniMajorSuggestions = ref(false)

const filteredUniMajorSuggestions = computed(() => {
  if (!showUniMajorSuggestions.value) return []
  const query = tempMajorValue.value.toLowerCase().trim()
  if (query.length < 3) return []
  const unique = Array.from(new Set(MAJOR_SUGGESTIONS.map(s => s.trim())))
  const list = unique.filter(s => s.toLowerCase().includes(query)).slice(0, 15)
  if (list.length === 1 && list[0].toLowerCase() === query) return []
  return list
})

const selectUniMajorSuggestion = (sug: string) => {
  tempMajorValue.value = sug.toUpperCase()
  showUniMajorSuggestions.value = false
}

const onUniMajorInput = () => {
  showUniMajorSuggestions.value = tempMajorValue.value.trim().length >= 3
}

const testDateYears = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i)

// Dynamic University Statuses & Colors from Settings / DB
const {
  statusesRegistry: universityStatusList,
  fetchStatuses: fetchUniversityStatuses,
  getStatusDotClass,
  getStatusBadgeClass: getUniStatusBadgeClass
} = useUniversityStatuses()

// Helper: Initials
const getInitials = (name?: string | null) => {
  if (!name) return 'ST'
  const parts = name.trim().split(' ')
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

// Helper: Registration Date Formatting
const formatRegistrationDate = (dateStr?: string | null) => {
  if (!dateStr) return '—'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    const day = String(d.getDate()).padStart(2, '0')
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const year = d.getFullYear()
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    return `${day}.${month}.${year} ${hours}:${minutes}`
  } catch {
    return dateStr
  }
}

// Synchronize state when student changes - only show slots if actually provided
watch(() => props.student, (s) => {
  if (s) {
    isExpanded.value = true
    showLevel2.value = !!(s.level2 && s.level2.trim())
    showCert2.value = !!(s.language_certificate_2 && s.language_certificate_2.trim() && s.language_certificate_2 !== 'NO CERTIFICATE')
    showCert3.value = !!(s.language_certificate_3 && s.language_certificate_3.trim() && s.language_certificate_3 !== 'NO CERTIFICATE')
    showUni2.value = !!(s.university_2 && s.university_2.trim())
    showUni3.value = !!(s.university_3 && s.university_3.trim())
    showUni4.value = !!(s.university_4 && s.university_4.trim())
    showUni5.value = !!(s.university_5 && s.university_5.trim())
    editingField.value = null
    activeStatusDropdown.value = null
  } else {
    showLevel2.value = false
    showCert2.value = false
    showCert3.value = false
    showUni2.value = false
    showUni3.value = false
    showUni4.value = false
    showUni5.value = false
  }
}, { immediate: true })

watch(() => props.isOpen, (open) => {
  if (open) {
    isExpanded.value = true
  }
})

// 1-Click Copy Handler
const handleCopy = (fieldKey: string, text?: string | null) => {
  if (!text || text === 'Not provided' || text === '—') return
  navigator.clipboard.writeText(String(text).trim())
  copiedField.value = fieldKey
  setTimeout(() => {
    if (copiedField.value === fieldKey) copiedField.value = null
  }, 1600)
}

// Inline Edit Handlers
const startInlineEdit = (field: string, val: any) => {
  editingField.value = field
  editValue.value = val ? formatEditValueForField(field, String(val)) : ''
}

const cancelInlineEdit = () => {
  editingField.value = null
  editValue.value = ''
}

const saveInlineEdit = (field: string) => {
  if (!props.student) return
  emit('update-student', { [field]: editValue.value })
  editingField.value = null
}

// Global Keydown Handler (Esc to close sub-modals, inline edits, and drawer)
const handleGlobalKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) {
    // 1. If currently inline-editing, cancel inline edit
    if (editingField.value !== null) {
      cancelInlineEdit()
      return
    }
    // 2. If status dropdown popover is open, close it
    if (activeStatusDropdown.value !== null) {
      activeStatusDropdown.value = null
      return
    }
    // 3. If any sub-modal is open, close that sub-modal
    if (isUniModalOpen.value) {
      closeUniversityModal()
      return
    }
    if (isCertModalOpen.value) {
      closeCertModal()
      return
    }
    if (isMajorModalOpen.value) {
      isMajorModalOpen.value = false
      return
    }
    if (isSchoolModalOpen.value) {
      isSchoolModalOpen.value = false
      return
    }
    if (isDriveModalOpen.value) {
      isDriveModalOpen.value = false
      return
    }
    if (isPermanentConfirmOpen.value) {
      isPermanentConfirmOpen.value = false
      return
    }
    // 4. Otherwise, close the drawer itself
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeyDown)
  fetchUniversityStatuses()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeyDown)
})

// Student Payments Query (Fetching live payments history for student)
const studentId = computed(() => props.student?.id)

const { data: studentPaymentsData, isLoading: isPaymentsLoading } = useQuery({
  queryKey: ['student-payments', studentId],
  queryFn: () => paymentsApi.getPaymentHistory({ student_id: studentId.value, page_size: 100 }),
  enabled: computed(() => !!studentId.value && props.isOpen),
  staleTime: 1000 * 30,
})

const studentPayments = computed<Payment[]>(() => {
  return studentPaymentsData.value?.results || []
})

// Financial Calculations matching UniApp2
const computedTariffPrice = computed(() => {
  return getTariffPrice(
    props.student?.tariff,
    props.student?.language_certificate,
    props.options?.tariffs || []
  )
})

const computedPaymentsDone = computed(() => {
  // Only standard payments (non-discount, non-withdrawal)
  if (studentPayments.value && studentPayments.value.length > 0) {
    return studentPayments.value
      .filter(p => !p.is_discount && !p.is_withdrawal)
      .reduce((sum, p) => sum + (Number(p.amount) || 0), 0)
  }
  // Instant 0ms fallback while payments query is in-flight
  if (props.student?.balance !== undefined && props.student?.tariff) {
    const tariffVal = computedTariffPrice.value
    const balVal = Number(props.student.balance || 0)
    const discVal = Number(props.student.discount || 0)
    const estPaid = (balVal + tariffVal) - discVal
    if (estPaid >= 0) return estPaid
  }
  return Number((props.student as any)?.payments_sum || (props.student as any)?.total_paid || 0)
})

const computedDiscount = computed(() => {
  if (studentPayments.value && studentPayments.value.length > 0) {
    const fromPayments = studentPayments.value
      .filter(p => p.is_discount && Number(p.amount) > 0)
      .reduce((sum, p) => sum + Number(p.amount), 0)
    if (fromPayments > 0) return fromPayments
  }
  return Number(props.student?.discount || 0)
})

const computedWithdrawals = computed(() => {
  if (studentPayments.value && studentPayments.value.length > 0) {
    return studentPayments.value
      .filter(p => p.is_withdrawal)
      .reduce((sum, p) => sum + Math.abs(Number(p.amount) || 0), 0)
  }
  return 0
})

const computedBalance = computed(() => {
  // If Tariff is not set: fallback to student.balance
  if (!props.student?.tariff || props.student.tariff === 'Select' || props.student.tariff === '—') {
    return Number(props.student?.balance || 0)
  }
  // BALANCE = (PAYMENTS_DONE + DISCOUNT) - TARIFF_PRICE - WITHDRAWALS
  const balance = (computedPaymentsDone.value + computedDiscount.value) - computedTariffPrice.value - computedWithdrawals.value
  return Math.abs(balance) < 0.01 ? 0 : balance
})

// University Data from Settings
const { data: settingsUniversitiesData } = useQuery({
  queryKey: ['settings-universities'],
  queryFn: () => settingsApi.getUniversities(),
  staleTime: 1000 * 60 * 5,
})

const FALLBACK_UNIVERSITIES = [
  "KONKUK UNIVERSITY (GWANGJIN, SEOUL)",
  "SEJONG UNIVERSITY (GWANGJIN, SEOUL)",
  "KOOKMIN UNIVERSITY (SEONGBUK, SEOUL)",
  "GACHON UNIVERSITY (GLOBAL CAMPUS, SEONGNAM)",
  "HANYANG UNIVERSITY (ERICA CAMPUS, ANSAN)",
  "CHUNG-ANG UNIVERSITY (SEOUL CAMPUS)",
  "DONGGUK UNIVERSITY (SEOUL CAMPUS)",
  "INHA UNIVERSITY (INCHEON)",
  "INCHEON NATIONAL UNIVERSITY (INCHEON)",
  "KYUNG HEE UNIVERSITY (SEOUL/GLOBAL)",
  "WOOSUK UNIVERSITY (WANJU / JINCHEON)",
  "JEONJU UNIVERSITY (JEONJU)",
  "SUN MOON UNIVERSITY (ASAN)",
  "YEUNGNAM UNIVERSITY (GYEONGSAN)",
  "KYUNGPOOK NATIONAL UNIVERSITY (DAEGU)",
  "PUSAN NATIONAL UNIVERSITY (BUSAN)",
  "DONG-A UNIVERSITY (BUSAN)",
  "KYUNGSUNG UNIVERSITY (BUSAN)",
  "HONGIK UNIVERSITY (SEOUL)",
  "SOONGSIL UNIVERSITY (SEOUL)",
  "AJOU UNIVERSITY (SUWON)",
  "DANKOOK UNIVERSITY (JUKJEON)",
  "MYONGJI UNIVERSITY (SEOUL / YONGIN)",
  "SANGMYUNG UNIVERSITY (SEOUL)",
  "HANSUNG UNIVERSITY (SEOUL)",
  "SEOKYEONG UNIVERSITY (SEOUL)",
  "CHUNGBUK NATIONAL UNIVERSITY (CHEONGJU)",
  "CHONNAM NATIONAL UNIVERSITY (GWANGJU)",
  "CHONBUK NATIONAL UNIVERSITY (JEONJU)",
  "KANGWON NATIONAL UNIVERSITY (CHUNCHEON)",
  "JEJU NATIONAL UNIVERSITY (JEJU)"
]

const allUniversities = computed<string[]>(() => {
  const set = new Set<string>()

  // From props.options.universities
  if (Array.isArray(props.options?.universities)) {
    props.options.universities.forEach((u: any) => {
      if (typeof u === 'string' && u.trim()) set.add(u.trim().toUpperCase())
      else if (u && typeof u === 'object' && 'name' in u && (u as any).name) {
        set.add(String((u as any).name).trim().toUpperCase())
      }
    })
  }

  // From settingsApi.getUniversities()
  const rawSettings = settingsUniversitiesData.value as Array<any> | undefined
  if (Array.isArray(rawSettings)) {
    rawSettings.forEach(u => {
      if (u && typeof u === 'object' && 'name' in u && u.name) {
        set.add(String(u.name).trim().toUpperCase())
      } else if (typeof u === 'string' && (u as string).trim()) {
        set.add((u as string).trim().toUpperCase())
      }
    })
  }

  // Add fallback partner universities
  FALLBACK_UNIVERSITIES.forEach(u => set.add(u.toUpperCase()))

  return Array.from(set).sort((a, b) => a.localeCompare(b))
})

const showUniSuggestions = ref(false)

const filteredUniSuggestions = computed(() => {
  if (!showUniSuggestions.value) return []
  const query = tempUniName.value.trim().toLowerCase()
  if (query.length < 3) return []
  const list = allUniversities.value.filter(u => u.toLowerCase().includes(query)).slice(0, 15)
  if (list.length === 1 && list[0].toLowerCase() === query) return []
  return list
})

const selectUniSuggestion = (sug: string) => {
  tempUniName.value = sug.toUpperCase()
  showUniSuggestions.value = false
}

const onUniInput = () => {
  showUniSuggestions.value = tempUniName.value.trim().length >= 3
}

// Option lists
const tariffOptions = computed(() => (props.options?.tariffs || []).map((t: any) => typeof t === 'string' ? t : t.name))
const levelOptions = computed(() => props.options?.levels || ['COLLEGE', 'BACHELOR', 'MASTERS', 'MASTER NO CERTIFICATE', 'LANGUAGE COURSE'])
const groupOptions = computed(() => props.options?.groups || [])
const leadByOptions = computed(() => props.options?.leads || [])
const coordinatorOptions = computed(() => props.options?.coordinators || [])
const universityOptions = computed(() => allUniversities.value)
const officeOptions = computed(() => props.options?.offices || ['ANDIJON OFFIS', 'TOSHKENT OFFIS'])

// Major Modal Handlers
const openMajorModal = (slot: number) => {
  if (!props.student) return
  activeStatusDropdown.value = null
  majorModalSlot.value = slot
  const current = (props.student as any)[`university_${slot}_major`] || ''
  tempMajorValue.value = current
  showMajorSuggestions.value = false
  isMajorModalOpen.value = true
}

const saveMajorModal = async () => {
  if (!props.student) return
  savingMajor.value = true
  try {
    const slot = majorModalSlot.value
    const patch: Record<string, any> = {}
    patch[`university_${slot}_major`] = tempMajorValue.value.trim() ? tempMajorValue.value.trim().toUpperCase() : null
    emit('update-student', patch)
    isMajorModalOpen.value = false
  } finally {
    savingMajor.value = false
  }
}

// University Status Popover Handler
const handleStatusSelect = (slot: number, newStatus: string) => {
  const patch: Record<string, any> = {}
  patch[`university_${slot}_status`] = newStatus
  emit('update-student', patch)
  activeStatusDropdown.value = null
}

// Clear University Slot Handler (with Confirmation)
const clearUniversitySlot = (slot: number) => {
  if (!window.confirm('Clear this university selection?')) return
  const patch: Record<string, any> = {}
  patch[`university_${slot}`] = null
  patch[`university_${slot}_status`] = ''
  patch[`university_${slot}_major`] = null
  emit('update-student', patch)
}

// University Edit Modal Handlers (Show ONLY University Name with live suggestions)
const openUniversityModal = (slot: number) => {
  if (!props.student) return
  activeStatusDropdown.value = null
  uniModalSlot.value = slot
  const s = props.student as any
  tempUniName.value = s[`university_${slot}`] || ''
  showUniSuggestions.value = false
  isUniModalOpen.value = true
}

const closeUniversityModal = () => {
  const slot = uniModalSlot.value
  const s = props.student as any
  if (slot === 2 && !s?.university_2) showUni2.value = false
  if (slot === 3 && !s?.university_3) showUni3.value = false
  if (slot === 4 && !s?.university_4) showUni4.value = false
  if (slot === 5 && !s?.university_5) showUni5.value = false
  isUniModalOpen.value = false
}

const closeCertModal = () => {
  const slot = certModalSlot.value
  const s = props.student as any
  if (slot === 2 && (!s?.language_certificate_2 || s?.language_certificate_2 === 'NO CERTIFICATE')) showCert2.value = false
  if (slot === 3 && (!s?.language_certificate_3 || s?.language_certificate_3 === 'NO CERTIFICATE')) showCert3.value = false
  isCertModalOpen.value = false
}

const saveUniversityModal = () => {
  if (!props.student) return
  const slot = uniModalSlot.value
  const patch: Record<string, any> = {}
  const val = tempUniName.value.trim() ? tempUniName.value.trim().toUpperCase() : null
  patch[`university_${slot}`] = val
  // If assigning a university and status is currently empty, default to Chosen
  const currentStatus = (props.student as any)[`university_${slot}_status`]
  if (val && !currentStatus) {
    patch[`university_${slot}_status`] = 'Chosen'
  }
  emit('update-student', patch)
  if (!val && slot >= 2) {
    if (slot === 2) showUni2.value = false
    if (slot === 3) showUni3.value = false
    if (slot === 4) showUni4.value = false
    if (slot === 5) showUni5.value = false
  }
  isUniModalOpen.value = false
}// ═════════════════════════════════════════════════════════════
// Educational Background Modal (100% UniApp2 UX & Behavior)
// ═════════════════════════════════════════════════════════════
const gpaSystemManual = ref(false)
const gradExpected = ref(false)
const showSchoolSuggestions = ref(false)
const showMajorSuggestions = ref(false)
const savingSchool = ref(false)

const EXPECTED_YEAR = 'EXPECTED'
const ENTRY_MONTH = '09'
const ENTRY_DAY = '02'
const GRADUATION_MONTH = '07'
const GRADUATION_DAY = '20'
const DEFAULT_COURSE_YEARS = 4
const GPA_SYSTEM_OPTIONS = ['4', '4.5', '5', '100', 'MANUAL ENTRY']

const normalizeSuggestion = (s: string) =>
  (s || '').toUpperCase().replace(/[ʻʼʽ‘’'`]/g, '').replace(/\s+/g, ' ').trim()

const dedupeSuggestions = (values: (string | null | undefined)[], builtIn: string[]) => {
  const known = new Set(builtIn.map(normalizeSuggestion))
  const out: string[] = []
  for (const raw of values) {
    const value = (raw || '').trim()
    if (!value) continue
    const key = normalizeSuggestion(value)
    if (known.has(key)) continue
    known.add(key)
    out.push(value.toUpperCase())
  }
  return out.sort((a, b) => a.localeCompare(b, 'en'))
}

const matchSuggestions = (list: string[], input: string) => {
  const query = normalizeSuggestion(input)
  if (!query) return []
  if (list.some(s => normalizeSuggestion(s) === query)) return []
  return list.filter(s => normalizeSuggestion(s).includes(query)).slice(0, 50)
}

const isFutureDate = (date: string) => {
  if (!date) return false
  const parsed = new Date(`${date}T00:00:00`)
  if (isNaN(parsed.getTime())) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return parsed.getTime() > today.getTime()
}

// Persistent / Learned Custom School Directory & Suggestions
const loadSavedSchoolDirectory = (): Record<string, SchoolEntry> => {
  try {
    const raw = localStorage.getItem('salom_crm_school_directory')
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

const loadSavedCustomSchools = (): string[] => {
  try {
    const raw = localStorage.getItem('salom_crm_custom_schools')
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

const loadSavedCustomMajors = (): string[] => {
  try {
    const raw = localStorage.getItem('salom_crm_custom_majors')
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

const customSchoolDirectory = ref<Record<string, SchoolEntry>>(loadSavedSchoolDirectory())
const customSchools = ref<string[]>(loadSavedCustomSchools())
const customMajors = ref<string[]>(loadSavedCustomMajors())

// Database School & Major Directory (Multi-Branch Synchronization)
const { data: dbSchoolsData, refetch: refetchDbSchools } = useQuery({
  queryKey: ['schools-directory'],
  queryFn: () => settingsApi.getSchools(),
  staleTime: 1000 * 60 * 5,
})

const { data: dbMajorsData, refetch: refetchDbMajors } = useQuery({
  queryKey: ['majors-directory'],
  queryFn: () => settingsApi.getMajors(),
  staleTime: 1000 * 60 * 5,
})

const getSchoolEntry = (schoolName: string): SchoolEntry | undefined => {
  const norm = normalizeSuggestion(schoolName)
  // 1. Check local recent edits
  if (customSchoolDirectory.value[norm]) {
    return customSchoolDirectory.value[norm]
  }
  // 2. Check Database records (synced from all branches)
  if (Array.isArray(dbSchoolsData.value)) {
    const found = dbSchoolsData.value.find((s: any) => normalizeSuggestion(s.name) === norm)
    if (found) {
      return {
        name: found.name,
        address: found.address || '',
        website: found.website || '',
        phone: found.phone || '',
        email: found.email || ''
      }
    }
  }
  // 3. Check Built-in directory
  return BUILTIN_SCHOOL_DIRECTORY[norm]
}

const allSchoolSuggestions = computed(() => {
  const dbSchoolNames = Array.isArray(dbSchoolsData.value) ? dbSchoolsData.value.map((s: any) => s.name) : []
  return dedupeSuggestions([...customSchools.value, ...dbSchoolNames, ...UNIVERSITY_SUGGESTIONS], [])
})

const allMajorSuggestions = computed(() => {
  const dbMajorNames = Array.isArray(dbMajorsData.value) ? dbMajorsData.value.map((m: any) => m.name) : []
  return dedupeSuggestions([...customMajors.value, ...dbMajorNames, ...UZ_MAJOR_SUGGESTIONS], [])
})

const schoolSuggestions = computed(() => {
  return matchSuggestions(allSchoolSuggestions.value, schoolForm.value.final_school_name || '')
})

const uzMajorSuggestions = computed(() => {
  return matchSuggestions(allMajorSuggestions.value, schoolForm.value.major || '')
})

const applySchoolDefaults = (schoolName: string, replace = false) => {
  const known = getSchoolEntry(schoolName)
  if (!known && !replace) return
  if (replace) {
    schoolForm.value.school_address = known?.address || ''
    schoolForm.value.school_website = known?.website || ''
    schoolForm.value.school_phone = formatSchoolPhone(known?.phone || '')
    schoolForm.value.school_email = known?.email || ''
  } else {
    if (!schoolForm.value.school_address && known?.address) schoolForm.value.school_address = known.address
    if (!schoolForm.value.school_website && known?.website) schoolForm.value.school_website = known.website
    if (!schoolForm.value.school_phone && known?.phone) schoolForm.value.school_phone = formatSchoolPhone(known.phone)
    if (!schoolForm.value.school_email && known?.email) schoolForm.value.school_email = known.email
  }
}

const onSchoolPhoneBlur = () => {
  if (schoolForm.value.school_phone) {
    schoolForm.value.school_phone = formatSchoolPhone(schoolForm.value.school_phone)
  }
}

const onSchoolNameInput = (e: Event) => {
  const val = ((e.target as HTMLInputElement).value || '').toUpperCase()
  schoolForm.value.final_school_name = val
  applySchoolDefaults(val, false)
  showSchoolSuggestions.value = true
}

const selectSchoolSuggestion = (suggestion: string) => {
  schoolForm.value.final_school_name = suggestion
  applySchoolDefaults(suggestion, true)
  showSchoolSuggestions.value = false
}

const onMajorInput = (e: Event) => {
  const val = ((e.target as HTMLInputElement).value || '').toUpperCase()
  schoolForm.value.major = val
  showMajorSuggestions.value = true
}

const selectMajorSuggestion = (suggestion: string) => {
  schoolForm.value.major = suggestion
  showMajorSuggestions.value = false
}

// School Date Pickers
const schoolCurrentYear = new Date().getFullYear()
const schoolYears = Array.from({ length: 71 }, (_, i) => String(schoolCurrentYear + 10 - i))
const schoolMonths = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'))

const getEntryDateParts = () => {
  const parts = schoolForm.value.date_of_entry ? schoolForm.value.date_of_entry.split('-') : ['', '', '']
  return { y: parts[0] || '', m: parts[1] || '', d: parts[2] || '' }
}

const getGradDateParts = () => {
  const parts = schoolForm.value.date_of_graduation ? schoolForm.value.date_of_graduation.split('-') : ['', '', '']
  return { y: parts[0] || '', m: parts[1] || '', d: parts[2] || '' }
}

const getDaysInMonth = (y: string, m: string) => {
  const count = y && m ? new Date(parseInt(y), parseInt(m), 0).getDate() : 31
  return Array.from({ length: count }, (_, i) => String(i + 1).padStart(2, '0'))
}

const updateEntryDate = (part: 'y' | 'm' | 'd', val: string) => {
  const parts = getEntryDateParts()
  if (val === '') {
    schoolForm.value.date_of_entry = ''
    return
  }
  if (part === 'y') {
    const newY = val
    schoolForm.value.date_of_entry = `${newY}-${ENTRY_MONTH}-${ENTRY_DAY}`
    const gradYear = String(parseInt(newY) + DEFAULT_COURSE_YEARS)
    const gradDate = `${gradYear}-${GRADUATION_MONTH}-${GRADUATION_DAY}`
    const expected = isFutureDate(gradDate)
    gradExpected.value = expected
    schoolForm.value.date_of_graduation = expected ? '' : gradDate
    return
  }
  let newY = parts.y || String(schoolCurrentYear)
  let newM = part === 'm' ? val : (parts.m || '01')
  let newD = part === 'd' ? val : (parts.d || '01')
  const maxD = new Date(parseInt(newY), parseInt(newM), 0).getDate()
  if (parseInt(newD) > maxD) newD = String(maxD).padStart(2, '0')
  schoolForm.value.date_of_entry = `${newY}-${newM}-${newD}`
}

const updateGradDate = (part: 'y' | 'm' | 'd', val: string) => {
  const parts = getGradDateParts()
  if (val === '') {
    gradExpected.value = false
    schoolForm.value.date_of_graduation = ''
    return
  }
  if (part === 'y' && val === EXPECTED_YEAR) {
    gradExpected.value = true
    schoolForm.value.date_of_graduation = ''
    return
  }
  if (part === 'y') {
    const newY = val
    let newM = parts.m || GRADUATION_MONTH
    let newD = parts.d || GRADUATION_DAY
    const maxD = new Date(parseInt(newY), parseInt(newM), 0).getDate()
    if (parseInt(newD) > maxD) newD = String(maxD).padStart(2, '0')
    const fullDate = `${newY}-${newM}-${newD}`
    const expected = isFutureDate(fullDate)
    gradExpected.value = expected
    schoolForm.value.date_of_graduation = fullDate
    return
  }
  let newY = parts.y || String(schoolCurrentYear)
  let newM = part === 'm' ? val : (parts.m || '01')
  let newD = part === 'd' ? val : (parts.d || '01')
  const maxD = new Date(parseInt(newY), parseInt(newM), 0).getDate()
  if (parseInt(newD) > maxD) newD = String(maxD).padStart(2, '0')
  const fullDate = `${newY}-${newM}-${newD}`
  gradExpected.value = isFutureDate(fullDate)
  schoolForm.value.date_of_graduation = fullDate
}

const handleGpaSystemChange = (e: Event) => {
  const target = e.target as HTMLSelectElement
  if (target.value === 'MANUAL ENTRY') {
    gpaSystemManual.value = true
    schoolForm.value.gpa_system = ''
  } else {
    schoolForm.value.gpa_system = target.value
  }
}

const handleEntryDateChange = (part: 'y' | 'm' | 'd', e: Event) => {
  const target = e.target as HTMLSelectElement
  updateEntryDate(part, target.value)
}

const handleGradDateChange = (part: 'y' | 'm' | 'd', e: Event) => {
  const target = e.target as HTMLSelectElement
  updateGradDate(part, target.value)
}

// School Details Modal Handlers
const openSchoolModal = () => {
  if (!props.student) return
  const s = props.student
  const systemVal = (s.gpa_system || '').trim()
  const isPreset = ['4', '4.5', '5', '100'].includes(systemVal)
  gpaSystemManual.value = !isPreset && systemVal !== ''
  
  const isGradExp = s.graduation_expected ?? (isFutureDate(s.date_of_graduation || '') || !s.date_of_graduation)
  gradExpected.value = !!isGradExp && (!s.date_of_graduation || isFutureDate(s.date_of_graduation))

  schoolForm.value = {
    final_school_name: s.final_school_name || '',
    major: s.major || '',
    gpa: s.gpa || '',
    gpa_system: systemVal, // Default is "" so SYSTEM dropdown selects "Select" by default
    degree_no: s.degree_no || '',
    date_of_entry: s.date_of_entry || '',
    date_of_graduation: s.date_of_graduation || '',
    school_address: s.school_address || '',
    school_website: s.school_website || '',
    school_phone: formatSchoolPhone(s.school_phone || ''),
    school_email: s.school_email || ''
  }
  showSchoolSuggestions.value = false
  showMajorSuggestions.value = false
  isSchoolModalOpen.value = true
}

const saveSchoolModal = async () => {
  savingSchool.value = true
  try {
    const schoolName = (schoolForm.value.final_school_name || '').trim()
    const majorName = (schoolForm.value.major || '').trim()
    
    // Save new or edited school data for future autocomplete and auto-fill
    if (schoolName) {
      const norm = normalizeSuggestion(schoolName)
      const updatedEntry: SchoolEntry = {
        name: schoolName,
        address: (schoolForm.value.school_address || '').trim(),
        website: (schoolForm.value.school_website || '').trim(),
        phone: formatSchoolPhone(schoolForm.value.school_phone || '').trim(),
        email: (schoolForm.value.school_email || '').trim()
      }
      
      customSchoolDirectory.value = {
        ...customSchoolDirectory.value,
        [norm]: updatedEntry
      }
      try {
        localStorage.setItem('salom_crm_school_directory', JSON.stringify(customSchoolDirectory.value))
      } catch (e) {
        console.error('Failed to save school directory to storage', e)
      }

      customSchools.value = dedupeSuggestions([...customSchools.value, schoolName], UNIVERSITY_SUGGESTIONS)
      try {
        localStorage.setItem('salom_crm_custom_schools', JSON.stringify(customSchools.value))
      } catch (e) {
        console.error('Failed to save custom schools to storage', e)
      }

      // Persist to Central Database for all branches to see
      settingsApi.upsertSchool(updatedEntry)
        .then(() => refetchDbSchools())
        .catch(e => console.error('Database school sync error:', e))
    }

    // Save new or edited major for future autocomplete
    if (majorName) {
      customMajors.value = dedupeSuggestions([...customMajors.value, majorName], UZ_MAJOR_SUGGESTIONS)
      try {
        localStorage.setItem('salom_crm_custom_majors', JSON.stringify(customMajors.value))
      } catch (e) {
        console.error('Failed to save custom majors to storage', e)
      }

      // Persist to Central Database for all branches to see
      settingsApi.upsertMajor({ name: majorName })
        .then(() => refetchDbMajors())
        .catch(e => console.error('Database major sync error:', e))
    }

    const cleaned: Record<string, any> = {}
    for (const [k, v] of Object.entries(schoolForm.value)) {
      if (typeof v === 'string') {
        cleaned[k] = v.trim() === '' ? null : v.trim()
      } else {
        cleaned[k] = v
      }
    }
    cleaned.graduation_expected = gradExpected.value
    emit('update-student', cleaned)
    isSchoolModalOpen.value = false
  } finally {
    savingSchool.value = false
  }
}

// Certificate Date Helpers
const currentYear = new Date().getFullYear()
const validDateYears = Array.from({ length: 20 }, (_, i) => String(currentYear - 8 + i))
const dateMonths = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'))

const getTestDateParts = () => {
  const parts = certForm.value.test_date ? certForm.value.test_date.split('-') : ['', '', '']
  return { y: parts[0] || '', m: parts[1] || '', d: parts[2] || '' }
}

const getValidDateParts = () => {
  const parts = certForm.value.valid_date ? certForm.value.valid_date.split('-') : ['', '', '']
  return { y: parts[0] || '', m: parts[1] || '', d: parts[2] || '' }
}

const updateCertTestDate = (field: 'y' | 'm' | 'd', val: string) => {
  const parts = getTestDateParts()
  let newY = field === 'y' ? val : parts.y || String(new Date().getFullYear())
  let newM = field === 'm' ? val : parts.m || '01'
  let newD = field === 'd' ? val : parts.d || '01'
  if (newY && newM) {
    const maxD = new Date(parseInt(newY), parseInt(newM), 0).getDate()
    if (parseInt(newD) > maxD) newD = String(maxD).padStart(2, '0')
  }
  const newDate = `${newY}-${newM}-${newD}`
  certForm.value.test_date = newDate
  // Auto calculate valid date: +2 years minus 1 day (UniApp2 rule)
  try {
    const dateObj = new Date(parseInt(newY), parseInt(newM) - 1, parseInt(newD))
    dateObj.setFullYear(dateObj.getFullYear() + 2)
    dateObj.setDate(dateObj.getDate() - 1)
    const validY = String(dateObj.getFullYear())
    const validM = String(dateObj.getMonth() + 1).padStart(2, '0')
    const validD = String(dateObj.getDate()).padStart(2, '0')
    certForm.value.valid_date = `${validY}-${validM}-${validD}`
  } catch (e) {
    // fallback
  }
}

const updateCertValidDate = (field: 'y' | 'm' | 'd', val: string) => {
  const parts = getValidDateParts()
  let newY = field === 'y' ? val : parts.y || String(new Date().getFullYear() + 2)
  let newM = field === 'm' ? val : parts.m || '01'
  let newD = field === 'd' ? val : parts.d || '01'
  if (newY && newM) {
    const maxD = new Date(parseInt(newY), parseInt(newM), 0).getDate()
    if (parseInt(newD) > maxD) newD = String(maxD).padStart(2, '0')
  }
  certForm.value.valid_date = `${newY}-${newM}-${newD}`
}

// Certificate Modal Handlers
const openCertModal = (slot: 1 | 2 | 3) => {
  if (!props.student) return
  certModalSlot.value = slot
  const s = props.student
  if (slot === 1) {
    certForm.value = {
      type: s.language_certificate || 'TOPIK',
      score: s.certificate_score || '',
      test_date: s.certificate_test_date || '',
      valid_date: s.certificate_valid_date || ''
    }
  } else if (slot === 2) {
    certForm.value = {
      type: s.language_certificate_2 || 'IELTS',
      score: s.certificate_score_2 || '',
      test_date: s.certificate_2_test_date || '',
      valid_date: s.certificate_2_valid_date || ''
    }
  } else {
    certForm.value = {
      type: s.language_certificate_3 || 'SAT',
      score: s.certificate_score_3 || '',
      test_date: s.certificate_3_test_date || '',
      valid_date: s.certificate_3_valid_date || ''
    }
  }
  isCertModalOpen.value = true
}

const saveCertModal = () => {
  const slot = certModalSlot.value
  const patch: Record<string, any> = {}
  if (slot === 1) {
    patch.language_certificate = certForm.value.type || null
    patch.certificate_score = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.score || null)
    patch.certificate_test_date = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.test_date || null)
    patch.certificate_valid_date = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.valid_date || null)
  } else if (slot === 2) {
    patch.language_certificate_2 = certForm.value.type || null
    patch.certificate_score_2 = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.score || null)
    patch.certificate_2_test_date = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.test_date || null)
    patch.certificate_2_valid_date = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.valid_date || null)
  } else {
    patch.language_certificate_3 = certForm.value.type || null
    patch.certificate_score_3 = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.score || null)
    patch.certificate_3_test_date = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.test_date || null)
    patch.certificate_3_valid_date = certForm.value.type === 'NO CERTIFICATE' ? null : (certForm.value.valid_date || null)
  }
  emit('update-student', patch)
  if (slot === 2 && (!certForm.value.type || certForm.value.type === 'NO CERTIFICATE')) {
    showCert2.value = false
    showCert3.value = false
  } else if (slot === 3 && (!certForm.value.type || certForm.value.type === 'NO CERTIFICATE')) {
    showCert3.value = false
  }
  isCertModalOpen.value = false
}

// Clear and hide slots
const clearAndHideLevel2 = () => {
  emit('update-student', { level2: null })
  showLevel2.value = false
}

const clearAndHideCert = (slot: 2 | 3) => {
  if (slot === 2) {
    emit('update-student', {
      language_certificate_2: null,
      certificate_score_2: null,
      certificate_2_test_date: null,
      certificate_2_valid_date: null
    })
    showCert2.value = false
    showCert3.value = false
  } else {
    emit('update-student', {
      language_certificate_3: null,
      certificate_score_3: null,
      certificate_3_test_date: null,
      certificate_3_valid_date: null
    })
    showCert3.value = false
  }
}

const clearAndHideUni = (slot: number) => {
  const patch: Record<string, any> = {}
  patch[`university_${slot}`] = null
  patch[`university_${slot}_status`] = null
  patch[`university_${slot}_major`] = null
  emit('update-student', patch)
  if (slot === 2) { showUni2.value = false; showUni3.value = false; showUni4.value = false; showUni5.value = false; }
  else if (slot === 3) { showUni3.value = false; showUni4.value = false; showUni5.value = false; }
  else if (slot === 4) { showUni4.value = false; showUni5.value = false; }
  else if (slot === 5) { showUni5.value = false; }
}

// Google Drive Actions
const handleDriveAction = () => {
  if (props.student?.google_drive_url) {
    window.open(props.student.google_drive_url, '_blank')
  } else {
    driveUrlInput.value = ''
    isDriveModalOpen.value = true
  }
}

const saveDriveUrl = () => {
  if (driveUrlInput.value.trim()) {
    emit('update-student', { google_drive_url: driveUrlInput.value.trim() })
  }
  isDriveModalOpen.value = false
}

const handleDeleteStudent = () => {
  const name = props.student?.full_name || 'student'
  if (!confirm(`Are you sure you want to delete student profile "${name}"?`)) return
  emit('archive')
}

const handleRestoreStudent = () => {
  const name = props.student?.full_name || 'student'
  if (!confirm(`Are you sure you want to restore student profile "${name}"?`)) return
  emit('restore')
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <transition
      enter-active-class="transition duration-250 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs"
        @click="emit('close')"
      />
    </transition>

    <!-- Slide-over Drawer Panel -->
    <transition
      enter-active-class="transition duration-300 cubic-bezier(0.16, 1, 0.3, 1)"
      enter-from-class="translate-x-full"
      enter-to-class="translate-x-0"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="translate-x-0"
      leave-to-class="translate-x-full"
    >
      <div
        v-if="isOpen && student"
        class="fixed inset-y-0 right-0 z-50 flex flex-col bg-[#f4f6f9] dark:bg-[#0e1114] shadow-2xl text-zinc-900 dark:text-zinc-100 overflow-hidden select-none transition-all duration-300 pointer-events-auto"
        :class="isExpanded
          ? 'left-0 w-full rounded-none'
          : 'w-full max-w-[calc(98vw+20px)] md:max-w-[calc(95vw+20px)] lg:max-w-[calc(90vw+20px)] xl:max-w-[calc(80vw+20px)] rounded-l-2xl border-l border-zinc-200 dark:border-zinc-800'"
        @click.stop
      >
        <!-- 1. Top Header Bar -->
        <div class="flex items-center justify-between gap-3 px-5 py-3 border-b border-zinc-200/90 dark:border-zinc-800 bg-white dark:bg-[#14171a] shrink-0">
          <div class="flex items-center gap-3 min-w-0">
            <!-- Back / Close Button -->
            <button
              type="button"
              @click="emit('close')"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 text-xs font-bold shadow-2xs hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-colors cursor-pointer"
            >
              <ArrowLeft class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span>Close</span>
            </button>

            <!-- Initials Avatar Badge -->
            <div class="w-10 h-10 rounded-full bg-[#1868db] text-white font-bold flex items-center justify-center text-sm shadow-xs shrink-0 select-none">
              {{ getInitials(student.full_name) }}
            </div>

            <!-- Student Name & Monospace ID Subtitle -->
            <div class="min-w-0">
              <h2 class="text-base lg:text-[17px] font-bold uppercase tracking-wide text-zinc-900 dark:text-zinc-100 truncate" :title="student.full_name">
                {{ student.full_name }}
              </h2>
              <div class="flex items-center gap-2 text-xs font-semibold text-zinc-500 dark:text-zinc-400 mt-0.5 flex-wrap">
                <span class="inline-flex items-center gap-1">
                  ID: <span class="font-mono text-blue-600 dark:text-blue-400 font-bold">{{ student.id }}</span>
                </span>
                <span class="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
                <!-- Active/Deleted Badge -->
                <span
                  v-if="student.is_deleted"
                  class="bg-rose-500/10 text-rose-600 border border-rose-500/20 px-1.5 py-0.2 rounded-full text-[10px] font-extrabold uppercase"
                >
                  DELETED
                </span>
                <span
                  v-else
                  class="bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 px-1.5 py-0.2 rounded-full text-[10px] font-extrabold uppercase"
                >
                  ACTIVE
                </span>

                <template v-if="student.student_group">
                  <span class="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
                  <span class="text-zinc-700 dark:text-zinc-300 uppercase font-bold text-[11px]">{{ student.student_group }}</span>
                </template>

                <template v-if="student.created_at">
                  <span class="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
                  <span class="inline-flex items-center gap-1 text-[11px] text-zinc-400">
                    <Calendar class="w-3.5 h-3.5 text-blue-500" />
                    <span>Registered: <strong class="text-zinc-700 dark:text-zinc-300 font-mono">{{ formatRegistrationDate(student.created_at) }}</strong></span>
                  </span>
                </template>
              </div>
            </div>
          </div>

          <!-- Header Right Action Buttons -->
          <div class="flex items-center gap-2 shrink-0">
            <!-- Fill By Document -->
            <button
              type="button"
              @click="navigateToExtract"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-zinc-800 hover:bg-zinc-50 border border-zinc-200 dark:border-zinc-700 rounded-lg text-xs font-semibold text-zinc-700 dark:text-zinc-300 transition-all shadow-2xs cursor-pointer hover:border-blue-500/50"
              title="Fill student details from document scan (Python OCR)"
            >
              <FileText class="w-3.5 h-3.5 text-blue-600" />
              <span class="hidden sm:inline">Fill By Document</span>
            </button>

            <!-- See documents / Google Drive Folder -->
            <button
              type="button"
              @click="handleDriveAction"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-zinc-800 hover:bg-emerald-50/60 dark:hover:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40 rounded-lg text-xs font-bold transition-all shadow-2xs cursor-pointer"
              :title="student.google_drive_url ? 'Open Student Google Drive Folder' : 'Set Google Drive Folder URL'"
            >
              <Folder class="w-3.5 h-3.5 text-emerald-600" />
              <span>{{ student.google_drive_url ? 'See documents' : 'Create folder' }}</span>
              <ExternalLink v-if="student.google_drive_url" class="w-3 h-3 text-emerald-600 ml-0.5" />
            </button>

            <!-- Delete / Restore -->
            <template v-if="student.is_deleted">
              <button
                type="button"
                @click="handleRestoreStudent"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-zinc-800 hover:bg-emerald-50 border border-emerald-500/40 text-emerald-600 rounded-lg text-xs font-bold transition-all cursor-pointer"
                title="Restore student profile"
              >
                <RefreshCw class="w-3.5 h-3.5" />
                <span>Restore</span>
              </button>
            </template>
            <template v-else>
              <button
                type="button"
                @click="handleDeleteStudent"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-zinc-800 hover:bg-rose-50 dark:hover:bg-rose-950/30 border border-rose-500/30 text-rose-600 rounded-lg text-xs font-bold transition-all cursor-pointer shadow-2xs"
                title="Delete student profile"
              >
                <Trash2 class="w-3.5 h-3.5 text-rose-500" />
                <span>Delete</span>
              </button>
            </template>

            <span class="w-[1px] h-5 bg-zinc-200 dark:bg-zinc-800 mx-0.5" />

            <!-- Fullscreen / Expand Button -->
            <button
              type="button"
              @click="isExpanded = !isExpanded"
              class="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-500 hover:text-zinc-900 transition-colors cursor-pointer"
              :title="isExpanded ? 'Collapse panel' : 'Expand to full screen'"
            >
              <Minimize2 v-if="isExpanded" class="w-4 h-4" />
              <Maximize2 v-else class="w-4 h-4" />
            </button>

            <!-- Close Button -->
            <button
              type="button"
              @click="emit('close')"
              class="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-500 hover:text-zinc-900 transition-colors cursor-pointer"
              title="Close Student Details"
            >
              <X class="w-4.5 h-4.5" />
            </button>
          </div>
        </div>

        <!-- 2. Main 3-Column Dashboard Body -->
        <div class="flex-1 overflow-y-auto p-2.5 lg:p-3">
          <div class="grid grid-cols-1 lg:grid-cols-[1.65fr_1.25fr_0.68fr] gap-2.5">
            
            <!-- ═════════════════════════════════════════════════════════════
                 COLUMN 1: Passport Details, Contact & Educational Background
                 ═════════════════════════════════════════════════════════════ -->
            <div class="flex flex-col gap-2">
              
              <!-- 1.1 Passport Details Section Header & Cards -->
              <div class="flex flex-col gap-1.5">
                <div class="flex items-center justify-between px-1">
                  <div class="flex items-center gap-1.5 text-zinc-500 dark:text-zinc-400 font-bold uppercase tracking-wider text-[11.5px]">
                    <User class="w-3.5 h-3.5 text-blue-600" />
                    <span>PASSPORT DETAILS</span>
                  </div>

                  <!-- EN / KR Switcher -->
                  <div class="flex items-center rounded-md border border-zinc-200 dark:border-zinc-700 overflow-hidden text-[10px] font-bold">
                    <button
                      type="button"
                      @click="nameLanguage = 'EN'"
                      class="px-2 py-0.5 transition-all cursor-pointer"
                      :class="nameLanguage === 'EN' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50'"
                    >
                      EN
                    </button>
                    <button
                      type="button"
                      @click="nameLanguage = 'KR'"
                      class="px-2 py-0.5 transition-all border-l border-zinc-200 dark:border-zinc-700 cursor-pointer"
                      :class="nameLanguage === 'KR' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50'"
                    >
                      KR
                    </button>
                  </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1">
                  <!-- FULL NAME -->
                  <div
                    class="sm:col-span-2 relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      (nameLanguage === 'KR' ? student.korean_name : student.full_name) ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'full_name' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('full_name', (nameLanguage === 'KR' ? student.korean_name : student.full_name))"
                    title="Single-click to copy Full Name"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">
                        {{ nameLanguage === 'KR' ? 'FULL NAME (KOREAN)' : 'FULL NAME' }}
                      </span>
                      <div class="flex items-center gap-1">
                        <button
                          type="button"
                          @click.stop="handleCopy('full_name', (nameLanguage === 'KR' ? student.korean_name : student.full_name))"
                          class="p-0.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 opacity-0 group-hover/card:opacity-100 transition-opacity"
                        >
                          <Check v-if="copiedField === 'full_name'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          @click.stop="startInlineEdit(nameLanguage === 'KR' ? 'korean_name' : 'full_name', nameLanguage === 'KR' ? student.korean_name : student.full_name)"
                          class="p-0.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
                        >
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div class="mt-1">
                      <template v-if="editingField === (nameLanguage === 'KR' ? 'korean_name' : 'full_name')">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit(nameLanguage === 'KR' ? 'korean_name' : 'full_name')" @keydown.esc="cancelInlineEdit">
                          <input
                            v-model="editValue"
                            type="text"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded-md outline-none"
                            autoFocus
                          />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit(nameLanguage === 'KR' ? 'korean_name' : 'full_name')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="(nameLanguage === 'KR' ? student.korean_name : student.full_name)" class="text-[13.5px] font-bold text-[#0f172a] dark:text-zinc-100 uppercase tracking-wide">
                          {{ (nameLanguage === 'KR' ? student.korean_name : student.full_name) }}
                        </span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- FAMILY NAME [AUTO] -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] border-l-blue-600 rounded-lg p-2.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[copiedField === 'family_name' && 'animate-copy-press']"
                    @click="handleCopy('family_name', student.full_name ? student.full_name.split(' ')[0] : '')"
                    title="Single-click to copy Family Name"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-1">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">FAMILY NAME</span>
                        <span class="text-[9px] font-bold px-1 py-0.2 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-400">AUTO</span>
                      </div>
                      <button
                        type="button"
                        class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100 transition-opacity"
                      >
                        <Check v-if="copiedField === 'family_name'" class="w-3.5 h-3.5 text-emerald-500" />
                        <Copy v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div class="mt-1 text-[13.5px] font-bold text-[#0f172a] dark:text-zinc-100 uppercase">
                      {{ student.full_name ? student.full_name.split(' ')[0] : '—' }}
                    </div>
                  </div>

                  <!-- GIVEN NAME [AUTO] -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] border-l-blue-600 rounded-lg p-2.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[copiedField === 'given_name' && 'animate-copy-press']"
                    @click="handleCopy('given_name', student.full_name ? student.full_name.split(' ').slice(1).join(' ') : '')"
                    title="Single-click to copy Given Name"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-1">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">GIVEN NAME</span>
                        <span class="text-[9px] font-bold px-1 py-0.2 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-400">AUTO</span>
                      </div>
                      <button
                        type="button"
                        class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100 transition-opacity"
                      >
                        <Check v-if="copiedField === 'given_name'" class="w-3.5 h-3.5 text-emerald-500" />
                        <Copy v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div class="mt-1 text-[13.5px] font-bold text-[#0f172a] dark:text-zinc-100 uppercase truncate">
                      {{ student.full_name ? (student.full_name.split(' ').slice(1).join(' ') || '—') : '—' }}
                    </div>
                  </div>

                  <!-- SEX & BIRTHDAY ROW -->
                  <div class="sm:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-1">
                    <!-- SEX -->
                    <div
                      class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                      :class="[
                        student.gender ? 'border-l-blue-600' : 'border-l-rose-500',
                        copiedField === 'gender' && 'animate-copy-press'
                      ]"
                      @click="handleCopy('gender', student.gender)"
                      title="Single-click to copy Sex"
                    >
                      <div class="flex items-center justify-between">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">SEX</span>
                        <div class="flex items-center gap-1">
                          <button type="button" @click.stop="handleCopy('gender', student.gender)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                            <Check v-if="copiedField === 'gender'" class="w-3.5 h-3.5 text-emerald-500" />
                            <Copy v-else class="w-3.5 h-3.5" />
                          </button>
                          <button type="button" @click.stop="startInlineEdit('gender', student.gender)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                            <Pencil class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <div class="mt-0.5">
                        <template v-if="editingField === 'gender'">
                          <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                            <select
                              v-model="editValue"
                              class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                              autoFocus
                            >
                              <option value="MALE">MALE</option>
                              <option value="FEMALE">FEMALE</option>
                            </select>
                            <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                              <button
                                type="button"
                                @click="saveInlineEdit('gender')"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Save"
                              >
                                <Check class="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                @click="cancelInlineEdit"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Cancel"
                              >
                                <X class="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <span v-if="student.gender" class="text-[13.5px] font-bold text-[#0f172a] dark:text-zinc-100 uppercase">{{ student.gender }}</span>
                          <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                        </template>
                      </div>
                    </div>

                    <!-- BIRTHDAY -->
                    <div
                      class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                      :class="[
                        student.birthday ? 'border-l-blue-600' : 'border-l-rose-500',
                        copiedField === 'birthday' && 'animate-copy-press'
                      ]"
                      @click="handleCopy('birthday', student.birthday)"
                      title="Single-click to copy Birthday"
                    >
                      <div class="flex items-center justify-between">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">BIRTHDAY</span>
                        <div class="flex items-center gap-1">
                          <button type="button" @click.stop="handleCopy('birthday', student.birthday)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                            <Check v-if="copiedField === 'birthday'" class="w-3.5 h-3.5 text-emerald-500" />
                            <Copy v-else class="w-3.5 h-3.5" />
                          </button>
                          <button type="button" @click.stop="startInlineEdit('birthday', student.birthday)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                            <Pencil class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <div class="mt-0.5">
                        <template v-if="editingField === 'birthday'">
                          <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('birthday')" @keydown.esc="cancelInlineEdit">
                            <input
                              v-model="editValue"
                              type="date"
                              class="w-full pl-2 pr-14 py-1 text-xs font-bold bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                              autoFocus
                            />
                            <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                              <button
                                type="button"
                                @click="saveInlineEdit('birthday')"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Save"
                              >
                                <Check class="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                @click="cancelInlineEdit"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Cancel"
                              >
                                <X class="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <span v-if="student.birthday" class="text-[13.5px] font-bold font-mono text-[#0f172a] dark:text-zinc-100">{{ student.birthday }}</span>
                          <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                        </template>
                      </div>
                    </div>
                  </div>

                  <!-- PASSPORT, DATE OF ISSUE, DATE OF EXPIRATION - ALL IN ONE SINGLE ROW (UniApp2 Layout) -->
                  <div class="sm:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-1">
                    <!-- PASSPORT -->
                    <div
                      class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                      :class="[
                        student.passport ? 'border-l-blue-600' : 'border-l-rose-500',
                        copiedField === 'passport' && 'animate-copy-press'
                      ]"
                      @click="handleCopy('passport', student.passport)"
                      title="Single-click to copy Passport"
                    >
                      <div class="flex items-center justify-between">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8] truncate" title="PASSPORT">PASSPORT</span>
                        <div class="flex items-center gap-1">
                          <button type="button" @click.stop="handleCopy('passport', student.passport)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                            <Check v-if="copiedField === 'passport'" class="w-3.5 h-3.5 text-emerald-500" />
                            <Copy v-else class="w-3.5 h-3.5" />
                          </button>
                          <button type="button" @click.stop="startInlineEdit('passport', student.passport)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                            <Pencil class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <div class="mt-0.5">
                        <template v-if="editingField === 'passport'">
                          <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('passport')" @keydown.esc="cancelInlineEdit">
                            <input
                              :value="editValue"
                              @input="onInlineInput('passport', $event)"
                              type="text"
                              class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase font-mono bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                              autoFocus
                            />
                            <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                              <button
                                type="button"
                                @click="saveInlineEdit('passport')"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Save"
                              >
                                <Check class="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                @click="cancelInlineEdit"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Cancel"
                              >
                                <X class="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <span v-if="student.passport" class="text-[13.5px] font-bold font-mono text-[#0f172a] dark:text-zinc-100 uppercase">{{ student.passport }}</span>
                          <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                        </template>
                      </div>
                    </div>

                    <!-- DATE OF ISSUE -->
                    <div
                      class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                      :class="[
                        student.passport_issue_date ? 'border-l-blue-600' : 'border-l-rose-500',
                        copiedField === 'passport_issue_date' && 'animate-copy-press'
                      ]"
                      @click="handleCopy('passport_issue_date', student.passport_issue_date)"
                      title="Single-click to copy Date of Issue"
                    >
                      <div class="flex items-center justify-between">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8] truncate" title="DATE OF ISSUE">DATE OF ISSUE</span>
                        <div class="flex items-center gap-1">
                          <button type="button" @click.stop="handleCopy('passport_issue_date', student.passport_issue_date)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                            <Check v-if="copiedField === 'passport_issue_date'" class="w-3.5 h-3.5 text-emerald-500" />
                            <Copy v-else class="w-3.5 h-3.5" />
                          </button>
                          <button type="button" @click.stop="startInlineEdit('passport_issue_date', student.passport_issue_date)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                            <Pencil class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <div class="mt-0.5">
                        <template v-if="editingField === 'passport_issue_date'">
                          <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('passport_issue_date')" @keydown.esc="cancelInlineEdit">
                            <input
                              v-model="editValue"
                              type="date"
                              class="w-full pl-2 pr-14 py-1 text-xs font-bold bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                              autoFocus
                            />
                            <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                              <button
                                type="button"
                                @click="saveInlineEdit('passport_issue_date')"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Save"
                              >
                                <Check class="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                @click="cancelInlineEdit"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Cancel"
                              >
                                <X class="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <span v-if="student.passport_issue_date" class="text-[13.5px] font-bold font-mono text-[#0f172a] dark:text-zinc-100">{{ student.passport_issue_date }}</span>
                          <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                        </template>
                      </div>
                    </div>

                    <!-- DATE OF EXPIRATION -->
                    <div
                      class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                      :class="[
                        student.passport_expire_date ? 'border-l-blue-600' : 'border-l-rose-500',
                        copiedField === 'passport_expire_date' && 'animate-copy-press'
                      ]"
                      @click="handleCopy('passport_expire_date', student.passport_expire_date)"
                      title="Single-click to copy Date of Expiration"
                    >
                      <div class="flex items-center justify-between">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8] truncate" title="DATE OF EXPIRATION">DATE OF EXPIRATION</span>
                        <div class="flex items-center gap-1">
                          <button type="button" @click.stop="handleCopy('passport_expire_date', student.passport_expire_date)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                            <Check v-if="copiedField === 'passport_expire_date'" class="w-3.5 h-3.5 text-emerald-500" />
                            <Copy v-else class="w-3.5 h-3.5" />
                          </button>
                          <button type="button" @click.stop="startInlineEdit('passport_expire_date', student.passport_expire_date)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                            <Pencil class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <div class="mt-0.5">
                        <template v-if="editingField === 'passport_expire_date'">
                          <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('passport_expire_date')" @keydown.esc="cancelInlineEdit">
                            <input
                              v-model="editValue"
                              type="date"
                              class="w-full pl-2 pr-14 py-1 text-xs font-bold bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                              autoFocus
                            />
                            <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                              <button
                                type="button"
                                @click="saveInlineEdit('passport_expire_date')"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Save"
                              >
                                <Check class="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                @click="cancelInlineEdit"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Cancel"
                              >
                                <X class="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <span v-if="student.passport_expire_date" class="text-[13.5px] font-bold font-mono text-[#0f172a] dark:text-zinc-100">{{ student.passport_expire_date }}</span>
                          <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 1.2 Contact Section Header & Cards -->
              <div class="flex flex-col gap-2">
                <div class="flex items-center justify-between px-1">
                  <div class="flex items-center gap-1.5 text-zinc-500 dark:text-zinc-400 font-bold uppercase tracking-wider text-[11.5px]">
                    <Mail class="w-3.5 h-3.5 text-blue-600" />
                    <span>CONTACT</span>
                  </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  <!-- PHONE 1 (Formatted) -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.phone1 ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'phone1' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('phone1', formatPhoneValue(student.phone1))"
                    title="Single-click to copy Phone 1"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">PHONE 1</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('phone1', formatPhoneValue(student.phone1))" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'phone1'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('phone1', student.phone1)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'phone1'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('phone1')" @keydown.esc="cancelInlineEdit">
                          <input
                            :value="editValue"
                            @input="onInlineInput('phone1', $event)"
                            type="text"
                            placeholder="88-146-47-07"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold font-mono bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit('phone1')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.phone1" class="text-[13.5px] font-bold font-mono text-[#0f172a] dark:text-zinc-100">{{ formatPhoneValue(student.phone1) }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- PHONE 2 (Formatted) -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.phone2 ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'phone2' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('phone2', formatPhoneValue(student.phone2))"
                    title="Single-click to copy Phone 2"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">PHONE 2</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('phone2', formatPhoneValue(student.phone2))" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'phone2'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('phone2', student.phone2)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'phone2'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('phone2')" @keydown.esc="cancelInlineEdit">
                          <input
                            :value="editValue"
                            @input="onInlineInput('phone2', $event)"
                            type="text"
                            placeholder="88-083-56-83"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold font-mono bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit('phone2')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.phone2" class="text-[13.5px] font-bold font-mono text-[#0f172a] dark:text-zinc-100">{{ formatPhoneValue(student.phone2) }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- EMAIL (Always Visible) -->
                  <div
                    class="sm:col-span-2 relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.email ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'email' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('email', student.email)"
                    title="Single-click to copy Email"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">EMAIL</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('email', student.email)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'email'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('email', student.email)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'email'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('email')" @keydown.esc="cancelInlineEdit">
                          <input
                            v-model="editValue"
                            type="email"
                            class="w-full pl-2 pr-14 py-1 text-xs font-medium bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit('email')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.email" class="text-[13px] font-semibold text-[#0f172a] dark:text-zinc-100">{{ student.email }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- ADDRESS (Expanded Only) -->
                  <template v-if="contactExpanded">
                    <div
                      class="sm:col-span-2 relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                      :class="[
                        student.address ? 'border-l-blue-600' : 'border-l-rose-500',
                        copiedField === 'address' && 'animate-copy-press'
                      ]"
                      @click="handleCopy('address', student.address)"
                      title="Single-click to copy Address"
                    >
                      <div class="flex items-center justify-between">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">ADDRESS</span>
                        <div class="flex items-center gap-1">
                          <button type="button" @click.stop="handleCopy('address', student.address)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                            <Check v-if="copiedField === 'address'" class="w-3.5 h-3.5 text-emerald-500" />
                            <Copy v-else class="w-3.5 h-3.5" />
                          </button>
                          <button type="button" @click.stop="startInlineEdit('address', student.address)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                            <Pencil class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <div class="mt-0.5">
                        <template v-if="editingField === 'address'">
                          <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                            <textarea
                              v-model="editValue"
                              rows="2"
                              class="w-full pl-2 pr-14 py-1 text-xs font-medium bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                              autoFocus
                            />
                            <div class="absolute right-1 top-2 flex items-center gap-1">
                              <button
                                type="button"
                                @click="saveInlineEdit('address')"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Save"
                              >
                                <Check class="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                @click="cancelInlineEdit"
                                class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                                title="Cancel"
                              >
                                <X class="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <span v-if="student.address" class="text-[13px] font-bold uppercase text-[#0f172a] dark:text-zinc-100 leading-snug">{{ student.address }}</span>
                          <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                        </template>
                      </div>
                    </div>
                  </template>
                </div>

                <!-- SHOW MORE / SHOW LESS TOGGLE -->
                <button
                  type="button"
                  @click="toggleSection('contact')"
                  class="flex items-center justify-center gap-1 w-full py-0.5 text-[11px] font-semibold uppercase tracking-wide text-zinc-400 hover:text-blue-600 transition-colors cursor-pointer"
                >
                  <span>{{ contactExpanded ? 'SHOW LESS' : 'SHOW MORE' }}</span>
                  <ChevronDown class="w-3 h-3 transition-transform duration-200" :class="contactExpanded ? 'rotate-180' : ''" />
                </button>
              </div>

              <!-- 1.3 Educational Background Section Header & Card -->
              <div class="flex flex-col gap-2">
                <div class="flex items-center justify-between px-1">
                  <div class="flex items-center gap-1.5 text-zinc-500 dark:text-zinc-400 font-bold uppercase tracking-wider text-[11.5px]">
                    <GraduationCap class="w-3.5 h-3.5 text-blue-600" />
                    <span>EDUCATIONAL BACKGROUND</span>
                  </div>
                  <button
                    type="button"
                    @click="openSchoolModal"
                    class="p-0.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 cursor-pointer"
                    title="Edit educational background"
                  >
                    <Pencil class="w-3.5 h-3.5" />
                  </button>
                </div>

                <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-2 shadow-2xs flex flex-col gap-1">
                  <div
                    class="flex flex-col gap-0.5 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                    :class="[copiedField === 'final_school_name' && 'animate-copy-press']"
                    @click="handleCopy('final_school_name', student.final_school_name)"
                    title="Single-click to copy Final School Name"
                  >
                    <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">FINAL SCHOOL NAME</span>
                    <span class="text-[13px] font-semibold text-zinc-800 dark:text-zinc-200">{{ student.final_school_name || '—' }}</span>
                  </div>

                  <div
                    class="flex flex-col gap-0.5 pt-1 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                    :class="[copiedField === 'major' && 'animate-copy-press']"
                    @click="handleCopy('major', student.major)"
                    title="Single-click to copy Major"
                  >
                    <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">MAJOR</span>
                    <span class="text-[13px] font-semibold text-zinc-800 dark:text-zinc-200">{{ student.major || '—' }}</span>
                  </div>

                  <template v-if="eduExpanded">
                    <div
                      class="flex items-baseline justify-between gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                      :class="[copiedField === 'gpa' && 'animate-copy-press']"
                      @click="handleCopy('gpa', student.gpa ? `${student.gpa} (${student.gpa_system || '5'})` : '')"
                      title="Single-click to copy GPA"
                    >
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">GPA</span>
                      <span class="text-xs font-bold font-mono">{{ student.gpa ? `${student.gpa} (${student.gpa_system || '5'})` : '—' }}</span>
                    </div>

                    <div
                      class="flex items-baseline justify-between gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                      :class="[copiedField === 'degree_no' && 'animate-copy-press']"
                      @click="handleCopy('degree_no', student.degree_no)"
                      title="Single-click to copy Degree No"
                    >
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">DEGREE NO</span>
                      <span class="text-xs font-bold font-mono">{{ student.degree_no || '—' }}</span>
                    </div>

                    <div
                      class="flex items-baseline justify-between gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                      :class="[copiedField === 'date_of_entry' && 'animate-copy-press']"
                      @click="handleCopy('date_of_entry', student.date_of_entry)"
                      title="Single-click to copy Date of Entry"
                    >
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">DATE OF ENTRY</span>
                      <span class="text-xs font-bold font-mono">{{ student.date_of_entry || '—' }}</span>
                    </div>

                    <div
                      class="flex items-baseline justify-between gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                      :class="[copiedField === 'date_of_graduation' && 'animate-copy-press']"
                      @click="handleCopy('date_of_graduation', student.date_of_graduation)"
                      title="Single-click to copy Date of Graduation"
                    >
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">DATE OF GRADUATION</span>
                      <span class="text-xs font-bold font-mono">{{ student.date_of_graduation || '—' }}</span>
                    </div>

                    <div
                      v-if="student.school_address"
                      class="flex flex-col gap-0.5 pt-1 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                      :class="[copiedField === 'school_address' && 'animate-copy-press']"
                      @click="handleCopy('school_address', student.school_address)"
                      title="Single-click to copy School Address"
                    >
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">SCHOOL ADDRESS</span>
                      <span class="text-xs font-medium text-zinc-700 dark:text-zinc-300">{{ student.school_address }}</span>
                    </div>

                    <div
                      v-if="student.school_phone"
                      class="flex items-baseline justify-between gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                      :class="[copiedField === 'school_phone' && 'animate-copy-press']"
                      @click="handleCopy('school_phone', formatPhoneValue(student.school_phone))"
                      title="Single-click to copy School Phone"
                    >
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">SCHOOL PHONE</span>
                      <span class="text-xs font-bold font-mono">{{ formatPhoneValue(student.school_phone) }}</span>
                    </div>

                    <div
                      v-if="student.school_email"
                      class="flex items-baseline justify-between gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/60 p-1 -m-1 rounded transition-all duration-150"
                      :class="[copiedField === 'school_email' && 'animate-copy-press']"
                      @click="handleCopy('school_email', student.school_email)"
                      title="Single-click to copy School Email"
                    >
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">SCHOOL E-MAIL</span>
                      <span class="text-xs font-medium">{{ student.school_email }}</span>
                    </div>
                  </template>

                  <button
                    type="button"
                    @click="toggleSection('education')"
                    class="mt-1 pt-1.5 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-zinc-400 hover:text-blue-600 transition-colors cursor-pointer"
                  >
                    <span>{{ eduExpanded ? 'SHOW LESS' : 'SHOW MORE' }}</span>
                    <ChevronDown class="w-3 h-3 transition-transform duration-200" :class="eduExpanded ? 'rotate-180' : ''" />
                  </button>
                </div>
              </div>

            </div>

            <!-- ═════════════════════════════════════════════════════════════
                 COLUMN 2: Academic & Languages, Chosen Universities & Family
                 ═════════════════════════════════════════════════════════════ -->
            <div class="flex flex-col gap-2">
              
              <!-- 2.1 Academic & Languages Header & Cards -->
              <div class="flex flex-col gap-1.5">
                <div class="flex items-center gap-1.5 px-1 text-zinc-500 dark:text-zinc-400 font-bold uppercase tracking-wider text-[11.5px]">
                  <Layers class="w-3.5 h-3.5 text-blue-600" />
                  <span>ACADEMIC & LANGUAGES</span>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1">
                  <!-- TARIFF CARD -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.tariff ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'tariff' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('tariff', student.tariff)"
                    title="Single-click to copy Tariff"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">TARIFF</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('tariff', student.tariff)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'tariff'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('tariff', student.tariff)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div class="mt-0.5">
                      <template v-if="editingField === 'tariff'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                          <select
                            v-model="editValue"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          >
                            <option value="">Select Tariff</option>
                            <option v-for="t in tariffOptions" :key="t" :value="t">{{ t }}</option>
                          </select>
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit('tariff')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <div class="flex flex-col gap-1">
                          <span v-if="student.tariff" class="inline-flex self-start px-2 py-0.5 rounded text-xs font-bold uppercase bg-[#00875a] text-white shadow-2xs">
                            {{ student.tariff }}
                          </span>
                          <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                          <span v-if="student.tariff && computedTariffPrice > 0" class="text-[12px] font-semibold text-zinc-400 font-mono tracking-tight">
                            {{ formatCurrency(computedTariffPrice) }}
                          </span>
                        </div>
                      </template>
                    </div>
                  </div>

                  <!-- LEVEL TO STUDY 1 -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.level ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'level' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('level', student.level)"
                    title="Single-click to copy Level to Study"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">LEVEL TO STUDY</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('level', student.level)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'level'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('level', student.level)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                        <button
                          v-if="!showLevel2"
                          type="button"
                          @click.stop="showLevel2 = true"
                          class="p-0.5 text-zinc-400 hover:text-blue-600"
                          title="Add Level to Study 2"
                        >
                          <Plus class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div class="mt-0.5">
                      <template v-if="editingField === 'level'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                          <select
                            v-model="editValue"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          >
                            <option value="">Select Level</option>
                            <option v-for="l in levelOptions" :key="l" :value="l">{{ l }}</option>
                          </select>
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit('level')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.level" class="inline-flex px-2 py-0.5 rounded text-xs font-bold uppercase bg-[#0052cc] text-white shadow-2xs">
                          {{ student.level }}
                        </span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- LEVEL TO STUDY 2 (Optional) -->
                  <div
                    v-if="showLevel2"
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.level2 ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'level2' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('level2', student.level2)"
                    title="Single-click to copy Level to Study 2"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">LEVEL TO STUDY 2</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('level2', student.level2)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'level2'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('level2', student.level2)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="clearAndHideLevel2" class="p-0.5 text-zinc-400 hover:text-rose-500" title="Remove Level 2">
                          <X class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div class="mt-0.5">
                      <template v-if="editingField === 'level2'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                          <select
                            v-model="editValue"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          >
                            <option value="">Select Level 2</option>
                            <option v-for="l in levelOptions" :key="l" :value="l">{{ l }}</option>
                          </select>
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit('level2')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.level2" class="inline-flex px-2 py-0.5 rounded text-xs font-bold uppercase bg-[#ff9900] text-white shadow-2xs">
                          {{ student.level2 }}
                        </span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- LANGUAGE CERTIFICATE 1 (Split Badge Box) -->
                  <div
                    class="sm:col-span-2 relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      (student.language_certificate && student.language_certificate !== 'NO CERTIFICATE') ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'cert1' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('cert1', `${student.language_certificate || ''} (SCORE: ${student.certificate_score || '—'})`)"
                    title="Single-click to copy Language Certificate 1"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">LANGUAGE CERTIFICATE 1</span>
                      <div class="flex items-center gap-1.5">
                        <button
                          v-if="student.language_certificate && student.language_certificate !== 'NO CERTIFICATE'"
                          type="button"
                          @click.stop="handleCopy('cert1', `${student.language_certificate || ''} (SCORE: ${student.certificate_score || '—'})`)"
                          class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100"
                        >
                          <Check v-if="copiedField === 'cert1'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="openCertModal(1)" class="p-0.5 text-zinc-400 hover:text-zinc-700" title="Edit Certificate">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                        <button
                          v-if="!showCert2"
                          type="button"
                          @click.stop="showCert2 = true; openCertModal(2);"
                          class="p-0.5 text-zinc-400 hover:text-blue-600"
                          title="Add Language Certificate 2"
                        >
                          <Plus class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div class="mt-0.5">
                      <div v-if="student.language_certificate && student.language_certificate !== 'NO CERTIFICATE'" class="inline-flex items-center text-xs font-bold rounded overflow-hidden shadow-2xs select-none">
                        <span class="bg-[#de350b] text-white px-2 py-0.5 uppercase tracking-wide">{{ student.language_certificate }}</span>
                        <span class="bg-[#0052cc] text-white px-2 py-0.5">SCORE: {{ student.certificate_score || '—' }}</span>
                      </div>
                      <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                    </div>
                  </div>

                  <!-- LANGUAGE CERTIFICATE 2 (Optional) -->
                  <div
                    v-if="showCert2"
                    class="sm:col-span-2 relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      (student.language_certificate_2 && student.language_certificate_2 !== 'NO CERTIFICATE') ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'cert2' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('cert2', `${student.language_certificate_2 || ''} (SCORE: ${student.certificate_score_2 || '—'})`)"
                    title="Single-click to copy Language Certificate 2"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">LANGUAGE CERTIFICATE 2</span>
                      <div class="flex items-center gap-1.5">
                        <button
                          v-if="student.language_certificate_2 && student.language_certificate_2 !== 'NO CERTIFICATE'"
                          type="button"
                          @click.stop="handleCopy('cert2', `${student.language_certificate_2 || ''} (SCORE: ${student.certificate_score_2 || '—'})`)"
                          class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100"
                        >
                          <Check v-if="copiedField === 'cert2'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="openCertModal(2)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                        <button
                          v-if="!showCert3"
                          type="button"
                          @click.stop="showCert3 = true; openCertModal(3);"
                          class="p-0.5 text-zinc-400 hover:text-blue-600"
                          title="Add Language Certificate 3"
                        >
                          <Plus class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="clearAndHideCert(2)" class="p-0.5 text-zinc-400 hover:text-rose-500" title="Remove Certificate 2">
                          <X class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div class="mt-0.5">
                      <div v-if="student.language_certificate_2 && student.language_certificate_2 !== 'NO CERTIFICATE'" class="inline-flex items-center text-xs font-bold rounded overflow-hidden shadow-2xs select-none">
                        <span class="bg-[#00b8d9] text-white px-2 py-0.5 uppercase tracking-wide">{{ student.language_certificate_2 }}</span>
                        <span class="bg-[#0052cc] text-white px-2 py-0.5">SCORE: {{ student.certificate_score_2 || '—' }}</span>
                      </div>
                      <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                    </div>
                  </div>

                  <!-- LANGUAGE CERTIFICATE 3 (Optional) -->
                  <div
                    v-if="showCert3"
                    class="sm:col-span-2 relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      (student.language_certificate_3 && student.language_certificate_3 !== 'NO CERTIFICATE') ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'cert3' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('cert3', `${student.language_certificate_3 || ''} (SCORE: ${student.certificate_score_3 || '—'})`)"
                    title="Single-click to copy Language Certificate 3"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">LANGUAGE CERTIFICATE 3</span>
                      <div class="flex items-center gap-1.5">
                        <button
                          v-if="student.language_certificate_3 && student.language_certificate_3 !== 'NO CERTIFICATE'"
                          type="button"
                          @click.stop="handleCopy('cert3', `${student.language_certificate_3 || ''} (SCORE: ${student.certificate_score_3 || '—'})`)"
                          class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100"
                        >
                          <Check v-if="copiedField === 'cert3'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="openCertModal(3)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="clearAndHideCert(3)" class="p-0.5 text-zinc-400 hover:text-rose-500" title="Remove Certificate 3">
                          <X class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div class="mt-0.5">
                      <div v-if="student.language_certificate_3 && student.language_certificate_3 !== 'NO CERTIFICATE'" class="inline-flex items-center text-xs font-bold rounded overflow-hidden shadow-2xs select-none">
                        <span class="bg-[#ff5630] text-white px-2 py-0.5 uppercase tracking-wide">{{ student.language_certificate_3 }}</span>
                        <span class="bg-[#0052cc] text-white px-2 py-0.5">SCORE: {{ student.certificate_score_3 || '—' }}</span>
                      </div>
                      <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 2.2 Chosen Universities Header & Cards (100% UniApp2 UX & Behavior) -->
              <div class="flex flex-col gap-2">
                <div class="flex items-center gap-1.5 px-1 text-zinc-500 dark:text-zinc-400 font-bold uppercase tracking-wider text-[11.5px]">
                  <GraduationCap class="w-3.5 h-3.5 text-blue-600" />
                  <span>CHOSEN UNIVERSITIES</span>
                </div>

                <div class="flex flex-col gap-1.5">
                  <!-- Dynamic Loop for 5 University Slots -->
                  <template v-for="slot in 5" :key="slot">
                    <div
                      v-if="slot === 1 || (slot === 2 && showUni2) || (slot === 3 && showUni3) || (slot === 4 && showUni4) || (slot === 5 && showUni5)"
                      class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                      :class="[
                        (student as any)[`university_${slot}`] ? 'border-l-blue-600' : 'border-l-rose-500',
                        copiedField === `uni${slot}` && 'animate-copy-press'
                      ]"
                      @click="handleCopy(`uni${slot}`, (student as any)[`university_${slot}`] ? `${(student as any)[`university_${slot}`]} (${(student as any)[`university_${slot}_status`] || 'Chosen'})` : '')"
                      :title="`Single-click to copy University ${slot}`"
                    >
                      <!-- Top title and actions -->
                      <div class="flex items-center justify-between">
                        <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">
                          UNIVERSITY {{ slot }}
                        </span>
                        <div class="flex items-center gap-1.5">
                          <!-- Copy -->
                          <button
                            v-if="(student as any)[`university_${slot}`]"
                            type="button"
                            @click.stop="handleCopy(`uni${slot}`, `${(student as any)[`university_${slot}`]} (${(student as any)[`university_${slot}_status`] || 'Chosen'})`)"
                            class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100"
                            title="Copy university details"
                          >
                            <Check v-if="copiedField === `uni${slot}`" class="w-3.5 h-3.5 text-emerald-500" />
                            <Copy v-else class="w-3.5 h-3.5" />
                          </button>
                          
                          <!-- Edit University Name (Modal) -->
                          <button
                            type="button"
                            @click.stop="openUniversityModal(slot)"
                            class="p-0.5 text-zinc-400 hover:text-zinc-700"
                            :title="`Edit University ${slot}`"
                          >
                            <Pencil class="w-3.5 h-3.5" />
                          </button>

                          <!-- Eraser (Clear university selection with prompt) -->
                          <button
                            v-if="(student as any)[`university_${slot}`]"
                            type="button"
                            @click.stop="clearUniversitySlot(slot)"
                            class="p-0.5 text-zinc-400 hover:text-rose-600"
                            title="Clear university selection"
                          >
                            <Eraser class="w-3.5 h-3.5" />
                          </button>

                          <!-- Sequential + Adder Button -->
                          <button
                            v-if="slot === 1 && !showUni2"
                            type="button"
                            @click.stop="showUni2 = true; openUniversityModal(2);"
                            class="p-0.5 text-zinc-400 hover:text-blue-600"
                            title="Add University 2"
                          >
                            <Plus class="w-3.5 h-3.5" />
                          </button>
                          <button
                            v-else-if="slot === 2 && !showUni3"
                            type="button"
                            @click.stop="showUni3 = true; openUniversityModal(3);"
                            class="p-0.5 text-zinc-400 hover:text-blue-600"
                            title="Add University 3"
                          >
                            <Plus class="w-3.5 h-3.5" />
                          </button>
                          <button
                            v-else-if="slot === 3 && !showUni4"
                            type="button"
                            @click.stop="showUni4 = true; openUniversityModal(4);"
                            class="p-0.5 text-zinc-400 hover:text-blue-600"
                            title="Add University 4"
                          >
                            <Plus class="w-3.5 h-3.5" />
                          </button>
                          <button
                            v-else-if="slot === 4 && !showUni5"
                            type="button"
                            @click.stop="showUni5 = true; openUniversityModal(5);"
                            class="p-0.5 text-zinc-400 hover:text-blue-600"
                            title="Add University 5"
                          >
                            <Plus class="w-3.5 h-3.5" />
                          </button>

                          <!-- Sequential X Remover Button for slots >= 2 -->
                          <button
                            v-if="slot >= 2"
                            type="button"
                            @click.stop="clearAndHideUni(slot)"
                            class="p-0.5 text-zinc-400 hover:text-rose-500"
                            :title="`Remove University ${slot}`"
                          >
                            <X class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      <!-- Card Body -->
                      <div class="mt-0.5">
                        <template v-if="(student as any)[`university_${slot}`]">
                          <div class="text-[13.5px] font-bold text-[#0f172a] dark:text-zinc-100 uppercase tracking-wide">
                            {{ (student as any)[`university_${slot}`] }}
                          </div>
                          
                          <div class="mt-1.5 flex items-center relative flex-wrap gap-2">
                            <!-- Clickable Status Badge Pill (Clean text only, no bullet mark) -->
                            <div class="relative">
                              <button
                                type="button"
                                @click.stop="activeStatusDropdown = activeStatusDropdown === slot ? null : slot"
                                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10.5px] font-extrabold uppercase shadow-2xs border cursor-pointer hover:opacity-90 active:scale-95 transition-all select-none"
                                :class="getUniStatusBadgeClass((student as any)[`university_${slot}_status`])"
                                title="Click to change application status"
                              >
                                <span>{{ (student as any)[`university_${slot}_status`] || 'Chosen' }}</span>
                              </button>

                              <!-- Floating Status Dropdown Popover (Matching UniApp2) -->
                              <div
                                v-if="activeStatusDropdown === slot"
                                class="absolute left-0 top-full mt-1.5 w-36 bg-white dark:bg-[#1c1c1e] border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-xl z-50 py-1 flex flex-col gap-0.5 animate-in fade-in slide-in-from-top-1 duration-100"
                                @click.stop
                              >
                                <div class="px-2.5 py-1 text-[10px] uppercase font-bold tracking-wider text-zinc-400 border-b border-zinc-100 dark:border-zinc-800 select-none">
                                  University Status
                                </div>
                                <button
                                  v-for="st in universityStatusList"
                                  :key="st.name"
                                  type="button"
                                  @click.stop="handleStatusSelect(slot, st.name)"
                                  class="w-full text-left px-2.5 py-1 text-[12.5px] font-semibold text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 flex items-center gap-2 cursor-pointer transition-all"
                                >
                                  <span class="h-2 w-2 rounded-full flex-shrink-0" :class="getStatusDotClass(st.name)" />
                                  <span>{{ st.name }}</span>
                                </button>
                              </div>
                            </div>

                            <!-- Clickable Major Pill (Clean text only, no icon) -->
                            <button
                              type="button"
                              @click.stop="openMajorModal(slot)"
                              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10.5px] font-bold border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/40 active:scale-95 transition-all shadow-2xs select-none cursor-pointer"
                              :title="`Click to edit major for University ${slot}`"
                            >
                              <span>{{ (((student as any)[`university_${slot}_major`]) || 'Add Major').toUpperCase() }}</span>
                            </button>
                          </div>
                        </template>
                        <template v-else>
                          <span class="text-[13px] font-semibold text-rose-600">Not provided</span>
                        </template>
                      </div>
                    </div>
                  </template>
                </div>
              </div>

              <!-- 2.3 Family Info Header & Cards -->
              <div class="flex flex-col gap-2">
                <div class="flex items-center gap-1.5 px-1 text-zinc-500 dark:text-zinc-400 font-bold uppercase tracking-wider text-[11.5px]">
                  <User class="w-3.5 h-3.5 text-blue-600" />
                  <span>FAMILY INFO</span>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  <!-- FATHER FULLNAME -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.father_name ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'father_name' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('father_name', student.father_name)"
                    title="Single-click to copy Father Full Name"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">FATHER FULLNAME</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('father_name', student.father_name)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'father_name'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('father_name', student.father_name)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'father_name'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('father_name')" @keydown.esc="cancelInlineEdit">
                          <input v-model="editValue" type="text" class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none" autoFocus />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('father_name')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.father_name" class="text-[13px] font-bold uppercase text-[#0f172a] dark:text-zinc-100">{{ student.father_name }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- MOTHER FULLNAME -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.mother_name ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'mother_name' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('mother_name', student.mother_name)"
                    title="Single-click to copy Mother Full Name"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">MOTHER FULLNAME</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('mother_name', student.mother_name)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'mother_name'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('mother_name', student.mother_name)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'mother_name'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('mother_name')" @keydown.esc="cancelInlineEdit">
                          <input v-model="editValue" type="text" class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none" autoFocus />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('mother_name')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.mother_name" class="text-[13px] font-bold uppercase text-[#0f172a] dark:text-zinc-100">{{ student.mother_name }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- FATHER PHONE (Formatted) -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.father_phone ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'father_phone' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('father_phone', formatPhoneValue(student.father_phone))"
                    title="Single-click to copy Father Phone"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">FATHER PHONE</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('father_phone', formatPhoneValue(student.father_phone))" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'father_phone'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('father_phone', student.father_phone)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'father_phone'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('father_phone')" @keydown.esc="cancelInlineEdit">
                          <input
                            :value="editValue"
                            @input="onInlineInput('father_phone', $event)"
                            type="text"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold font-mono bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('father_phone')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.father_phone" class="text-[13px] font-bold font-mono text-[#0f172a] dark:text-zinc-100">{{ formatPhoneValue(student.father_phone) }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- MOTHER PHONE (Formatted) -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.mother_phone ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'mother_phone' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('mother_phone', formatPhoneValue(student.mother_phone))"
                    title="Single-click to copy Mother Phone"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">MOTHER PHONE</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('mother_phone', formatPhoneValue(student.mother_phone))" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'mother_phone'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('mother_phone', student.mother_phone)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'mother_phone'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('mother_phone')" @keydown.esc="cancelInlineEdit">
                          <input
                            :value="editValue"
                            @input="onInlineInput('mother_phone', $event)"
                            type="text"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold font-mono bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('mother_phone')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.mother_phone" class="text-[13px] font-bold font-mono text-[#0f172a] dark:text-zinc-100">{{ formatPhoneValue(student.mother_phone) }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- FATHER JOB -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.father_job ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'father_job' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('father_job', student.father_job)"
                    title="Single-click to copy Father Job"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">FATHER JOB</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('father_job', student.father_job)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'father_job'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('father_job', student.father_job)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'father_job'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('father_job')" @keydown.esc="cancelInlineEdit">
                          <input v-model="editValue" type="text" class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none" autoFocus />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('father_job')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.father_job" class="text-[13px] font-bold uppercase text-[#0f172a] dark:text-zinc-100">{{ student.father_job }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- MOTHER JOB -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.mother_job ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'mother_job' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('mother_job', student.mother_job)"
                    title="Single-click to copy Mother Job"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">MOTHER JOB</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('mother_job', student.mother_job)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'mother_job'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('mother_job', student.mother_job)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'mother_job'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('mother_job')" @keydown.esc="cancelInlineEdit">
                          <input v-model="editValue" type="text" class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none" autoFocus />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('mother_job')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.mother_job" class="text-[13px] font-bold uppercase text-[#0f172a] dark:text-zinc-100">{{ student.mother_job }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- NOTES -->
                  <div
                    class="sm:col-span-2 relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.notes ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'notes' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('notes', student.notes)"
                    title="Single-click to copy Notes"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">NOTES</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('notes', student.notes)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'notes'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('notes', student.notes)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'notes'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                          <textarea
                            v-model="editValue"
                            rows="2"
                            class="w-full pl-2 pr-14 py-1 text-xs font-medium bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          />
                          <div class="absolute right-1 top-2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit('notes')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.notes" class="text-[13px] font-bold uppercase text-[#0f172a] dark:text-zinc-100 leading-snug">{{ student.notes }}</span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <!-- =============================================================
                 COLUMN 3: System & Finance (Matching Solid Color Style)
                 ============================================================= -->
            <div class="flex flex-col gap-3.5">
              <div class="flex flex-col gap-2">
                <div class="flex items-center gap-1.5 px-1 text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider text-[11.5px]">
                  <Landmark class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                  <span>SYSTEM & FINANCE</span>
                </div>

                <div class="flex flex-col gap-2">
                  <!-- 3.1 OFFICE CARD (Solid Blue) -->
                  <div
                    class="bg-[#1d70f2] rounded-xl px-3.5 py-2.5 text-white flex flex-col justify-between shadow-xs cursor-pointer hover:brightness-105 transition-all duration-150 group/card"
                    :class="[copiedField === 'office' && 'animate-copy-press']"
                    @click="handleCopy('office', student.office)"
                    title="Single-click to copy Office"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[11px] uppercase font-extrabold tracking-wider text-blue-100 flex items-center gap-1.5">
                        <Building2 class="w-3.5 h-3.5" />
                        OFFICE
                      </span>
                      <div class="flex items-center gap-1.5">
                        <button type="button" @click.stop="handleCopy('office', student.office)" class="p-0.5 text-blue-200 hover:text-white transition-colors" title="Copy Office">
                          <Check v-if="copiedField === 'office'" class="w-3.5 h-3.5 text-white" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('office', student.office)" class="p-0.5 text-blue-200 hover:text-white transition-colors" title="Edit Office">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-1">
                      <template v-if="editingField === 'office'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                          <select
                            v-model="editValue"
                            class="bg-blue-800 text-white text-xs font-bold pl-2 pr-14 py-1 rounded border border-blue-400 outline-none w-full"
                            autoFocus
                          >
                            <option v-for="opt in officeOptions" :key="opt" :value="opt">{{ opt }}</option>
                          </select>
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button
                              type="button"
                              @click="saveInlineEdit('office')"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Save"
                            >
                              <Check class="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              @click="cancelInlineEdit"
                              class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs"
                              title="Cancel"
                            >
                              <X class="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span class="text-[15.5px] font-extrabold tracking-wide uppercase">{{ student.office || 'Not provided' }}</span>
                      </template>
                    </div>
                  </div>

                  <!-- 3.2 BALANCE CARD (Solid Crimson / Green) -->
                  <div
                    class="rounded-xl px-3.5 py-2.5 text-white flex flex-col justify-between shadow-xs cursor-pointer hover:brightness-105 transition-all duration-150 group/card"
                    :class="[
                      computedBalance < 0 ? 'bg-[#ff1853]' : 'bg-[#00b074]',
                      copiedField === 'balance' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('balance', String(computedBalance))"
                    title="Single-click to copy Balance"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[11px] uppercase font-extrabold tracking-wider text-white/95 flex items-center gap-1.5">
                        <Landmark class="w-3.5 h-3.5" />
                        BALANCE
                      </span>
                      <button type="button" @click.stop="handleCopy('balance', String(computedBalance))" class="p-0.5 text-white/80 hover:text-white transition-colors" title="Copy Balance">
                        <Check v-if="copiedField === 'balance'" class="w-3.5 h-3.5 text-white" />
                        <Copy v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div v-if="isPaymentsLoading && !student?.tariff" class="h-6 w-32 bg-white/30 rounded-md animate-pulse mt-1" />
                    <div v-else class="mt-1 text-[16px] font-extrabold tracking-wide font-mono">
                      {{ formatCurrency(computedBalance) }}
                    </div>
                  </div>

                  <!-- 3.3 PAYMENTS DONE CARD (Solid Emerald) -->
                  <div
                    class="bg-[#00b074] rounded-xl px-3.5 py-2.5 text-white flex flex-col justify-between shadow-xs cursor-pointer hover:brightness-105 transition-all duration-150 group/card"
                    :class="[copiedField === 'payments_done' && 'animate-copy-press']"
                    @click="handleCopy('payments_done', String(computedPaymentsDone))"
                    title="Single-click to copy Payments Done"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[11px] uppercase font-extrabold tracking-wider text-emerald-100 flex items-center gap-1.5">
                        <CheckSquare class="w-3.5 h-3.5" />
                        PAYMENTS DONE
                      </span>
                      <button type="button" @click.stop="handleCopy('payments_done', String(computedPaymentsDone))" class="p-0.5 text-emerald-200 hover:text-white transition-colors" title="Copy Payments Done">
                        <Check v-if="copiedField === 'payments_done'" class="w-3.5 h-3.5 text-white" />
                        <Copy v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div v-if="isPaymentsLoading && student?.balance === undefined" class="h-6 w-32 bg-white/30 rounded-md animate-pulse mt-1" />
                    <div v-else class="mt-1 text-[16px] font-extrabold tracking-wide font-mono">
                      {{ formatCurrency(computedPaymentsDone) }}
                    </div>
                  </div>

                  <!-- 3.4 DISCOUNT CARD (Solid Orange) -->
                  <div
                    class="bg-[#ff6700] rounded-xl px-3.5 py-2.5 text-white flex flex-col justify-between shadow-xs cursor-pointer hover:brightness-105 transition-all duration-150 group/card"
                    :class="[copiedField === 'discount' && 'animate-copy-press']"
                    @click="handleCopy('discount', String(computedDiscount))"
                    title="Single-click to copy Discount"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[11px] uppercase font-extrabold tracking-wider text-orange-100 flex items-center gap-1.5">
                        <Tag class="w-3.5 h-3.5" />
                        DISCOUNT
                      </span>
                      <button type="button" @click.stop="handleCopy('discount', String(computedDiscount))" class="p-0.5 text-orange-200 hover:text-white transition-colors" title="Copy Discount">
                        <Check v-if="copiedField === 'discount'" class="w-3.5 h-3.5 text-white" />
                        <Copy v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div v-if="isPaymentsLoading && student?.discount === undefined" class="h-6 w-24 bg-white/30 rounded-md animate-pulse mt-1" />
                    <div v-else class="mt-1 text-[16px] font-extrabold tracking-wide font-mono">
                      {{ formatCurrency(computedDiscount) }}
                    </div>
                  </div>

                  <!-- 3.5 WITHDRAWN CARD (Solid Rose) -->
                  <div
                    v-if="computedWithdrawals > 0"
                    class="bg-[#e11d48] rounded-xl px-3.5 py-2.5 text-white flex flex-col justify-between shadow-xs cursor-pointer hover:brightness-105 transition-all duration-150 group/card"
                    :class="[copiedField === 'withdrawn' && 'animate-copy-press']"
                    @click="handleCopy('withdrawn', String(computedWithdrawals))"
                    title="Single-click to copy Withdrawn"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[11px] uppercase font-extrabold tracking-wider text-rose-100 flex items-center gap-1.5">
                        <ArrowDownCircle class="w-3.5 h-3.5" />
                        WITHDRAWN
                      </span>
                      <button type="button" @click.stop="handleCopy('withdrawn', String(computedWithdrawals))" class="p-0.5 text-rose-200 hover:text-white transition-colors" title="Copy Withdrawn">
                        <Check v-if="copiedField === 'withdrawn'" class="w-3.5 h-3.5 text-white" />
                        <Copy v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div class="mt-1 text-[16px] font-extrabold tracking-wide font-mono">
                      {{ formatCurrency(computedWithdrawals) }}
                    </div>
                  </div>

                  <!-- 3.6 STUDENT ID -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] border-l-blue-600 rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[copiedField === 'student_id' && 'animate-copy-press']"
                    @click="handleCopy('student_id', student.id)"
                    title="Single-click to copy Student ID"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">STUDENT ID</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('student_id', student.id)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'student_id'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('id', student.id)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'id'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.enter="saveInlineEdit('id')" @keydown.esc="cancelInlineEdit">
                          <input v-model="editValue" type="text" class="w-full pl-2 pr-14 py-1 text-xs font-bold font-mono uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none" autoFocus />
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('id')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span class="font-bold font-mono text-[14px] text-zinc-900 dark:text-zinc-100 uppercase">{{ student.id }}</span>
                      </template>
                    </div>
                  </div>

                  <!-- 3.6 GROUP -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.student_group ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'student_group' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('student_group', student.student_group)"
                    title="Single-click to copy Group"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">GROUP</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('student_group', student.student_group)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'student_group'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('student_group', student.student_group)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'student_group'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                          <select
                            v-model="editValue"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          >
                            <option value="">Select Group</option>
                            <option v-for="g in groupOptions" :key="g" :value="g">{{ g }}</option>
                          </select>
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('student_group')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.student_group" class="inline-flex px-2 py-0.5 rounded text-xs font-bold uppercase bg-[#6554c0] text-white shadow-2xs">
                          {{ student.student_group }}
                        </span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- 3.7 LEAD BY -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.lead_by ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'lead_by' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('lead_by', student.lead_by)"
                    title="Single-click to copy Lead Source"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">LEAD BY</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('lead_by', student.lead_by)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'lead_by'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('lead_by', student.lead_by)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'lead_by'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                          <select
                            v-model="editValue"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          >
                            <option value="">Select Lead Source</option>
                            <option v-for="l in leadByOptions" :key="l" :value="l">{{ l }}</option>
                          </select>
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('lead_by')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.lead_by" class="inline-flex px-2 py-0.5 rounded text-xs font-bold uppercase bg-[#00b8d9] text-white shadow-2xs">
                          {{ student.lead_by }}
                        </span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>

                  <!-- 3.8 MISSING DOCUMENTS -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      (student.pick_needed && student.pick_needed.length > 0) ? 'border-l-rose-500' : 'border-l-blue-600',
                      copiedField === 'missing_docs' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('missing_docs', student.pick_needed ? student.pick_needed.join(', ') : 'FULL OK')"
                    title="Single-click to copy Missing Documents"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">MISSING DOCUMENTS</span>
                      <button type="button" @click.stop="handleCopy('missing_docs', student.pick_needed ? student.pick_needed.join(', ') : 'FULL OK')" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                        <Check v-if="copiedField === 'missing_docs'" class="w-3.5 h-3.5 text-emerald-500" />
                        <Copy v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div class="mt-0.5">
                      <div v-if="student.pick_needed && student.pick_needed.length > 0" class="flex flex-wrap gap-1">
                        <span
                          v-for="item in student.pick_needed"
                          :key="item"
                          class="inline-flex px-1.5 py-0.5 rounded text-[11px] font-bold uppercase bg-[#5243aa] text-white shadow-2xs"
                        >
                          {{ item }}
                        </span>
                      </div>
                      <span v-else class="inline-flex px-2 py-0.5 rounded text-[11px] font-black uppercase bg-[#5243aa] text-white shadow-2xs">
                        FULL OK
                      </span>
                    </div>
                  </div>

                  <!-- 3.9 KORDINATOR -->
                  <div
                    class="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-[3.5px] rounded-lg px-2.5 py-1.5 shadow-2xs hover:bg-zinc-50/70 transition-all duration-150 cursor-pointer group/card"
                    :class="[
                      student.coordinator ? 'border-l-blue-600' : 'border-l-rose-500',
                      copiedField === 'coordinator' && 'animate-copy-press'
                    ]"
                    @click="handleCopy('coordinator', student.coordinator)"
                    title="Single-click to copy Coordinator"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-[10.5px] font-bold uppercase tracking-wider text-[#0066cc] dark:text-[#38bdf8]">KORDINATOR</span>
                      <div class="flex items-center gap-1">
                        <button type="button" @click.stop="handleCopy('coordinator', student.coordinator)" class="p-0.5 text-zinc-400 hover:text-zinc-700 opacity-0 group-hover/card:opacity-100">
                          <Check v-if="copiedField === 'coordinator'" class="w-3.5 h-3.5 text-emerald-500" />
                          <Copy v-else class="w-3.5 h-3.5" />
                        </button>
                        <button type="button" @click.stop="startInlineEdit('coordinator', student.coordinator)" class="p-0.5 text-zinc-400 hover:text-zinc-700">
                          <Pencil class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-0.5">
                      <template v-if="editingField === 'coordinator'">
                        <div class="relative w-full min-w-0" @click.stop @keydown.esc="cancelInlineEdit">
                          <select
                            v-model="editValue"
                            class="w-full pl-2 pr-14 py-1 text-xs font-bold uppercase bg-zinc-50 dark:bg-zinc-800 border border-blue-500 rounded outline-none"
                            autoFocus
                          >
                            <option value="">Select Coordinator</option>
                            <option v-for="c in coordinatorOptions" :key="c" :value="c">{{ c }}</option>
                          </select>
                          <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <button type="button" @click="saveInlineEdit('coordinator')" class="h-5 w-5 inline-flex items-center justify-center rounded bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Save"><Check class="w-3.5 h-3.5" /></button>
                            <button type="button" @click="cancelInlineEdit" class="h-5 w-5 inline-flex items-center justify-center rounded bg-rose-500 hover:bg-rose-600 text-white cursor-pointer active:scale-90 transition-all shadow-2xs" title="Cancel"><X class="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <span v-if="student.coordinator" class="inline-flex px-2 py-0.5 rounded text-xs font-bold uppercase bg-[#00875a] text-white shadow-2xs">
                          {{ student.coordinator }}
                        </span>
                        <span v-else class="text-[13px] font-semibold text-rose-600">Not provided</span>
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </transition>

    <!-- ═════════════════════════════════════════════════════════════
         MODAL 1: Educational Background Modal (100% UniApp2 UX & UI)
         ═════════════════════════════════════════════════════════════ -->
    <transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isSchoolModalOpen"
        class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto"
        @click.self="isSchoolModalOpen = false"
      >
        <div class="relative bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl p-6 w-full max-w-4xl mx-4 z-[80] max-h-[90vh] overflow-y-auto">
          <button
            type="button"
            @click="isSchoolModalOpen = false"
            class="absolute right-4 top-4 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded transition-all cursor-pointer"
          >
            <X class="w-4 h-4" />
          </button>

          <h3 class="text-[17px] font-bold text-zinc-900 dark:text-zinc-100 mb-1 pr-6">
            Edit Educational Background
          </h3>
          <p class="text-[12px] text-zinc-400 dark:text-zinc-500 mb-5">
            All fields are optional — leave blank to clear.
          </p>

          <!-- 8 Columns Grid matching UniApp2 -->
          <div class="grid grid-cols-1 sm:grid-cols-8 gap-4">
            <!-- 1. FINAL SCHOOL NAME (sm:col-span-8) -->
            <div class="sm:col-span-8">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                FINAL SCHOOL NAME
              </label>
              <div class="relative">
                <input
                  type="text"
                  :value="schoolForm.final_school_name"
                  @input="onSchoolNameInput"
                  @focus="showSchoolSuggestions = true"
                  placeholder="e.g. Tashkent State University"
                  autoComplete="off"
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px]"
                />
                <!-- School Suggestions Dropdown -->
                <div
                  v-if="showSchoolSuggestions && schoolSuggestions.length > 0"
                  class="absolute left-0 right-0 mt-1 max-h-52 overflow-y-auto border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 shadow-xl z-50 divide-y divide-zinc-100 dark:divide-zinc-700/60 animate-in fade-in slide-in-from-top-1 duration-100"
                >
                  <button
                    v-for="suggestion in schoolSuggestions"
                    :key="suggestion"
                    type="button"
                    @click="selectSchoolSuggestion(suggestion)"
                    class="w-full text-left px-3.5 py-2 text-xs font-semibold hover:bg-zinc-100 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-100 transition-colors cursor-pointer"
                  >
                    {{ suggestion }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 2. MAJOR (sm:col-span-8) -->
            <div class="sm:col-span-8">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                MAJOR
              </label>
              <div class="relative">
                <input
                  type="text"
                  :value="schoolForm.major"
                  @input="onMajorInput"
                  @focus="showMajorSuggestions = true"
                  placeholder="e.g. Computer Science"
                  autoComplete="off"
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px]"
                />
                <!-- Major Suggestions Dropdown -->
                <div
                  v-if="showMajorSuggestions && uzMajorSuggestions.length > 0"
                  class="absolute left-0 right-0 mt-1 max-h-52 overflow-y-auto border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 shadow-xl z-50 divide-y divide-zinc-100 dark:divide-zinc-700/60 animate-in fade-in slide-in-from-top-1 duration-100"
                >
                  <button
                    v-for="suggestion in uzMajorSuggestions"
                    :key="suggestion"
                    type="button"
                    @click="selectMajorSuggestion(suggestion)"
                    class="w-full text-left px-3.5 py-2 text-xs font-semibold hover:bg-zinc-100 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-100 transition-colors cursor-pointer"
                  >
                    {{ suggestion }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 3. GPA (sm:col-span-2) -->
            <div class="sm:col-span-2">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                GPA
              </label>
              <input
                type="text"
                v-model="schoolForm.gpa"
                placeholder="e.g. 3.8"
                class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px] font-mono"
              />
            </div>

            <!-- 4. SYSTEM (sm:col-span-2) -->
            <div class="sm:col-span-2">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                SYSTEM
              </label>
              <div v-if="gpaSystemManual" class="flex gap-1">
                <input
                  type="text"
                  v-model="schoolForm.gpa_system"
                  placeholder="e.g. 10"
                  autoFocus
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px]"
                />
                <button
                  type="button"
                  @click="gpaSystemManual = false; schoolForm.gpa_system = '4.5'"
                  title="Back to preset systems"
                  class="shrink-0 px-2 rounded-lg border border-zinc-200 dark:border-zinc-700 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                >
                  <X class="h-3.5 w-3.5" />
                </button>
              </div>
              <select
                v-else
                :value="schoolForm.gpa_system"
                @change="handleGpaSystemChange"
                class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px]"
              >
                <option value="">Select</option>
                <option v-for="opt in GPA_SYSTEM_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>

            <!-- 5. DEGREE NO (sm:col-span-4) -->
            <div class="sm:col-span-4">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                DEGREE NO
              </label>
              <input
                type="text"
                v-model="schoolForm.degree_no"
                placeholder="e.g. AB1234567"
                class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px] font-mono uppercase"
              />
            </div>

            <!-- 6. DATE OF ENTRY (sm:col-span-4) -->
            <div class="sm:col-span-4">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                DATE OF ENTRY
              </label>
              <div class="grid grid-cols-3 gap-1 w-full">
                <!-- Year -->
                <select
                  :value="getEntryDateParts().y"
                  @change="handleEntryDateChange('y', $event)"
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-2 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[13px]"
                >
                  <option value="">YYYY</option>
                  <option v-for="yr in schoolYears" :key="yr" :value="yr">{{ yr }}</option>
                </select>
                <!-- Month -->
                <select
                  :value="getEntryDateParts().m"
                  @change="handleEntryDateChange('m', $event)"
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-2 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[13px]"
                >
                  <option value="">MM</option>
                  <option v-for="mo in schoolMonths" :key="mo" :value="mo">{{ mo }}</option>
                </select>
                <!-- Day -->
                <select
                  :value="getEntryDateParts().d"
                  @change="handleEntryDateChange('d', $event)"
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-2 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[13px]"
                >
                  <option value="">DD</option>
                  <option v-for="dy in getDaysInMonth(getEntryDateParts().y, getEntryDateParts().m)" :key="dy" :value="dy">{{ dy }}</option>
                </select>
              </div>
            </div>

            <!-- 7. DATE OF GRADUATION (sm:col-span-4) -->
            <div class="sm:col-span-4">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                DATE OF GRADUATION
              </label>
              <div class="grid grid-cols-3 gap-1 w-full">
                <!-- Year with EXPECTED -->
                <select
                  :value="gradExpected ? EXPECTED_YEAR : getGradDateParts().y"
                  @change="handleGradDateChange('y', $event)"
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border text-zinc-900 dark:text-zinc-100 px-2 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[13px]"
                  :class="gradExpected ? 'border-blue-500 text-blue-600 dark:text-blue-400 font-bold' : 'border-zinc-200 dark:border-zinc-700'"
                >
                  <option value="">YYYY</option>
                  <option :value="EXPECTED_YEAR">{{ EXPECTED_YEAR }}</option>
                  <option v-for="yr in schoolYears" :key="yr" :value="yr">{{ yr }}</option>
                </select>
                <!-- Month -->
                <select
                  :disabled="gradExpected"
                  :value="gradExpected ? '' : getGradDateParts().m"
                  @change="handleGradDateChange('m', $event)"
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-2 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[13px] disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <option value="">MM</option>
                  <option v-for="mo in schoolMonths" :key="mo" :value="mo">{{ mo }}</option>
                </select>
                <!-- Day -->
                <select
                  :disabled="gradExpected"
                  :value="gradExpected ? '' : getGradDateParts().d"
                  @change="handleGradDateChange('d', $event)"
                  class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-2 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[13px] disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <option value="">DD</option>
                  <option v-for="dy in getDaysInMonth(getGradDateParts().y, getGradDateParts().m)" :key="dy" :value="dy">{{ dy }}</option>
                </select>
              </div>
            </div>

            <!-- 8. SCHOOL ADDRESS (sm:col-span-8) -->
            <div class="sm:col-span-8">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                SCHOOL ADDRESS
              </label>
              <input
                type="text"
                v-model="schoolForm.school_address"
                placeholder="Street, city, country"
                class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px]"
              />
            </div>

            <!-- 9. SCHOOL WEBSITE (sm:col-span-3) -->
            <div class="sm:col-span-3">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                SCHOOL WEBSITE
              </label>
              <input
                type="url"
                v-model="schoolForm.school_website"
                placeholder="https://example.edu"
                class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px]"
              />
            </div>

            <!-- 10. SCHOOL PHONE (sm:col-span-2) -->
            <div class="sm:col-span-2">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                SCHOOL PHONE
              </label>
              <input
                type="tel"
                v-model="schoolForm.school_phone"
                @blur="onSchoolPhoneBlur"
                placeholder="+998 XX XXX XX XX"
                class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px] font-mono"
              />
            </div>

            <!-- 11. SCHOOL E-MAIL (sm:col-span-3) -->
            <div class="sm:col-span-3">
              <label class="block text-[12px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase mb-1.5">
                SCHOOL E-MAIL
              </label>
              <input
                type="email"
                v-model="schoolForm.school_email"
                placeholder="info@example.edu"
                class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-lg outline-none focus:border-blue-500 transition-colors text-[14px]"
              />
            </div>
          </div>

          <!-- Footer Buttons -->
          <div class="flex justify-end gap-2 mt-8">
            <button
              type="button"
              @click="isSchoolModalOpen = false"
              class="px-4 py-2 rounded-lg text-[13px] font-semibold text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
              :disabled="savingSchool"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="saveSchoolModal"
              class="px-4 py-2 rounded-lg text-[13px] font-semibold bg-blue-600 hover:bg-blue-700 text-white hover:opacity-90 transition-opacity flex items-center gap-2 shadow-xs cursor-pointer"
              :disabled="savingSchool"
            >
              <Loader2 v-if="savingSchool" class="w-4 h-4 animate-spin" />
              <span>{{ savingSchool ? 'Saving...' : 'Save Changes' }}</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═════════════════════════════════════════════════════════════
         MODAL 2: Language Certificate Modal (Matching UniApp2)
         ═════════════════════════════════════════════════════════════ -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isCertModalOpen"
        class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @click.self="isCertModalOpen = false"
      >
        <div class="relative w-full max-w-lg overflow-visible rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl p-6 z-[80]">
          <button
            type="button"
            @click="isCertModalOpen = false"
            class="absolute right-4 top-4 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded transition-all cursor-pointer"
          >
            <X class="w-4 h-4" />
          </button>

          <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 mb-3 pr-6">
            Edit Language Certificate {{ certModalSlot }}
          </h3>

          <!-- Student Info Banner (Top Banner matching UniApp2) -->
          <div v-if="student" class="flex flex-col gap-1 mb-4 p-3 bg-zinc-50 dark:bg-zinc-800/60 rounded-xl border border-zinc-200/80 dark:border-zinc-800">
            <div class="text-[13.5px] font-bold text-zinc-900 dark:text-zinc-100 uppercase">
              {{ student.full_name }}
            </div>
            <div class="flex flex-wrap items-center gap-1.5 mt-0.5">
              <span v-if="student.tariff" class="text-[10.5px] font-bold px-2 py-0.5 rounded bg-blue-600 text-white uppercase">
                {{ student.tariff }}
              </span>
              <span v-if="student.student_group" class="text-[10.5px] font-bold px-2 py-0.5 rounded bg-gray-500 text-white uppercase">
                {{ student.student_group }}
              </span>
              <span v-if="student.level" class="text-[10.5px] font-bold px-2 py-0.5 rounded bg-[#0052cc] text-white uppercase">
                {{ student.level }}
              </span>
            </div>
          </div>

          <div class="space-y-4">
            <!-- Certificate Type -->
            <div>
              <label class="block text-[11px] font-bold uppercase text-zinc-500 mb-1.5 tracking-wider">
                Certificate Type
              </label>
              <select
                v-model="certForm.type"
                class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-xl outline-none focus:border-blue-500 font-bold text-xs"
              >
                <option value="">-- Select Certificate --</option>
                <option value="NO CERTIFICATE">NO CERTIFICATE</option>
                <option v-for="opt in ['TOPIK', 'IELTS', 'TOEFL', 'CEFR', 'SAT', 'SKA']" :key="opt" :value="opt">
                  {{ opt }}
                </option>
              </select>
            </div>

            <!-- Score & Dates if Certificate is selected -->
            <template v-if="certForm.type && certForm.type !== 'NO CERTIFICATE'">
              <!-- Score Field -->
              <div>
                <label class="block text-[11px] font-bold uppercase text-zinc-500 mb-1.5 tracking-wider">
                  Score
                </label>
                <!-- Dynamic Select for TOPIK, IELTS, CEFR -->
                <select
                  v-if="['TOPIK', 'IELTS', 'CEFR'].includes(certForm.type)"
                  v-model="certForm.score"
                  class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-xl outline-none focus:border-blue-500 font-bold text-xs"
                >
                  <option value="">-- Select Score --</option>
                  <template v-if="certForm.type === 'TOPIK'">
                    <option v-for="opt in ['EXPECTED', '1', '2', '3', '4', '5', '6']" :key="opt" :value="opt">{{ opt }}</option>
                  </template>
                  <template v-else-if="certForm.type === 'IELTS'">
                    <option v-for="opt in ['EXPECTED', '4.0', '4.5', '5.0', '5.5', '6.0', '6.5', '7.0', '7.5', '8.0', '8.5', '9.0']" :key="opt" :value="opt">{{ opt }}</option>
                  </template>
                  <template v-else-if="certForm.type === 'CEFR'">
                    <option v-for="opt in ['EXPECTED', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2']" :key="opt" :value="opt">{{ opt }}</option>
                  </template>
                </select>
                <!-- Generic Input for TOEFL, SAT, SKA -->
                <input
                  v-else
                  v-model="certForm.score"
                  type="text"
                  placeholder="e.g. 6.0 or 1400"
                  class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-3 py-2 rounded-xl outline-none focus:border-blue-500 font-bold text-xs"
                />
              </div>

              <!-- Test Date & Valid Date (3-select picker with auto 2-year valid date calculation) -->
              <div v-if="['TOPIK', 'IELTS', 'CEFR', 'TOEFL', 'SKA'].includes(certForm.type)" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <!-- Test Date -->
                <div>
                  <label class="block text-[11px] font-bold uppercase text-zinc-500 mb-1.5 tracking-wider">
                    Test Date
                  </label>
                  <div class="flex gap-1">
                    <select
                      :value="getTestDateParts().y"
                      @change="updateCertTestDate('y', ($event.target as HTMLSelectElement).value)"
                      class="w-[45%] bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-2 py-1.5 rounded-lg outline-none font-bold text-xs"
                    >
                      <option value="">YYYY</option>
                      <option v-for="yr in testDateYears" :key="yr" :value="yr">{{ yr }}</option>
                    </select>
                    <select
                      :value="getTestDateParts().m"
                      @change="updateCertTestDate('m', ($event.target as HTMLSelectElement).value)"
                      class="w-[27%] bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-1.5 py-1.5 rounded-lg outline-none font-bold text-xs"
                    >
                      <option value="">MM</option>
                      <option v-for="mo in dateMonths" :key="mo" :value="mo">{{ mo }}</option>
                    </select>
                    <select
                      :value="getTestDateParts().d"
                      @change="updateCertTestDate('d', ($event.target as HTMLSelectElement).value)"
                      class="w-[28%] bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-1.5 py-1.5 rounded-lg outline-none font-bold text-xs"
                    >
                      <option value="">DD</option>
                      <option v-for="dy in Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, '0'))" :key="dy" :value="dy">{{ dy }}</option>
                    </select>
                  </div>
                </div>

                <!-- Valid Date -->
                <div>
                  <label class="block text-[11px] font-bold uppercase text-zinc-500 mb-1.5 tracking-wider">
                    Valid Date
                  </label>
                  <div class="flex gap-1">
                    <select
                      :value="getValidDateParts().y"
                      @change="updateCertValidDate('y', ($event.target as HTMLSelectElement).value)"
                      class="w-[45%] bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-2 py-1.5 rounded-lg outline-none font-bold text-xs"
                    >
                      <option value="">YYYY</option>
                      <option v-for="yr in validDateYears" :key="yr" :value="yr">{{ yr }}</option>
                    </select>
                    <select
                      :value="getValidDateParts().m"
                      @change="updateCertValidDate('m', ($event.target as HTMLSelectElement).value)"
                      class="w-[27%] bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-1.5 py-1.5 rounded-lg outline-none font-bold text-xs"
                    >
                      <option value="">MM</option>
                      <option v-for="mo in dateMonths" :key="mo" :value="mo">{{ mo }}</option>
                    </select>
                    <select
                      :value="getValidDateParts().d"
                      @change="updateCertValidDate('d', ($event.target as HTMLSelectElement).value)"
                      class="w-[28%] bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 px-1.5 py-1.5 rounded-lg outline-none font-bold text-xs"
                    >
                      <option value="">DD</option>
                      <option v-for="dy in Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, '0'))" :key="dy" :value="dy">{{ dy }}</option>
                    </select>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div class="flex items-center justify-end gap-2 pt-4 mt-4 border-t border-zinc-100 dark:border-zinc-800">
            <button
              type="button"
              @click="closeCertModal"
              class="px-4 py-2 text-xs font-bold rounded-xl bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="saveCertModal"
              class="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20 active:scale-[0.98] transition-all cursor-pointer"
            >
              Save Certificate
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═════════════════════════════════════════════════════════════
         MODAL 3: Dedicated University Name Modal with Live Suggestions
         ═════════════════════════════════════════════════════════════ -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isUniModalOpen"
        class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @click.self="closeUniversityModal"
      >
        <div class="relative w-full max-w-md overflow-visible rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl p-6 z-[80]">
          <button
            type="button"
            @click="closeUniversityModal"
            class="absolute right-4 top-4 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded transition-all cursor-pointer"
          >
            <X class="w-4 h-4" />
          </button>

          <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 mb-1 flex items-center gap-2">
            <Landmark class="h-5 w-5 text-blue-600" />
            <span>Edit University {{ uniModalSlot }}</span>
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 mb-3">
            Enter or select the university name for <strong>University {{ uniModalSlot }}</strong>.
          </p>

          <div class="relative mb-5">
            <label class="block text-[11px] font-bold uppercase text-zinc-500 mb-1.5 tracking-wider">
              University Name
            </label>
            <input
              v-model="tempUniName"
              @input="onUniInput"
              type="text"
              placeholder="e.g. KONKUK UNIVERSITY (GWANGJIN, SEOUL)"
              class="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 px-3.5 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase font-bold"
              autoFocus
              @keydown.enter="saveUniversityModal"
            />

            <!-- Live Suggestions matching all universities from Settings & options -->
            <div
              v-if="filteredUniSuggestions.length > 0"
              class="absolute left-0 right-0 mt-1 max-h-56 overflow-y-auto border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-800 shadow-2xl z-[9999] divide-y divide-zinc-100 dark:divide-zinc-700"
            >
              <button
                v-for="sug in filteredUniSuggestions"
                :key="sug"
                type="button"
                @click="selectUniSuggestion(sug)"
                class="w-full text-left px-3.5 py-2.5 text-xs font-semibold hover:bg-blue-50 dark:hover:bg-blue-950/40 text-zinc-800 dark:text-zinc-200 transition-colors cursor-pointer"
              >
                {{ sug.toUpperCase() }}
              </button>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <button
              type="button"
              @click="closeUniversityModal"
              class="px-4 py-2 text-xs font-bold rounded-xl bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="saveUniversityModal"
              class="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white active:scale-[0.98] transition-all cursor-pointer flex items-center gap-1.5 shadow-md shadow-blue-500/20"
            >
              <span>Save</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═════════════════════════════════════════════════════════════
         MODAL 4: Dedicated Major Editing Modal (Write Selected Major)
         ═════════════════════════════════════════════════════════════ -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isMajorModalOpen"
        class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @click.self="isMajorModalOpen = false"
      >
        <div class="relative w-full max-w-md overflow-visible rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl p-6 z-[80]">
          <button
            type="button"
            @click="isMajorModalOpen = false"
            class="absolute right-4 top-4 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded transition-all cursor-pointer"
          >
            <X class="w-4 h-4" />
          </button>

          <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 mb-1 flex items-center gap-2">
            <GraduationCap class="h-5 w-5 text-blue-600" />
            <span>Write Selected Major</span>
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 mb-3">
            Enter the major manually for <strong>University {{ majorModalSlot }}</strong>.
          </p>

          <div class="relative mb-5">
            <input
              v-model="tempMajorValue"
              @input="onUniMajorInput"
              type="text"
              placeholder="e.g. BUSINESS ADMINISTRATION"
              class="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 px-3.5 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase font-bold"
              autoFocus
              @keydown.enter="saveMajorModal"
            />
            
            <!-- Live Suggestions matching MAJOR_SUGGESTIONS with high z-index and shadow -->
            <div
              v-if="filteredUniMajorSuggestions.length > 0"
              class="absolute left-0 right-0 mt-1 max-h-56 overflow-y-auto border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-800 shadow-2xl z-[9999] divide-y divide-zinc-100 dark:divide-zinc-700"
            >
              <button
                v-for="sug in filteredUniMajorSuggestions"
                :key="sug"
                type="button"
                @click="selectUniMajorSuggestion(sug)"
                class="w-full text-left px-3.5 py-2.5 text-xs font-semibold hover:bg-blue-50 dark:hover:bg-blue-950/40 text-zinc-800 dark:text-zinc-200 transition-colors cursor-pointer"
              >
                {{ sug.toUpperCase() }}
              </button>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <button
              type="button"
              @click="isMajorModalOpen = false"
              class="px-4 py-2 text-xs font-bold rounded-xl bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="saveMajorModal"
              :disabled="savingMajor"
              class="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white active:scale-[0.98] transition-all disabled:opacity-50 cursor-pointer flex items-center gap-1.5 shadow-md shadow-blue-500/20"
            >
              <Loader2 v-if="savingMajor" class="w-3.5 h-3.5 animate-spin" />
              <span>Save</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═════════════════════════════════════════════════════════════
         MODAL 5: Google Drive Folder URL Modal
         ═════════════════════════════════════════════════════════════ -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isDriveModalOpen"
        class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @click.self="isDriveModalOpen = false"
      >
        <div class="relative w-full max-w-md overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl p-6 space-y-4 text-xs z-[80]">
          <div class="flex items-center justify-between pb-2 border-b border-zinc-100 dark:border-zinc-800">
            <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100">Set Google Drive Folder</h3>
            <button @click="isDriveModalOpen = false" class="rounded-lg p-1 text-zinc-400 hover:text-zinc-600">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div>
            <label class="block text-[10.5px] font-bold uppercase text-zinc-500 mb-1.5">Google Drive Folder URL</label>
            <input
              v-model="driveUrlInput"
              type="url"
              placeholder="https://drive.google.com/drive/folders/..."
              class="w-full px-3.5 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 font-medium"
            />
          </div>

          <div class="flex items-center justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
            <button type="button" @click="isDriveModalOpen = false" class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 font-bold hover:bg-zinc-100">Cancel</button>
            <button type="button" @click="saveDriveUrl" class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-md shadow-emerald-500/20">Save Folder URL</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═════════════════════════════════════════════════════════════
         MODAL 6: Permanent Delete Confirmation Dialog
         ═════════════════════════════════════════════════════════════ -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isPermanentConfirmOpen"
        class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @click.self="isPermanentConfirmOpen = false"
      >
        <div class="relative w-full max-w-md overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl p-6 space-y-4 text-xs z-[80]">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100">Confirm Permanent Deletion</h3>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">This action cannot be undone.</p>
            </div>
            <button @click="isPermanentConfirmOpen = false" class="rounded-lg p-1 text-zinc-400 hover:text-zinc-600">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 flex items-start gap-2.5">
            <AlertTriangle class="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
            <p class="leading-relaxed">
              Are you sure you want to permanently delete <strong>{{ student?.full_name }}</strong> (ID: <strong>{{ student?.id }}</strong>)? All associated records will be permanently removed.
            </p>
          </div>

          <div class="flex items-center justify-end gap-2.5 pt-2">
            <button type="button" @click="isPermanentConfirmOpen = false" class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 font-bold hover:bg-zinc-100">Cancel</button>
            <button
              type="button"
              @click="() => { emit('permanent-delete'); isPermanentConfirmOpen = false; emit('close'); }"
              class="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold shadow-md shadow-rose-600/20"
            >
              Permanently Delete
            </button>
          </div>
        </div>
      </div>
    </transition>

  </Teleport>
</template>
