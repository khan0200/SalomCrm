<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import { statusApi } from '@/api/status'
import type { Student, Folder, StudentLevel, PaginatedResponse } from '@/types'
import { useUiStore } from '@/stores/ui'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import { useCustomTags } from '@/composables/useCustomTags'
import { useDocumentHelpers } from '@/composables/useDocumentHelpers'
import {
  Search, Plus, Filter, ChevronLeft, ChevronRight,
  Folder as FolderIcon, X, Tag, Layers, Users, BookOpen
} from 'lucide-vue-next'

import StatusTable from './components/StatusTable.vue'
import EmbassyDocumentsDrawer from './components/EmbassyDocumentsDrawer.vue'
import KdbDatePickerModal from './components/KdbDatePickerModal.vue'
import ChooseUniversityModal from './components/ChooseUniversityModal.vue'
import StudentFilters from '@/modules/students/components/StudentFilters.vue'
import ExportExcelModal from '@/modules/students/components/ExportExcelModal.vue'
import StudentActionsModal from '@/modules/students/components/StudentActionsModal.vue'
import AddStudentsToFolderModal from '@/modules/students/components/AddStudentsToFolderModal.vue'

const queryClient = useQueryClient()
const uiStore = useUiStore()
const dashboardStore = useStudentDashboardStore()
const { getTagIcon, fetchTags } = useCustomTags()
fetchTags()
const { getEffectiveMissingDocs } = useDocumentHelpers()

// Active Folder state
const activeFolder = ref('all')
const currentPage = ref(1)
const PAGE_SIZE = 50

// Sorting state
const sortBy = ref<'id' | 'left'>('id')
const sortOrder = ref<'asc' | 'desc'>('asc')

// Two-way bindings with central dashboardStore (Searchbar, Filters, Excel)
const searchQuery = computed({
  get: () => dashboardStore.searchQuery,
  set: (v) => dashboardStore.searchQuery = v,
})
const searchMode = computed({
  get: () => dashboardStore.searchMode,
  set: (v) => dashboardStore.searchMode = v,
})
const isFilterPanelOpen = computed({
  get: () => dashboardStore.isFilterPanelOpen,
  set: (v) => dashboardStore.isFilterPanelOpen = v,
})
const isExcelModalOpen = computed({
  get: () => dashboardStore.isExcelModalOpen,
  set: (v) => dashboardStore.isExcelModalOpen = v,
})
const selectedTariffs = computed({
  get: () => dashboardStore.selectedTariffs,
  set: (v) => dashboardStore.selectedTariffs = v,
})
const selectedLevels = computed({
  get: () => dashboardStore.selectedLevels,
  set: (v) => dashboardStore.selectedLevels = v,
})
const selectedGroups = computed({
  get: () => dashboardStore.selectedGroups,
  set: (v) => dashboardStore.selectedGroups = v,
})
const selectedCerts = computed({
  get: () => dashboardStore.selectedCerts,
  set: (v) => dashboardStore.selectedCerts = v,
})
const selectedScores = computed({
  get: () => dashboardStore.selectedScores,
  set: (v) => dashboardStore.selectedScores = v,
})
const selectedTags = computed({
  get: () => dashboardStore.selectedTags,
  set: (v) => dashboardStore.selectedTags = v,
})
const selectedLeads = computed({
  get: () => dashboardStore.selectedLeads,
  set: (v) => dashboardStore.selectedLeads = v,
})
const selectedMissingDocs = computed({
  get: () => dashboardStore.selectedMissingDocs,
  set: (v) => dashboardStore.selectedMissingDocs = v,
})

// Modals and Drawers
const activeEmbassyStudentId = ref<string | null>(null)
const isEmbassyDrawerOpen = ref(false)

// Choose University for Invoice Modal
const isChooseUniModalOpen = ref(false)
const activeInvoiceStudentId = ref<string | null>(null)
const invoicePendingStatus = ref<string | null>(null)

// KDB Date Picker Modal
const isKdbDateModalOpen = ref(false)
const kdbDateModalType = ref<'PUT' | 'TAKE'>('PUT')
const kdbDateModalStudentId = ref<string | null>(null)
const kdbDateModalInitialValue = ref<string | null>(null)

// Student Actions Modal
const isActionsModalOpen = ref(false)
const selectedActionStudent = ref<Student | null>(null)

// ── Query Master Students (Shared Cache with /students) ──────────────────────────
const { data: studentsData, isLoading } = useQuery({
  queryKey: ['all-students-master'],
  queryFn: () => studentsApi.getStudents({ page: 1, page_size: 5000, folder: 'all', include_archive: true }),
  staleTime: 1000 * 60 * 5,
})

const allStudents = computed<Student[]>(() => {
  return studentsData.value?.results || []
})

// Query Folders
const { data: foldersData } = useQuery({
  queryKey: ['folders'],
  queryFn: () => studentsApi.getFolders(),
  staleTime: 1000 * 60 * 10,
})

const foldersOptions = computed<Folder[]>(() => foldersData.value || [])

// Query Options (Tariffs, Levels, Groups, Leads, Universities)
const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
  staleTime: 1000 * 60 * 10,
})

const universityOptions = computed<string[]>(() => optionsData.value?.universities?.map((u: any) => u.name || u) || [])

// ── Folders & KDB Detection ───────────────────────────────────────────────────
const kdbFolder = computed(() => {
  return foldersOptions.value.find(f => f.name.toUpperCase() === 'KDB')
})

const isKdbFolderActive = computed(() => {
  if (activeFolder.value === 'kdb') return true
  return !!(kdbFolder.value && activeFolder.value === kdbFolder.value.id)
})

