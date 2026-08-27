<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import {
  FileSpreadsheet,
  Upload,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Download,
  RefreshCw,
  Sparkles,
  Settings2,
  Users,
  Search,
  Check,
  Eye,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  Trash2,
  FileText,
  Info,
  Folder,
  Tag,
  GraduationCap,
  Award,
  Contact,
  Bookmark,
  X
} from 'lucide-vue-next'
import { excelFillApi, type ExcelAnalysisResult, type ColumnMappingConfig, type ExcelSheet } from '@/api/excelFill'
import { studentsApi } from '@/api/students'
import type { Student } from '@/types'
import { ROW_COLOR_MAP } from '@/types'

// ─── Step State ─────────────────────────────────────────────────────────────
const currentStep = ref<1 | 2 | 3 | 4>(1)

// ─── File & Template State ──────────────────────────────────────────────────
const uploadedFile = ref<File | null>(null)
const isAnalyzing = ref(false)
const analysisError = ref<string | null>(null)
const analysisData = ref<ExcelAnalysisResult | null>(null)
const selectedSheetName = ref<string>('')
const isDragging = ref(false)

// ─── Mappings State ─────────────────────────────────────────────────────────
const columnMappings = ref<ColumnMappingConfig[]>([])
const onlyMappedFilter = ref(false)

// ─── Student Selection State & Advanced Filters ─────────────────────────────
const searchType = ref<'all' | 'id' | 'name' | 'phone' | 'university'>('all')
const searchQuery = ref('')
const selectedStudentIds = ref<Set<string>>(new Set())

const selectedFolders = ref<string[]>([])
const selectedTariffs = ref<string[]>([])
const selectedLevels = ref<string[]>([])
const selectedGroups = ref<string[]>([])
const selectedCerts = ref<string[]>([])
const selectedTags = ref<string[]>([])
const selectedLeads = ref<string[]>([])

// Dropdown popover open states
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

const CERT_OPTIONS = ['NO CERTIFICATE', 'TOPIK', 'IELTS', 'TOEFL', 'CEFR', 'SAT', 'SKA']
const PREDEFINED_TAGS = ['Call', 'Apply', 'Documents', 'Payment']
const TAG_OPTIONS = [...PREDEFINED_TAGS, 'Custom']

// ─── Generation & Output State ──────────────────────────────────────────────
const fillMode = ref<'append' | 'overwrite'>('append')
const autoIncrementSeq = ref(true)
const startRowOverride = ref<number | null>(null)
const isGenerating = ref(false)
const generationSuccess = ref(false)
const downloadUrl = ref<string | null>(null)
const downloadedFileName = ref<string>('')

// ─── Options & Folders from CRM ─────────────────────────────────────────────
const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
  staleTime: 1000 * 60 * 10,
})

const options = computed(() => optionsData.value || {
  tariffs: [],
  levels: [],
  groups: [],
  leads: [],
  coordinators: [],
  universities: [],
  folders: [],
  offices: ['ANDIJON OFFIS', 'TOSHKENT OFFIS']
})

const { data: foldersData } = useQuery({
  queryKey: ['folders'],
  queryFn: () => studentsApi.getFolders(),
  staleTime: 1000 * 60 * 5,
})

const folders = computed(() => foldersData.value || [])

// ─── Fetch Students from Master CRM ─────────────────────────────────────────
const { data: allStudentsData, isLoading: isLoadingStudents } = useQuery({
  queryKey: ['all-students-master-excel-fill'],
  queryFn: () => studentsApi.getStudents({
    page: 1,
    page_size: 5000,
    folder: 'all',
    include_archive: false,
  }),
  staleTime: 1000 * 60 * 5,
})

const allStudents = computed<Student[]>(() => (allStudentsData.value?.results || []).filter(s => !s.is_deleted))

// ─── Filter students for Step 3 matching ExportExcelModal ───────────────────
const filteredStudents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const filtered = allStudents.value.filter(s => {
    // Search query
    if (q) {
      if (searchType.value === 'id' && !s.id.toLowerCase().includes(q)) return false
      if (searchType.value === 'name' && !s.full_name.toLowerCase().includes(q) && !(s.korean_name || '').toLowerCase().includes(q)) return false
      if (searchType.value === 'phone' && !(s.phone1 || '').includes(q) && !(s.phone2 || '').includes(q)) return false
      if (searchType.value === 'university') {
        const unis = [s.university_1, s.university_2, s.university_3, s.university_4, s.university_5].filter(Boolean).join(' ').toLowerCase()
        if (!unis.includes(q)) return false
      }
      if (searchType.value === 'all') {
        const match = s.id.toLowerCase().includes(q) ||
          s.full_name.toLowerCase().includes(q) ||
          (s.korean_name || '').toLowerCase().includes(q) ||
          (s.passport || '').toLowerCase().includes(q) ||
          (s.phone1 || '').includes(q) ||
          (s.phone2 || '').includes(q) ||
          (s.university_1 || '').toLowerCase().includes(q)
        if (!match) return false
      }
    }

    // Folders
    if (selectedFolders.value.length > 0) {
      const studentFolderIds = (s.folders || []).map(f => f.id)
      const hasFolder = selectedFolders.value.some(fid => {
        if (fid === 'NO_FOLDER') return studentFolderIds.length === 0
        return studentFolderIds.includes(fid)
      })
      if (!hasFolder) return false
    }

    // Tariffs
    if (selectedTariffs.value.length > 0) {
      const t = s.tariff || 'NO_TARIFF'
      if (!selectedTariffs.value.includes(t)) return false
    }

    // Levels
    if (selectedLevels.value.length > 0) {
      const match = selectedLevels.value.includes(s.level || '') || selectedLevels.value.includes(s.level2 || '')
      if (!match) return false
    }

    // Groups
    if (selectedGroups.value.length > 0 && !selectedGroups.value.includes(s.student_group || '')) return false

    // Language Certs
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

    // Tags
    if (selectedTags.value.length > 0) {
      const tags = s.task_tags || []
      const match = selectedTags.value.some(tag => {
        if (tag === 'Custom') return tags.some(t => !PREDEFINED_TAGS.includes(t))
        return tags.includes(tag)
      })
      if (!match) return false
    }

    // Leads
    if (selectedLeads.value.length > 0 && !selectedLeads.value.includes(s.lead_by || '')) return false

    return true
  })

  return filtered
})

// ─── Active Filter Summary ──────────────────────────────────────────────────
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
    chips.push({ key: 'folder', label: `Folder: ${selectedFolders.value.length}`, clear: () => { selectedFolders.value = [] } })
  }
  if (selectedTariffs.value.length > 0) {
    chips.push({ key: 'tariff', label: `Tariff: ${selectedTariffs.value.length}`, clear: () => { selectedTariffs.value = [] } })
  }
  if (selectedLevels.value.length > 0) {
    chips.push({ key: 'level', label: `Level: ${selectedLevels.value.length}`, clear: () => { selectedLevels.value = [] } })
  }
  if (selectedGroups.value.length > 0) {
    chips.push({ key: 'group', label: `Group: ${selectedGroups.value.length}`, clear: () => { selectedGroups.value = [] } })
  }
  if (selectedCerts.value.length > 0) {
    chips.push({ key: 'cert', label: `Certificate: ${selectedCerts.value.length}`, clear: () => { selectedCerts.value = [] } })
  }
  if (selectedTags.value.length > 0) {
    chips.push({ key: 'tag', label: `Tag: ${selectedTags.value.length}`, clear: () => { selectedTags.value = [] } })
  }
  if (selectedLeads.value.length > 0) {
    chips.push({ key: 'lead', label: `Lead: ${selectedLeads.value.length}`, clear: () => { selectedLeads.value = [] } })
  }
  return chips
})

