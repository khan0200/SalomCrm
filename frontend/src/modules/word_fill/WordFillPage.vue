<script setup lang="ts">
import { ref, computed } from 'vue'
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
} from '@/api/wordFill'
import { studentsApi } from '@/api/students'
import type { Student } from '@/types'
import { ROW_COLOR_MAP } from '@/types'

// ─── Step State ─────────────────────────────────────────────────────────────
const currentStep = ref<1 | 2 | 3 | 4>(1)

// ─── File & Template State ──────────────────────────────────────────────────
const uploadedFile = ref<File | null>(null)
const isAnalyzing = ref(false)
const analysisError = ref<string | null>(null)
const analysisData = ref<WordAnalysisResult | null>(null)
const isDragging = ref(false)
// AI mapping is always on; the backend falls back to its own dictionary when no
// API key is configured, so there is nothing here for the user to decide.
const AI_PROVIDER = 'openai'

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

const CERT_OPTIONS = ['NO CERTIFICATE', 'TOPIK', 'IELTS', 'TOEFL', 'CEFR', 'SAT', 'SKA']
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

// Shared key with the Excel Fill tab so switching tabs reuses one fetch.
const { data: allStudentsData } = useQuery({
  queryKey: ['all-students-app-form'],
  queryFn: () => studentsApi.getStudents({
    page: 1,
    page_size: 5000,
    folder: 'all',
    include_archive: false,
  }),
  staleTime: 1000 * 60 * 5,
})

const allStudents = computed<Student[]>(
  () => (allStudentsData.value?.results || []).filter(s => !s.is_deleted)
)

// ─── Filter students ────────────────────────────────────────────────────────
const filteredStudents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return allStudents.value.filter(s => {
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

    if (selectedFolders.value.length > 0) {
      const studentFolderIds = (s.folders || []).map(f => f.id)
      const hasFolder = selectedFolders.value.some(fid => {
        if (fid === 'NO_FOLDER') return studentFolderIds.length === 0
        return studentFolderIds.includes(fid)
      })
      if (!hasFolder) return false
    }

    if (selectedTariffs.value.length > 0) {
      if (!selectedTariffs.value.includes(s.tariff || 'NO_TARIFF')) return false
    }

    if (selectedLevels.value.length > 0) {
      const match = selectedLevels.value.includes(s.level || '') || selectedLevels.value.includes(s.level2 || '')
      if (!match) return false
    }

    if (selectedGroups.value.length > 0 && !selectedGroups.value.includes(s.student_group || '')) return false

    if (selectedCerts.value.length > 0) {
      let matchesCert = false
      if (selectedCerts.value.includes('NO CERTIFICATE')) {
        if (!s.language_certificate || s.language_certificate === 'NO CERTIFICATE') matchesCert = true
      }
      const certs = [s.language_certificate, s.language_certificate_2, s.language_certificate_3]
      if (certs.some(c => c && c !== 'NO CERTIFICATE' && selectedCerts.value.includes(c))) matchesCert = true
      if (!matchesCert) return false
    }

    if (selectedTags.value.length > 0) {
      const tags = s.task_tags || []
      const match = selectedTags.value.some(tag => {
        if (tag === 'Custom') return tags.some(t => !PREDEFINED_TAGS.includes(t))
        return tags.includes(tag)
      })
      if (!match) return false
    }

    if (selectedLeads.value.length > 0 && !selectedLeads.value.includes(s.lead_by || '')) return false

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
  if (selectedFolders.value.length) chips.push({ key: 'folder', label: `Folder: ${selectedFolders.value.length}`, clear: () => { selectedFolders.value = [] } })
  if (selectedTariffs.value.length) chips.push({ key: 'tariff', label: `Tariff: ${selectedTariffs.value.length}`, clear: () => { selectedTariffs.value = [] } })
  if (selectedLevels.value.length) chips.push({ key: 'level', label: `Level: ${selectedLevels.value.length}`, clear: () => { selectedLevels.value = [] } })
  if (selectedGroups.value.length) chips.push({ key: 'group', label: `Group: ${selectedGroups.value.length}`, clear: () => { selectedGroups.value = [] } })
  if (selectedCerts.value.length) chips.push({ key: 'cert', label: `Certificate: ${selectedCerts.value.length}`, clear: () => { selectedCerts.value = [] } })
  if (selectedTags.value.length) chips.push({ key: 'tag', label: `Tag: ${selectedTags.value.length}`, clear: () => { selectedTags.value = [] } })
  if (selectedLeads.value.length) chips.push({ key: 'lead', label: `Lead: ${selectedLeads.value.length}`, clear: () => { selectedLeads.value = [] } })
  return chips
})