// Compute folder counts
const folderCounts = computed(() => {
  const counts: Record<string, number> = {
    all: 0,
    except: 0,
    hidden: 0,
    deleted: 0,
  }

  foldersOptions.value.forEach(f => {
    counts[f.id] = 0
  })

  allStudents.value.forEach(s => {
    if (s.is_deleted) {
      counts.deleted = (counts.deleted || 0) + 1
      return
    }

    if (s.status_hidden) {
      counts.hidden = (counts.hidden || 0) + 1
      return
    }

    counts.all = (counts.all || 0) + 1

    const fIds = s.folder_ids || []
    if (fIds.length === 0) {
      counts.except = (counts.except || 0) + 1
    } else {
      fIds.forEach(id => {
        counts[id] = (counts[id] || 0) + 1
      })
    }
  })

  return counts
})

// Recent PUT and TAKE dates list (top 5 most frequent)
const recentPutDates = computed(() => {
  const counts: Record<string, number> = {}
  allStudents.value.forEach(s => {
    const d = s.kdb_put_date
    if (d && d !== 'NO KDB' && d !== 'KDB DONE') {
      counts[d] = (counts[d] || 0) + 1
    }
  })
  return Object.keys(counts).sort((a, b) => counts[b] - counts[a]).slice(0, 5)
})

const recentTakeDates = computed(() => {
  const counts: Record<string, number> = {}
  allStudents.value.forEach(s => {
    const d = s.kdb_take_date
    if (d && d !== 'NO KDB' && d !== 'KDB DONE') {
      counts[d] = (counts[d] || 0) + 1
    }
  })
  return Object.keys(counts).sort((a, b) => counts[b] - counts[a]).slice(0, 5)
})

// ── Alphanumeric Sort & Remaining Days Sort ───────────────────────────────────
const compareStudentIds = (a: Student, b: Student, order: 'asc' | 'desc' = 'asc') => {
  const idA = a.id || ''
  const idB = b.id || ''

  const parseId = (idStr: string) => {
    const str = idStr.trim()
    const match = str.match(/^([A-Za-z\s_-]*)(\d*)$/)
    if (match) {
      return {
        prefix: match[1] || '',
        num: match[2] ? parseInt(match[2], 10) : null
      }
    }
    return { prefix: str, num: null }
  }

  const valA = parseId(idA)
  const valB = parseId(idB)

  const prefixComp = valA.prefix.localeCompare(valB.prefix, undefined, { sensitivity: 'base' })
  if (prefixComp !== 0) {
    return order === 'asc' ? prefixComp : -prefixComp
  }

  if (valA.num !== null && valB.num !== null) {
    return order === 'asc' ? valA.num - valB.num : valB.num - valA.num
  } else if (valA.num !== null) {
    return order === 'asc' ? 1 : -1
  } else if (valB.num !== null) {
    return order === 'asc' ? -1 : 1
  }

  return order === 'asc' ? idA.localeCompare(idB) : idB.localeCompare(idA)
}

const calculateTakeDays = (takeDateStr?: string | null) => {
  if (!takeDateStr) return 999999
  const takeDate = new Date(takeDateStr)
  if (isNaN(takeDate.getTime())) return 999999
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  takeDate.setHours(0, 0, 0, 0)
  return Math.ceil((takeDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}

// ── In-Memory Instant 0ms Filter Engine ────────────────────────────────────────
const filteredStudents = computed(() => {
  let list = allStudents.value
  const q = searchQuery.value.trim().toLowerCase()

  // 1. Folder filter
  if (activeFolder.value === 'deleted') {
    list = list.filter(s => s.is_deleted === true)
  } else {
    // If searching in 'all' folder, do not exclude archived/hidden students
    if (!q || activeFolder.value !== 'all') {
      list = list.filter(s => s.is_deleted !== true)

      if (activeFolder.value === 'hidden') {
        list = list.filter(s => s.status_hidden === true)
      } else {
        // In all standard folders on status page, hidden students are excluded
        list = list.filter(s => s.status_hidden !== true)

        if (activeFolder.value === 'except') {
          list = list.filter(s => !s.folder_ids || s.folder_ids.length === 0)
        } else if (activeFolder.value !== 'all') {
          list = list.filter(s => (s.folder_ids || []).includes(activeFolder.value))
        }
      }
    }
  }

  // 2. Global Search Query
  if (q) {
    list = list.filter(s => {
      const idMatch = (s.id || '').toLowerCase().includes(q)
      const nameMatch = (s.full_name || '').toLowerCase().includes(q)
      const passportMatch = (s.passport || '').toLowerCase().includes(q)
      const phoneMatch = (s.phone1 || '').includes(q) || (s.phone2 || '').includes(q)
      const uniMatch = [s.university_1, s.university_2, s.university_3, s.university_4, s.university_5, s.invoice_university]
        .filter(Boolean)
        .some(u => (u as string).toLowerCase().includes(q))
      return idMatch || nameMatch || passportMatch || phoneMatch || uniMatch
    })
  }

  // 3. Multi-Select Criteria Filters
  if (selectedTariffs.value.length > 0) {
    list = list.filter(s => {
      if (selectedTariffs.value.includes('NO_TARIFF') && !s.tariff) return true
      return s.tariff && selectedTariffs.value.includes(s.tariff)
    })
  }

  if (selectedLevels.value.length > 0) {
    list = list.filter(s => {
      if (selectedLevels.value.includes('NO_LEVEL') && !s.level) return true
      return s.level && selectedLevels.value.includes(s.level)
    })
  }

  if (selectedGroups.value.length > 0) {
    list = list.filter(s => {
      if (selectedGroups.value.includes('NO_GROUP') && !s.student_group) return true
      return s.student_group && selectedGroups.value.includes(s.student_group)
    })
  }

  if (selectedCerts.value.length > 0) {
    list = list.filter(s => {
      if (selectedCerts.value.includes('NO CERTIFICATE') && (!s.language_certificate || s.language_certificate === 'NO CERTIFICATE')) return true
      return s.language_certificate && selectedCerts.value.includes(s.language_certificate)
    })
  }

  if (selectedScores.value.length > 0) {
    list = list.filter(s => s.certificate_score && selectedScores.value.includes(s.certificate_score))
  }

  if (selectedTags.value.length > 0) {
    list = list.filter(s => (s.task_tags || []).some(t => selectedTags.value.includes(t)))
  }

  if (selectedLeads.value.length > 0) {
    list = list.filter(s => {
      if (selectedLeads.value.includes('NO_LEADBY') && !s.lead_by) return true
      return s.lead_by && selectedLeads.value.includes(s.lead_by)
    })
  }

  if (selectedMissingDocs.value.length > 0) {
    list = list.filter(s => {
      const missingList = getEffectiveMissingDocs(s)
      return selectedMissingDocs.value.some(d => missingList.includes(d))
    })
  }

  // 4. Sort
  return [...list].sort((a, b) => {
    if (sortBy.value === 'left') {
      const daysA = calculateTakeDays(a.kdb_take_date)
      const daysB = calculateTakeDays(b.kdb_take_date)
      if (daysA !== daysB) {
        return sortOrder.value === 'asc' ? daysA - daysB : daysB - daysA
      }
    }
    return compareStudentIds(a, b, sortOrder.value)
  })
})

const totalCount = computed(() => filteredStudents.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE)))
const paginatedStudents = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredStudents.value.slice(start, start + PAGE_SIZE)
})