const clearAllExcelFilters = () => {
  selectedFolders.value = []
  selectedTariffs.value = []
  selectedLevels.value = []
  selectedGroups.value = []
  selectedCerts.value = []
  selectedTags.value = []
  selectedLeads.value = []
}

// ─── Current selected sheet object ──────────────────────────────────────────
const currentSheet = computed<ExcelSheet | null>(() => {
  if (!analysisData.value?.sheets) return null
  return analysisData.value.sheets.find(s => s.name === selectedSheetName.value) || analysisData.value.sheets[0] || null
})

// Number of columns in preview table
const previewColCount = computed(() => {
  if (!currentSheet.value?.preview_rows?.length) return 0
  const maxInRows = Math.max(...currentSheet.value.preview_rows.map(r => r.values.length), 0)
  return Math.max(maxInRows, currentSheet.value.columns.length, currentSheet.value.max_column || 0)
})

// Column index to letter helper (0 -> A, 1 -> B, etc.)
const getColLetter = (index: number): string => {
  let s = ''
  let temp = index
  while (temp >= 0) {
    s = String.fromCharCode((temp % 26) + 65) + s
    temp = Math.floor(temp / 26) - 1
  }
  return s
}

// ─── File Upload & Inspection Handler ────────────────────────────────────────
const handleFileUpload = async (file: File) => {
  if (!file.name.toLowerCase().match(/\.(xlsx|xlsm|xltx)$/)) {
    analysisError.value = "Faqat .xlsx yoki .xlsm formatidagi Excel fayllari qabul qilinadi"
    return
  }

  uploadedFile.value = file
  isAnalyzing.value = true
  analysisError.value = null

  try {
    const res = await excelFillApi.analyzeTemplate(file)
    analysisData.value = res
    if (res.sheets.length > 0) {
      selectedSheetName.value = res.sheets[0].name
      initMappingsFromSheet(res.sheets[0])
    }
  } catch (err: any) {
    console.error('Error analyzing template:', err)
    analysisError.value = err.response?.data?.error || err.message || "Faylni tahlil qilishda xatolik yuz berdi"
  } finally {
    isAnalyzing.value = false
  }
}

const onDropFile = (e: DragEvent) => {
  isDragging.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    handleFileUpload(e.dataTransfer.files[0])
  }
}

const onFileInputChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    handleFileUpload(target.files[0])
  }
}

// ─── Initialize / Switch Sheet Mappings ─────────────────────────────────────
const initMappingsFromSheet = (sheet: ExcelSheet) => {
  columnMappings.value = sheet.columns
    .filter(col => col.header_name && col.header_name.trim() !== '')
    .map(col => {
      const isKoreanHeader = /[\uac00-\ud7a3]/.test(col.header_name || '')

      return {
        col_idx: col.col_idx,
        col_letter: col.col_letter,
        header_name: col.header_name,
        field: col.suggested_field || '_skip',
        static_value: '',
        fallback: '',
        format_rules: {
          dateFormat: isKoreanHeader ? 'YYYY.MM.DD' : 'YYYY-MM-DD',
          genderFormat: isKoreanHeader ? '남/여' : 'MALE/FEMALE',
          phoneFormat: 'original',
        }
      }
    })
}

watch(selectedSheetName, (newSheet) => {
  if (analysisData.value && newSheet) {
    const s = analysisData.value.sheets.find(item => item.name === newSheet)
    if (s) initMappingsFromSheet(s)
  }
})

// Mapped vs Skipped count
const mappedCount = computed(() => columnMappings.value.filter(m => m.field !== '_skip').length)
const skippedCount = computed(() => columnMappings.value.filter(m => m.field === '_skip').length)

// ─── Korean to English Header Translation Map & Helper ──────────────────────
const KOREAN_HEADER_TRANSLATIONS: Record<string, string> = {
  '순번': 'No',
  '연번': 'No',
  '번호': 'No',
  '성명': 'Name',
  '한글성명': 'Korean Name',
  '한글 성명': 'Korean Name',
  '국문성명': 'Korean Name',
  '국문 성명': 'Korean Name',
  '국문이름': 'Korean Name',
  '국문 이름': 'Korean Name',
  '영문성명': 'Full Name (English)',
  '영문 성명': 'Full Name (English)',
  '영문이름': 'Full Name (English)',
  '영문 이름': 'Full Name (English)',
  '영문성': 'Surname / Last Name',
  '영문 성': 'Surname / Last Name',
  '영문명': 'Given Name / First Name',
  '영문 명': 'Given Name / First Name',
  '성': 'Surname / Last Name',
  '이름': 'Given Name / First Name',
  '생년월일': 'Date of Birth',
  '생일': 'Birthday',
  '성별': 'Gender / Sex',
  '남/여': 'Sex (M/F)',
  '국적': 'Nationality',
  '여권번호': 'Passport No',
  '여권 번호': 'Passport No',
  '여권': 'Passport',
  '여권발급일': 'Passport Issue Date',
  '여권 발급일': 'Passport Issue Date',
  '여권발급일자': 'Passport Issue Date',
  '여권 만료일': 'Passport Expiry Date',
  '여권만료일': 'Passport Expiry Date',
  '여권만료일자': 'Passport Expiry Date',
  '발급일': 'Date of Issue',
  '만료일': 'Date of Expiry',
  '유효기간': 'Validity Period',
  '전화번호': 'Phone Number',
  '전화 번호': 'Phone Number',
  '연락처': 'Contact / Phone',
  '본인연락처': 'Student Phone',
  '휴대전화': 'Mobile Phone',
  '휴대폰': 'Mobile Phone',
  '비상연락처': 'Emergency Contact',
  '보호자연락처': 'Guardian Contact',
  '이메일': 'Email Address',
  '전자우편': 'Email',
  '주소': 'Address',
  '본국주소': 'Home Country Address',
  '거주지': 'Residence Address',
  '영문주소': 'English Address',
  '시/도': 'Province / State',
  '시·도': 'Province / State',
  '도/시': 'Province / State',
  '시/군/구': 'City / District',
  '시·군·구': 'City / District',
  '구/군': 'District',
  '최종학력': 'Final Education / Previous School',
  '최종학교': 'Final School Name',
  '출신학교': 'Graduated School',
  '학교명': 'School Name',
  '전공': 'Major / Department',
  '희망전공': 'Desired Major',
  '지원전공': 'Applied Major',
  '과정': 'Study Course / Program',
  '지원과정': 'Applied Program / Level',
  '학위과정': 'Degree Course',
  '학위': 'Degree',
  '어학능력': 'Language Proficiency',
  '한국어능력': 'Korean Language Ability',
  '공인어학성적': 'Language Test Score',
  '어학성적': 'Language Test Score',
  '토픽': 'TOPIK',
  'TOPIK급수': 'TOPIK Level',
  '급수': 'Score / Grade',
  '점수': 'Score / Points',
  '성적': 'Grades / Score',
  '학점': 'GPA',
  '평균평점': 'GPA Average',
  '부 성명': "Father's Full Name",
  '부성명': "Father's Full Name",
  '부이름': "Father's Name",
  '아버지성명': "Father's Full Name",
  '아버지': "Father",
  '부 연락처': "Father's Phone",
  '부연락처': "Father's Phone",
  '아버지연락처': "Father's Phone",
  '부 직업': "Father's Occupation",
  '부직업': "Father's Occupation",
  '아버지직업': "Father's Occupation",
  '모 성명': "Mother's Full Name",
  '모성명': "Mother's Full Name",
  '모이름': "Mother's Name",
  '어머니성명': "Mother's Full Name",
  '어머니': "Mother",
  '모 연락처': "Mother's Phone",
  '모연락처': "Mother's Phone",
  '어머니연락처': "Mother's Phone",
  '모 직업': "Mother's Occupation",
  '모직업': "Mother's Occupation",
  '어머니직업': "Mother's Occupation",
  '비고': 'Remarks / Notes',
  '특이사항': 'Special Notes / Remarks',
  '졸업일': 'Graduation Date',
  '졸업일자': 'Graduation Date',
  '졸업년월일': 'Graduation Date',
  '입학일': 'Admission Date',
  '입학일자': 'Admission Date',
  '입학년월일': 'Admission Date',
}

