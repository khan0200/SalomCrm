<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import {
  Upload,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Download,
  RefreshCw,
  Sparkles,
  Users,
  Search,
  Check,
  ChevronDown,
  FileText,
  Info,
  Folder,
  Tag,
  GraduationCap,
  Award,
  Contact,
  Bookmark,
  CheckSquare,
  X
} from 'lucide-vue-next'
import {
  wordFillApi,
  type WordAnalysisResult,
  type WordMappingConfig,
  type WordSlot,
  type WordScanTagsResult,
  type WordScannedTag,
} from '@/api/wordFill'
import WordPlaceholderCatalog from './components/WordPlaceholderCatalog.vue'
import { studentsApi } from '@/api/students'
import type { Student } from '@/types'
import { ROW_COLOR_MAP } from '@/types'

// ─── Step State ─────────────────────────────────────────────────────────────
const currentStep = ref<1 | 2 | 3 | 4>(1)
const showCatalogModal = ref(false)

const downloadExampleTemplate = () => {
  const link = document.createElement('a')
  link.href = '/APPFORM.docx'
  link.setAttribute('download', 'APPFORM.docx')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// ─── File & Template State ──────────────────────────────────────────────────
const uploadedFile = ref<File | null>(null)
const isAnalyzing = ref(false)
const analysisError = ref<string | null>(null)
const analysisData = ref<WordAnalysisResult | null>(null)
const scanResult = ref<WordScanTagsResult | null>(null)
const customTagMappings = ref<Record<string, string>>({})
const isDragging = ref(false)
// AI mapping is always on; the backend falls back to its own dictionary when no
// API key is configured, so there is nothing here for the user to decide.
const AI_PROVIDER = 'openai'

// ─── Catalog Fields for Samples & Labels ────────────────────────────────────
const { data: catalogFieldsData } = useQuery({
  queryKey: ['word-fill-catalog-fields'],
  queryFn: () => wordFillApi.getPlaceholderCatalog(),
  staleTime: 1000 * 60 * 30,
})
const catalogFields = computed(() => catalogFieldsData.value || [])

// ─── Mappings State ─────────────────────────────────────────────────────────
const mappings = ref<WordMappingConfig[]>([])
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
const TAG_OPTIONS = [...PREDEFINED_TAGS, 'Custom']

// ─── Generation & Output State ──────────────────────────────────────────────
const filenamePattern = ref('{full_name}')
const checkboxMark = ref('V')
const isGenerating = ref(false)
const generationSuccess = ref(false)
const downloadedFileName = ref('')

// ─── Options & Folders from CRM ─────────────────────────────────────────────
const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
  staleTime: 1000 * 60 * 10,
})

const options = computed(() => optionsData.value || {
  tariffs: [], levels: [], groups: [], leads: [],
  coordinators: [], universities: [], folders: [],
  offices: ['ANDIJON OFFIS', 'TOSHKENT OFFIS']
})

const { data: foldersData } = useQuery({
  queryKey: ['folders'],
  queryFn: () => studentsApi.getFolders(),
  staleTime: 1000 * 60 * 5,
})
const folders = computed(() => foldersData.value || [])

// Synchronized with Master Student Roster cache
const { data: allStudentsData, isLoading: isLoadingStudents } = useQuery({
  queryKey: ['all-students-master'],
  queryFn: () => studentsApi.getStudents({
    page: 1,
    page_size: 5000,
    folder: 'all',
    include_archive: true,
  }),
  staleTime: 1000 * 60 * 5,
})

const allStudents = computed<Student[]>(
  () => (allStudentsData.value?.results || []).filter(s => !s.is_deleted)
)