// Reset page on filter changes
watch([searchQuery, activeFolder, selectedTariffs, selectedLevels, selectedGroups, selectedCerts, selectedScores, selectedTags, selectedLeads, selectedMissingDocs], () => {
  currentPage.value = 1
})

// ── Optimistic Update Engine ──────────────────────────────────────────────────
const updateStudentOptimistically = (studentId: string, patch: Partial<Student>) => {
  queryClient.setQueryData(['all-students-master'], (old: any) => {
    if (!old || !old.results) return old
    return {
      ...old,
      results: old.results.map((s: Student) => s.id === studentId ? { ...s, ...patch } : s)
    }
  })
}

// ── Inline Actions Handlers ───────────────────────────────────────────────────
const handleToggleSort = (field: 'id' | 'left') => {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = field
    sortOrder.value = 'asc'
  }
}

const handleUpdateInvoice = async (studentId: string, status: string | null, university: string | null = null) => {
  updateStudentOptimistically(studentId, { invoice: status, invoice_university: university })
  try {
    await statusApi.quickUpdate(studentId, { invoice: status })
    if (university !== undefined) {
      await studentsApi.updateStudent(studentId, { invoice_university: university } as any)
    }
  } catch (err: any) {
    console.error('Invoice update failed:', err)
  }
}

const handleInvoiceChange = (studentId: string, currentStatus: string | null, newStatus: string) => {
  const isFirstAssign = (!currentStatus || currentStatus === 'NOT TAKEN') && newStatus !== 'NOT TAKEN'

  if (isFirstAssign) {
    activeInvoiceStudentId.value = studentId
    invoicePendingStatus.value = newStatus
    isChooseUniModalOpen.value = true
  } else {
    const student = allStudents.value.find(s => s.id === studentId)
    const uniToKeep = newStatus === 'NOT TAKEN' ? null : (student?.invoice_university || null)
    handleUpdateInvoice(studentId, newStatus, uniToKeep)
  }
}

const handleSelectInvoiceUni = (uni: string) => {
  if (activeInvoiceStudentId.value && invoicePendingStatus.value) {
    handleUpdateInvoice(activeInvoiceStudentId.value, invoicePendingStatus.value, uni)
  }
  isChooseUniModalOpen.value = false
  activeInvoiceStudentId.value = null
  invoicePendingStatus.value = null
}

const handleUpdateCoa = async (studentId: string, status: string | null) => {
  updateStudentOptimistically(studentId, { coa: status })
  try {
    await statusApi.quickUpdate(studentId, { coa: status })
  } catch (err) {
    console.error('CoA update failed:', err)
  }
}

const handleUpdateKdbPut = async (studentId: string, val: string) => {
  if (val === 'EDIT' || val === 'KDB DONE') {
    const student = allStudents.value.find(s => s.id === studentId)
    kdbDateModalType.value = 'PUT'
    kdbDateModalStudentId.value = studentId
    kdbDateModalInitialValue.value = student?.kdb_put_date || null
    isKdbDateModalOpen.value = true
    return
  }

  const dateVal = val === 'NO KDB' ? null : val
  let calculatedTakeDate: string | null = null

  if (dateVal) {
    const putDate = new Date(dateVal)
    if (!isNaN(putDate.getTime())) {
      putDate.setDate(putDate.getDate() + 31)
      const y = putDate.getFullYear()
      const m = String(putDate.getMonth() + 1).padStart(2, '0')
      const d = String(putDate.getDate()).padStart(2, '0')
      calculatedTakeDate = `${y}-${m}-${d}`
    }
  }

  const student = allStudents.value.find(s => s.id === studentId)
  const currentFolders = student?.folder_ids || []
  let updatedFolders = [...currentFolders]
  if (dateVal && kdbFolder.value && !currentFolders.includes(kdbFolder.value.id)) {
    updatedFolders.push(kdbFolder.value.id)
  }

  updateStudentOptimistically(studentId, { kdb_put_date: dateVal, kdb_take_date: calculatedTakeDate, folder_ids: updatedFolders })
  try {
    await statusApi.quickUpdate(studentId, { kdb_put_date: dateVal, kdb_take_date: calculatedTakeDate })
    if (updatedFolders.length !== currentFolders.length) {
      await studentsApi.setFolders(studentId, updatedFolders)
    }
  } catch (err) {
    console.error('KDB Put update failed:', err)
  }
}