const clearAllFilters = () => {
  selectedFolders.value = []
  selectedTariffs.value = []
  selectedLevels.value = []
  selectedGroups.value = []
  selectedCerts.value = []
  selectedTags.value = []
  selectedLeads.value = []
}

// ─── File Upload & AI Analysis ──────────────────────────────────────────────
const handleFileUpload = async (file: File) => {
  if (!file.name.toLowerCase().match(/\.(docx|dotx)$/)) {
    analysisError.value = "Faqat .docx formatidagi Word fayllari qabul qilinadi (eski .doc qo'llab-quvvatlanmaydi)"
    return
  }

  uploadedFile.value = file
  isAnalyzing.value = true
  analysisError.value = null
  analysisData.value = null

  try {
    const res = await wordFillApi.analyzeTemplate({
      file,
      use_ai: true,
      provider: AI_PROVIDER,
    })
    analysisData.value = res
    initMappings(res)
  } catch (err: any) {
    console.error('Error analyzing Word template:', err)
    analysisError.value = err.response?.data?.error || err.message || "Faylni tahlil qilishda xatolik yuz berdi"
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

/** Joins each detected slot with the AI's suggestion into an editable row. */
const initMappings = (res: WordAnalysisResult) => {
  const suggestionById = new Map(res.suggested_mappings.map(m => [m.slot_id, m]))

  mappings.value = res.slots.map((slot: WordSlot) => {
    const suggestion = suggestionById.get(slot.slot_id)
    const isKorean = /[가-힣]/.test(slot.label || '')

    return {
      slot_id: slot.slot_id,
      kind: slot.kind,
      label: slot.label,
      field: suggestion?.field || '_skip',
      options: slot.options || [],
      existing_placeholder: slot.existing_placeholder,
      static_value: '',
      fallback: '',
      confidence: suggestion?.confidence ?? 0,
      reason: suggestion?.reason || '',
      format_rules: {
        dateFormat: isKorean ? 'YYYY.MM.DD' : 'YYYY-MM-DD',
        genderFormat: isKorean ? '남/여' : 'MALE/FEMALE',
        phoneFormat: 'original',
      },
    }
  })
}

const mappedCount = computed(() => mappings.value.filter(m => m.field !== '_skip').length)
const skippedCount = computed(() => mappings.value.filter(m => m.field === '_skip').length)
const checkboxCount = computed(() => mappings.value.filter(m => m.kind === 'checkbox' && m.field !== '_skip').length)

/** Low-confidence rows the head manager should look at before generating. */
const lowConfidenceCount = computed(
  () => mappings.value.filter(m => m.field !== '_skip' && (m.confidence ?? 0) < 0.7).length
)

const visibleMappings = computed(() => {
  let list = [...mappings.value]
  if (onlyMappedFilter.value) list = list.filter(m => m.field !== '_skip')

  list.sort((a, b) => {
    const aSkip = a.field === '_skip' ? 1 : 0
    const bSkip = b.field === '_skip' ? 1 : 0
    if (aSkip !== bSkip) return aSkip - bSkip
    return a.slot_id.localeCompare(b.slot_id, undefined, { numeric: true })
  })
  return list
})

// All supported date fields that should display date format dropdown
const DATE_FIELDS = [
  'birthday',
  'passport_issue_date',
  'passport_expire_date',
  'date_of_entry',
  'date_of_graduation',
  'today_date',
  'certificate_test_date',
  'certificate_valid_date',
  'certificate_2_test_date',
  'certificate_2_valid_date',
  'certificate_3_test_date',
  'certificate_3_valid_date',
]

// Category ordering and labels
const CATEGORY_ORDER: { key: string; label: string }[] = [
  { key: 'system', label: 'Tizim / Maxsus' },
  { key: 'personal', label: 'Shaxsiy ma\'lumotlar' },
  { key: 'passport', label: 'Pasport ma\'lumotlari' },
  { key: 'contacts', label: 'Aloqa ma\'lumotlari' },
  { key: 'parents', label: 'Ota-ona ma\'lumotlari' },
  { key: 'education', label: 'Ta\'lim ma\'lumotlari (Educational Background)' },
  { key: 'certificates', label: 'Til sertifikatlari' },
  { key: 'university', label: 'Universitet tanlovlari' },
  { key: 'management', label: 'Boshqa / CRM' },
]

const categorizedCrmFields = computed(() => {
  if (!analysisData.value?.available_fields) return {}
  const groups: Record<string, { key: string; label: string }[]> = {}

  // Initialize ordered known categories
  CATEGORY_ORDER.forEach(c => {
    groups[c.label] = []
  })

  // Category key to display label mapping
  const categoryLabelMap = new Map(CATEGORY_ORDER.map(c => [c.key, c.label]))

  analysisData.value.available_fields.forEach(f => {
    let groupLabel = categoryLabelMap.get(f.category)
    if (!groupLabel) {
      groupLabel = f.category ? f.category.charAt(0).toUpperCase() + f.category.slice(1) : 'Boshqa'
      if (!groups[groupLabel]) {
        groups[groupLabel] = []
      }
    }
    groups[groupLabel].push(f)
  })

  // Filter out empty groups
  const nonEmptyGroups: Record<string, { key: string; label: string }[]> = {}
  for (const [name, items] of Object.entries(groups)) {
    if (items.length > 0) {
      nonEmptyGroups[name] = items
    }
  }

  return nonEmptyGroups
})

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
const handleGenerate = async () => {
  if (!uploadedFile.value || selectedStudentIds.value.size === 0) return

  isGenerating.value = true
  generationSuccess.value = false

  try {
    const blob = await wordFillApi.generateFilledWord({
      file: uploadedFile.value,
      mappings: mappings.value.filter(m => m.field !== '_skip'),
      student_ids: Array.from(selectedStudentIds.value),
      filename_pattern: filenamePattern.value,
      checkbox_mark: checkboxMark.value,
    })

    const count = selectedStudentIds.value.size
    const fileName = count > 1
      ? `Filled_${uploadedFile.value.name.replace(/\.[^/.]+$/, '')}_${count}ta.zip`
      : filenamePreview.value

    downloadedFileName.value = fileName

    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    generationSuccess.value = true
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

const resetWizard = () => {
  currentStep.value = 1
  uploadedFile.value = null
  analysisData.value = null
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
      <p class="text-xs text-zinc-500 dark:text-zinc-400 truncate">
        Application Form (.docx) shablonlarini AI yordamida tanib, tanlangan talabalar uchun avtomatik to'ldirish
      </p>

      <div class="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-800/60 p-1 rounded-xl border border-zinc-200/60 dark:border-zinc-700/60 shrink-0">
        <button
          v-for="s in [
            { num: 1, label: '1. Shablon' },
            { num: 2, label: '2. AI Mapping' },
            { num: 3, label: '3. Talabalar' },
            { num: 4, label: '4. Yuklab olish' }
          ]"
          :key="s.num"
          :disabled="s.num > 1 && !analysisData"
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

    <main class="flex-1 overflow-y-auto p-6 scrollbar-thin">
      <div class="max-w-6xl mx-auto">
        <!-- ═══════════════════ STEP 1: UPLOAD ═══════════════════ -->
        <div v-if="currentStep === 1" class="space-y-6">
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
                .docx formatidagi har qanday ariza shakli (Koreyscha, Inglizcha, Ruscha)
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
              AI hujjatni tahlil qilmoqda...
            </h4>
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              To'ldiriladigan joylar, checkbox maydonlari va CRM mosliklari aniqlanmoqda
            </p>
          </div>

          <div v-if="analysisError" class="bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-2xl p-4 flex items-center gap-3 text-rose-700 dark:text-rose-300 text-xs">
            <AlertTriangle class="w-5 h-5 shrink-0" />
            <span>{{ analysisError }}</span>
          </div>

          <!-- Analysis result -->
          <div v-if="analysisData && !isAnalyzing" class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-5">
            <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-blue-100 dark:bg-blue-950/60 flex items-center justify-center text-blue-600">
                  <CheckCircle2 class="w-5 h-5" />
                </div>
                <div>
                  <h4 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">{{ uploadedFile?.name }}</h4>
                  <p class="text-xs text-zinc-500 dark:text-zinc-400">
                    Hajmi: {{ ((uploadedFile?.size || 0) / 1024).toFixed(1) }} KB •
                    Jadvallar: {{ analysisData.tables.length }} ta
                  </p>
                </div>
              </div>
              <span class="text-[10px] font-bold px-2.5 py-1 rounded-full" :class="sourceLabel.cls">
                {{ sourceLabel.text }}
              </span>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Topilgan joylar</span>
                <span class="text-base font-extrabold text-zinc-900 dark:text-zinc-100">{{ analysisData.slots.length }} ta</span>
              </div>
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Moslangan maydonlar</span>
                <span class="text-base font-extrabold text-blue-600 dark:text-blue-400">{{ mappedCount }} ta</span>
              </div>
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Checkbox maydonlar</span>
                <span class="text-base font-extrabold text-violet-600 dark:text-violet-400">{{ checkboxCount }} ta</span>
              </div>
            </div>

            <div class="flex items-center justify-end">
              <button
                @click="currentStep = 2"
                class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all cursor-pointer"
              >
                AI takliflarini tekshirish
                <ArrowRight class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- ═══════════════════ STEP 2: MAPPING REVIEW ═══════════════════ -->
        <div v-if="currentStep === 2 && analysisData" class="space-y-5">
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                  <Sparkles class="w-4 h-4 text-violet-500" />
                  AI takliflarini tasdiqlang
                </h3>
                <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Har bir joy uchun taklif qilingan CRM maydonini tekshiring va kerak bo'lsa o'zgartiring.
                  Faqat siz tasdiqlagan maydonlar to'ldiriladi.
                </p>
              </div>
              <label class="flex items-center gap-2 text-[11px] font-bold text-zinc-600 dark:text-zinc-300 cursor-pointer shrink-0">
                <input type="checkbox" v-model="onlyMappedFilter" class="rounded text-blue-600 cursor-pointer" />
                Faqat moslanganlar
              </label>
            </div>

            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300">
                {{ mappedCount }} ta to'ldiriladi
              </span>
              <span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-zinc-100 dark:bg-zinc-800 text-zinc-500">
                {{ skippedCount }} ta o'tkazib yuboriladi
              </span>
              <span
                v-if="lowConfidenceCount > 0"
                class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 inline-flex items-center gap-1"
              >
                <AlertTriangle class="w-3 h-3" />
                {{ lowConfidenceCount }} ta past ishonchli — tekshiring
              </span>
            </div>

            <!-- Mapping rows -->
            <div class="border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden">
              <div class="max-h-[28rem] overflow-y-auto scrollbar-thin divide-y divide-zinc-100 dark:divide-zinc-800/60">
                <div
                  v-for="m in visibleMappings"
                  :key="m.slot_id"
                  class="p-3 flex items-start gap-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/30 transition-colors"
                  :class="m.field === '_skip' ? 'opacity-60' : ''"
                >
                  <!-- Slot info -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-1.5 flex-wrap">
                      <span
                        v-if="m.kind === 'checkbox'"
                        class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-violet-100 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300"
                      >
                        <CheckSquare class="w-2.5 h-2.5" />
                        CHECKBOX
                      </span>
                      <span
                        v-if="m.existing_placeholder"
                        class="px-1.5 py-0.5 rounded text-[9px] font-bold font-mono bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300"
                      >
                        &#123;&#123;{{ m.existing_placeholder }}&#125;&#125;
                      </span>
                      <span class="font-mono text-[9px] text-zinc-400">{{ m.slot_id }}</span>
                    </div>
                    <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 mt-0.5 truncate" :title="m.label">
                      {{ m.label || '(nomsiz joy)' }}
                    </div>
                    <div v-if="m.options?.length" class="text-[10px] text-zinc-500 mt-0.5">
                      Variantlar: {{ m.options.join(' / ') }}
                    </div>
                    <div v-if="m.reason && m.field !== '_skip'" class="text-[10px] text-zinc-400 dark:text-zinc-500 mt-0.5 italic truncate" :title="m.reason">
                      {{ m.reason }}
                    </div>
                  </div>

                  <!-- Confidence -->
                  <span
                    class="px-2 py-0.5 rounded-full text-[9px] font-bold shrink-0 mt-1"
                    :class="confidenceBadge(m.confidence ?? 0).cls"
                  >
                    {{ confidenceBadge(m.confidence ?? 0).text }}
                  </span>

                  <!-- Field selector -->
                  <div class="w-64 shrink-0 space-y-1.5">
                    <select
                      v-model="m.field"
                      @click.stop
                      class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-[11px] font-semibold rounded-lg px-2 py-1.5 text-zinc-800 dark:text-zinc-200 cursor-pointer focus:border-blue-500 focus:outline-none"
                    >
                      <optgroup v-for="(fields, groupName) in categorizedCrmFields" :key="groupName" :label="groupName">
                        <option v-for="f in fields" :key="f.key" :value="f.key">{{ f.label }}</option>
                      </optgroup>
                    </select>

                    <input
                      v-if="m.field === '_static_value'"
                      v-model="m.static_value"
                      @click.stop
                      type="text"
                      placeholder="Barchaga yoziladigan matn..."
                      class="w-full bg-white dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-[11px] rounded-lg px-2 py-1.5 text-zinc-800 dark:text-zinc-200 focus:border-blue-500 focus:outline-none"
                    />

                    <div v-if="DATE_FIELDS.includes(m.field)">
                      <select
                        v-model="m.format_rules.dateFormat"
                        @click.stop
                        class="w-full bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] rounded-lg px-2 py-1 text-zinc-600 dark:text-zinc-400 cursor-pointer"
                      >
                        <option value="YYYY-MM-DD">2003-05-14</option>
                        <option value="YYYY.MM.DD">2003.05.14</option>
                        <option value="DD.MM.YYYY">14.05.2003</option>
                        <option value="DD-MM-YYYY">14-05-2003</option>
                        <option value="YYYYMMDD">20030514</option>
                        <option value="YYYY/MM/DD">2003/05/14</option>
                      </select>
                    </div>

                    <div v-if="m.field === 'graduation_expected'">
                      <select
                        v-model="m.format_rules.boolFormat"
                        @click.stop
                        class="w-full bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] rounded-lg px-2 py-1 text-zinc-600 dark:text-zinc-400 cursor-pointer"
                      >
                        <option value="Yes/No">Yes / No</option>
                        <option value="예/아니오">예 / 아니오</option>
                        <option value="졸업예정/졸업">졸업예정 / 졸업</option>
                        <option value="Y/N">Y / N</option>
                        <option value="Ha/Yo'q">Ha / Yo'q</option>
                      </select>
                    </div>

                    <div v-if="m.field === 'gender' && m.kind === 'text'">
                      <select
                        v-model="m.format_rules.genderFormat"
                        @click.stop
                        class="w-full bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] rounded-lg px-2 py-1 text-zinc-600 dark:text-zinc-400 cursor-pointer"
                      >
                        <option value="MALE/FEMALE">MALE / FEMALE</option>
                        <option value="Male/Female">Male / Female</option>
                        <option value="M/F">M / F</option>
                        <option value="남/여">남 / 여</option>
                        <option value="남성/여성">남성 / 여성</option>
                      </select>
                    </div>

                    <div v-if="m.field.includes('phone')">
                      <select
                        v-model="m.format_rules.phoneFormat"
                        @click.stop
                        class="w-full bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] rounded-lg px-2 py-1 text-zinc-600 dark:text-zinc-400 cursor-pointer"
                      >
                        <option value="original">Asl holicha</option>
                        <option value="plus_998">+998901234567</option>
                        <option value="dashed">90-123-45-67</option>
                        <option value="digits_only">Faqat raqamlar</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="flex items-start gap-2 p-3 rounded-xl bg-blue-50/60 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/50 text-[11px] text-blue-800 dark:text-blue-300">
              <Info class="w-4 h-4 shrink-0 mt-0.5" />
              <span>
                Checkbox maydonlarda tanlangan variant qavs ichiga belgi qo'yiladi (masalan <strong>M (V) / F ( )</strong>).
                Hujjatning shrifti, ramkalari va joylashuvi butunlay saqlanadi — faqat matn yoziladi.
              </span>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <button
              @click="currentStep = 1"
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
            >
              <ArrowLeft class="w-4 h-4" />
              Ortga (Shablon)
            </button>
            <button
              :disabled="mappedCount === 0"
              @click="currentStep = 3"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              Talabalarni tanlashga o'tish ({{ mappedCount }} ta maydon)
              <ArrowRight class="w-4 h-4" />
            </button>
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
              <div class="relative">
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
                    <input type="checkbox" :checked="selectedFolders.includes(f.id)" @change="toggleInList(selectedFolders, f.id)" class="rounded text-blue-600" />
                    <span class="truncate">{{ f.name }}</span>
                  </label>
                </div>
              </div>

              <!-- Tariff -->
              <div class="relative">
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
                  <label v-for="t in options.tariffs" :key="t" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedTariffs.includes(t)" @change="toggleInList(selectedTariffs, t)" class="rounded text-blue-600" />
                    <span class="truncate">{{ t }}</span>
                  </label>
                </div>
              </div>

              <!-- Level -->
              <div class="relative">
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
                  <label v-for="l in options.levels" :key="l" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedLevels.includes(l)" @change="toggleInList(selectedLevels, l)" class="rounded text-blue-600" />
                    <span class="truncate">{{ l }}</span>
                  </label>
                </div>
              </div>

              <!-- Group -->
              <div class="relative">
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
                  <label v-for="g in options.groups" :key="g" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedGroups.includes(g)" @change="toggleInList(selectedGroups, g)" class="rounded text-blue-600" />
                    <span class="truncate">{{ g }}</span>
                  </label>
                </div>
              </div>

              <!-- Certificate -->
              <div class="relative">
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
              <div class="relative">
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
                  <label v-for="tg in TAG_OPTIONS" :key="tg" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="selectedTags.includes(tg)" @change="toggleInList(selectedTags, tg)" class="rounded text-blue-600" />
                    <span class="truncate">{{ tg }}</span>
                  </label>
                </div>
              </div>

              <!-- Lead By -->
              <div class="relative">
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
                  <label v-for="ld in options.leads" :key="ld" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
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

          <div class="flex items-center justify-between pt-4">
            <button
              @click="currentStep = 2"
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all cursor-pointer"
            >
              <ArrowLeft class="w-4 h-4" />
              Ortga (Mapping)
            </button>
            <button
              :disabled="selectedStudentIds.size === 0"
              @click="currentStep = 4"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              Yuklab olish bosqichiga o'tish ({{ selectedStudentIds.size }} ta tanlandi)
              <ArrowRight class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- ═══════════════════ STEP 4: DOWNLOAD ═══════════════════ -->
        <div v-if="currentStep === 4" class="space-y-6">
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
                  <div v-if="checkboxCount > 0" class="flex items-center justify-between">
                    <div>
                      <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block">Checkbox belgisi</span>
                      <span class="text-[11px] text-zinc-500 dark:text-zinc-400">Tanlangan variant qavsiga qo'yiladi</span>
                    </div>
                    <select
                      v-model="checkboxMark"
                      class="bg-white dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-xs font-bold rounded-lg px-3 py-1.5 cursor-pointer"
                    >
                      <option value="V">V</option>
                      <option value="O">O</option>
                      <option value="X">X</option>
                      <option value="✓">✓</option>
                    </select>
                  </div>

                  <hr v-if="checkboxCount > 0" class="border-zinc-200 dark:border-zinc-800" />

                  <div class="text-xs space-y-1.5 text-zinc-600 dark:text-zinc-400">
                    <div class="flex justify-between">
                      <span>Shablon fayl:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100 truncate ml-2">{{ uploadedFile?.name }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Tanlangan talabalar:</span>
                      <span class="font-bold text-blue-600 dark:text-blue-400">{{ selectedStudentIds.size }} nafar</span>
                    </div>
                    <div class="flex justify-between">
                      <span>To'ldiriladigan maydonlar:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ mappedCount }} ta</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Natija:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">
                        {{ selectedStudentIds.size > 1 ? `ZIP arxiv (${selectedStudentIds.size} ta .docx)` : '1 ta .docx fayl' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

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
                @click="handleGenerate"
                class="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold shadow-lg shadow-blue-600/25 transition-all disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw v-if="isGenerating" class="w-4 h-4 animate-spin" />
                <Download v-else class="w-4 h-4" />
                {{ isGenerating
                  ? "Hujjatlar to'ldirilmoqda..."
                  : selectedStudentIds.size > 1
                    ? `${selectedStudentIds.size} ta hujjatni to'ldirish (.zip)`
                    : "Hujjatni to'ldirish va yuklab olish (.docx)" }}
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
  </div>
</template>