const getHeaderDisplayInfo = (header: string) => {
  if (!header) return { isKorean: false, koreanText: '', englishText: '' }
  
  const hasKorean = /[\uac00-\ud7a3]/.test(header)
  if (!hasKorean) {
    return { isKorean: false, koreanText: '', englishText: header }
  }

  const trimmed = header.trim()
  if (KOREAN_HEADER_TRANSLATIONS[trimmed]) {
    return {
      isKorean: true,
      koreanText: trimmed,
      englishText: KOREAN_HEADER_TRANSLATIONS[trimmed]
    }
  }

  const parenMatch = trimmed.match(/^([^\(]+)\s*\(([^)]+)\)$/)
  if (parenMatch) {
    const kPart = parenMatch[1].trim()
    const ePart = parenMatch[2].trim()
    if (/[\uac00-\ud7a3]/.test(kPart) && /[a-zA-Z]/.test(ePart)) {
      return {
        isKorean: true,
        koreanText: kPart,
        englishText: ePart
      }
    }
  }

  for (const [kKey, eVal] of Object.entries(KOREAN_HEADER_TRANSLATIONS)) {
    if (trimmed.includes(kKey)) {
      return {
        isKorean: true,
        koreanText: trimmed,
        englishText: eVal
      }
    }
  }

  return {
    isKorean: true,
    koreanText: trimmed,
    englishText: 'Korean Header'
  }
}

// ─── Visible Mappings: Skipped columns shown at the end ─────────────────────
const visibleMappings = computed(() => {
  let list = [...columnMappings.value.filter(m => m.header_name && m.header_name.trim() !== '')]
  if (onlyMappedFilter.value) {
    list = list.filter(m => m.field !== '_skip')
  }

  // Sort so that mapped columns come first (sorted by col_idx), then skipped columns come at the end
  list.sort((a, b) => {
    const aSkipped = a.field === '_skip' ? 1 : 0
    const bSkipped = b.field === '_skip' ? 1 : 0
    if (aSkipped !== bSkipped) {
      return aSkipped - bSkipped
    }
    return a.col_idx - b.col_idx
  })

  return list
})

// Group CRM fields by category for clean dropdown
const categorizedCrmFields = computed(() => {
  if (!analysisData.value?.available_fields) return {}
  const groups: Record<string, { key: string; label: string }[]> = {
    'Tizim / Maxsus': [],
    'Shaxsiy ma\'lumotlar': [],
    'Pasport ma\'lumotlari': [],
    'Aloqa ma\'lumotlari': [],
    'Ota-ona ma\'lumotlari': [],
    'Ta\'lim va Sertifikatlar': [],
  }

  analysisData.value.available_fields.forEach(f => {
    if (f.category === 'system') groups['Tizim / Maxsus'].push(f)
    else if (f.category === 'personal') groups['Shaxsiy ma\'lumotlar'].push(f)
    else if (f.category === 'passport') groups['Pasport ma\'lumotlari'].push(f)
    else if (f.category === 'contacts') groups['Aloqa ma\'lumotlari'].push(f)
    else if (f.category === 'parents') groups['Ota-ona ma\'lumotlari'].push(f)
    else if (f.category === 'education') groups['Ta\'lim va Sertifikatlar'].push(f)
  })

  return groups
})

// ─── Student Selection Handlers ─────────────────────────────────────────────
const isAllFilteredSelected = computed(() => {
  if (filteredStudents.value.length === 0) return false
  return filteredStudents.value.every(s => selectedStudentIds.value.has(s.id))
})

const toggleSelectAllStudents = () => {
  if (isAllFilteredSelected.value) {
    filteredStudents.value.forEach(s => selectedStudentIds.value.delete(s.id))
  } else {
    filteredStudents.value.forEach(s => selectedStudentIds.value.add(s.id))
  }
}

const toggleStudentSelection = (id: string) => {
  if (selectedStudentIds.value.has(id)) {
    selectedStudentIds.value.delete(id)
  } else {
    selectedStudentIds.value.add(id)
  }
}

const isStudentSelected = (id: string) => selectedStudentIds.value.has(id)

// ─── Student Row display helpers ────────────────────────────────────────────
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

// ─── File Name Modal & Customization ────────────────────────────────────────
const isFileNameModalOpen = ref(false)
const customFileName = ref('')

const openFileNameModal = () => {
  if (!uploadedFile.value || selectedStudentIds.value.size === 0) return
  const originalName = uploadedFile.value.name.replace(/\.[^/.]+$/, '')
  const dateStr = new Date().toISOString().slice(0, 10)
  customFileName.value = `Filled_${originalName}_${dateStr}`
  isFileNameModalOpen.value = true
}

const setPresetName = (preset: string) => {
  customFileName.value = preset
}

const confirmAndDownload = async () => {
  let name = customFileName.value.trim()
  if (!name) {
    const originalName = uploadedFile.value?.name.replace(/\.[^/.]+$/, '') || 'Template'
    name = `Filled_${originalName}_${new Date().toISOString().slice(0, 10)}`
  }
  if (!name.toLowerCase().endsWith('.xlsx')) {
    name = `${name}.xlsx`
  }
  isFileNameModalOpen.value = false
  await handleGenerateExcel(name)
}