const handleUpdateKdbTake = async (studentId: string, val: string) => {
  if (val === 'EDIT' || val === 'KDB DONE') {
    const student = allStudents.value.find(s => s.id === studentId)
    kdbDateModalType.value = 'TAKE'
    kdbDateModalStudentId.value = studentId
    kdbDateModalInitialValue.value = student?.kdb_take_date || null
    isKdbDateModalOpen.value = true
    return
  }

  const dateVal = val === 'NO KDB' ? null : val
  const student = allStudents.value.find(s => s.id === studentId)
  const currentFolders = student?.folder_ids || []
  let updatedFolders = [...currentFolders]
  if (dateVal && kdbFolder.value && !currentFolders.includes(kdbFolder.value.id)) {
    updatedFolders.push(kdbFolder.value.id)
  }

  updateStudentOptimistically(studentId, { kdb_take_date: dateVal, folder_ids: updatedFolders })
  try {
    await statusApi.quickUpdate(studentId, { kdb_take_date: dateVal })
    if (updatedFolders.length !== currentFolders.length) {
      await studentsApi.setFolders(studentId, updatedFolders)
    }
  } catch (err) {
    console.error('KDB Take update failed:', err)
  }
}

const handleSaveCustomDate = async ({ studentId, type, date }: { studentId: string; type: 'PUT' | 'TAKE'; date: string }) => {
  if (type === 'PUT') {
    await handleUpdateKdbPut(studentId, date)
  } else {
    await handleUpdateKdbTake(studentId, date)
  }
}

const handleUpdateEmbassy = async (studentId: string, status: string | null) => {
  updateStudentOptimistically(studentId, { embassy: status })
  try {
    await statusApi.quickUpdate(studentId, { embassy: status })
  } catch (err) {
    console.error('Embassy status update failed:', err)
  }
}

const handleUpdateStatusHidden = async (studentId: string, isHidden: boolean) => {
  updateStudentOptimistically(studentId, { status_hidden: isHidden })
  try {
    await statusApi.quickUpdate(studentId, { status_hidden: isHidden })
  } catch (err) {
    console.error('Status hidden update failed:', err)
  }
}

const handleUpdateStatusRowColor = async (studentId: string, color: string | null) => {
  updateStudentOptimistically(studentId, { status_row_color: color })
  try {
    await studentsApi.setColor(studentId, { status_row_color: color })
  } catch (err) {
    console.error('Status row color update failed:', err)
  }
}

const handleSetFolders = async (studentId: string, folderIds: string[]) => {
  updateStudentOptimistically(studentId, { folder_ids: folderIds })
  try {
    await studentsApi.setFolders(studentId, folderIds)
  } catch (err) {
    console.error('Set folders failed:', err)
  }
}

const handleToggleTag = async (studentId: string, tagName: string) => {
  const student = allStudents.value.find(s => s.id === studentId)
  if (!student) return
  const currentTags = student.task_tags || []
  const newTags = currentTags.includes(tagName)
    ? currentTags.filter(t => t !== tagName)
    : [...currentTags, tagName]
  updateStudentOptimistically(studentId, { task_tags: newTags })
  try {
    await studentsApi.toggleTag(studentId, tagName)
  } catch (err) {
    console.error('Toggle tag failed:', err)
  }
}

const handleClearAllActions = async (studentId: string) => {
  updateStudentOptimistically(studentId, { row_color: null, status_row_color: null, task_tags: [] })
  try {
    await studentsApi.updateStudent(studentId, { row_color: null, status_row_color: null, task_tags: [] } as any)
  } catch (err) {
    console.error('Clear all failed:', err)
  }
}

const handleArchive = async (studentId: string) => {
  updateStudentOptimistically(studentId, { is_deleted: true })
  try {
    await studentsApi.archiveStudent(studentId)
  } catch (err) {
    console.error('Archive failed:', err)
  }
}

const handleRestore = async (studentId: string) => {
  updateStudentOptimistically(studentId, { is_deleted: false })
  try {
    await studentsApi.restoreStudent(studentId)
  } catch (err) {
    console.error('Restore failed:', err)
  }
}

const handlePermanentDelete = async (studentId: string) => {
  queryClient.setQueryData(['all-students-master'], (old: any) => {
    if (!old || !old.results) return old
    return {
      ...old,
      results: old.results.filter((s: Student) => s.id !== studentId)
    }
  })
  try {
    await studentsApi.permanentDeleteStudent(studentId)
  } catch (err) {
    console.error('Permanent delete failed:', err)
  }
}

const handleUpdateEmbassyFatherDocs = async (studentId: string, docs: string[]) => {
  updateStudentOptimistically(studentId, { embassy_father_docs: docs })
  try {
    await statusApi.updateEmbassyDrawer(studentId, { embassy_father_docs: docs })
  } catch (err) {
    console.error('Father docs update failed:', err)
  }
}

