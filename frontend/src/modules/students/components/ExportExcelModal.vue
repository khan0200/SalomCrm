<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  FileSpreadsheet,
  X,
  Search,
  ChevronDown,
  ChevronUp,
  Folder,
  Tag,
  GraduationCap,
  Users,
  Award,
  Contact,
  Bookmark,
  Check,
  MoreVertical
} from 'lucide-vue-next'
import type { Student } from '@/types'
import { ROW_COLOR_MAP } from '@/types'
import { useUiStore } from '@/stores/ui'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import { useAlphanumericSort } from '@/composables/useAlphanumericSort'
import XLSX from 'xlsx-js-style'

const props = defineProps<{
  isOpen: boolean
  students: Student[]
  folders?: { id: string | number; name: string }[]
  options?: any
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'open-detail', id: string): void
}>()

const uiStore = useUiStore()
const dashboardStore = useStudentDashboardStore()
const { compareStudentIds } = useAlphanumericSort()

// ── Search & Filter State inside Modal ──────────────────────────────
const searchType = ref<'all' | 'id' | 'name' | 'phone' | 'university'>('all')
const searchQuery = ref('')
const selectedFolders = ref<string[]>([])
const selectedTariffs = ref<string[]>([])
const selectedLevels = ref<string[]>([])
const selectedGroups = ref<string[]>([])
const selectedCerts = ref<string[]>([])
const selectedTags = ref<string[]>([])
const selectedLeads = ref<string[]>([])

// Dropdown open states
const isFolderDropdownOpen = ref(false)
const isTariffDropdownOpen = ref(false)
const isLevelDropdownOpen = ref(false)
const isGroupDropdownOpen = ref(false)
const isCertDropdownOpen = ref(false)
const isTagDropdownOpen = ref(false)
const isLeadDropdownOpen = ref(false)

const closeAllDropdowns = () => {
  isFolderDropdownOpen.value = false
  isTariffDropdownOpen.value = false
  isLevelDropdownOpen.value = false
  isGroupDropdownOpen.value = false
  isCertDropdownOpen.value = false
  isTagDropdownOpen.value = false
  isLeadDropdownOpen.value = false
}

type DropdownKey = 'folder' | 'tariff' | 'level' | 'group' | 'cert' | 'tag' | 'lead'
const dropdownRefs: Record<DropdownKey, typeof isFolderDropdownOpen> = {
  folder: isFolderDropdownOpen,
  tariff: isTariffDropdownOpen,
  level: isLevelDropdownOpen,
  group: isGroupDropdownOpen,
  cert: isCertDropdownOpen,
  tag: isTagDropdownOpen,
  lead: isLeadDropdownOpen,
}
const toggleDropdown = (key: DropdownKey) => {
  const target = dropdownRefs[key]
  const wasOpen = target.value
  closeAllDropdowns()
  target.value = !wasOpen
}

const toggleInList = (list: string[], value: string) => {
  const idx = list.indexOf(value)
  if (idx === -1) list.push(value)
  else list.splice(idx, 1)
}

const CERT_OPTIONS = ['NO CERTIFICATE', 'EXPECTED', 'TOPIK', 'IELTS', 'TOEFL', 'CEFR', 'SAT', 'SKA']
const PREDEFINED_TAGS = ['Call', 'Apply', 'Documents', 'Payment']

const foldersList = computed(() => {
  return (props.folders && props.folders.length > 0) ? props.folders : (props.options?.folders || [])
})