// ─── Generate & Download Filled Excel ───────────────────────────────────────
const handleGenerateExcel = async (targetFileName?: string) => {
  if (!uploadedFile.value || selectedStudentIds.value.size === 0) return

  isGenerating.value = true
  generationSuccess.value = false

  try {
    const blob = await excelFillApi.generateFilledExcel({
      file: uploadedFile.value,
      sheet_name: selectedSheetName.value,
      column_mappings: columnMappings.value,
      student_ids: Array.from(selectedStudentIds.value),
      fill_mode: fillMode.value,
      start_row: startRowOverride.value || undefined,
      auto_increment_sequence: autoIncrementSeq.value,
    })

    let fileName = targetFileName
    if (!fileName) {
      const originalName = uploadedFile.value.name.replace(/\.[^/.]+$/, '')
      fileName = `Filled_${originalName}_${new Date().toISOString().slice(0, 10)}.xlsx`
    }
    if (!fileName.toLowerCase().endsWith('.xlsx')) {
      fileName += '.xlsx'
    }
    downloadedFileName.value = fileName

    const url = window.URL.createObjectURL(blob)
    downloadUrl.value = url

    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    generationSuccess.value = true
  } catch (err: any) {
    console.error('Error generating filled Excel:', err)
    let errMsg = err.message || 'Server error'
    if (err.response?.data instanceof Blob) {
      try {
        const text = await err.response.data.text()
        const parsed = JSON.parse(text)
        if (parsed.error) errMsg = parsed.error
      } catch (e) {
        // ignore
      }
    } else if (err.response?.data?.error) {
      errMsg = err.response.data.error
    }
    alert("Excel faylni to'ldirishda xatolik yuz berdi: " + errMsg)
  } finally {
    isGenerating.value = false
  }
}

// Reset wizard
const resetWizard = () => {
  currentStep.value = 1
  uploadedFile.value = null
  analysisData.value = null
  analysisError.value = null
  columnMappings.value = []
  selectedStudentIds.value.clear()
  clearAllExcelFilters()
  searchQuery.value = ''
  searchType.value = 'all'
  generationSuccess.value = false
  downloadUrl.value = null
  isFileNameModalOpen.value = false
  customFileName.value = ''
}
</script>