const handleUpdateEmbassyMotherDocs = async (studentId: string, docs: string[]) => {
  updateStudentOptimistically(studentId, { embassy_mother_docs: docs })
  try {
    await statusApi.updateEmbassyDrawer(studentId, { embassy_mother_docs: docs })
  } catch (err) {
    console.error('Mother docs update failed:', err)
  }
}

const handleUpdateEmbassySponsorNotes = async (studentId: string, notes: string) => {
  updateStudentOptimistically(studentId, { embassy_sponsor_notes: notes })
  try {
    await statusApi.updateEmbassyDrawer(studentId, { embassy_sponsor_notes: notes || null })
  } catch (err) {
    console.error('Sponsor notes update failed:', err)
  }
}

// Click on Row / Embassy
const handleClickRow = (student: Student, e: MouseEvent) => {
  if (e.metaKey || e.ctrlKey) {
    window.open(`/students/${student.id}/extract`, '_blank')
  } else {
    activeEmbassyStudentId.value = student.id
    isEmbassyDrawerOpen.value = true
  }
}

const handleOpenEmbassy = (student: Student) => {
  activeEmbassyStudentId.value = student.id
  isEmbassyDrawerOpen.value = true
}

const handleOpenActions = (student: Student, e: MouseEvent) => {
  selectedActionStudent.value = student
  isActionsModalOpen.value = true
}

// Active Student for Embassy Drawer
const activeEmbassyStudent = computed(() => {
  if (!activeEmbassyStudentId.value) return null
  return allStudents.value.find(s => s.id === activeEmbassyStudentId.value) || null
})

// Assigned universities for invoice modal (University 1..5 chosen by student)
const activeInvoiceStudentAssignedUnis = computed(() => {
  if (!activeInvoiceStudentId.value) return []
  const s = allStudents.value.find(st => st.id === activeInvoiceStudentId.value)
  if (!s) return []
  const list = []
  if (s.university_1) list.push({ slot: 1, name: s.university_1, status: s.university_1_status, major: s.university_1_major })
  if (s.university_2) list.push({ slot: 2, name: s.university_2, status: s.university_2_status, major: s.university_2_major })
  if (s.university_3) list.push({ slot: 3, name: s.university_3, status: s.university_3_status, major: s.university_3_major })
  if (s.university_4) list.push({ slot: 4, name: s.university_4, status: s.university_4_status, major: s.university_4_major })
  if (s.university_5) list.push({ slot: 5, name: s.university_5, status: s.university_5_status, major: s.university_5_major })
  return list
})

const handleApplyFilters = (filters: any) => {
  selectedTariffs.value = filters.tariffs
  selectedLevels.value = filters.levels
  selectedGroups.value = filters.groups
  selectedCerts.value = filters.certs
  selectedScores.value = filters.scores
  selectedTags.value = filters.tags
  selectedLeads.value = filters.leads
  selectedMissingDocs.value = filters.missingDocs || []
}

const resetAllFilters = () => {
  dashboardStore.resetAllFilters()
}

const isFolderAddModalOpen = ref(false)
const activeFolderItem = computed(() => foldersOptions.value.find(f => String(f.id) === String(activeFolder.value)))
const activeFolderName = computed(() => {
  if (activeFolder.value === 'all') return 'All'
  if (activeFolder.value === 'except') return 'Except'
  if (activeFolder.value === 'deleted' || activeFolder.value === 'archive') return 'Archive'
  if (activeFolder.value === 'hidden') return 'Hidden'
  return activeFolderItem.value?.name || 'Folder'
})

const handleSaveFolderAdd = async (selectedIds: string[]) => {
  if (selectedIds.length === 0) return
  let folderId = String(activeFolder.value)
  if (folderId === 'kdb' && kdbFolder.value) {
    folderId = String(kdbFolder.value.id)
  }
  if (!folderId || activeFolder.value === 'all' || activeFolder.value === 'except' || activeFolder.value === 'deleted' || activeFolder.value === 'hidden') return

  isFolderAddModalOpen.value = false
  uiStore.addToast({
    type: 'success',
    title: 'Added to Folder',
    message: `Added ${selectedIds.length} student${selectedIds.length !== 1 ? 's' : ''} to "${activeFolderName.value}".`
  })

  // Optimistic update: append folderId to selected students
  queryClient.setQueryData<PaginatedResponse<Student> | { results: Student[] } | undefined>(
    ['all-students-master'],
    (oldData) => {
      if (!oldData || !oldData.results) return oldData
      return {
        ...oldData,
        results: oldData.results.map((s) => {
          if (selectedIds.includes(s.id)) {
            const curr = (s.folder_ids || []).map(String)
            if (!curr.includes(folderId)) {
              return { ...s, folder_ids: [...curr, folderId] }
            }
          }
          return s
        })
      }
    }
  )

  try {
    await studentsApi.addStudentsToFolder(folderId, selectedIds)
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
  } catch (err: any) {
    console.error('Error adding students to folder:', err)
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
  }
}
</script>

