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
  Check
} from 'lucide-vue-next'
import type { Student } from '@/types'
import { useUiStore } from '@/stores/ui'
import XLSX from 'xlsx-js-style'

const props = defineProps<{
  isOpen: boolean
  students: Student[]
  folders: { id: string; name: string }[]
  options: {
    tariffs: string[]
    levels: string[]
    groups: string[]
    leads: string[]
    coordinators: string[]
    folders: { id: string; name: string }[]
    offices: string[]
  }
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const uiStore = useUiStore()

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

// Student selection
const selectedStudentIds = ref<string[]>([])

// Field picker modal state
const isFieldPickerOpen = ref(false)
const fieldSearchQuery = ref('')
const expandedFieldGroup = ref<string | null>(null)

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
      { key: 'email', label: 'Email', checked: true, get: (s) => s.email || '' },
      { key: 'address', label: 'Address', checked: true, get: (s) => s.address || '' },
    ]
  },
  {
    title: 'Educational Background',
    fields: [
      { key: 'final_school_name', label: 'Final School Name', checked: true, get: (s) => s.final_school_name || '' },
      { key: 'major', label: 'Major', checked: true, get: (s) => s.major || '' },
      { key: 'gpa', label: 'GPA', checked: true, get: (s) => (s.gpa ? `${s.gpa} (${s.gpa_system || 100})` : '') },
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
      { key: 'language_certificate', label: 'Language Certificate', checked: true, get: (s) => (s.language_certificate ? `${s.language_certificate} ${s.certificate_score || ''}`.trim() : '') },
      { key: 'language_certificate_2', label: 'Language Certificate 2', checked: false, get: (s) => (s.language_certificate_2 ? `${s.language_certificate_2} ${s.certificate_score_2 || ''}`.trim() : '') },
      { key: 'language_certificate_3', label: 'Language Certificate 3', checked: false, get: (s) => (s.language_certificate_3 ? `${s.language_certificate_3} ${s.certificate_score_3 || ''}`.trim() : '') },
    ]
  },
  {
    title: 'Chosen Universities',
    fields: [
      { key: 'university_1', label: 'University 1', checked: false, get: (s) => s.university_1 || '' },
      { key: 'university_2', label: 'University 2', checked: false, get: (s) => s.university_2 || '' },
      { key: 'university_3', label: 'University 3', checked: false, get: (s) => s.university_3 || '' },
      { key: 'university_4', label: 'University 4', checked: false, get: (s) => s.university_4 || '' },
      { key: 'university_5', label: 'University 5', checked: false, get: (s) => s.university_5 || '' },
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

// When modal opens, select all students by default
watch(() => props.isOpen, (open) => {
  if (open) {
    selectedStudentIds.value = props.students.map(s => s.id)
    searchQuery.value = ''
    searchType.value = 'all'
    selectedFolders.value = []
    selectedTariffs.value = []
    selectedLevels.value = []
    selectedGroups.value = []
    selectedCerts.value = []
    selectedTags.value = []
    selectedLeads.value = []
    isFieldPickerOpen.value = false
    closeAllDropdowns()
  }
})

// ── Filtered Students List ──────────────────────────────────────────
const filteredStudents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return props.students.filter(s => {
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
      const certs = [s.language_certificate, s.language_certificate_2, s.language_certificate_3].filter(Boolean)
      const match = selectedCerts.value.some(c => certs.includes(c))
      if (!match) return false
    }

    // Tags
    if (selectedTags.value.length > 0) {
      const tags = s.task_tags || []
      const match = selectedTags.value.some(t => tags.includes(t))
      if (!match) return false
    }

    // Leads
    if (selectedLeads.value.length > 0 && !selectedLeads.value.includes(s.lead_by || '')) return false

    return true
  })
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

  const rowEven = {
    font: { name: 'Segoe UI', sz: 10 },
    fill: { fgColor: { rgb: 'F2F6FB' } },
    alignment: { horizontal: 'center', vertical: 'center' },
    border: {
      top: { style: 'thin', color: { rgb: 'D9D9D9' } },
      bottom: { style: 'thin', color: { rgb: 'D9D9D9' } },
      left: { style: 'thin', color: { rgb: 'D9D9D9' } },
      right: { style: 'thin', color: { rgb: 'D9D9D9' } }
    }
  }

  const rowOdd = {
    font: { name: 'Segoe UI', sz: 10 },
    fill: { fgColor: { rgb: 'FFFFFF' } },
    alignment: { horizontal: 'center', vertical: 'center' },
    border: {
      top: { style: 'thin', color: { rgb: 'D9D9D9' } },
      bottom: { style: 'thin', color: { rgb: 'D9D9D9' } },
      left: { style: 'thin', color: { rgb: 'D9D9D9' } },
      right: { style: 'thin', color: { rgb: 'D9D9D9' } }
    }
  }

  for (let r = startCell.r; r <= endCell.r; r++) {
    for (let c = startCell.c; c <= endCell.c; c++) {
      const address = encodeCell(c, r)
      if (!ws[address]) continue
      if (r === 0) {
        ws[address].s = headerStyle
      } else {
        ws[address].s = r % 2 === 0 ? rowEven : rowOdd
      }
    }
  }
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
    .sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true, sensitivity: 'base' }))

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
        <div class="flex flex-col md:flex-row gap-2.5 items-end">
          <!-- Search Type -->
          <div class="w-full md:w-36">
            <label class="block text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-1">Search Type</label>
            <select
              v-model="searchType"
              class="w-full h-9 px-2.5 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-xs font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 cursor-pointer"
            >
              <option value="all">All Fields</option>
              <option value="id">ID</option>
              <option value="name">Name</option>
              <option value="phone">Phone</option>
              <option value="university">University</option>
            </select>
          </div>

          <!-- Search Query -->
          <div class="flex-1 w-full">
            <label class="block text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-1">Search Query</label>
            <div class="relative">
              <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search students..."
                class="w-full h-9 pl-8 pr-3 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Folder Filter Dropdown -->
          <div class="w-full md:w-44 relative">
            <label class="block text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-1">Folder</label>
            <button
              type="button"
              @click="isFolderDropdownOpen = !isFolderDropdownOpen"
              class="w-full h-9 px-2.5 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-xs font-semibold text-zinc-800 dark:text-zinc-200 flex items-center justify-between cursor-pointer"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Folder class="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                <span class="truncate">{{ selectedFolders.length === 0 ? 'All Folders' : `${selectedFolders.length} selected` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 text-zinc-400 shrink-0 ml-1" />
            </button>

            <!-- Popover -->
            <div
              v-if="isFolderDropdownOpen"
              class="absolute left-0 mt-1 w-52 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
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
                  @change="selectedFolders.includes('NO_FOLDER') ? selectedFolders = selectedFolders.filter(x => x !== 'NO_FOLDER') : selectedFolders.push('NO_FOLDER')"
                  class="rounded text-blue-600"
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
                  @change="selectedFolders.includes(f.id) ? selectedFolders = selectedFolders.filter(x => x !== f.id) : selectedFolders.push(f.id)"
                  class="rounded text-blue-600"
                />
                <span class="truncate">{{ f.name }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Student Selection Counter & Select All -->
      <div class="flex items-center justify-between mb-2 text-xs font-bold text-zinc-700 dark:text-zinc-300">
        <label class="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            :checked="isAllFilteredSelected"
            @change="toggleSelectAllFiltered"
            class="h-4 w-4 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
          />
          <span>Select All ({{ filteredStudents.length }} matching)</span>
        </label>
        <span class="text-blue-600 dark:text-blue-400 font-bold font-mono">
          {{ selectedStudentIds.length }} students selected
        </span>
      </div>

      <!-- Live Students Table -->
      <div class="flex-1 overflow-y-auto border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 shadow-2xs divide-y divide-zinc-100 dark:divide-zinc-800 max-h-80 text-xs">
        <table class="w-full text-left border-collapse">
          <thead class="sticky top-0 bg-zinc-50 dark:bg-zinc-850 text-zinc-500 font-bold uppercase tracking-wider text-[10px] border-b border-zinc-200 dark:border-zinc-750 z-10">
            <tr>
              <th class="p-2.5 w-10 text-center"></th>
              <th class="p-2.5 w-20">ID</th>
              <th class="p-2.5">Name</th>
              <th class="p-2.5">Phone</th>
              <th class="p-2.5">Tariff</th>
              <th class="p-2.5">Level</th>
              <th class="p-2.5">Language Cert</th>
              <th class="p-2.5">University</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
            <tr
              v-for="s in filteredStudents"
              :key="s.id"
              @click="toggleStudentSelection(s.id)"
              class="hover:bg-blue-50/50 dark:hover:bg-blue-950/20 cursor-pointer transition-colors"
              :class="selectedStudentIds.includes(s.id) ? 'bg-blue-50/30 dark:bg-blue-950/10' : ''"
            >
              <td class="p-2.5 text-center" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedStudentIds.includes(s.id)"
                  @change="toggleStudentSelection(s.id)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
              </td>
              <td class="p-2.5 font-bold font-mono text-zinc-900 dark:text-zinc-100">{{ s.id }}</td>
              <td class="p-2.5 font-bold text-zinc-900 dark:text-zinc-100">{{ s.full_name }}</td>
              <td class="p-2.5 text-zinc-600 dark:text-zinc-400 font-mono">{{ s.phone1 || '-' }}</td>
              <td class="p-2.5">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-600">
                  {{ s.tariff || 'NO TARIFF' }}
                </span>
              </td>
              <td class="p-2.5 font-medium">{{ s.level || '-' }}</td>
              <td class="p-2.5 font-medium text-emerald-600 dark:text-emerald-400">{{ s.language_certificate || '-' }}</td>
              <td class="p-2.5 text-zinc-600 dark:text-zinc-400 truncate max-w-[140px]">{{ s.university_1 || '-' }}</td>
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