<template>
  <div class="h-full flex flex-col bg-zinc-50 dark:bg-[#0c0d0e] overflow-hidden" @click="closeAllDropdowns">
    <!-- Top Header Banner -->
    <header class="bg-white dark:bg-[#111315] border-b border-zinc-200 dark:border-zinc-800/80 px-6 py-4 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
          <FileSpreadsheet class="w-5 h-5" />
        </div>
        <div>
          <h1 class="text-lg font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            Excel Fill Engine
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              AI Powered
            </span>
          </h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400">
            Universitetlarning murakkab Excel shablonlarini asl formatini buzmasdan avtomatik to'ldirish
          </p>
        </div>
      </div>

      <!-- Step Stepper -->
      <div class="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-800/60 p-1 rounded-xl border border-zinc-200/60 dark:border-zinc-700/60">
        <button
          v-for="s in [
            { num: 1, label: '1. Shablon' },
            { num: 2, label: '2. Ustunlar' },
            { num: 3, label: '3. Talabalar' },
            { num: 4, label: '4. Yuklab olish' }
          ]"
          :key="s.num"
          :disabled="s.num > 1 && !uploadedFile"
          @click="currentStep = s.num as any"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer"
          :class="[
            currentStep === s.num
              ? 'bg-white dark:bg-zinc-700 text-emerald-600 dark:text-emerald-400 shadow-xs font-bold'
              : s.num < currentStep
                ? 'text-zinc-700 dark:text-zinc-300 hover:bg-white/50 dark:hover:bg-zinc-700/50'
                : 'text-zinc-400 dark:text-zinc-500 cursor-not-allowed'
          ]"
        >
          <span
            class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold"
            :class="currentStep === s.num ? 'bg-emerald-500 text-white' : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-400'"
          >
            {{ s.num }}
          </span>
          {{ s.label }}
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 overflow-y-auto p-6 scrollbar-thin">
      <div class="max-w-6xl mx-auto">
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- STEP 1: UPLOAD TEMPLATE & INSPECT -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="currentStep === 1" class="space-y-6">
          <!-- Upload Area Card -->
          <div
            class="border-2 border-dashed rounded-2xl p-8 text-center transition-all bg-white dark:bg-[#111315]"
            :class="[
              isDragging
                ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20'
                : 'border-zinc-300 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-700'
            ]"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDropFile"
          >
            <div class="max-w-md mx-auto flex flex-col items-center">
              <div class="w-16 h-16 rounded-2xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400 mb-4 shadow-sm">
                <Upload class="w-8 h-8" />
              </div>
              <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 mb-1">
                Universitetning Excel shablonini yuklang
              </h3>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 mb-5">
                .xlsx yoki .xlsm formatidagi har qanday universitet fayli (Koreyscha, Inglizcha, Ruscha)
              </p>

              <label class="cursor-pointer inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all">
                <FileSpreadsheet class="w-4 h-4" />
                Kompyuterdan tanlash
                <input type="file" class="hidden" accept=".xlsx, .xlsm, .xltx" @change="onFileInputChange" />
              </label>
            </div>
          </div>

          <!-- Loading state -->
          <div v-if="isAnalyzing" class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 text-center space-y-3">
            <RefreshCw class="w-8 h-8 text-emerald-500 animate-spin mx-auto" />
            <h4 class="text-sm font-bold text-zinc-800 dark:text-zinc-200">
              Excel shabloni tahlil qilinmoqda...
            </h4>
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              Sarlavhalar, yashirin ustunlar va CRM maydonlari aniqlanmoqda
            </p>
          </div>

          <!-- Error Alert -->
          <div v-if="analysisError" class="bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-2xl p-4 flex items-center gap-3 text-rose-700 dark:text-rose-300 text-xs">
            <AlertTriangle class="w-5 h-5 shrink-0" />
            <span>{{ analysisError }}</span>
          </div>

          <!-- Inspection Result Card -->
          <div v-if="analysisData && currentSheet && !isAnalyzing" class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-5">
            <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600">
                  <CheckCircle2 class="w-5 h-5" />
                </div>
                <div>
                  <h4 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                    {{ uploadedFile?.name }}
                  </h4>
                  <p class="text-xs text-zinc-500 dark:text-zinc-400">
                    Hajmi: {{ (uploadedFile?.size ? uploadedFile.size / 1024 : 0).toFixed(1) }} KB • Jami varaqlar: {{ analysisData.sheets.length }} ta
                  </p>
                </div>
              </div>

              <!-- Sheet Selector -->
              <div v-if="analysisData.sheets.length > 1" class="flex items-center gap-2">
                <span class="text-xs font-semibold text-zinc-500">Varaq:</span>
                <select
                  v-model="selectedSheetName"
                  class="bg-zinc-100 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-xs font-bold rounded-lg px-3 py-1.5 text-zinc-800 dark:text-zinc-200 cursor-pointer"
                >
                  <option v-for="sheet in analysisData.sheets" :key="sheet.name" :value="sheet.name">
                    {{ sheet.name }} ({{ sheet.columns.length }} ustun)
                  </option>
                </select>
              </div>
            </div>

            <!-- Sheet Stats Grid -->
            <div class="grid grid-cols-3 gap-4">
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Sarlavha qatori</span>
                <span class="text-base font-extrabold text-zinc-900 dark:text-zinc-100">{{ currentSheet.detected_header_row }}-qator</span>
              </div>
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Aniqlangan ustunlar</span>
                <span class="text-base font-extrabold text-emerald-600 dark:text-emerald-400">{{ mappedCount }} ta mos keldi</span>
              </div>
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Jami ustunlar</span>
                <span class="text-base font-extrabold text-zinc-900 dark:text-zinc-100">{{ currentSheet.columns.length }} ta ustun</span>
              </div>
            </div>

            <!-- Preview Table of Excel Sheet (With A, B, C, D... Column Letters) -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
                  <Eye class="w-3.5 h-3.5 text-zinc-400" />
                  Excel varag'ining dastlabki ko'rinishi:
                </span>
                <span class="text-[10px] text-zinc-400">
                  (Yashil rangda sarlavha qatori belgilandi)
                </span>
              </div>

              <div class="border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-x-auto max-h-64 scrollbar-thin">
                <table class="w-full text-[11px] border-collapse">
                  <!-- Excel Column Header Row: A, B, C, D... -->
                  <thead class="sticky top-0 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 font-mono font-bold select-none border-b border-zinc-200 dark:border-zinc-700 z-10">
                    <tr>
                      <th class="px-2.5 py-1.5 bg-zinc-200 dark:bg-zinc-750 text-zinc-500 text-center w-10 text-[10px] border-r border-zinc-200 dark:border-zinc-700">
                        #
                      </th>
                      <th
                        v-for="colIdx in previewColCount"
                        :key="colIdx"
                        class="px-3 py-1.5 text-center border-r border-zinc-200 dark:border-zinc-700 min-w-[120px]"
                      >
                        {{ getColLetter(colIdx - 1) }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="row in currentSheet.preview_rows"
                      :key="row.row_idx"
                      class="border-b border-zinc-100 dark:border-zinc-800/60 transition-colors"
                      :class="row.row_idx === currentSheet.detected_header_row ? 'bg-emerald-50/80 dark:bg-emerald-950/40 font-bold text-emerald-900 dark:text-emerald-200' : 'hover:bg-zinc-50/50 dark:hover:bg-zinc-800/30 text-zinc-700 dark:text-zinc-300'"
                    >
                      <td class="px-2.5 py-1.5 bg-zinc-100 dark:bg-zinc-800/80 text-zinc-400 text-center font-mono w-10 text-[10px] select-none border-r border-zinc-200 dark:border-zinc-800">
                        {{ row.row_idx }}
                      </td>
                      <td
                        v-for="colIdx in previewColCount"
                        :key="colIdx"
                        class="px-3 py-1.5 border-r border-zinc-100 dark:border-zinc-800/60 whitespace-nowrap max-w-[200px] truncate"
                      >
                        {{ row.values[colIdx - 1] || '-' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Proceed to Step 2 Button -->
            <div class="flex justify-end pt-2">
              <button
                @click="currentStep = 2"
                class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
              >
                Ustunlarni sozlashga o'tish
                <ArrowRight class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- STEP 2: COLUMN MAPPING & CONFIGURATION -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="currentStep === 2" class="space-y-5">
          <!-- Filter & Stats Bar -->
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 flex items-center justify-between">
            <div class="flex items-center gap-4 text-xs">
              <span class="font-bold text-zinc-800 dark:text-zinc-200">
                Ustunlar tahlili:
              </span>
              <span class="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-800">
                {{ mappedCount }} ta to'ldiriladi
              </span>
              <span class="px-2.5 py-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 font-medium">
                {{ skippedCount }} ta o'tkazib yuboriladi
              </span>
            </div>

            <div class="flex items-center gap-3">
              <label class="flex items-center gap-2 text-xs font-semibold text-zinc-600 dark:text-zinc-400 cursor-pointer select-none">
                <input
                  type="checkbox"
                  v-model="onlyMappedFilter"
                  class="rounded text-emerald-600 focus:ring-emerald-500 border-zinc-300 dark:border-zinc-700"
                />
                Faqat to'ldiriladigan ustunlarni ko'rsatish
              </label>
            </div>
          </div>

          <!-- Column Mapping Cards Grid -->
          <!-- Format: A-Column | Header: Koreyscha (English tarjima) | CRM field -->
          <!-- Skipped columns shown at the end -->
          <div class="space-y-3">
            <div
              v-for="mapping in visibleMappings"
              :key="mapping.col_idx"
              class="bg-white dark:bg-[#111315] border rounded-2xl p-4 transition-all"
              :class="[
                mapping.field !== '_skip'
                  ? 'border-zinc-200 dark:border-zinc-800 shadow-xs'
                  : 'border-zinc-200/60 dark:border-zinc-800/40 opacity-70 bg-zinc-50/50 dark:bg-zinc-900/30'
              ]"
            >
              <div class="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                <!-- 1. A-Column badge / tag -->
                <div class="md:col-span-2 flex items-center gap-2">
                  <div
                    class="px-2.5 py-1 rounded-lg text-xs font-mono font-extrabold flex items-center justify-center gap-1 shrink-0"
                    :class="mapping.field !== '_skip' ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 border border-zinc-200 dark:border-zinc-700'"
                  >
                    <span>{{ mapping.col_letter }}-Column</span>
                  </div>
                  <span class="text-[10px] text-zinc-400 font-mono">
                    (#{{ mapping.col_idx }})
                  </span>
                </div>

                <!-- 2. Header Info (Korean + English translation if Korean, or English directly) -->
                <div class="md:col-span-5">
                  <div class="text-xs font-medium text-zinc-800 dark:text-zinc-200">
                    <span class="text-[11px] text-zinc-400 font-semibold mr-1">Header:</span>
                    <template v-if="getHeaderDisplayInfo(mapping.header_name).isKorean">
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">
                        {{ getHeaderDisplayInfo(mapping.header_name).koreanText }}
                      </span>
                      <span class="text-zinc-500 dark:text-zinc-400 text-xs ml-1.5 font-semibold">
                        ({{ getHeaderDisplayInfo(mapping.header_name).englishText }})
                      </span>
                    </template>
                    <template v-else>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">
                        {{ getHeaderDisplayInfo(mapping.header_name).englishText }}
                      </span>
                    </template>
                  </div>
                </div>

                <!-- 3. CRM Field Selector & Options -->
                <div class="md:col-span-5 space-y-2">
                  <div class="flex items-center gap-2">
                    <div class="relative flex-1">
                      <select
                        v-model="mapping.field"
                        class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-300 dark:border-zinc-700 text-xs font-semibold rounded-xl pl-3 pr-8 py-2 text-zinc-800 dark:text-zinc-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none appearance-none cursor-pointer"
                        :class="mapping.field !== '_skip' ? 'border-emerald-400 dark:border-emerald-700/80 bg-emerald-50/20' : ''"
                      >
                        <option value="_skip">❌ O'tkazib yuborish (Bo'sh qoldirish)</option>
                        <optgroup v-for="(fields, groupName) in categorizedCrmFields" :key="groupName" :label="groupName">
                          <option v-for="f in fields" :key="f.key" :value="f.key">
                            {{ f.label }}
                          </option>
                        </optgroup>
                      </select>
                      <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>

                  <!-- Extra settings (Static Value, Date format, Gender format, Fallback) -->
                  <div v-if="mapping.field === '_static_value'">
                    <input
                      type="text"
                      v-model="mapping.static_value"
                      placeholder="Barchaga yoziladigan matn (masalan Salom CRM)"
                      class="w-full bg-zinc-50 dark:bg-zinc-800 border border-amber-300 dark:border-amber-700/60 text-xs rounded-xl px-3 py-1.5 text-zinc-800 dark:text-zinc-200 placeholder-zinc-400"
                    />
                  </div>
                  <div v-else-if="['birthday', 'passport_issue_date', 'passport_expire_date', 'certificate_valid_date'].includes(mapping.field)" class="flex items-center gap-2">
                    <select
                      v-model="mapping.format_rules.dateFormat"
                      class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-[11px] font-semibold rounded-lg px-2.5 py-1.5 text-zinc-700 dark:text-zinc-300 cursor-pointer"
                    >
                      <option value="YYYY-MM-DD">Sana formati: 2004-11-15</option>
                      <option value="YYYY.MM.DD">Sana formati: 2004.11.15</option>
                      <option value="YYYYMMDD">Sana formati: 20041115</option>
                      <option value="DD.MM.YYYY">Sana formati: 15.11.2004</option>
                    </select>
                  </div>
                  <div v-else-if="mapping.field === 'gender'">
                    <select
                      v-model="mapping.format_rules.genderFormat"
                      class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-[11px] font-semibold rounded-lg px-2.5 py-1.5 text-zinc-700 dark:text-zinc-300 cursor-pointer"
                    >
                      <option value="MALE/FEMALE">Jins: MALE / FEMALE</option>
                      <option value="남/여">Jins: 남 / 여 (Koreyscha)</option>
                      <option value="남성/여성">Jins: 남성 / 여성 (To'liq)</option>
                      <option value="Male/Female">Jins: Male / Female</option>
                      <option value="M/F">Jins: M / F</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Step Buttons -->
          <div class="flex items-center justify-between pt-4">
            <button
              @click="currentStep = 1"
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
            >
              <ArrowLeft class="w-4 h-4" />
              Ortga (Shablon)
            </button>

            <button
              @click="currentStep = 3"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
            >
              Talabalarni tanlashga o'tish
              <ArrowRight class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- STEP 3: SELECT STUDENTS (WITH FULL EXPORT MODAL FILTERS) -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="currentStep === 3" class="space-y-5" @click="closeAllDropdowns">
          <!-- Search & Filter Controls Box (Matching ExportExcelModal) -->
          <div
            class="space-y-3 bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-750 rounded-2xl p-4 shadow-2xs"
            @click.stop
          >
            <!-- Search Row -->
            <div class="flex items-stretch gap-0 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 overflow-hidden focus-within:border-emerald-500 transition-colors">
              <div class="relative shrink-0 border-r border-zinc-200 dark:border-zinc-700">
                <select
                  v-model="searchType"
                  class="h-10 pl-3 pr-7 bg-transparent text-xs font-bold text-zinc-600 dark:text-zinc-300 focus:outline-none cursor-pointer appearance-none"
                >
                  <option value="all">Barcha maydonlar</option>
                  <option value="id">ID</option>
                  <option value="name">Ism (Full Name)</option>
                  <option value="phone">Telefon</option>
                  <option value="university">Universitet</option>
                </select>
                <ChevronDown class="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-zinc-400 pointer-events-none" />
              </div>
              <div class="relative flex-1">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Talaba ismi, ID, pasport, telefon yoki universitet bo'yicha qidirish..."
                  class="w-full h-10 pl-9 pr-3 bg-transparent text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none"
                />
              </div>
            </div>

            <!-- Filter Grid: 7 Dropdowns -->
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-2">
              <!-- 1. Folder Filter Dropdown -->
              <div class="relative">
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
                      class="rounded text-emerald-600"
                    />
                    <span>All Folders</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input
                      type="checkbox"
                      :checked="selectedFolders.includes('NO_FOLDER')"
                      @change="toggleInList(selectedFolders, 'NO_FOLDER')"
                      class="rounded text-emerald-600"
                    />
                    <span>No Folder</span>
                  </label>
                  <label
                    v-for="f in folders"
                    :key="f.id"
                    class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      :checked="selectedFolders.includes(f.id)"
                      @change="toggleInList(selectedFolders, f.id)"
                      class="rounded text-emerald-600"
                    />
                    <span class="truncate">{{ f.name }}</span>
                  </label>
                </div>
              </div>

              <!-- 2. Tariff Filter Dropdown -->
              <div class="relative">
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
                    <input type="checkbox" :checked="selectedTariffs.length === 0" @change="selectedTariffs = []" class="rounded text-emerald-600" />
                    <span>All Tariffs</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedTariffs.includes('NO_TARIFF')" @change="toggleInList(selectedTariffs, 'NO_TARIFF')" class="rounded text-emerald-600" />
                    <span>No Tariff</span>
                  </label>
                  <label v-for="t in options.tariffs" :key="t" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedTariffs.includes(t)" @change="toggleInList(selectedTariffs, t)" class="rounded text-emerald-600" />
                    <span class="truncate">{{ t }}</span>
                  </label>
                </div>
              </div>

              <!-- 3. Level Filter Dropdown -->
              <div class="relative">
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
                    <input type="checkbox" :checked="selectedLevels.length === 0" @change="selectedLevels = []" class="rounded text-emerald-600" />
                    <span>All Levels</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="l in options.levels" :key="l" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedLevels.includes(l)" @change="toggleInList(selectedLevels, l)" class="rounded text-emerald-600" />
                    <span class="truncate">{{ l }}</span>
                  </label>
                </div>
              </div>

              <!-- 4. Group Filter Dropdown -->
              <div class="relative">
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
                    <input type="checkbox" :checked="selectedGroups.length === 0" @change="selectedGroups = []" class="rounded text-emerald-600" />
                    <span>All Groups</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="g in options.groups" :key="g" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedGroups.includes(g)" @change="toggleInList(selectedGroups, g)" class="rounded text-emerald-600" />
                    <span class="truncate">{{ g }}</span>
                  </label>
                </div>
              </div>

              <!-- 5. Certificate Filter Dropdown -->
              <div class="relative">
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
                    <input type="checkbox" :checked="selectedCerts.length === 0" @change="selectedCerts = []" class="rounded text-emerald-600" />
                    <span>All Certificates</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="c in CERT_OPTIONS" :key="c" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedCerts.includes(c)" @change="toggleInList(selectedCerts, c)" class="rounded text-emerald-600" />
                    <span class="truncate">{{ c }}</span>
                  </label>
                </div>
              </div>

              <!-- 6. Tags Filter Dropdown -->
              <div class="relative">
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
                    <input type="checkbox" :checked="selectedTags.length === 0" @change="selectedTags = []" class="rounded text-emerald-600" />
                    <span>All Tags</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="tg in TAG_OPTIONS" :key="tg" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedTags.includes(tg)" @change="toggleInList(selectedTags, tg)" class="rounded text-emerald-600" />
                    <span class="truncate">{{ tg }}</span>
                  </label>
                </div>
              </div>

              <!-- 7. Lead By Filter Dropdown -->
              <div class="relative">
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
                    <input type="checkbox" :checked="selectedLeads.length === 0" @change="selectedLeads = []" class="rounded text-emerald-600" />
                    <span>All Leads</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedLeads.includes('NO_LEADBY')" @change="toggleInList(selectedLeads, 'NO_LEADBY')" class="rounded text-emerald-600" />
                    <span>No Lead by</span>
                  </label>
                  <label v-for="ld in options.leads" :key="ld" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedLeads.includes(ld)" @change="toggleInList(selectedLeads, ld)" class="rounded text-emerald-600" />
                    <span class="truncate">{{ ld }}</span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Active filter chips + Clear All -->
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
                Filtrlarni tozalash
              </button>
            </div>
          </div>

          <!-- Selection Controls Bar -->
          <div class="flex items-center justify-between text-xs font-bold text-zinc-700 dark:text-zinc-300">
            <label class="flex items-center gap-2 cursor-pointer select-none uppercase tracking-wide text-[11px]">
              <input
                type="checkbox"
                :checked="isAllFilteredSelected"
                @change="toggleSelectAllStudents"
                class="h-4 w-4 rounded border-zinc-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
              />
              <span>Talabalarni tanlash (Barchasini belgilash)</span>
            </label>

            <span class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide bg-emerald-500 text-white shadow-2xs">
              {{ selectedStudentIds.size }} / {{ filteredStudents.length }} ta tanlandi
            </span>
          </div>

          <!-- Students List Table -->
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden shadow-xs">
            <div class="overflow-x-auto max-h-96 scrollbar-thin">
              <table class="w-full text-xs text-left">
                <thead class="bg-zinc-50 dark:bg-zinc-800/60 text-zinc-500 border-b border-zinc-200 dark:border-zinc-800 sticky top-0 z-10 select-none">
                  <tr>
                    <th class="p-3 w-10 text-center">
                      <input
                        type="checkbox"
                        :checked="isAllFilteredSelected"
                        @change="toggleSelectAllStudents"
                        class="rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                      />
                    </th>
                    <th class="p-3 font-bold w-24">ID</th>
                    <th class="p-3 font-bold">F.I.SH / Ism</th>
                    <th class="p-3 font-bold">Daraja (Level)</th>
                    <th class="p-3 font-bold">Pasport</th>
                    <th class="p-3 font-bold">Tug'ilgan sana</th>
                    <th class="p-3 font-bold">Telefon</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800/60">
                  <tr
                    v-for="student in filteredStudents"
                    :key="student.id"
                    @click="toggleStudentSelection(student.id)"
                    class="cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition-colors"
                    :class="isStudentSelected(student.id) ? 'bg-emerald-50/50 dark:bg-emerald-950/20' : ''"
                    :style="getRowStripeStyle(student)"
                  >
                    <td class="p-3 text-center" @click.stop>
                      <input
                        type="checkbox"
                        :checked="isStudentSelected(student.id)"
                        @change="toggleStudentSelection(student.id)"
                        class="rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                      />
                    </td>
                    <td class="p-3 align-top">
                      <div class="inline-flex items-center justify-center px-2 py-1 text-[11px] font-mono font-bold bg-[#007aff] text-white rounded-[4px] shadow-2xs min-w-[34px]">
                        {{ student.id }}
                      </div>
                    </td>
                    <td class="p-3 align-top">
                      <div class="flex items-center gap-1.5">
                        <span class="font-bold text-zinc-900 dark:text-zinc-100 uppercase">{{ student.full_name }}</span>
                        <span v-if="student.korean_name" class="text-zinc-400 text-[11px]">({{ student.korean_name }})</span>
                      </div>
                      <div class="mt-0.5 text-[9px] font-bold uppercase tracking-wide text-zinc-400 dark:text-zinc-500 whitespace-nowrap">
                        {{ getTariffDisplayName(student) }}
                      </div>
                    </td>
                    <td class="p-3 align-top">
                      <div class="flex flex-wrap gap-1">
                        <span
                          v-if="student.level"
                          class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide shadow-2xs"
                          :class="getLevelBadgeClass(student.level)"
                        >
                          {{ student.level }}
                        </span>
                        <span
                          v-if="student.level2"
                          class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-[#ffab00] text-zinc-900 shadow-2xs"
                        >
                          {{ student.level2 }}
                        </span>
                      </div>
                      <div v-if="getStudentCerts(student).length > 0" class="flex flex-wrap gap-1 mt-1">
                        <span
                          v-for="(c, cIdx) in getStudentCerts(student)"
                          :key="cIdx"
                          class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-bold shadow-2xs"
                          :class="c.type?.toUpperCase() === 'TOPIK' ? 'bg-rose-500 text-white' : 'bg-blue-600 text-white'"
                        >
                          <span>{{ c.type }}</span>
                          <span v-if="c.score" class="opacity-90 font-mono">{{ c.score }}</span>
                        </span>
                      </div>
                    </td>
                    <td class="p-3 font-mono text-zinc-800 dark:text-zinc-200 align-top">
                      {{ student.passport || '-' }}
                    </td>
                    <td class="p-3 text-zinc-600 dark:text-zinc-400 align-top">
                      {{ student.birthday || '-' }}
                    </td>
                    <td class="p-3 text-zinc-600 dark:text-zinc-400 font-mono align-top">
                      {{ student.phone1 || '-' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Bottom Step Navigation -->
          <div class="flex items-center justify-between pt-4">
            <button
              @click="currentStep = 2"
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
            >
              <ArrowLeft class="w-4 h-4" />
              Ortga (Ustunlar)
            </button>

            <button
              :disabled="selectedStudentIds.size === 0"
              @click="currentStep = 4"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              Yuklab olish bosqichiga o'tish ({{ selectedStudentIds.size }} ta tanlandi)
              <ArrowRight class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- STEP 4: GENERATION OPTIONS & DOWNLOAD -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="currentStep === 4" class="space-y-6">
          <!-- Summary Box -->
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-6">
            <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <Settings2 class="w-4 h-4 text-emerald-500" />
              Faylga yozish parametrlari
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Fill Mode Selection -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-zinc-700 dark:text-zinc-300 block">
                  Yozish rejimi (Fill Mode):
                </label>

                <div class="space-y-2">
                  <label
                    class="flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition-all"
                    :class="fillMode === 'append' ? 'border-emerald-500 bg-emerald-50/40 dark:bg-emerald-950/20' : 'border-zinc-200 dark:border-zinc-800'"
                  >
                    <input type="radio" v-model="fillMode" value="append" class="mt-0.5 text-emerald-600 focus:ring-emerald-500" />
                    <div>
                      <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block">
                        Davomidan qo'shish (Append) — Tavsiya etiladi
                      </span>
                      <span class="text-[11px] text-zinc-500 dark:text-zinc-400">
                        Jadvaldagi mavjud qatorlarga teginmasdan, eng pastki birinchi bo'sh qatordan boshlab yozadi.
                      </span>
                    </div>
                  </label>

                  <label
                    class="flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition-all"
                    :class="fillMode === 'overwrite' ? 'border-amber-500 bg-amber-50/40 dark:bg-amber-950/20' : 'border-zinc-200 dark:border-zinc-800'"
                  >
                    <input type="radio" v-model="fillMode" value="overwrite" class="mt-0.5 text-amber-600 focus:ring-amber-500" />
                    <div>
                      <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block">
                        Namunaviy qatorlarni almashtirish (Overwrite)
                      </span>
                      <span class="text-[11px] text-zinc-500 dark:text-zinc-400">
                        Sarlavhadan keyingi namunaviy talabalar o'rniga yangi tanlangan talabalarni yozadi.
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <!-- Sequence Number & Summary -->
              <div class="space-y-4">
                <div class="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 space-y-3">
                  <div class="flex items-center justify-between">
                    <div>
                      <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block">
                        Tartib raqamini avtomatik davom ettirish
                      </span>
                      <span class="text-[11px] text-zinc-500 dark:text-zinc-400">
                        № ustunini 1, 2, 3... yoki mavjud raqamdan davom ettiradi
                      </span>
                    </div>
                    <input
                      type="checkbox"
                      v-model="autoIncrementSeq"
                      class="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
                    />
                  </div>

                  <hr class="border-zinc-200 dark:border-zinc-800" />

                  <div class="text-xs space-y-1.5 text-zinc-600 dark:text-zinc-400">
                    <div class="flex justify-between">
                      <span>Shablon fayl:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ uploadedFile?.name }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Varaq nomi:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ selectedSheetName }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Tanlangan talabalar:</span>
                      <span class="font-bold text-emerald-600 dark:text-emerald-400">{{ selectedStudentIds.size }} nafar</span>
                    </div>
                    <div class="flex justify-between">
                      <span>To'ldiriladigan ustunlar:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ mappedCount }} ta</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800">
              <button
                @click="currentStep = 3"
                class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
              >
                <ArrowLeft class="w-4 h-4" />
                Ortga (Talabalar)
              </button>

              <button
                :disabled="isGenerating || selectedStudentIds.size === 0"
                @click="openFileNameModal"
                class="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold shadow-lg shadow-emerald-600/25 transition-all disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw v-if="isGenerating" class="w-4 h-4 animate-spin" />
                <Download v-else class="w-4 h-4" />
                {{ isGenerating ? "Fayl to'ldirilmoqda..." : "Faylni to'ldirish va yuklab olish (.xlsx)" }}
              </button>
            </div>
          </div>

          <!-- Success Download Card -->
          <div v-if="generationSuccess" class="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-2xl p-6 text-center space-y-4">
            <div class="w-12 h-12 rounded-full bg-emerald-500 text-white flex items-center justify-center mx-auto shadow-md shadow-emerald-500/30">
              <Check class="w-6 h-6 stroke-[3]" />
            </div>
            <div>
              <h4 class="text-base font-extrabold text-emerald-900 dark:text-emerald-100">
                Excel fayl muvaffaqiyatli to'ldirildi va yuklab olindi!
              </h4>
              <p class="text-xs text-emerald-700 dark:text-emerald-300 mt-1">
                Fayl nomi: <span class="font-mono font-bold">{{ downloadedFileName }}</span>
              </p>
            </div>

            <div class="flex items-center justify-center gap-4 pt-2">
              <button
                @click="resetWizard"
                class="px-5 py-2.5 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs font-bold text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
              >
                Yangi fayl to'ldirish
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- File Name Modal -->
    <Teleport to="body">
      <div
        v-if="isFileNameModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150"
        @click.self="isFileNameModalOpen = false"
      >
        <div
          class="bg-white dark:bg-[#15171a] border border-zinc-200 dark:border-zinc-800 rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-150 relative"
          @click.stop
        >
          <!-- Modal Header -->
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/25">
                <FileSpreadsheet class="w-6 h-6" />
              </div>
              <div>
                <h3 class="text-base font-extrabold text-zinc-900 dark:text-zinc-100">
                  Excel fayl nomini kiriting
                </h3>
                <p class="text-xs text-zinc-500 dark:text-zinc-400">
                  Yuklab olinadigan tayyor fayl uchun nom belgilang
                </p>
              </div>
            </div>

            <button
              @click="isFileNameModalOpen = false"
              class="w-8 h-8 rounded-xl flex items-center justify-center text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- File Name Input -->
          <div class="space-y-2">
            <label class="text-xs font-bold text-zinc-700 dark:text-zinc-300 block">
              Fayl nomi:
            </label>
            <div class="relative flex items-center rounded-2xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50/80 dark:bg-zinc-800/80 focus-within:border-emerald-500 focus-within:ring-2 focus-within:ring-emerald-500/20 overflow-hidden transition-all">
              <input
                type="text"
                v-model="customFileName"
                autofocus
                placeholder="Fayl nomini kiriting..."
                @keydown.enter="confirmAndDownload"
                class="flex-1 px-4 py-3 bg-transparent text-sm font-semibold text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none"
              />
              <span class="px-3 py-1.5 mr-2 rounded-xl bg-zinc-200/70 dark:bg-zinc-700 text-xs font-mono font-bold text-zinc-600 dark:text-zinc-300 select-none">
                .xlsx
              </span>
            </div>
          </div>

          <!-- Quick presets / suggestions -->
          <div class="space-y-1.5">
            <span class="text-[11px] font-semibold text-zinc-400 block">
              Tezkor namunalar:
            </span>
            <div class="flex flex-wrap gap-1.5">
              <button
                type="button"
                @click="setPresetName(`Filled_${uploadedFile?.name.replace(/\.[^/.]+$/, '')}_${new Date().toISOString().slice(0, 10)}`)"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-zinc-100 dark:bg-zinc-800 hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-emerald-950/50 dark:hover:text-emerald-300 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 transition-colors cursor-pointer"
              >
                Filled_{{ uploadedFile?.name.replace(/\.[^/.]+$/, '') }}
              </button>
              <button
                type="button"
                @click="setPresetName(`${uploadedFile?.name.replace(/\.[^/.]+$/, '')}_(${selectedStudentIds.size}_talaba)`)"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-zinc-100 dark:bg-zinc-800 hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-emerald-950/50 dark:hover:text-emerald-300 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 transition-colors cursor-pointer"
              >
                {{ uploadedFile?.name.replace(/\.[^/.]+$/, '') }}_({{ selectedStudentIds.size }}_talaba)
              </button>
              <button
                type="button"
                @click="setPresetName(`${selectedSheetName}_${new Date().toISOString().slice(0, 10)}`)"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-zinc-100 dark:bg-zinc-800 hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-emerald-950/50 dark:hover:text-emerald-300 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 transition-colors cursor-pointer"
              >
                {{ selectedSheetName }}_{{ new Date().toISOString().slice(0, 10) }}
              </button>
            </div>
          </div>

          <!-- Export Details Summary Chips -->
          <div class="p-3 rounded-2xl bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between text-xs">
            <div class="flex items-center gap-1.5 truncate">
              <span class="text-zinc-400">Varaq:</span>
              <span class="font-bold text-zinc-800 dark:text-zinc-200 truncate">{{ selectedSheetName }}</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <span class="text-zinc-400">Talabalar:</span>
              <span class="font-bold text-emerald-600 dark:text-emerald-400">{{ selectedStudentIds.size }} nafar</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <span class="text-zinc-400">Ustunlar:</span>
              <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ mappedCount }} ta</span>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              @click="isFileNameModalOpen = false"
              class="px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
            >
              Bekor qilish
            </button>

            <button
              type="button"
              :disabled="isGenerating"
              @click="confirmAndDownload"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/25 transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw v-if="isGenerating" class="w-4 h-4 animate-spin" />
              <Download v-else class="w-4 h-4" />
              {{ isGenerating ? "To'ldirilmoqda..." : "Yuklab olish" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