<template>
  <div class="space-y-3 select-none">
    <!-- Active Filter Chips matching Uniapp2 -->
    <div
      v-if="dashboardStore.activeFiltersCount > 0"
      class="flex flex-wrap items-center gap-2 mb-2 select-none"
    >
      <span class="text-xs font-bold text-zinc-500 uppercase tracking-wider">Filters:</span>

      <!-- Tariff chips -->
      <div
        v-for="t in selectedTariffs"
        :key="`tariff-${t}`"
        class="inline-flex items-center gap-1.5 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-800 dark:text-zinc-200 font-semibold rounded-full shadow-xs"
      >
        <span>Tariff: {{ t === 'NO_TARIFF' ? 'No Tariff' : t }}</span>
        <button
          type="button"
          @click="selectedTariffs = selectedTariffs.filter(x => x !== t)"
          class="text-zinc-400 hover:text-red-500 rounded-full hover:bg-red-500/10 h-4 w-4 flex items-center justify-center cursor-pointer transition-colors"
        >
          <X class="h-3 w-3" />
        </button>
      </div>

      <!-- Level chips -->
      <div
        v-for="l in selectedLevels"
        :key="`level-${l}`"
        class="inline-flex items-center gap-1.5 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-800 dark:text-zinc-200 font-semibold rounded-full shadow-xs"
      >
        <span>Level: {{ l === 'NO_LEVEL' ? 'No Level' : l }}</span>
        <button
          type="button"
          @click="selectedLevels = selectedLevels.filter(x => x !== l)"
          class="text-zinc-400 hover:text-red-500 rounded-full hover:bg-red-500/10 h-4 w-4 flex items-center justify-center cursor-pointer transition-colors"
        >
          <X class="h-3 w-3" />
        </button>
      </div>

      <!-- Group chips -->
      <div
        v-for="g in selectedGroups"
        :key="`group-${g}`"
        class="inline-flex items-center gap-1.5 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-800 dark:text-zinc-200 font-semibold rounded-full shadow-xs"
      >
        <span>Group: {{ g === 'NO_GROUP' ? 'No Group' : g }}</span>
        <button
          type="button"
          @click="selectedGroups = selectedGroups.filter(x => x !== g)"
          class="text-zinc-400 hover:text-red-500 rounded-full hover:bg-red-500/10 h-4 w-4 flex items-center justify-center cursor-pointer transition-colors"
        >
          <X class="h-3 w-3" />
        </button>
      </div>

      <!-- Cert chips -->
      <div
        v-for="c in selectedCerts"
        :key="`cert-${c}`"
        class="inline-flex items-center gap-1.5 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-800 dark:text-zinc-200 font-semibold rounded-full shadow-xs"
      >
        <span>Cert: {{ c }}</span>
        <button
          type="button"
          @click="selectedCerts = selectedCerts.filter(x => x !== c)"
          class="text-zinc-400 hover:text-red-500 rounded-full hover:bg-red-500/10 h-4 w-4 flex items-center justify-center cursor-pointer transition-colors"
        >
          <X class="h-3 w-3" />
        </button>
      </div>

      <!-- Tag chips -->
      <div
        v-for="tag in selectedTags"
        :key="`tag-${tag}`"
        class="inline-flex items-center gap-1.5 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-800 dark:text-zinc-200 font-semibold rounded-full shadow-xs"
      >
        <span>Tag: {{ getTagIcon(tag) }} {{ tag }}</span>
        <button
          type="button"
          @click="selectedTags = selectedTags.filter(x => x !== tag)"
          class="text-zinc-400 hover:text-red-500 rounded-full hover:bg-red-500/10 h-4 w-4 flex items-center justify-center cursor-pointer transition-colors"
        >
          <X class="h-3 w-3" />
        </button>
      </div>

      <!-- Missing Docs chips -->
      <div
        v-for="m in selectedMissingDocs"
        :key="`missing-${m}`"
        class="inline-flex items-center gap-1.5 px-3 py-1 bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800 text-xs text-orange-700 dark:text-orange-300 font-semibold rounded-full shadow-xs"
      >
        <span>Missing: {{ m }}</span>
        <button
          type="button"
          @click="selectedMissingDocs = selectedMissingDocs.filter(x => x !== m)"
          class="text-orange-400 hover:text-red-500 rounded-full hover:bg-red-500/10 h-4 w-4 flex items-center justify-center cursor-pointer transition-colors"
        >
          <X class="h-3 w-3" />
        </button>
      </div>

      <!-- Lead chips -->
      <div
        v-for="lead in selectedLeads"
        :key="`lead-${lead}`"
        class="inline-flex items-center gap-1.5 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-800 dark:text-zinc-200 font-semibold rounded-full shadow-xs"
      >
        <span>Lead: {{ lead === 'NO_LEADBY' ? 'No Lead by' : lead }}</span>
        <button
          type="button"
          @click="selectedLeads = selectedLeads.filter(x => x !== lead)"
          class="text-zinc-400 hover:text-red-500 rounded-full hover:bg-red-500/10 h-4 w-4 flex items-center justify-center cursor-pointer transition-colors"
        >
          <X class="h-3 w-3" />
        </button>
      </div>

      <button
        type="button"
        @click="resetAllFilters"
        class="text-xs font-bold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors ml-1 cursor-pointer select-none"
      >
        Clear All
      </button>
    </div>

    <!-- Telegram-Style Folders Selector matching Uniapp2 -->
    <div className="mb-2 flex items-center overflow-x-auto scrollbar-none gap-3 md:gap-4 select-none shrink-0 border-b border-zinc-200 dark:border-zinc-800 pb-2 px-1">
      <!-- All Folder -->
      <button
        type="button"
        @click="activeFolder = 'all'"
        class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2 -mb-2.5 border-b-2"
        :class="[
          activeFolder === 'all'
            ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 font-bold'
            : 'text-zinc-500 dark:text-zinc-400 border-transparent hover:text-zinc-900 dark:hover:text-zinc-100'
        ]"
      >
        All
        <span class="text-xs font-normal ml-0.5" :class="activeFolder === 'all' ? 'text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-400 dark:text-zinc-500'">
          ({{ folderCounts.all || 0 }})
        </span>
      </button>

      <!-- Custom Folders (excluding KDB which is rendered separately) -->
      <button
        v-for="folder in foldersOptions.filter(f => f.name.toUpperCase() !== 'KDB')"
        :key="folder.id"
        type="button"
        @click="activeFolder = folder.id"
        class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2 -mb-2.5 border-b-2"
        :class="[
          activeFolder === folder.id
            ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 font-bold'
            : 'text-zinc-500 dark:text-zinc-400 border-transparent hover:text-zinc-900 dark:hover:text-zinc-100'
        ]"
      >
        {{ folder.name }}
        <span class="text-xs font-normal ml-0.5" :class="activeFolder === folder.id ? 'text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-400 dark:text-zinc-500'">
          ({{ folderCounts[folder.id] || 0 }})
        </span>
      </button>

      <!-- KDB Folder (Status Page only, pinned right) -->
      <button
        v-if="kdbFolder"
        type="button"
        @click="activeFolder = kdbFolder.id"
        class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2 -mb-2.5 border-b-2 ml-auto"
        :class="[
          activeFolder === kdbFolder.id
            ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 font-bold'
            : 'text-zinc-500 dark:text-zinc-400 border-transparent hover:text-zinc-900 dark:hover:text-zinc-100'
        ]"
      >
        KDB
        <span class="text-xs font-normal ml-0.5" :class="activeFolder === kdbFolder.id ? 'text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-400 dark:text-zinc-500'">
          ({{ folderCounts[kdbFolder.id] || 0 }})
        </span>
      </button>

      <!-- Except Folder -->
      <button
        type="button"
        @click="activeFolder = 'except'"
        class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2 -mb-2.5 border-b-2"
        :class="[
          !kdbFolder ? 'ml-auto' : '',
          activeFolder === 'except'
            ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 font-bold'
            : 'text-zinc-500 dark:text-zinc-400 border-transparent hover:text-zinc-900 dark:hover:text-zinc-100'
        ]"
      >
        Except
        <span class="text-xs font-normal ml-0.5" :class="activeFolder === 'except' ? 'text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-400 dark:text-zinc-500'">
          ({{ folderCounts.except || 0 }})
        </span>
      </button>

      <!-- Hidden Folder (Status Page only, amber theme) -->
      <button
        type="button"
        @click="activeFolder = 'hidden'"
        class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2 -mb-2.5 border-b-2"
        :class="[
          activeFolder === 'hidden'
            ? 'text-amber-500 border-amber-500 font-bold'
            : 'text-zinc-500 dark:text-zinc-400 border-transparent hover:text-amber-500'
        ]"
      >
        Hidden
        <span class="text-xs font-normal ml-0.5" :class="activeFolder === 'hidden' ? 'text-amber-500 font-semibold' : 'text-zinc-400 dark:text-zinc-500'">
          ({{ folderCounts.hidden || 0 }})
        </span>
      </button>

      <!-- Archive Folder (red theme) -->
      <button
        type="button"
        @click="activeFolder = 'deleted'"
        class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2 -mb-2.5 border-b-2"
        :class="[
          activeFolder === 'deleted'
            ? 'text-red-500 border-red-500 font-bold'
            : 'text-zinc-500 dark:text-zinc-400 border-transparent hover:text-red-500'
        ]"
      >
        Archive
        <span class="text-xs font-normal ml-0.5" :class="activeFolder === 'deleted' ? 'text-red-500 font-semibold' : 'text-zinc-400 dark:text-zinc-500'">
          ({{ folderCounts.deleted || 0 }})
        </span>
      </button>
    </div>

    <!-- Roster Total Count Info -->
    <div class="mb-2 flex justify-between items-center text-xs text-zinc-500 dark:text-zinc-400 italic px-1 font-medium select-none min-h-[28px]">
      <div>
        <span v-if="searchQuery || dashboardStore.activeFiltersCount > 0">
          Showing {{ filteredStudents.length }} of {{ allStudents.length }} students
        </span>
        <span v-else>
          Showing all students in {{ activeFolder === 'all' ? 'All' : activeFolder === 'deleted' ? 'Archive' : activeFolder === 'hidden' ? 'Hidden' : activeFolder === 'except' ? 'Except' : (foldersOptions.find(f => f.id === activeFolder)?.name || 'Folder') }}
        </span>
      </div>
      <div class="flex items-center gap-3">
        <!-- Add to Folder button -->
        <button
          v-if="activeFolder !== 'all' && activeFolder !== 'deleted' && activeFolder !== 'except' && activeFolder !== 'hidden'"
          type="button"
          @click="isFolderAddModalOpen = true"
          class="not-italic inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold cursor-pointer transition-all shadow-xs"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>Add to Folder</span>
        </button>
        <div class="text-right">
          Total {{ filteredStudents.length }} students
        </div>
      </div>
    </div>

    <!-- Main Status Data Table matching Uniapp2 -->
    <StatusTable
      :students="paginatedStudents"
      :is-loading="isLoading"
      :is-kdb-mode="isKdbFolderActive"
      :sort-by="sortBy"
      :sort-order="sortOrder"
      :recent-put-dates="recentPutDates"
      :recent-take-dates="recentTakeDates"
      @toggle-sort="handleToggleSort"
      @click-row="handleClickRow"
      @open-actions="handleOpenActions"
      @change-invoice="handleInvoiceChange"
      @change-coa="handleUpdateCoa"
      @change-put-date="handleUpdateKdbPut"
      @change-take-date="handleUpdateKdbTake"
      @open-embassy="handleOpenEmbassy"
    />

    <!-- Pagination Footer -->
    <div
      v-if="totalPages > 1"
      class="flex items-center justify-between px-4 py-3 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 select-none shadow-xs mt-2"
    >
      <div>
        Showing <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min((currentPage - 1) * PAGE_SIZE + 1, totalCount) }}</span> to
        <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min(currentPage * PAGE_SIZE, totalCount) }}</span> of
        <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ totalCount }}</span> students
      </div>

      <div class="flex items-center gap-1.5">
        <button
          type="button"
          @click="currentPage = Math.max(1, currentPage - 1)"
          :disabled="currentPage === 1"
          class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed hover:bg-zinc-100 dark:hover:bg-zinc-750 transition-colors"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>

        <span class="px-3 py-1 font-bold text-zinc-800 dark:text-zinc-200">
          Page {{ currentPage }} of {{ totalPages }}
        </span>

        <button
          type="button"
          @click="currentPage = Math.min(totalPages, currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed hover:bg-zinc-100 dark:hover:bg-zinc-750 transition-colors"
        >
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- ── Modals & Drawers ────────────────────────────────────────────────── -->
    <!-- Add Students to Folder Modal -->
    <AddStudentsToFolderModal
      :is-open="isFolderAddModalOpen"
      :folder-id="activeFolder"
      :folder-name="activeFolderName"
      :folders="foldersOptions"
      :all-students="allStudents"
      @close="isFolderAddModalOpen = false"
      @save="handleSaveFolderAdd"
    />

    <!-- Embassy Documents Drawer -->
    <EmbassyDocumentsDrawer
      :is-open="isEmbassyDrawerOpen"
      :student="activeEmbassyStudent"
      @close="isEmbassyDrawerOpen = false; activeEmbassyStudentId = null"
      @update-father-docs="docs => activeEmbassyStudentId && handleUpdateEmbassyFatherDocs(activeEmbassyStudentId, docs)"
      @update-mother-docs="docs => activeEmbassyStudentId && handleUpdateEmbassyMotherDocs(activeEmbassyStudentId, docs)"
      @update-sponsor-notes="notes => activeEmbassyStudentId && handleUpdateEmbassySponsorNotes(activeEmbassyStudentId, notes)"
      @update-visa-status="status => activeEmbassyStudentId && handleUpdateEmbassy(activeEmbassyStudentId, status)"
      @update-status-hidden="isHidden => activeEmbassyStudentId && handleUpdateStatusHidden(activeEmbassyStudentId, isHidden)"
    />

    <!-- KDB Date Picker Modal -->
    <KdbDatePickerModal
      :is-open="isKdbDateModalOpen"
      :type="kdbDateModalType"
      :student-id="kdbDateModalStudentId"
      :student-name="allStudents.find(s => s.id === kdbDateModalStudentId)?.full_name"
      :initial-value="kdbDateModalInitialValue"
      @close="isKdbDateModalOpen = false; kdbDateModalStudentId = null"
      @save="handleSaveCustomDate"
    />

    <!-- Choose University for Invoice Modal -->
    <ChooseUniversityModal
      :is-open="isChooseUniModalOpen"
      :student-id="activeInvoiceStudentId"
      :student-name="allStudents.find(s => s.id === activeInvoiceStudentId)?.full_name"
      :pending-status="invoicePendingStatus"
      :assigned-universities="activeInvoiceStudentAssignedUnis"
      @close="isChooseUniModalOpen = false; activeInvoiceStudentId = null; invoicePendingStatus = null"
      @select="handleSelectInvoiceUni"
    />

    <!-- Shared Filter Drawer -->
    <StudentFilters
      :is-open="isFilterPanelOpen"
      :options="optionsData || { tariffs: [], levels: [], groups: [], leads: [], folders: [] }"
      :students="allStudents"
      :selected-tariffs="selectedTariffs"
      :selected-levels="selectedLevels"
      :selected-groups="selectedGroups"
      :selected-certs="selectedCerts"
      :selected-scores="selectedScores"
      :selected-tags="selectedTags"
      :selected-leads="selectedLeads"
      :selected-missing-docs="selectedMissingDocs"
      :matching-count="filteredStudents.length"
      @close="isFilterPanelOpen = false"
      @apply="handleApplyFilters"
    />

    <!-- Export to Excel Modal -->
    <ExportExcelModal
      :is-open="isExcelModalOpen"
      :students="allStudents"
      :folders="foldersOptions"
      :options="optionsData || { tariffs: [], levels: [], groups: [], leads: [], coordinators: [], universities: [], folders: [], offices: [] }"
      @close="isExcelModalOpen = false"
    />

    <!-- Student Actions Modal (Context Menu) -->
    <StudentActionsModal
      :is-open="isActionsModalOpen"
      :student="selectedActionStudent"
      :folders="foldersOptions"
      @close="isActionsModalOpen = false; selectedActionStudent = null"
      @set-color="c => selectedActionStudent && handleUpdateStatusRowColor(selectedActionStudent.id, c)"
      @set-folders="fIds => selectedActionStudent && handleSetFolders(selectedActionStudent.id, fIds)"
      @toggle-tag="t => selectedActionStudent && handleToggleTag(selectedActionStudent.id, t)"
      @clear-all="() => selectedActionStudent && handleClearAllActions(selectedActionStudent.id)"
      @archive="() => selectedActionStudent && handleArchive(selectedActionStudent.id)"
      @restore="() => selectedActionStudent && handleRestore(selectedActionStudent.id)"
      @permanent-delete="() => selectedActionStudent && handlePermanentDelete(selectedActionStudent.id)"
    />
  </div>
</template>