// Dynamic Option Sources (from Config + Master Students)
const tariffOptions = computed<string[]>(() => {
  const custom = (props.options?.tariffs || []).map((t: any) => typeof t === 'string' ? t : (t?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  props.students.forEach(s => { if (s.tariff) set.add(s.tariff) })
  return Array.from(set).filter(t => t !== 'NO_TARIFF' && t !== 'No Tariff').sort((a, b) => a.localeCompare(b))
})

const levelOptions = computed<string[]>(() => {
  const custom = (props.options?.levels || []).map((l: any) => typeof l === 'string' ? l : (l?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  props.students.forEach(s => {
    if (s.level) set.add(s.level)
    if (s.level2) set.add(s.level2)
  })
  return Array.from(set).filter(l => l !== 'NO_LEVEL' && l !== 'No Level').sort((a, b) => a.localeCompare(b))
})

const groupOptions = computed<string[]>(() => {
  const custom = (props.options?.groups || []).map((g: any) => typeof g === 'string' ? g : (g?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  props.students.forEach(s => { if (s.student_group) set.add(s.student_group) })
  return Array.from(set).filter(g => g !== 'NO_GROUP' && g !== 'No Group').sort((a, b) => a.localeCompare(b))
})

const leadOptions = computed<string[]>(() => {
  const custom = (props.options?.leads || []).map((l: any) => typeof l === 'string' ? l : (l?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  props.students.forEach(s => { if (s.lead_by) set.add(s.lead_by) })
  return Array.from(set).filter(l => l !== 'NO_LEADBY' && l !== 'No Lead by').sort((a, b) => a.localeCompare(b))
})

const tagOptions = computed<string[]>(() => {
  const backendTags = (props.options?.tags || []).map((t: any) => typeof t === 'string' ? t : (t?.name || '')).filter(Boolean)
  const set = new Set<string>([...PREDEFINED_TAGS, ...backendTags])
  props.students.forEach(s => {
    if (Array.isArray(s.task_tags)) {
      s.task_tags.forEach(t => { if (t) set.add(t) })
    }
  })
  const list = Array.from(set).filter(t => t !== 'Custom').sort((a, b) => a.localeCompare(b))
  return [...list, 'Custom']
})

// Student selection
const selectedStudentIds = ref<string[]>([])

// Field picker modal state
const isFieldPickerOpen = ref(false)
const fieldSearchQuery = ref('')
const expandedFieldGroup = ref<string | null>('Contact')

// ── Field Definitions (1-to-1 with UniApp2) ─────────────────────────
interface ExcelField {
  key: string
  label: string
  checked: boolean
  get: (s: Student) => any
}

interface FieldGroup {
  title: string
  fields: ExcelField[]
}

const formatGpa = (gpa: string | null | undefined, system: string | null | undefined): string => {
  const score = (gpa || '').trim()
  if (!score) return ''
  const scale = (system || '').trim()
  return scale ? `${score}/${scale}` : score
}

const formatCertificate = (cert: string | null | undefined, score: string | null | undefined): string => {
  const name = (cert || '').trim()
  const points = (score || '').trim()
  if (name && points) return `${name} ${points}`
  return name || points
}

const FIELD_GROUPS: FieldGroup[] = [
  {
    title: 'Passport Details',
    fields: [
      { key: 'full_name', label: 'Full Name', checked: true, get: (s) => s.full_name || '' },
      { key: 'family_name', label: 'Family Name', checked: true, get: (s) => (s.full_name ? s.full_name.split(' ')[0] || '' : '') },
      { key: 'given_name', label: 'Given Name', checked: true, get: (s) => (s.full_name ? s.full_name.split(' ').slice(1).join(' ') || '' : '') },
      { key: 'korean_name', label: 'Korean Name', checked: true, get: (s) => s.korean_name || '' },
      { key: 'gender', label: 'Sex', checked: true, get: (s) => s.gender || '' },
      { key: 'birthday', label: 'Birthday', checked: true, get: (s) => s.birthday || '' },
      { key: 'passport', label: 'Passport', checked: true, get: (s) => s.passport || '' },
      { key: 'passport_issue_date', label: 'Date of Issue', checked: true, get: (s) => s.passport_issue_date || '' },
      { key: 'passport_expire_date', label: 'Date of Expiration', checked: true, get: (s) => s.passport_expire_date || '' },
    ]
  },
  {
    title: 'Contact',
    fields: [
      { key: 'phone1', label: 'Phone 1', checked: true, get: (s) => s.phone1 || '' },
      { key: 'phone2', label: 'Phone 2', checked: true, get: (s) => s.phone2 || '' },
      { key: 'telegram_username', label: 'TG Username', checked: true, get: (s) => s.telegram_username || '' },
      { key: 'email', label: 'Email', checked: true, get: (s) => s.email || '' },

      { key: 'address', label: 'Address', checked: true, get: (s) => s.address || '' },

    ]
  },
  {
    title: 'Educational Background',
    fields: [
      { key: 'final_school_name', label: 'Final School Name', checked: true, get: (s) => s.final_school_name || '' },
      { key: 'major', label: 'Major', checked: true, get: (s) => s.major || '' },
      { key: 'gpa', label: 'GPA', checked: true, get: (s) => formatGpa(s.gpa, s.gpa_system) },
      { key: 'degree_no', label: 'Degree No', checked: false, get: (s) => s.degree_no || '' },
      { key: 'date_of_entry', label: 'Date of Entry', checked: false, get: (s) => s.date_of_entry || '' },
      { key: 'date_of_graduation', label: 'Date of Graduation', checked: false, get: (s) => (s.graduation_expected ? 'EXPECTED' : (s.date_of_graduation || '')) },
      { key: 'school_address', label: 'School Address', checked: false, get: (s) => s.school_address || '' },
      { key: 'school_website', label: 'School Website', checked: false, get: (s) => s.school_website || '' },
      { key: 'school_phone', label: 'School Phone', checked: false, get: (s) => s.school_phone || '' },
      { key: 'school_email', label: 'School E-mail', checked: false, get: (s) => s.school_email || '' },
    ]
  },
  {
    title: 'Academic & Languages',
    fields: [
      { key: 'tariff', label: 'Tariff', checked: false, get: (s) => s.tariff || '' },
      { key: 'level', label: 'Level to Study', checked: true, get: (s) => s.level || '' },
      { key: 'level2', label: 'Level to Study 2', checked: false, get: (s) => s.level2 || '' },
      { key: 'language_certificate', label: 'Language Certificate', checked: true, get: (s) => formatCertificate(s.language_certificate, s.certificate_score) },
      { key: 'language_certificate_2', label: 'Language Certificate 2', checked: false, get: (s) => formatCertificate(s.language_certificate_2, s.certificate_score_2) },
      { key: 'language_certificate_3', label: 'Language Certificate 3', checked: false, get: (s) => formatCertificate(s.language_certificate_3, s.certificate_score_3) },
    ]
  },
  {
    title: 'Chosen Universities',
    fields: [
      { key: 'university_1', label: 'University 1', checked: false, get: (s) => s.university_1 || '' },
      { key: 'university_1_status', label: 'University 1 Status', checked: false, get: (s) => s.university_1_status || '' },
      { key: 'university_1_major', label: 'University 1 Major', checked: false, get: (s) => s.university_1_major || '' },
      { key: 'university_2', label: 'University 2', checked: false, get: (s) => s.university_2 || '' },
      { key: 'university_2_status', label: 'University 2 Status', checked: false, get: (s) => s.university_2_status || '' },
      { key: 'university_2_major', label: 'University 2 Major', checked: false, get: (s) => s.university_2_major || '' },
      { key: 'university_3', label: 'University 3', checked: false, get: (s) => s.university_3 || '' },
      { key: 'university_3_status', label: 'University 3 Status', checked: false, get: (s) => s.university_3_status || '' },
      { key: 'university_3_major', label: 'University 3 Major', checked: false, get: (s) => s.university_3_major || '' },
      { key: 'university_4', label: 'University 4', checked: false, get: (s) => s.university_4 || '' },
      { key: 'university_4_status', label: 'University 4 Status', checked: false, get: (s) => s.university_4_status || '' },
      { key: 'university_4_major', label: 'University 4 Major', checked: false, get: (s) => s.university_4_major || '' },
      { key: 'university_5', label: 'University 5', checked: false, get: (s) => s.university_5 || '' },
      { key: 'university_5_status', label: 'University 5 Status', checked: false, get: (s) => s.university_5_status || '' },
      { key: 'university_5_major', label: 'University 5 Major', checked: false, get: (s) => s.university_5_major || '' },
    ]
  },
  {
    title: 'Family Info',
    fields: [
      { key: 'father_name', label: 'Father Fullname', checked: true, get: (s) => s.father_name || '' },
      { key: 'mother_name', label: 'Mother Fullname', checked: true, get: (s) => s.mother_name || '' },
      { key: 'father_phone', label: 'Father Phone', checked: true, get: (s) => s.father_phone || '' },
      { key: 'mother_phone', label: 'Mother Phone', checked: true, get: (s) => s.mother_phone || '' },
      { key: 'father_job', label: 'Father Job', checked: false, get: (s) => s.father_job || '' },
      { key: 'mother_job', label: 'Mother Job', checked: false, get: (s) => s.mother_job || '' },
      { key: 'notes', label: 'Notes', checked: true, get: (s) => s.notes || '' },
    ]
  },
  {
    title: 'System & Finance',
    fields: [
      { key: 'id', label: 'Student ID', checked: true, get: (s) => s.id || '' },
      { key: 'student_group', label: 'Group', checked: false, get: (s) => s.student_group || '' },
      { key: 'lead_by', label: 'Lead by', checked: false, get: (s) => s.lead_by || '' },
      { key: 'coordinator', label: 'Coordinator', checked: false, get: (s) => s.coordinator || '' },
      { key: 'office', label: 'Office', checked: false, get: (s) => s.office || '' },
      { key: 'balance', label: 'Balance (UZS)', checked: false, get: (s) => s.balance || 0 },
      { key: 'discount', label: 'Discount (UZS)', checked: false, get: (s) => s.discount || 0 },
    ]
  }
]

const checkedFields = ref<string[]>(
  FIELD_GROUPS.flatMap(g => g.fields.filter(f => f.checked).map(f => f.key))
)

// When modal opens, initialize selection or honor external triggers
watch(() => props.isOpen, (open) => {
  if (open) {
    const preselected = dashboardStore.excelInitialSelectedIds
    const autoOpen = dashboardStore.excelAutoOpenFieldPicker
    if (preselected && preselected.length > 0) {
      selectedStudentIds.value = [...preselected]
      dashboardStore.excelInitialSelectedIds = []
    } else {
      selectedStudentIds.value = []
    }

    searchQuery.value = ''
    searchType.value = 'all'
    selectedFolders.value = []
    selectedTariffs.value = []
    selectedLevels.value = []
    selectedGroups.value = []
    selectedCerts.value = []
    selectedTags.value = []
    selectedLeads.value = []
    isFieldPickerOpen.value = !!autoOpen
    dashboardStore.excelAutoOpenFieldPicker = false
    expandedFieldGroup.value = 'Contact'
    closeAllDropdowns()
  }
})

// Also watch external selection updates if modal is already opening or active
watch(() => dashboardStore.excelInitialSelectedIds, (newIds) => {
  if (newIds && newIds.length > 0) {
    selectedStudentIds.value = [...newIds]
    if (dashboardStore.excelAutoOpenFieldPicker) {
      isFieldPickerOpen.value = true
      dashboardStore.excelAutoOpenFieldPicker = false
    }
  }
}, { deep: true })

// ── Filtered Students List ──────────────────────────────────────────
const filteredStudents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const filtered = props.students.filter(s => {
    // Search query
    if (q) {
      const sId = (s.id || '').toLowerCase()
      const sName = (s.full_name || '').toLowerCase()
      const sKorean = (s.korean_name || '').toLowerCase()
      const sPassport = (s.passport || '').toLowerCase()
      const sPhone1 = (s.phone1 || '').toLowerCase()
      const sPhone2 = (s.phone2 || '').toLowerCase()

      if (searchType.value === 'id' && !sId.includes(q)) return false
      if (searchType.value === 'name' && !sName.includes(q) && !sKorean.includes(q)) return false
      if (searchType.value === 'phone' && !sPhone1.includes(q) && !sPhone2.includes(q)) return false
      if (searchType.value === 'university') {
        const unis = [s.university_1, s.university_2, s.university_3, s.university_4, s.university_5].filter(Boolean).join(' ').toLowerCase()
        if (!unis.includes(q)) return false
      }
      if (searchType.value === 'all') {
        const match = sId.includes(q) ||
          sName.includes(q) ||
          sKorean.includes(q) ||
          sPassport.includes(q) ||
          sPhone1.includes(q) ||
          sPhone2.includes(q) ||
          (s.university_1 || '').toLowerCase().includes(q)
        if (!match) return false
      }
    }

    // Folders
    if (selectedFolders.value.length > 0) {
      const studentFolderIds = (s.folder_ids || (s.folders || []).map((f: any) => f.id) || []).map((x: any) => String(x).toLowerCase())
      const hasFolder = selectedFolders.value.some(fid => {
        if (fid === 'NO_FOLDER') return studentFolderIds.length === 0
        return studentFolderIds.includes(String(fid).toLowerCase())
      })
      if (!hasFolder) return false
    }

    // Tariffs
    if (selectedTariffs.value.length > 0) {
      const hasNoTariff = selectedTariffs.value.includes('NO_TARIFF') || selectedTariffs.value.includes('No Tariff')
      const cleanTariffs = selectedTariffs.value.filter(t => t !== 'NO_TARIFF' && t !== 'No Tariff')
      const sTariff = s.tariff || ''
      const matchNo = hasNoTariff && (!sTariff || sTariff === 'NO_TARIFF' || sTariff === 'No Tariff')
      const matchTariff = cleanTariffs.length > 0 && cleanTariffs.includes(sTariff)
      if (!matchNo && !matchTariff) return false
    }

    // Levels
    if (selectedLevels.value.length > 0) {
      const hasNoLevel = selectedLevels.value.includes('NO_LEVEL') || selectedLevels.value.includes('No Level')
      const cleanLevels = selectedLevels.value.filter(l => l !== 'NO_LEVEL' && l !== 'No Level')
      const sLevel = s.level || ''
      const sLevel2 = s.level2 || ''
      const matchNo = hasNoLevel && (!sLevel || cleanLevels.includes(sLevel) || cleanLevels.includes(sLevel2))
      const matchLevel = (sLevel && cleanLevels.includes(sLevel)) || (sLevel2 && cleanLevels.includes(sLevel2))
      if (!matchNo && !matchLevel) return false
    }

    // Groups
    if (selectedGroups.value.length > 0) {
      const hasNoGroup = selectedGroups.value.includes('NO_GROUP') || selectedGroups.value.includes('No Group')
      const cleanGroups = selectedGroups.value.filter(g => g !== 'NO_GROUP' && g !== 'No Group')
      const sGroup = s.student_group || ''
      const matchNo = hasNoGroup && (!sGroup || cleanGroups.includes(sGroup))
      const matchGroup = cleanGroups.length > 0 && cleanGroups.includes(sGroup)
      if (!matchNo && !matchGroup) return false
    }

    // Language Certs (NO CERTIFICATE / EXPECTED are special, not raw cert names)
    if (selectedCerts.value.length > 0) {
      let matchesCert = false
      if (selectedCerts.value.includes('NO CERTIFICATE')) {
        if (!s.language_certificate || s.language_certificate === 'NO CERTIFICATE') matchesCert = true
      }
      if (selectedCerts.value.includes('EXPECTED')) {
        const expected = [s.certificate_score, s.certificate_score_2, s.certificate_score_3]
          .some(sc => (sc || '').toUpperCase() === 'EXPECTED')
        if (expected) matchesCert = true
      }
      const certs = [s.language_certificate, s.language_certificate_2, s.language_certificate_3]
      if (certs.some(c => c && c !== 'NO CERTIFICATE' && selectedCerts.value.includes(c))) matchesCert = true
      if (!matchesCert) return false
    }

    // Tags ("Custom" = any tag not in the predefined set)
    if (selectedTags.value.length > 0) {
      const tags = Array.isArray(s.task_tags) ? s.task_tags : []
      const match = selectedTags.value.some(tag => {
        if (tag === 'Custom') return tags.some(t => !PREDEFINED_TAGS.includes(t))
        return tags.includes(tag)
      })
      if (!match) return false
    }

    // Leads
    if (selectedLeads.value.length > 0) {
      const hasNoLead = selectedLeads.value.includes('NO_LEADBY') || selectedLeads.value.includes('No Lead by')
      const cleanLeads = selectedLeads.value.filter(l => l !== 'NO_LEADBY' && l !== 'No Lead by')
      const cleanLeadsLower = cleanLeads.map(l => l.toLowerCase())
      const studentLead = (s.lead_by || '').trim()
      const matchNo = hasNoLead && (!studentLead || cleanLeadsLower.includes(studentLead.toLowerCase()))
      const matchLead = !!studentLead && cleanLeadsLower.includes(studentLead.toLowerCase())
      if (!matchNo && !matchLead) return false
    }

    return true
  })

  // Active students always before archived ones; stable within each group.
  return [...filtered].sort((a, b) => Number(!!a.is_deleted) - Number(!!b.is_deleted))
})

// ── Active filter summary (chips + clear-all) ────────────────────────
const hasActiveFilters = computed(() =>
  selectedFolders.value.length > 0 ||
  selectedTariffs.value.length > 0 ||
  selectedLevels.value.length > 0 ||
  selectedGroups.value.length > 0 ||
  selectedCerts.value.length > 0 ||
  selectedTags.value.length > 0 ||
  selectedLeads.value.length > 0
)

const activeFilterChips = computed(() => {
  const chips: { key: string; label: string; clear: () => void }[] = []
  if (selectedFolders.value.length > 0) {
    const label = selectedFolders.value.length === 1
      ? (selectedFolders.value[0] === 'NO_FOLDER' ? 'Folder: No Folder' : `Folder: ${(foldersList.value as any[]).find((f: any) => String(f.id).toLowerCase() === String(selectedFolders.value[0]).toLowerCase())?.name || '1'}`)
      : `Folder: ${selectedFolders.value.length}`
    chips.push({ key: 'folder', label, clear: () => { selectedFolders.value = [] } })
  }
  if (selectedTariffs.value.length > 0) {
    const label = selectedTariffs.value.length === 1
      ? `Tariff: ${selectedTariffs.value[0] === 'NO_TARIFF' ? 'No Tariff' : selectedTariffs.value[0]}`
      : `Tariff: ${selectedTariffs.value.length}`
    chips.push({ key: 'tariff', label, clear: () => { selectedTariffs.value = [] } })
  }
  if (selectedLevels.value.length > 0) {
    const label = selectedLevels.value.length === 1
      ? `Level: ${selectedLevels.value[0] === 'NO_LEVEL' ? 'No Level' : selectedLevels.value[0]}`
      : `Level: ${selectedLevels.value.length}`
    chips.push({ key: 'level', label, clear: () => { selectedLevels.value = [] } })
  }
  if (selectedGroups.value.length > 0) {
    const label = selectedGroups.value.length === 1
      ? `Group: ${selectedGroups.value[0] === 'NO_GROUP' ? 'No Group' : selectedGroups.value[0]}`
      : `Group: ${selectedGroups.value.length}`
    chips.push({ key: 'group', label, clear: () => { selectedGroups.value = [] } })
  }
  if (selectedCerts.value.length > 0) {
    const label = selectedCerts.value.length === 1
      ? `Cert: ${selectedCerts.value[0]}`
      : `Certificate: ${selectedCerts.value.length}`
    chips.push({ key: 'cert', label, clear: () => { selectedCerts.value = [] } })
  }
  if (selectedTags.value.length > 0) {
    const label = selectedTags.value.length === 1
      ? `Tag: ${selectedTags.value[0]}`
      : `Tag: ${selectedTags.value.length}`
    chips.push({ key: 'tag', label, clear: () => { selectedTags.value = [] } })
  }
  if (selectedLeads.value.length > 0) {
    const label = selectedLeads.value.length === 1
      ? `Lead: ${selectedLeads.value[0] === 'NO_LEADBY' ? 'No Lead by' : selectedLeads.value[0]}`
      : `Lead: ${selectedLeads.value.length}`
    chips.push({ key: 'lead', label, clear: () => { selectedLeads.value = [] } })
  }
  return chips
})

const clearAllExcelFilters = () => {
  searchQuery.value = ''
  selectedFolders.value = []
  selectedTariffs.value = []
  selectedLevels.value = []
  selectedGroups.value = []
  selectedCerts.value = []
  selectedTags.value = []
  selectedLeads.value = []
}

// ─── Click outside handler to dismiss open dropdowns ───────────────────────
const handleWindowClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null
  if (!target?.closest('.filter-dropdown-container')) {
    closeAllDropdowns()
  }
}

onMounted(() => {
  window.addEventListener('click', handleWindowClick)
})

onUnmounted(() => {
  window.removeEventListener('click', handleWindowClick)
})

const isAllFilteredSelected = computed(() => {
  if (filteredStudents.value.length === 0) return false
  return filteredStudents.value.every(s => selectedStudentIds.value.includes(s.id))
})

const toggleSelectAllFiltered = () => {
  if (isAllFilteredSelected.value) {
    const idsToRemove = new Set(filteredStudents.value.map(s => s.id))
    selectedStudentIds.value = selectedStudentIds.value.filter(id => !idsToRemove.has(id))
  } else {
    const newIds = new Set([...selectedStudentIds.value, ...filteredStudents.value.map(s => s.id)])
    selectedStudentIds.value = Array.from(newIds)
  }
}

const toggleStudentSelection = (id: string) => {
  if (selectedStudentIds.value.includes(id)) {
    selectedStudentIds.value = selectedStudentIds.value.filter(x => x !== id)
  } else {
    selectedStudentIds.value.push(id)
  }
}

// ── Table row display helpers (match StudentRow.vue / PaymentStudentOverview.vue) ──
const getTariffDisplayName = (s: Student): string => {
  if (!s.tariff) return 'NO TARIFF'
  if (s.tariff === 'E-VISA') {
    const hasCert = !!s.language_certificate && s.language_certificate !== 'NO CERTIFICATE'
    return `E-VISA ${hasCert ? '(TIL SERTIFIKATLI)' : '(TIL SERTIFIKATISIZ)'}`
  }
  return s.tariff
}

const getLevelBadgeClass = (level?: string | null) => {
  switch (level?.toUpperCase()) {
    case 'COLLEGE': return 'bg-[#6554c0] text-white'
    case 'LANGUAGE COURSE': return 'bg-[#ffab00] text-zinc-900'
    case 'MASTERS': return 'bg-[#00875a] text-white'
    case 'MASTER NO CERTIFICATE': return 'bg-[#00875a] text-white'
    case 'BACHELOR': return 'bg-[#0052cc] text-white'
    default: return 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300'
  }
}

const getRowStripeStyle = (s: Student) => {
  const colorKey = s.row_color?.toUpperCase()
  if (!colorKey || !ROW_COLOR_MAP[colorKey]) return {}
  return { borderLeft: `4px solid ${ROW_COLOR_MAP[colorKey].ball}` }
}

const getStudentCerts = (s: Student) => {
  const list = [
    { type: s.language_certificate, score: s.certificate_score },
    { type: s.language_certificate_2, score: s.certificate_score_2 },
    { type: s.language_certificate_3, score: s.certificate_score_3 },
  ]
  return list.filter(c => c.type && c.type !== 'NO CERTIFICATE')
}

// ── Column width helper ─────────────────────────────────────────────
const getColWidth = (key: string, label: string) => {
  const narrow = ['gpa', 'gender', 'balance', 'discount']
  const wide = ['full_name', 'given_name', 'korean_name', 'address', 'school_address', 'father_name', 'mother_name', 'final_school_name']
  if (narrow.includes(key)) return { wch: 10 }
  if (wide.includes(key)) return { wch: 35 }
  if (key === 'notes') return { wch: 30 }
  return { wch: Math.max(12, Math.min(25, label.length + 4)) }
}

// ── Style SheetJS Worksheet ─────────────────────────────────────────
const styleWorksheet = (ws: any) => {
  if (!ws || !ws['!ref']) return

  const rangeParts = ws['!ref'].split(':')
  const start = rangeParts[0]
  const end = rangeParts[1] || rangeParts[0]

  const parseCell = (str: string) => {
    const match = str.match(/^([A-Z]+)([0-9]+)$/)
    if (!match) return { c: 0, r: 0 }
    let c = 0
    for (let i = 0; i < match[1].length; i++) {
      c = c * 26 + (match[1].charCodeAt(i) - 64)
    }
    return { c: c - 1, r: parseInt(match[2], 10) - 1 }
  }

  const encodeCell = (c: number, r: number) => {
    let s = ''
    let temp = c
    while (temp >= 0) {
      s = String.fromCharCode((temp % 26) + 65) + s
      temp = Math.floor(temp / 26) - 1
    }
    return `${s}${r + 1}`
  }

  const startCell = parseCell(start)
  const endCell = parseCell(end)

  const headerStyle = {
    font: { name: 'Segoe UI', sz: 11, bold: true, color: { rgb: 'FFFFFF' } },
    fill: { fgColor: { rgb: '1F497D' } }, // Premium Deep Navy Blue
    alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
    border: {
      top: { style: 'thin', color: { rgb: '1F497D' } },
      bottom: { style: 'medium', color: { rgb: '000000' } },
      left: { style: 'thin', color: { rgb: '1F497D' } },
      right: { style: 'thin', color: { rgb: '1F497D' } }
    }
  }

  const thinBorder = {
    top: { style: 'thin', color: { rgb: 'D9D9D9' } },
    bottom: { style: 'thin', color: { rgb: 'D9D9D9' } },
    left: { style: 'thin', color: { rgb: 'D9D9D9' } },
    right: { style: 'thin', color: { rgb: 'D9D9D9' } }
  }
  const zebraFill = (isEven: boolean) => ({ fgColor: { rgb: isEven ? 'F2F6FB' : 'FFFFFF' } })
  const baseFont = { name: 'Segoe UI', sz: 10 }

  const dataStyle = (align: 'left' | 'center' | 'right', isEven: boolean) => ({
    font: baseFont,
    fill: zebraFill(isEven),
    alignment: { horizontal: align, vertical: 'center' },
    border: thinBorder
  })

  // Columns whose header (matched by substring, case-insensitive) should be
  // center-aligned rather than the default left alignment.
  const CENTER_HEADERS = [
    'NO', 'STUDENT ID', 'SEX', 'BIRTHDAY', 'PASSPORT', 'DATE OF ISSUE',
    'DATE OF EXPIRATION', 'STATUS', 'SCORE', 'PRIORITY', 'DATE & TIME',
    'DATE', 'PHONE', 'TARIFF', 'GROUP', 'OFFICE', 'LEAD', 'LEVEL'
  ]
  // Columns whose header indicates a currency/amount value: right-aligned and
  // coerced to a numeric cell with a thousands-separator format, matching how
  // Excel displays money regardless of whether the source value was a string.
  const CURRENCY_HEADERS = ['UZS', 'BALANCE', 'DISCOUNT', 'AMOUNT']

  for (let r = startCell.r; r <= endCell.r; r++) {
    for (let c = startCell.c; c <= endCell.c; c++) {
      const address = encodeCell(c, r)
      // Backfill missing cells as empty text so borders render across the
      // full rectangle even where a row had no value for that column.
      if (!ws[address]) {
        ws[address] = { t: 's', v: '' }
      }
      const cell = ws[address]

      if (r === 0) {
        cell.s = headerStyle
        continue
      }

      const isEven = r % 2 === 0
      const headerCell = ws[encodeCell(c, 0)]
      const headerName = headerCell ? String(headerCell.v).toUpperCase() : ''

      if (CURRENCY_HEADERS.some(h => headerName.includes(h))) {
        cell.s = dataStyle('right', isEven)
        if (cell.v !== '' && cell.v !== null && cell.v !== undefined) {
          const num = parseFloat(String(cell.v).replace(/,/g, ''))
          if (!isNaN(num)) {
            cell.t = 'n'
            cell.v = num
            cell.z = '#,##0'
          }
        }
      } else if (CENTER_HEADERS.some(h => headerName.includes(h))) {
        cell.s = dataStyle('center', isEven)
      } else {
        cell.s = dataStyle('left', isEven)
      }
    }
  }

  const rowHeights: { hpx: number }[] = [{ hpx: 28 }]
  for (let r = 1; r <= endCell.r; r++) {
    rowHeights.push({ hpx: 22 })
  }
  ws['!rows'] = rowHeights
}

// ── Download Excel Action ───────────────────────────────────────────
const downloadSelectedAsExcel = () => {
  if (selectedStudentIds.value.length === 0) {
    uiStore.addToast({ type: 'warning', title: 'Selection Empty', message: 'Please select at least one student!' })
    return
  }
  if (checkedFields.value.length === 0) {
    uiStore.addToast({ type: 'warning', title: 'Fields Empty', message: 'Please select at least one field to export!' })
    return
  }

  const selectedStudents = props.students
    .filter(s => selectedStudentIds.value.includes(s.id))
    .sort((a, b) => compareStudentIds(a.id, b.id, 'asc'))

  const allChecked = FIELD_GROUPS.flatMap(g => g.fields).filter(f => checkedFields.value.includes(f.key))
  const idField = allChecked.find(f => f.key === 'id')
  const orderedFields = [
    ...(idField ? [idField] : []),
    ...allChecked.filter(f => f.key !== 'id')
  ]

  const excelData = selectedStudents.map((s, index) => {
    const row: Record<string, any> = { No: index + 1 }
    for (const field of orderedFields) {
      row[field.label] = field.get(s)
    }
    return row
  })

  const colWidths = [
    { wch: 5 },
    ...orderedFields.map(f => getColWidth(f.key, f.label))
  ]

  const ws = XLSX.utils.json_to_sheet(excelData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Students')
  ws['!cols'] = colWidths

  styleWorksheet(ws)

  const dateStr = new Date().toISOString().split('T')[0]
  const filename = `Students_Export_${dateStr}.xlsx`

  XLSX.writeFile(wb, filename)

  isFieldPickerOpen.value = false
  emit('close')

  uiStore.addToast({
    type: 'success',
    title: 'Export Complete',
    message: `Downloaded ${selectedStudents.length} students to ${filename}`
  })
}

// Helper: Toggle group fields
const handleToggleGroupFields = (fields: ExcelField[]) => {
  const keys = fields.map(f => f.key)
  const allChecked = keys.every(k => checkedFields.value.includes(k))
  if (allChecked) {
    checkedFields.value = checkedFields.value.filter(k => !keys.includes(k))
  } else {
    checkedFields.value = Array.from(new Set([...checkedFields.value, ...keys]))
  }
}

// Close on Escape key
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) {
    if (isFieldPickerOpen.value) {
      isFieldPickerOpen.value = false
    } else {
      emit('close')
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <!-- 1. Main Student Selection & Filtering Modal -->
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none animate-page-in"
    @click.self="emit('close')"
  >
    <div
      class="relative w-full max-w-5xl overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-6 shadow-2xl z-10 flex flex-col max-h-[90vh]"
      @click="closeAllDropdowns"
    >
      <!-- Close Button -->
      <button
        type="button"
        @click="emit('close')"
        class="absolute right-4 top-4 rounded-xl p-1.5 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-700 dark:hover:text-zinc-200 transition-all cursor-pointer"
      >
        <X class="w-5 h-5" />
      </button>

      <h2 class="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 mb-1 flex items-center gap-2">
        <FileSpreadsheet class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
        <span>Download as Excel</span>
      </h2>
      <p class="text-xs text-zinc-500 font-medium mb-4">
        Filter and select specific students to compile into a styled Excel workbook.
      </p>

      <!-- Search & Filter Controls Box -->
      <div
        class="mb-4 space-y-3 bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-750 rounded-xl p-3.5 shadow-2xs"
        @click.stop
      >
        <!-- Search Row -->
        <div class="flex items-stretch gap-0 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 overflow-hidden focus-within:border-blue-500 transition-colors">
          <div class="relative shrink-0 border-r border-zinc-200 dark:border-zinc-700">
            <select
              v-model="searchType"
              class="h-10 pl-3 pr-7 bg-transparent text-xs font-bold text-zinc-600 dark:text-zinc-300 focus:outline-none cursor-pointer appearance-none"
            >
              <option value="all">All Fields</option>
              <option value="id">ID</option>
              <option value="name">Name</option>
              <option value="phone">Phone</option>
              <option value="university">University</option>
            </select>
            <ChevronDown class="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-zinc-400 pointer-events-none" />
          </div>
          <div class="relative flex-1">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search by name, ID, phone, university..."
              class="w-full h-10 pl-9 pr-3 bg-transparent text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none"
            />
          </div>
        </div>

        <!-- Filter Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-2">
          <!-- Folder Filter Dropdown -->
          <div class="relative filter-dropdown-container">
            <button
              type="button"
              @click="toggleDropdown('folder')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
              :class="selectedFolders.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Folder class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedFolders.length === 0 ? 'Folder' : `Folder · ${selectedFolders.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>

            <!-- Popover -->
            <div
              v-if="isFolderDropdownOpen"
              class="absolute left-0 mt-1 w-52 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input
                  type="checkbox"
                  :checked="selectedFolders.length === 0"
                  @change="selectedFolders = []"
                  class="rounded text-blue-600"
                />
                <span>All Folders</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="selectedFolders.includes('NO_FOLDER')"
                  @change="toggleInList(selectedFolders, 'NO_FOLDER')"
                  class="rounded text-blue-600"
                />
                <span>No Folder</span>
              </label>
              <label
                v-for="f in foldersList"
                :key="f.id"
                class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="selectedFolders.includes(String(f.id))"
                  @change="toggleInList(selectedFolders, String(f.id))"
                  class="rounded text-blue-600"
                />
                <span class="truncate">{{ f.name }}</span>
              </label>
            </div>
          </div>

          <!-- Tariff Filter Dropdown -->
          <div class="relative filter-dropdown-container">
            <button
              type="button"
              @click="toggleDropdown('tariff')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
              :class="selectedTariffs.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Award class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedTariffs.length === 0 ? 'Tariff' : `Tariff · ${selectedTariffs.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isTariffDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedTariffs.length === 0" @change="selectedTariffs = []" class="rounded text-blue-600" />
                <span>All Tariffs</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedTariffs.includes('NO_TARIFF')" @change="toggleInList(selectedTariffs, 'NO_TARIFF')" class="rounded text-blue-600" />
                <span>No Tariff</span>
              </label>
              <label v-for="t in tariffOptions" :key="t" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedTariffs.includes(t)" @change="toggleInList(selectedTariffs, t)" class="rounded text-blue-600" />
                <span class="truncate">{{ t }}</span>
              </label>
            </div>
          </div>

          <!-- Level Filter Dropdown -->
          <div class="relative filter-dropdown-container">
            <button
              type="button"
              @click="toggleDropdown('level')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
              :class="selectedLevels.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <GraduationCap class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedLevels.length === 0 ? 'Level' : `Level · ${selectedLevels.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isLevelDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedLevels.length === 0" @change="selectedLevels = []" class="rounded text-blue-600" />
                <span>All Levels</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedLevels.includes('NO_LEVEL')" @change="toggleInList(selectedLevels, 'NO_LEVEL')" class="rounded text-blue-600" />
                <span>No Level</span>
              </label>
              <label v-for="l in levelOptions" :key="l" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedLevels.includes(l)" @change="toggleInList(selectedLevels, l)" class="rounded text-blue-600" />
                <span class="truncate">{{ l }}</span>
              </label>
            </div>
          </div>

          <!-- Group Filter Dropdown -->
          <div class="relative filter-dropdown-container">
            <button
              type="button"
              @click="toggleDropdown('group')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
              :class="selectedGroups.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Users class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedGroups.length === 0 ? 'Group' : `Group · ${selectedGroups.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isGroupDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedGroups.length === 0" @change="selectedGroups = []" class="rounded text-blue-600" />
                <span>All Groups</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedGroups.includes('NO_GROUP')" @change="toggleInList(selectedGroups, 'NO_GROUP')" class="rounded text-blue-600" />
                <span>No Group</span>
              </label>
              <label v-for="g in groupOptions" :key="g" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedGroups.includes(g)" @change="toggleInList(selectedGroups, g)" class="rounded text-blue-600" />
                <span class="truncate">{{ g }}</span>
              </label>
            </div>
          </div>

          <!-- Certificate Filter Dropdown -->
          <div class="relative filter-dropdown-container">
            <button
              type="button"
              @click="toggleDropdown('cert')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
              :class="selectedCerts.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Bookmark class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedCerts.length === 0 ? 'Certificate' : `Certificate · ${selectedCerts.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isCertDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedCerts.length === 0" @change="selectedCerts = []" class="rounded text-blue-600" />
                <span>All Certificates</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label v-for="c in CERT_OPTIONS" :key="c" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedCerts.includes(c)" @change="toggleInList(selectedCerts, c)" class="rounded text-blue-600" />
                <span class="truncate">{{ c }}</span>
              </label>
            </div>
          </div>

          <!-- Tags Filter Dropdown -->
          <div class="relative filter-dropdown-container">
            <button
              type="button"
              @click="toggleDropdown('tag')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
              :class="selectedTags.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Tag class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedTags.length === 0 ? 'Tags' : `Tags · ${selectedTags.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isTagDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedTags.length === 0" @change="selectedTags = []" class="rounded text-blue-600" />
                <span>All Tags</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label v-for="tg in tagOptions" :key="tg" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedTags.includes(tg)" @change="toggleInList(selectedTags, tg)" class="rounded text-blue-600" />
                <span class="truncate">{{ tg }}</span>
              </label>
            </div>
          </div>

          <!-- Lead By Filter Dropdown -->
          <div class="relative filter-dropdown-container">
            <button
              type="button"
              @click="toggleDropdown('lead')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
              :class="selectedLeads.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Contact class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedLeads.length === 0 ? 'Lead By' : `Lead By · ${selectedLeads.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isLeadDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedLeads.length === 0" @change="selectedLeads = []" class="rounded text-blue-600" />
                <span>All Leads</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedLeads.includes('NO_LEADBY')" @change="toggleInList(selectedLeads, 'NO_LEADBY')" class="rounded text-blue-600" />
                <span>No Lead by</span>
              </label>
              <label v-for="ld in leadOptions" :key="ld" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedLeads.includes(ld)" @change="toggleInList(selectedLeads, ld)" class="rounded text-blue-600" />
                <span class="truncate">{{ ld }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Active filter chips + Clear -->
        <div v-if="hasActiveFilters" class="flex items-center gap-1.5 flex-wrap pt-0.5">
          <span
            v-for="chip in activeFilterChips"
            :key="chip.key"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
          >
            {{ chip.label }}
            <X class="w-2.5 h-2.5 cursor-pointer hover:text-rose-500" @click="chip.clear()" />
          </span>
          <button
            type="button"
            @click="clearAllExcelFilters"
            class="text-[10px] font-bold text-rose-600 hover:text-rose-700 cursor-pointer"
          >
            Clear All
          </button>
        </div>
      </div>

      <!-- Student Selection Counter & Select All -->
      <div class="flex items-center justify-between mb-2 text-xs font-bold text-zinc-700 dark:text-zinc-300">
        <label class="flex items-center gap-2 cursor-pointer select-none uppercase tracking-wide text-[11px]">
          <input
            type="checkbox"
            :checked="isAllFilteredSelected"
            @change="toggleSelectAllFiltered"
            class="h-4 w-4 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
          />
          <span>Select Students to Export</span>
        </label>
        <span class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide bg-emerald-500 text-white shadow-2xs">
          {{ selectedStudentIds.length }} selected
        </span>
      </div>

      <!-- Live Students Table -->
      <div class="flex-1 overflow-y-auto border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 shadow-2xs divide-y divide-zinc-100 dark:divide-zinc-800 max-h-80 text-xs">
        <table class="w-full text-left border-collapse">
          <thead class="sticky top-0 bg-zinc-50 dark:bg-zinc-850 text-zinc-500 font-bold uppercase tracking-wider text-[10px] border-b border-zinc-200 dark:border-zinc-750 z-10">
            <tr>
              <th class="p-2.5 w-10 text-center"></th>
              <th class="p-2.5 w-20">ID</th>
              <th class="p-2.5">Full Name</th>
              <th class="p-2.5">Level</th>
              <th class="p-2.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
            <tr v-if="filteredStudents.length === 0">
              <td colspan="5" class="p-8 text-center text-zinc-400">
                Tanlangan filtrlarga mos keluvchi talabalar topilmadi.
              </td>
            </tr>
            <tr
              v-for="s in filteredStudents"
              :key="s.id"
              @click="toggleStudentSelection(s.id)"
              class="hover:bg-blue-50/50 dark:hover:bg-blue-950/20 cursor-pointer transition-colors"
              :class="[
                selectedStudentIds.includes(s.id) ? 'bg-blue-50/30 dark:bg-blue-950/10' : '',
                s.is_deleted ? 'opacity-60' : ''
              ]"
              :style="getRowStripeStyle(s)"
            >
              <td class="p-2.5 text-center" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedStudentIds.includes(s.id)"
                  @change="toggleStudentSelection(s.id)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
              </td>
              <td class="p-2.5 align-top">
                <div class="inline-flex items-center justify-center px-2 py-1 text-[11px] font-mono font-bold bg-[#007aff] text-white rounded-[4px] shadow-2xs min-w-[34px]">
                  {{ s.id }}
                </div>
              </td>
              <td class="p-2.5 align-top">
                <div class="flex items-center gap-1.5">
                  <span class="font-bold text-zinc-900 dark:text-zinc-100 uppercase">{{ s.full_name }}</span>
                  <span
                    v-if="s.is_deleted"
                    class="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shrink-0"
                  >
                    Archive
                  </span>
                </div>
                <div class="mt-0.5 text-[9px] font-bold uppercase tracking-wide text-zinc-400 dark:text-zinc-500 whitespace-nowrap">
                  {{ getTariffDisplayName(s) }}
                </div>
              </td>
              <td class="p-2.5 align-top">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-if="s.level"
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide shadow-2xs"
                    :class="getLevelBadgeClass(s.level)"
                  >
                    {{ s.level }}
                  </span>
                  <span
                    v-if="s.level2"
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-[#ffab00] text-zinc-900 shadow-2xs"
                  >
                    {{ s.level2 }}
                  </span>
                </div>
                <div v-if="getStudentCerts(s).length > 0" class="flex flex-wrap gap-1 mt-1">
                  <span
                    v-for="(c, cIdx) in getStudentCerts(s)"
                    :key="cIdx"
                    class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-bold shadow-2xs"
                    :class="c.type?.toUpperCase() === 'TOPIK' ? 'bg-rose-500 text-white' : 'bg-blue-600 text-white'"
                  >
                    <span>{{ c.type }}</span>
                    <span v-if="c.score" class="opacity-90 font-mono">{{ c.score }}</span>
                  </span>
                </div>
              </td>
              <td class="p-2.5 text-right align-top" @click.stop="emit('open-detail', s.id); emit('close')">
                <button
                  type="button"
                  class="inline-flex items-center justify-center w-6 h-6 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700 cursor-pointer transition-colors"
                  title="Open student"
                >
                  <MoreVertical class="w-3.5 h-3.5" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer Buttons -->
      <div class="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-end gap-3 shrink-0">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="button"
          @click="isFieldPickerOpen = true"
          :disabled="selectedStudentIds.length === 0"
          class="flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-500/20 cursor-pointer disabled:opacity-50"
        >
          <FileSpreadsheet class="w-4 h-4" />
          <span>Choose Fields to Export ({{ selectedStudentIds.length }})</span>
        </button>
      </div>
    </div>
  </div>

  <!-- 2. Choose Fields to Export Modal Dialog (Accordion) -->
  <div
    v-if="isFieldPickerOpen"
    class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none animate-page-in"
    @click.self="isFieldPickerOpen = false"
  >
    <div class="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-6 shadow-2xl z-10 flex flex-col max-h-[90vh]">
      <button
        type="button"
        @click="isFieldPickerOpen = false"
        class="absolute right-4 top-4 rounded-xl p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 cursor-pointer"
      >
        <X class="w-5 h-5" />
      </button>

      <h2 class="text-lg font-extrabold text-zinc-900 dark:text-zinc-100 mb-1 flex items-center gap-2">
        <FileSpreadsheet class="w-5 h-5 text-emerald-600" />
        <span>Choose Fields to Export</span>
      </h2>
      <p class="text-xs text-zinc-500 font-medium mb-3">
        Pick which columns to include in the workbook for {{ selectedStudentIds.length }} selected student{{ selectedStudentIds.length === 1 ? '' : 's' }}.
      </p>

      <!-- Field Search -->
      <div class="relative mb-3">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400" />
        <input
          v-model="fieldSearchQuery"
          type="text"
          placeholder="Search fields..."
          class="w-full bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 pl-9 pr-3 py-2 rounded-xl outline-none focus:border-blue-500 text-xs"
        />
      </div>

      <!-- Accordion of Field Groups -->
      <div class="flex-1 overflow-y-auto border border-zinc-200 dark:border-zinc-800 rounded-xl bg-zinc-50/50 dark:bg-zinc-900 divide-y divide-zinc-100 dark:divide-zinc-800">
        <div v-for="group in FIELD_GROUPS" :key="group.title">
          <button
            type="button"
            @click="expandedFieldGroup = expandedFieldGroup === group.title ? null : group.title"
            class="w-full flex items-center justify-between px-4 py-3 hover:bg-zinc-100/70 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <div class="flex items-center gap-3">
              <input
                type="checkbox"
                :checked="group.fields.every(f => checkedFields.includes(f.key))"
                @click.stop
                @change="handleToggleGroupFields(group.fields)"
                class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <span class="font-bold text-xs uppercase tracking-wider text-zinc-800 dark:text-zinc-200">
                {{ group.title }}
              </span>
              <span class="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300">
                {{ group.fields.filter(f => checkedFields.includes(f.key)).length }}/{{ group.fields.length }}
              </span>
            </div>
            <component
              :is="expandedFieldGroup === group.title || fieldSearchQuery ? ChevronUp : ChevronDown"
              class="w-4 h-4 text-zinc-400"
            />
          </button>

          <!-- Group Fields Checklist -->
          <div
            v-if="expandedFieldGroup === group.title || fieldSearchQuery"
            class="px-4 pb-3 grid grid-cols-2 gap-x-4 gap-y-2 bg-white dark:bg-zinc-850/50"
          >
            <label
              v-for="field in group.fields.filter(f => !fieldSearchQuery || f.label.toLowerCase().includes(fieldSearchQuery.toLowerCase()))"
              :key="field.key"
              class="flex items-center gap-2 text-xs font-medium text-zinc-700 dark:text-zinc-300 cursor-pointer select-none py-0.5"
            >
              <input
                type="checkbox"
                :checked="checkedFields.includes(field.key)"
                @change="checkedFields.includes(field.key) ? checkedFields = checkedFields.filter(k => k !== field.key) : checkedFields.push(field.key)"
                class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <span>{{ field.label }}</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-end gap-3">
        <button
          type="button"
          @click="isFieldPickerOpen = false"
          class="px-4 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 cursor-pointer"
        >
          Back
        </button>
        <button
          type="button"
          @click="downloadSelectedAsExcel"
          class="flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-500/20 cursor-pointer"
        >
          <FileSpreadsheet class="w-4 h-4" />
          <span>Download Excel (.xlsx)</span>
        </button>
      </div>
    </div>
  </div>
</template>