// Dynamic Option Sources (from Config + Master Students)
const tariffOptions = computed<string[]>(() => {
  const custom = (options.value.tariffs || []).map((t: any) => typeof t === 'string' ? t : (t?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  allStudents.value.forEach(s => { if (s.tariff) set.add(s.tariff) })
  return Array.from(set).filter(t => t !== 'NO_TARIFF' && t !== 'No Tariff').sort((a, b) => a.localeCompare(b))
})

const levelOptions = computed<string[]>(() => {
  const custom = (options.value.levels || []).map((l: any) => typeof l === 'string' ? l : (l?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  allStudents.value.forEach(s => {
    if (s.level) set.add(s.level)
    if (s.level2) set.add(s.level2)
  })
  return Array.from(set).filter(l => l !== 'NO_LEVEL' && l !== 'No Level').sort((a, b) => a.localeCompare(b))
})

const groupOptions = computed<string[]>(() => {
  const custom = (options.value.groups || []).map((g: any) => typeof g === 'string' ? g : (g?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  allStudents.value.forEach(s => { if (s.student_group) set.add(s.student_group) })
  return Array.from(set).filter(g => g !== 'NO_GROUP' && g !== 'No Group').sort((a, b) => a.localeCompare(b))
})

const leadOptions = computed<string[]>(() => {
  const custom = (options.value.leads || []).map((l: any) => typeof l === 'string' ? l : (l?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  allStudents.value.forEach(s => { if (s.lead_by) set.add(s.lead_by) })
  return Array.from(set).filter(l => l !== 'NO_LEADBY' && l !== 'No Lead by').sort((a, b) => a.localeCompare(b))
})

const tagOptions = computed<string[]>(() => {
  const backendTags = ((options.value as any).tags || []).map((t: any) => typeof t === 'string' ? t : (t?.name || '')).filter(Boolean)
  const set = new Set<string>([...PREDEFINED_TAGS, ...backendTags])
  allStudents.value.forEach(s => {
    if (Array.isArray(s.task_tags)) {
      s.task_tags.forEach(t => { if (t) set.add(t) })
    }
  })
  const list = Array.from(set).filter(t => t !== 'Custom').sort((a, b) => a.localeCompare(b))
  return [...list, 'Custom']
})

// ─── Filter students ────────────────────────────────────────────────────────
const filteredStudents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return allStudents.value.filter(s => {
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

    if (selectedFolders.value.length > 0) {
      const studentFolderIds = (s.folder_ids || (s.folders || []).map((f: any) => f.id) || []).map((x: any) => String(x).toLowerCase())
      const hasFolder = selectedFolders.value.some(fid => {
        if (fid === 'NO_FOLDER') return studentFolderIds.length === 0
        return studentFolderIds.includes(String(fid).toLowerCase())
      })
      if (!hasFolder) return false
    }

    if (selectedTariffs.value.length > 0) {
      const hasNoTariff = selectedTariffs.value.includes('NO_TARIFF') || selectedTariffs.value.includes('No Tariff')
      const cleanTariffs = selectedTariffs.value.filter(t => t !== 'NO_TARIFF' && t !== 'No Tariff')
      const sTariff = s.tariff || ''
      const matchNo = hasNoTariff && (!sTariff || sTariff === 'NO_TARIFF' || sTariff === 'No Tariff')
      const matchTariff = cleanTariffs.length > 0 && cleanTariffs.includes(sTariff)
      if (!matchNo && !matchTariff) return false
    }

    if (selectedLevels.value.length > 0) {
      const hasNoLevel = selectedLevels.value.includes('NO_LEVEL') || selectedLevels.value.includes('No Level')
      const cleanLevels = selectedLevels.value.filter(l => l !== 'NO_LEVEL' && l !== 'No Level')
      const sLevel = s.level || ''
      const sLevel2 = s.level2 || ''
      const matchNo = hasNoLevel && (!sLevel || cleanLevels.includes(sLevel) || cleanLevels.includes(sLevel2))
      const matchLevel = (sLevel && cleanLevels.includes(sLevel)) || (sLevel2 && cleanLevels.includes(sLevel2))
      if (!matchNo && !matchLevel) return false
    }

    if (selectedGroups.value.length > 0) {
      const hasNoGroup = selectedGroups.value.includes('NO_GROUP') || selectedGroups.value.includes('No Group')
      const cleanGroups = selectedGroups.value.filter(g => g !== 'NO_GROUP' && g !== 'No Group')
      const sGroup = s.student_group || ''
      const matchNo = hasNoGroup && (!sGroup || cleanGroups.includes(sGroup))
      const matchGroup = cleanGroups.length > 0 && cleanGroups.includes(sGroup)
      if (!matchNo && !matchGroup) return false
    }

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

    if (selectedTags.value.length > 0) {
      const tags = Array.isArray(s.task_tags) ? s.task_tags : []
      const match = selectedTags.value.some(tag => {
        if (tag === 'Custom') return tags.some(t => !PREDEFINED_TAGS.includes(t))
        return tags.includes(tag)
      })
      if (!match) return false
    }

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
})

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
  if (selectedFolders.value.length) {
    const label = selectedFolders.value.length === 1
      ? (selectedFolders.value[0] === 'NO_FOLDER' ? 'Folder: No Folder' : `Folder: ${folders.value.find(f => String(f.id).toLowerCase() === String(selectedFolders.value[0]).toLowerCase())?.name || '1'}`)
      : `Folder: ${selectedFolders.value.length}`
    chips.push({ key: 'folder', label, clear: () => { selectedFolders.value = [] } })
  }
  if (selectedTariffs.value.length) {
    const label = selectedTariffs.value.length === 1
      ? `Tariff: ${selectedTariffs.value[0] === 'NO_TARIFF' ? 'No Tariff' : selectedTariffs.value[0]}`
      : `Tariff: ${selectedTariffs.value.length}`
    chips.push({ key: 'tariff', label, clear: () => { selectedTariffs.value = [] } })
  }
  if (selectedLevels.value.length) {
    const label = selectedLevels.value.length === 1
      ? `Level: ${selectedLevels.value[0] === 'NO_LEVEL' ? 'No Level' : selectedLevels.value[0]}`
      : `Level: ${selectedLevels.value.length}`
    chips.push({ key: 'level', label, clear: () => { selectedLevels.value = [] } })
  }
  if (selectedGroups.value.length) {
    const label = selectedGroups.value.length === 1
      ? `Group: ${selectedGroups.value[0] === 'NO_GROUP' ? 'No Group' : selectedGroups.value[0]}`
      : `Group: ${selectedGroups.value.length}`
    chips.push({ key: 'group', label, clear: () => { selectedGroups.value = [] } })
  }
  if (selectedCerts.value.length) {
    const label = selectedCerts.value.length === 1
      ? `Cert: ${selectedCerts.value[0]}`
      : `Certificate: ${selectedCerts.value.length}`
    chips.push({ key: 'cert', label, clear: () => { selectedCerts.value = [] } })
  }
  if (selectedTags.value.length) {
    const label = selectedTags.value.length === 1
      ? `Tag: ${selectedTags.value[0]}`
      : `Tag: ${selectedTags.value.length}`
    chips.push({ key: 'tag', label, clear: () => { selectedTags.value = [] } })
  }
  if (selectedLeads.value.length) {
    const label = selectedLeads.value.length === 1
      ? `Lead: ${selectedLeads.value[0] === 'NO_LEADBY' ? 'No Lead by' : selectedLeads.value[0]}`
      : `Lead: ${selectedLeads.value.length}`
    chips.push({ key: 'lead', label, clear: () => { selectedLeads.value = [] } })
  }
  return chips
})

const clearAllFilters = () => {
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

// ─── File Upload & Tag Scan ──────────────────────────────────────────────
const handleFileUpload = async (file: File) => {
  if (!file.name.toLowerCase().match(/\.(docx|dotx)$/)) {
    analysisError.value = "Faqat .docx formatidagi Word fayllari qabul qilinadi (eski .doc qo'llab-quvvatlanmaydi)"
    return
  }

  uploadedFile.value = file
  isAnalyzing.value = true
  analysisError.value = null
  scanResult.value = null

  try {
    const res = await wordFillApi.scanTags(file)
    scanResult.value = res

    const mapObj: Record<string, string> = {}
    for (const t of res.tags) {
      mapObj[t.tag_name] = t.crm_field || '_skip'
    }
    customTagMappings.value = mapObj

    currentStep.value = 2
  } catch (err: any) {
    console.error('Error scanning Word template:', err)
    analysisError.value = err.response?.data?.error || err.message || "Faylni tekshirishda xatolik yuz berdi"
  } finally {
    isAnalyzing.value = false
  }
}

const onDropFile = (e: DragEvent) => {
  isDragging.value = false
  if (e.dataTransfer?.files?.length) handleFileUpload(e.dataTransfer.files[0])
}

const onFileInputChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files?.length) handleFileUpload(target.files[0])
}

// Category ordering and labels
const CATEGORY_ORDER: { key: string; label: string }[] = [
  { key: 'personal', label: 'Shaxsiy ma\'lumotlar' },
  { key: 'passport', label: 'Pasport ma\'lumotlari' },
  { key: 'contacts', label: 'Aloqa ma\'lumotlari' },
  { key: 'parents', label: 'Ota-ona ma\'lumotlari' },
  { key: 'education', label: 'Ta\'lim ma\'lumotlari' },
  { key: 'certificates', label: 'Til sertifikatlari' },
  { key: 'university', label: 'Universitet tanlovlari' },
  { key: 'management', label: 'Boshqa / CRM' },
  { key: 'system', label: 'Tizim / Sanalar' },
]

const categorizedCrmFields = computed(() => {
  const fields = scanResult.value?.available_fields?.length
    ? scanResult.value.available_fields
    : (catalogFields.value || [])
  if (!fields.length) return {}

  const groups: Record<string, { key: string; label: string }[]> = {}

  CATEGORY_ORDER.forEach(c => {
    groups[c.label] = []
  })

  const categoryLabelMap = new Map(CATEGORY_ORDER.map(c => [c.key, c.label]))

  fields.forEach((f: any) => {
    const rawCat = typeof f?.category === 'string' ? f.category : ''
    const mapped = categoryLabelMap.get(rawCat)
    const groupLabel: string = mapped || (rawCat ? rawCat.charAt(0).toUpperCase() + rawCat.slice(1) : 'Boshqa')
    if (!groups[groupLabel]) {
      groups[groupLabel] = []
    }
    groups[groupLabel]!.push({ key: f.key, label: f.label })
  })

  const nonEmptyGroups: Record<string, { key: string; label: string }[]> = {}
  for (const [name, items] of Object.entries(groups)) {
    if (items.length > 0) {
      nonEmptyGroups[name] = items
    }
  }

  return nonEmptyGroups
})

const getFieldSample = (fieldKey?: string | null) => {
  if (!fieldKey || fieldKey === '_skip') return "—"
  const item = catalogFields.value.find(f => f.key === fieldKey)
  return item?.sample || ''
}

const mappedCount = computed(() => {
  if (!customTagMappings.value) return 0
  return Object.values(customTagMappings.value).filter(f => f && f !== '_skip').length
})

const checkboxCount = computed(() => 0)

const confidenceBadge = (conf: number) => {
  if (conf >= 0.9) return { text: 'Yuqori', cls: 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300' }
  if (conf >= 0.7) return { text: "O'rtacha", cls: 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300' }
  if (conf > 0) return { text: 'Past', cls: 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300' }
  return { text: 'Yo\'q', cls: 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500' }
}

const sourceLabel = computed(() => {
  const src = analysisData.value?.mapping_source
  if (src === 'ai') return { text: 'AI tomonidan moslandi', cls: 'bg-violet-100 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300' }
  if (src === 'ai_partial') return { text: "AI qisman moslandi", cls: 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300' }
  return { text: "Lug'at asosida moslandi (AI kaliti yo'q)", cls: 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300' }
})

// ─── Student Selection Handlers ─────────────────────────────────────────────
const isAllFilteredSelected = computed(() => {
  if (!filteredStudents.value.length) return false
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
  if (selectedStudentIds.value.has(id)) selectedStudentIds.value.delete(id)
  else selectedStudentIds.value.add(id)
}

const isStudentSelected = (id: string) => selectedStudentIds.value.has(id)

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

// ─── Filename preview ───────────────────────────────────────────────────────
const FILENAME_PRESETS = [
  { pattern: '{full_name}', label: 'ISM FAMILIYA' },
  { pattern: '{full_name}_{id}', label: 'ISM FAMILIYA_ID' },
  { pattern: '{id}_{full_name}', label: 'ID_ISM FAMILIYA' },
  { pattern: '{full_name}_{passport}', label: 'ISM FAMILIYA_PASPORT' },
  { pattern: 'AppForm_{full_name}_{date}', label: 'AppForm_ISM_SANA' },
]

const filenamePreview = computed(() => {
  const first = filteredStudents.value.find(s => selectedStudentIds.value.has(s.id))
  const sample = {
    full_name: first?.full_name || 'ABDUVOIDOV KHAYITALI',
    id: first?.id || '1024',
    passport: first?.passport || 'AD1234567',
    index: '1',
    date: new Date().toISOString().slice(0, 10),
  }
  let out = filenamePattern.value || '{full_name}'
  Object.entries(sample).forEach(([k, v]) => {
    out = out.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v))
  })
  return `${out.replace(/[\\/:*?"<>|]+/g, '_').trim() || 'document'}.docx`
})

// ─── Generate & Download ────────────────────────────────────────────────────
const downloadedBlob = ref<Blob | null>(null)

const triggerBrowserDownload = (blob: Blob, fileName: string) => {
  const mimeType = fileName.endsWith('.zip')
    ? 'application/zip'
    : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  const file = new File([blob], fileName, { type: mimeType })
  const url = window.URL.createObjectURL(file)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', fileName)
  link.download = fileName
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  setTimeout(() => {
    if (document.body.contains(link)) {
      document.body.removeChild(link)
    }
    window.URL.revokeObjectURL(url)
  }, 2000)
}

const handleGenerate = async () => {
  if (!uploadedFile.value || selectedStudentIds.value.size === 0) return

  isGenerating.value = true
  generationSuccess.value = false

  try {
    const blob = await wordFillApi.generateFilledWord({
      file: uploadedFile.value,
      mappings: mappings.value.filter(m => m.field !== '_skip'),
      custom_tag_mappings: customTagMappings.value,
      student_ids: Array.from(selectedStudentIds.value),
      filename_pattern: filenamePattern.value,
      checkbox_mark: checkboxMark.value,
    })

    downloadedBlob.value = blob
    const count = selectedStudentIds.value.size
    const baseName = uploadedFile.value.name.replace(/\.[^/.]+$/, '')
    const fileName = count > 1
      ? `Filled_${baseName}_${count}ta.zip`
      : filenamePreview.value

    downloadedFileName.value = fileName
    triggerBrowserDownload(blob, fileName)

    generationSuccess.value = true
    currentStep.value = 4
  } catch (err: any) {
    console.error('Error generating Word documents:', err)
    let errMsg = err.message || 'Server error'
    if (err.response?.data instanceof Blob) {
      try {
        const parsed = JSON.parse(await err.response.data.text())
        if (parsed.error) errMsg = parsed.error
      } catch { /* keep original message */ }
    } else if (err.response?.data?.error) {
      errMsg = err.response.data.error
    }
    alert("Word faylni to'ldirishda xatolik yuz berdi: " + errMsg)
  } finally {
    isGenerating.value = false
  }
}

const downloadAgain = () => {
  if (downloadedBlob.value && downloadedFileName.value) {
    triggerBrowserDownload(downloadedBlob.value, downloadedFileName.value)
  } else {
    handleGenerate()
  }
}

const resetWizard = () => {
  currentStep.value = 1
  uploadedFile.value = null
  analysisData.value = null
  scanResult.value = null
  customTagMappings.value = {}
  downloadedBlob.value = null
  downloadedFileName.value = ''
  analysisError.value = null
  mappings.value = []
  selectedStudentIds.value.clear()
  clearAllFilters()
  searchQuery.value = ''
  searchType.value = 'all'
  generationSuccess.value = false
  filenamePattern.value = '{full_name}'
}
</script>

<template>
  <div class="h-full flex flex-col bg-zinc-50 dark:bg-[#0c0d0e] overflow-hidden" @click="closeAllDropdowns">
    <!-- Sub header: the App Form tab bar above already names this engine -->
    <header class="bg-white dark:bg-[#111315] border-b border-zinc-200 dark:border-zinc-800/80 px-6 py-3 flex items-center justify-between gap-4 shrink-0">
      <div class="flex items-center gap-3 min-w-0">
        <p class="text-xs text-zinc-500 dark:text-zinc-400 truncate hidden sm:block">
          Application Form (.docx) shablonlarini tanlangan talabalar uchun avtomatik to'ldirish
        </p>
        <button
          type="button"
          @click="showCatalogModal = true"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 hover:bg-blue-100 dark:hover:bg-blue-900/60 border border-blue-200 dark:border-blue-800 transition-all cursor-pointer shrink-0"
          title="Barcha mavjud {{...}} teglari ro'yxatini ochish"
        >
          <Sparkles class="w-3.5 h-3.5" />
          <span>Teglar katalogi (&#123;&#123; &#125;&#125;)</span>
        </button>
      </div>

      <div class="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-800/60 p-1 rounded-xl border border-zinc-200/60 dark:border-zinc-700/60 shrink-0">
        <button
          v-for="s in [
            { num: 1, label: '1. Shablon' },
            { num: 2, label: '2. Teglarni tekshirish' },
            { num: 3, label: '3. Talabalar' },
            { num: 4, label: '4. Yuklab olish' }
          ]"
          :key="s.num"
          :disabled="(s.num === 2 && !scanResult) || (s.num >= 3 && !uploadedFile)"
          @click="currentStep = s.num as any"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer"
          :class="[
            currentStep === s.num
              ? 'bg-white dark:bg-zinc-700 text-blue-600 dark:text-blue-400 shadow-xs font-bold'
              : s.num < currentStep
                ? 'text-zinc-700 dark:text-zinc-300 hover:bg-white/50 dark:hover:bg-zinc-700/50'
                : 'text-zinc-400 dark:text-zinc-500 cursor-not-allowed'
          ]"
        >
          <span
            class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold"
            :class="currentStep === s.num ? 'bg-blue-500 text-white' : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-400'"
          >
            {{ s.num }}
          </span>
          {{ s.label }}
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 overflow-y-auto p-4 sm:p-6 scrollbar-thin">
      <div class="w-full max-w-[1800px] mx-auto">
        <!-- ═══════════════════ STEP 1: UPLOAD ═══════════════════ -->
        <div v-if="currentStep === 1" class="space-y-6">
          <!-- Quick-Copy Demonstration of All Fields & {{field name}} -->
          <WordPlaceholderCatalog />

          <!-- Word Template Upload Zone -->
          <div
            class="border-2 border-dashed rounded-2xl p-8 text-center transition-all bg-white dark:bg-[#111315]"
            :class="isDragging
              ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20'
              : 'border-zinc-300 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-700'"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDropFile"
          >
            <div class="max-w-md mx-auto flex flex-col items-center">
              <div class="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800/60 flex items-center justify-center text-blue-600 dark:text-blue-400 mb-4 shadow-sm">
                <Upload class="w-8 h-8" />
              </div>
              <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 mb-1">
                Universitetning Word application formini yuklang
              </h3>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 mb-5">
                .docx formatidagi ariza shakli yoki yuqoridagi teglar bilan tayyorlangan shablon (Koreyscha, Inglizcha, Ruscha)
              </p>

              <label class="cursor-pointer inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all">
                <FileText class="w-4 h-4" />
                Kompyuterdan tanlash
                <input type="file" class="hidden" accept=".docx, .dotx" @change="onFileInputChange" />
              </label>
            </div>
          </div>

          <div v-if="isAnalyzing" class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 text-center space-y-3">
            <RefreshCw class="w-8 h-8 text-blue-500 animate-spin mx-auto" />
            <h4 class="text-sm font-bold text-zinc-800 dark:text-zinc-200">
              Word fayldagi teglarni tekshirish...
            </h4>
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              Hujjatdagi barcha jadvallar, paragraflar va katakchalardagi teglarning to'g'riligi tahlil qilinmoqda
            </p>
          </div>

          <div v-if="analysisError" class="bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-2xl p-4 flex items-center gap-3 text-rose-700 dark:text-rose-300 text-xs">
            <AlertTriangle class="w-5 h-5 shrink-0" />
            <span>{{ analysisError }}</span>
          </div>
        </div>

        <!-- ═══════════════════ STEP 2: TAG VERIFICATION & REMAPPING ═══════════════════ -->
        <div v-if="currentStep === 2 && scanResult" class="space-y-5">
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 sm:p-6 space-y-5">
            <!-- Header row -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 dark:border-zinc-800 pb-4">
              <div>
                <h3 class="text-base font-extrabold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                  <CheckCircle2 class="w-5 h-5 text-emerald-500" />
                  Hujjatdagi teglarni tekshirish
                </h3>
                <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                  <strong>{{ uploadedFile?.name }}</strong> faylidan jami <strong>{{ scanResult.total_tags_count }}</strong> ta teg topildi.
                  To'g'ri kelgan va begona teglarni tekshiring.
                </p>
              </div>

              <div class="flex items-center gap-2">
                <button
                  type="button"
                  @click="currentStep = 1"
                  class="px-3.5 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-all cursor-pointer"
                >
                  Boshqa fayl tanlash
                </button>
              </div>
            </div>

            <!-- 3 Stat Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              <div class="p-4 rounded-2xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800">
                <span class="text-xs font-medium text-zinc-500 dark:text-zinc-400 block">Jami topilgan teglar</span>
                <span class="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 mt-0.5 block">
                  {{ scanResult.total_tags_count }} <span class="text-xs font-normal text-zinc-400">({{ scanResult.unique_tags_count }} xil teg)</span>
                </span>
              </div>

              <div class="p-4 rounded-2xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-800/60">
                <span class="text-xs font-medium text-emerald-700 dark:text-emerald-400 block">To'g'ri moslangan teglar</span>
                <span class="text-xl font-extrabold text-emerald-700 dark:text-emerald-300 mt-0.5 block">
                  {{ scanResult.recognized_count }} ta ✅
                </span>
              </div>

              <div
                class="p-4 rounded-2xl border transition-all"
                :class="scanResult.alien_count > 0
                  ? 'bg-amber-50/70 dark:bg-amber-950/30 border-amber-300 dark:border-amber-800'
                  : 'bg-zinc-50 dark:bg-zinc-900/60 border-zinc-200 dark:border-zinc-800'"
              >
                <span class="text-xs font-medium block" :class="scanResult.alien_count > 0 ? 'text-amber-800 dark:text-amber-400' : 'text-zinc-500 dark:text-zinc-400'">
                  Begona / Noma'lum teglar
                </span>
                <span class="text-xl font-extrabold mt-0.5 block" :class="scanResult.alien_count > 0 ? 'text-amber-700 dark:text-amber-300' : 'text-zinc-700 dark:text-zinc-300'">
                  {{ scanResult.alien_count }} ta {{ scanResult.alien_count > 0 ? '⚠️' : '✓' }}
                </span>
              </div>
            </div>

            <!-- Alien tags notice if any -->
            <div
              v-if="scanResult.alien_count > 0"
              class="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2.5 leading-relaxed"
            >
              <AlertTriangle class="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
              <div>
                <strong>Diqqat:</strong> Hujjatda <strong>{{ scanResult.alien_count }} ta noma'lum teg</strong> aniqlandi.
                Ular arizangizda qaysi ma'lumotga almashtirilishi kerakligini quyidagi jadvaldan tanlang yoki <em>"O'tkazib yuborish"</em> ni belgilang.
              </div>
            </div>

            <!-- Tags Table -->
            <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden shadow-2xs">
              <table class="w-full text-left border-collapse text-xs">
                <thead class="bg-zinc-50/90 dark:bg-[#151719] border-b border-zinc-200 dark:border-zinc-800 text-[11px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider select-none">
                  <tr>
                    <th class="py-3 px-3 w-12 text-center">№</th>
                    <th class="py-3 px-4 min-w-[200px]">Hujjatdagi Teg</th>
                    <th class="py-3 px-4 w-40">Holati</th>
                    <th class="py-3 px-4 min-w-[260px]">CRM Maydoni (Moslash)</th>
                    <th class="py-3 px-4 min-w-[200px]">Namuna ma'lumot</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-200/70 dark:divide-zinc-800/70 bg-white dark:bg-[#111315]">
                  <tr
                    v-for="(tag, idx) in scanResult.tags"
                    :key="tag.tag_name"
                    class="hover:bg-zinc-50/70 dark:hover:bg-zinc-800/30 transition-colors"
                  >
                    <td class="py-3 px-3 text-center text-[11px] font-mono font-medium text-zinc-400">
                      {{ idx + 1 }}
                    </td>
                    <td class="py-3 px-4">
                      <div class="flex items-center gap-2">
                        <span class="px-2.5 py-1 rounded-lg font-mono font-bold text-xs bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 border border-zinc-200 dark:border-zinc-700">
                          {{ tag.raw_tag }}
                        </span>
                        <span class="text-[10px] text-zinc-400 font-medium">
                          ({{ tag.occurrences }} marta)
                        </span>
                      </div>
                    </td>
                    <td class="py-3 px-4">
                      <span
                        v-if="tag.is_recognized"
                        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300"
                      >
                        <CheckCircle2 class="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                        Moslandi
                      </span>
                      <span
                        v-else
                        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300"
                      >
                        <AlertTriangle class="w-3 h-3 text-amber-600 dark:text-amber-400" />
                        Begona teg
                      </span>
                    </td>
                    <td class="py-3 px-4">
                      <select
                        v-model="customTagMappings[tag.tag_name]"
                        class="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-xs font-semibold rounded-xl px-3 py-2 text-zinc-900 dark:text-zinc-100 cursor-pointer focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition-all"
                      >
                        <option value="_skip">❌ O'tkazib yuborish (Bo'sh qoldirish)</option>
                        <optgroup
                          v-for="(fields, groupName) in categorizedCrmFields"
                          :key="groupName"
                          :label="groupName"
                        >
                          <option v-for="f in fields" :key="f.key" :value="f.key">
                            {{ f.label }}
                          </option>
                        </optgroup>
                      </select>
                    </td>
                    <td class="py-3 px-4 text-xs font-medium text-zinc-700 dark:text-zinc-300">
                      <span class="px-2 py-1 rounded-md bg-zinc-100/80 dark:bg-zinc-800/80 font-mono text-[11px] text-zinc-700 dark:text-zinc-300 border border-zinc-200/60 dark:border-zinc-700/60 inline-block max-w-[220px] truncate" :title="getFieldSample(customTagMappings[tag.tag_name])">
                        {{ getFieldSample(customTagMappings[tag.tag_name]) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Navigation bottom -->
            <div class="flex items-center justify-between pt-2">
              <button
                type="button"
                @click="currentStep = 1"
                class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
              >
                <ArrowLeft class="w-4 h-4" />
                Ortga (Shablon)
              </button>

              <button
                type="button"
                @click="currentStep = 3"
                class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all cursor-pointer"
              >
                Talabalarni tanlashga o'tish
                <ArrowRight class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- ═══════════════════ STEP 3: SELECT STUDENTS ═══════════════════ -->
        <div v-if="currentStep === 3" class="space-y-5" @click="closeAllDropdowns">
          <div class="space-y-3 bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200 dark:border-zinc-750 rounded-2xl p-4 shadow-2xs" @click.stop>
            <div class="flex items-stretch gap-0 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 overflow-hidden focus-within:border-blue-500 transition-colors">
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

            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-2">
              <!-- Folder -->
              <div class="relative filter-dropdown-container">
                <button
                  type="button"
                  @click="toggleDropdown('folder')"
                  class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="selectedFolders.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Folder class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ selectedFolders.length === 0 ? 'Folder' : `Folder · ${selectedFolders.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
                </button>
                <div v-if="isFolderDropdownOpen" class="absolute left-0 mt-1 w-52 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs" @click.stop>
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="selectedFolders.length === 0" @change="selectedFolders = []" class="rounded text-blue-600" />
                    <span>All Folders</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedFolders.includes('NO_FOLDER')" @change="toggleInList(selectedFolders, 'NO_FOLDER')" class="rounded text-blue-600" />
                    <span>No Folder</span>
                  </label>
                  <label v-for="f in folders" :key="f.id" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedFolders.includes(String(f.id))" @change="toggleInList(selectedFolders, String(f.id))" class="rounded text-blue-600" />
                    <span class="truncate">{{ f.name }}</span>
                  </label>
                </div>
              </div>

              <!-- Tariff -->
              <div class="relative filter-dropdown-container">
                <button
                  type="button"
                  @click="toggleDropdown('tariff')"
                  class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="selectedTariffs.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Award class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ selectedTariffs.length === 0 ? 'Tariff' : `Tariff · ${selectedTariffs.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
                </button>
                <div v-if="isTariffDropdownOpen" class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs" @click.stop>
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

              <!-- Level -->
              <div class="relative filter-dropdown-container">
                <button
                  type="button"
                  @click="toggleDropdown('level')"
                  class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="selectedLevels.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <GraduationCap class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ selectedLevels.length === 0 ? 'Level' : `Level · ${selectedLevels.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
                </button>
                <div v-if="isLevelDropdownOpen" class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs" @click.stop>
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

              <!-- Group -->
              <div class="relative filter-dropdown-container">
                <button
                  type="button"
                  @click="toggleDropdown('group')"
                  class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="selectedGroups.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Users class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ selectedGroups.length === 0 ? 'Group' : `Group · ${selectedGroups.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
                </button>
                <div v-if="isGroupDropdownOpen" class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs" @click.stop>
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

              <!-- Certificate -->
              <div class="relative filter-dropdown-container">
                <button
                  type="button"
                  @click="toggleDropdown('cert')"
                  class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="selectedCerts.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Bookmark class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ selectedCerts.length === 0 ? 'Certificate' : `Certificate · ${selectedCerts.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
                </button>
                <div v-if="isCertDropdownOpen" class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs" @click.stop>
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

              <!-- Tags -->
              <div class="relative filter-dropdown-container">
                <button
                  type="button"
                  @click="toggleDropdown('tag')"
                  class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="selectedTags.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Tag class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ selectedTags.length === 0 ? 'Tags' : `Tags · ${selectedTags.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
                </button>
                <div v-if="isTagDropdownOpen" class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs" @click.stop>
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

              <!-- Lead By -->
              <div class="relative filter-dropdown-container">
                <button
                  type="button"
                  @click="toggleDropdown('lead')"
                  class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="selectedLeads.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Contact class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ selectedLeads.length === 0 ? 'Lead By' : `Lead By · ${selectedLeads.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
                </button>
                <div v-if="isLeadDropdownOpen" class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs" @click.stop>
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

            <div v-if="hasActiveFilters" class="flex items-center gap-1.5 flex-wrap pt-0.5">
              <span
                v-for="chip in activeFilterChips"
                :key="chip.key"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
              >
                {{ chip.label }}
                <X class="w-2.5 h-2.5 cursor-pointer hover:text-rose-500" @click="chip.clear()" />
              </span>
              <button type="button" @click="clearAllFilters" class="text-[10px] font-bold text-rose-600 hover:text-rose-700 cursor-pointer">
                Filtrlarni tozalash
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between text-xs font-bold text-zinc-700 dark:text-zinc-300">
            <label class="flex items-center gap-2 cursor-pointer select-none uppercase tracking-wide text-[11px]">
              <input
                type="checkbox"
                :checked="isAllFilteredSelected"
                @change="toggleSelectAllStudents"
                class="h-4 w-4 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <span>Talabalarni tanlash (Barchasini belgilash)</span>
            </label>
            <span class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide bg-blue-500 text-white shadow-2xs">
              {{ selectedStudentIds.size }} / {{ filteredStudents.length }} ta tanlandi
            </span>
          </div>

          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden shadow-xs">
            <div class="overflow-x-auto max-h-96 scrollbar-thin">
              <table class="w-full text-xs text-left">
                <thead class="bg-zinc-50 dark:bg-zinc-800/60 text-zinc-500 border-b border-zinc-200 dark:border-zinc-800 sticky top-0 z-10 select-none">
                  <tr>
                    <th class="p-3 w-10 text-center">
                      <input type="checkbox" :checked="isAllFilteredSelected" @change="toggleSelectAllStudents" class="rounded text-blue-600 cursor-pointer" />
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
                  <tr v-if="isLoadingStudents">
                    <td colspan="7" class="p-8 text-center text-zinc-400">
                      <div class="flex items-center justify-center gap-2">
                        <RefreshCw class="w-4 h-4 animate-spin text-blue-500" />
                        <span>Talabalar ro'yxati yuklanmoqda...</span>
                      </div>
                    </td>
                  </tr>
                  <tr v-else-if="filteredStudents.length === 0">
                    <td colspan="7" class="p-8 text-center text-zinc-400">
                      Tanlangan filtrlarga mos keluvchi talabalar topilmadi.
                    </td>
                  </tr>
                  <tr
                    v-for="student in filteredStudents"
                    :key="student.id"
                    @click="toggleStudentSelection(student.id)"
                    class="cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition-colors"
                    :class="isStudentSelected(student.id) ? 'bg-blue-50/50 dark:bg-blue-950/20' : ''"
                    :style="getRowStripeStyle(student)"
                  >
                    <td class="p-3 text-center" @click.stop>
                      <input type="checkbox" :checked="isStudentSelected(student.id)" @change="toggleStudentSelection(student.id)" class="rounded text-blue-600 cursor-pointer" />
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
                      </div>
                    </td>
                    <td class="p-3 font-mono text-zinc-800 dark:text-zinc-200 align-top">{{ student.passport || '-' }}</td>
                    <td class="p-3 text-zinc-600 dark:text-zinc-400 align-top">{{ student.birthday || '-' }}</td>
                    <td class="p-3 text-zinc-600 dark:text-zinc-400 font-mono align-top">{{ student.phone1 || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Action Bar bottom -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-4">
            <button
              type="button"
              @click="currentStep = 2"
              class="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
            >
              <ArrowLeft class="w-4 h-4" />
              Ortga (Teglar tahlili)
            </button>

            <div class="flex items-center gap-2.5">
              <button
                type="button"
                :disabled="selectedStudentIds.size === 0"
                @click="currentStep = 4"
                class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                title="Fayl nomi shablonini ko'rish va o'zgartirish"
              >
                Fayl nomi sozlamasi
              </button>

              <button
                type="button"
                :disabled="isGenerating || selectedStudentIds.size === 0"
                @click="handleGenerate"
                class="inline-flex items-center justify-center gap-2 px-7 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-extrabold shadow-md shadow-blue-600/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                <RefreshCw v-if="isGenerating" class="w-4 h-4 animate-spin" />
                <Download v-else class="w-4 h-4" />
                <span v-if="isGenerating">Hujjatlar tayyorlanmoqda...</span>
                <span v-else-if="selectedStudentIds.size > 1">
                  Generate App Form ({{ selectedStudentIds.size }} ta talaba .zip)
                </span>
                <span v-else-if="selectedStudentIds.size === 1">
                  Generate App Form (1 ta talaba .docx)
                </span>
                <span v-else>
                  Generate App Form (Talabalarni tanlang)
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- ═══════════════════ STEP 4: DOWNLOAD / SUCCESS ═══════════════════ -->
        <div v-if="currentStep === 4" class="space-y-6">
          <!-- Generation Success Banner -->
          <div v-if="generationSuccess" class="bg-white dark:bg-[#111315] border-2 border-emerald-500/50 dark:border-emerald-500/40 rounded-2xl p-6 text-center space-y-4 shadow-lg">
            <div class="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-700 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto shadow-sm">
              <CheckCircle2 class="w-8 h-8 stroke-[2.5]" />
            </div>
            <div class="space-y-1">
              <h4 class="text-lg font-extrabold text-zinc-900 dark:text-zinc-100">
                App Form muvaffaqiyatli tayyorlandi va yuklab olindi!
              </h4>
              <p class="text-xs text-zinc-600 dark:text-zinc-400 max-w-lg mx-auto">
                <span v-if="selectedStudentIds.size > 1">
                  Tanlangan <strong>{{ selectedStudentIds.size }} ta talaba</strong> uchun alohida .docx arizalari yaratildi va <strong>.zip</strong> arxiv shaklida yuklab berildi.
                </span>
                <span v-else>
                  Tanlangan talaba uchun .docx arizasi yaratildi va yuklab berildi.
                </span>
              </p>
              <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-zinc-100 dark:bg-zinc-800 text-xs font-mono font-bold text-zinc-800 dark:text-zinc-200 mt-2 border border-zinc-200 dark:border-zinc-700">
                <Download class="w-3.5 h-3.5 text-blue-500" />
                <span>{{ downloadedFileName }}</span>
              </div>
            </div>

            <div class="flex flex-wrap items-center justify-center gap-3 pt-2">
              <button
                type="button"
                @click="downloadAgain"
                class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
              >
                <Download class="w-4 h-4" />
                Qayta yuklab olish
              </button>
              <button
                type="button"
                @click="currentStep = 3"
                class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs font-bold text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
              >
                <Users class="w-4 h-4 text-blue-500" />
                Boshqa talabalarni tanlash
              </button>
              <button
                type="button"
                @click="resetWizard"
                class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs font-bold text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
              >
                <RefreshCw class="w-4 h-4 text-zinc-400" />
                Yangi fayl yuklash
              </button>
            </div>
          </div>

          <!-- Configuration & Generate Box -->
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-6">
            <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <FileText class="w-4 h-4 text-blue-500" />
              Fayl nomi va yakuniy sozlamalar
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-3">
                <label class="text-xs font-bold text-zinc-700 dark:text-zinc-300 block">
                  Fayl nomi shabloni:
                </label>
                <input
                  v-model="filenamePattern"
                  type="text"
                  placeholder="{full_name}"
                  class="w-full px-3 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-xs font-semibold text-zinc-900 dark:text-zinc-100 focus:border-blue-500 focus:outline-none"
                />
                <div class="flex flex-wrap gap-1.5">
                  <button
                    v-for="preset in FILENAME_PRESETS"
                    :key="preset.pattern"
                    type="button"
                    @click="filenamePattern = preset.pattern"
                    class="px-2.5 py-1 rounded-lg text-[10px] font-medium border transition-colors cursor-pointer"
                    :class="filenamePattern === preset.pattern
                      ? 'bg-blue-50 dark:bg-blue-950/50 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                      : 'bg-zinc-100 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:bg-blue-50 hover:text-blue-700'"
                  >
                    {{ preset.label }}
                  </button>
                </div>
                <p class="text-[10px] text-zinc-400">
                  Mavjud tokenlar: <span class="font-mono">&#123;full_name&#125; &#123;id&#125; &#123;passport&#125; &#123;index&#125; &#123;date&#125;</span>
                </p>

                <div class="p-3 rounded-xl bg-blue-50/60 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/50">
                  <span class="text-[10px] font-bold text-blue-600 dark:text-blue-400 block mb-0.5">Namuna:</span>
                  <span class="text-[11px] font-mono font-bold text-blue-900 dark:text-blue-200 break-all">{{ filenamePreview }}</span>
                </div>
              </div>

              <div class="space-y-4">
                <div class="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 space-y-3">
                  <div class="text-xs space-y-2 text-zinc-600 dark:text-zinc-400">
                    <div class="flex justify-between">
                      <span>Shablon fayl:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100 truncate ml-2 max-w-[200px]">{{ uploadedFile?.name }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Tanlangan talabalar:</span>
                      <span class="font-bold text-blue-600 dark:text-blue-400">{{ selectedStudentIds.size }} nafar</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Moslangan teglar:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ mappedCount }} ta</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Natijaviy format:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">
                        {{ selectedStudentIds.size > 1 ? `ZIP arxiv (${selectedStudentIds.size} ta .docx fayl)` : '1 ta .docx fayl' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="flex items-center justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800">
              <button
                type="button"
                @click="currentStep = 3"
                class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
              >
                <ArrowLeft class="w-4 h-4" />
                Ortga (Talabalar)
              </button>

              <button
                type="button"
                :disabled="isGenerating || selectedStudentIds.size === 0"
                @click="handleGenerate"
                class="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-extrabold shadow-lg shadow-blue-600/25 transition-all disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw v-if="isGenerating" class="w-4 h-4 animate-spin" />
                <Download v-else class="w-4 h-4" />
                {{ isGenerating
                  ? "Hujjatlar to'ldirilmoqda..."
                  : selectedStudentIds.size > 1
                    ? `Generate App Form (${selectedStudentIds.size} ta .zip)`
                    : "Generate App Form (1 ta .docx)" }}
              </button>
            </div>
          </div>

          <div v-if="generationSuccess" class="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 rounded-2xl p-6 text-center space-y-4">
            <div class="w-12 h-12 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto shadow-md shadow-blue-500/30">
              <Check class="w-6 h-6 stroke-[3]" />
            </div>
            <div>
              <h4 class="text-base font-extrabold text-blue-900 dark:text-blue-100">
                Hujjatlar muvaffaqiyatli to'ldirildi va yuklab olindi!
              </h4>
              <p class="text-xs text-blue-700 dark:text-blue-300 mt-1">
                Fayl nomi: <span class="font-mono font-bold">{{ downloadedFileName }}</span>
              </p>
            </div>
            <button
              @click="resetWizard"
              class="px-5 py-2.5 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs font-bold text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
            >
              Yangi shablon to'ldirish
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal for Catalog when triggered from any step -->
    <div
      v-if="showCatalogModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto"
      @click.self="showCatalogModal = false"
    >
      <div class="w-full max-w-6xl bg-white dark:bg-[#111315] rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-800 max-h-[92vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div class="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between shrink-0 bg-zinc-50/50 dark:bg-zinc-900/50">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-950/60 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <FileText class="w-4 h-4" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                Word Mail-Merge Teglari Katalogi (Quick-Copy)
              </h3>
              <p class="text-[11px] text-zinc-500 dark:text-zinc-400">
                Word shabloningizga joylashtirish uchun kerakli tegni 1 marta bosing
              </p>
            </div>
          </div>
          <button
            type="button"
            @click="showCatalogModal = false"
            class="p-2 rounded-xl text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="p-6 overflow-y-auto scrollbar-thin">
          <WordPlaceholderCatalog :is-collapsible="false" />
        </div>
      </div>
    </div>
  </div>
</template>
