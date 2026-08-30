<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import type { Student, Folder, PaginatedResponse } from '@/types'
import { useUiStore } from '@/stores/ui'
import {
  Search, Plus, Filter, ChevronLeft, ChevronRight,
  RefreshCw, Users, Hash, BookOpen, FileSpreadsheet, X
} from 'lucide-vue-next'

import StudentTable from './components/StudentTable.vue'
import StudentFilters from './components/StudentFilters.vue'
import AddStudentModal from './components/AddStudentModal.vue'
import StudentActionsModal from './components/StudentActionsModal.vue'
import StudentFoldersManager from './components/StudentFoldersManager.vue'
import StudentDetailDrawer from './components/StudentDetailDrawer.vue'
import ExportExcelModal from './components/ExportExcelModal.vue'
import AddStudentsToFolderModal from './components/AddStudentsToFolderModal.vue'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import { useCustomTags } from '@/composables/useCustomTags'
import { useDocumentHelpers } from '@/composables/useDocumentHelpers'
import { getTariffPrice } from '@/utils/tariff'
import { normalizeCertificateScore } from '@/utils/certificateScore'

const queryClient = useQueryClient()
const uiStore = useUiStore()
const dashboardStore = useStudentDashboardStore()
const { fetchTags } = useCustomTags()
fetchTags()
const { getEffectiveMissingDocs } = useDocumentHelpers()

const activeFolder = ref('all')
const currentPage = ref(1)
const sortOrder = ref<'asc' | 'desc'>('asc')
const isExportingExcel = computed(() => dashboardStore.isExcelExporting)
const isFolderAddModalOpen = ref(false)

// Alphanumeric sorting logic matching UniApp2
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

// Two-way bindings with dashboardStore
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
const isAddModalOpen = computed({
  get: () => dashboardStore.isAddStudentModalOpen,
  set: (v) => dashboardStore.isAddStudentModalOpen = v,
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
const selectedBranches = computed({
  get: () => dashboardStore.selectedBranches,
  set: (v) => dashboardStore.selectedBranches = v,
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
const activeFiltersCount = computed(() => dashboardStore.activeFiltersCount)

// Reset pagination to page 1 on any filter or search change
watch([
  searchQuery,
  searchMode,
  activeFolder,
  selectedTariffs,
  selectedLevels,
  selectedGroups,
  selectedBranches,
  selectedCerts,
  selectedScores,
  selectedTags,
  selectedLeads,
  selectedMissingDocs,
], () => {
  currentPage.value = 1
})

// Modals / Drawers
const isActionsModalOpen = ref(false)
const selectedActionStudent = ref<Student | null>(null)
const selectedDetailStudentId = ref<string | null>(null)
const isDetailDrawerOpen = ref(false)

// Query: Student Options
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
  offices: []
})

// Query: Folders
const { data: foldersData } = useQuery({
  queryKey: ['folders'],
  queryFn: () => studentsApi.getFolders(),
  staleTime: 1000 * 60 * 5,
})

const folders = computed(() => foldersData.value || [])

// ── Full Master Students Roster (Loaded ONCE into In-Memory Cache) ───────────
const { data: allStudentsData, isLoading, refetch } = useQuery({
  queryKey: ['all-students-master'],
  queryFn: () => studentsApi.getStudents({
    page: 1,
    page_size: 5000,
    folder: 'all',
    include_archive: true,
  }),
  staleTime: 1000 * 60 * 5,
})

const allStudents = computed<Student[]>(() => allStudentsData.value?.results || [])

// Dynamic real-time folder counts calculated from in-memory master roster
const dynamicFolderCounts = computed(() => {
  const list = allStudents.value
  const activeList = list.filter(s => !s.is_deleted)
  const counts: Record<string, number> = {
    all: activeList.length,
    except: activeList.filter(s => !s.folder_ids || s.folder_ids.length === 0).length,
    deleted: list.filter(s => s.is_deleted).length,
    archive: list.filter(s => s.is_deleted).length,
    hidden: activeList.filter(s => s.status_hidden).length,
  }
  for (const f of folders.value) {
    const fId = String(f.id)
    counts[fId] = activeList.filter(s => (s.folder_ids || []).map(String).includes(fId)).length
  }
  return counts
})

// ── Ultra-Fast Instant In-Memory Filter (0ms Latency on Folder Switch & Keystrokes) ──────────
// Folder scope + search only — this is the base the filter modal's live
// "Show N Students" preview must also start from, so its count matches the
// table (which additionally applies the multi-criteria filters below).
const folderScopedStudents = computed(() => {
  let list = allStudents.value

  // 1. Folder Scope (In-Memory Filter - 0 network delay)
  const q = searchQuery.value.trim().toLowerCase()

  if (activeFolder.value === 'deleted' || activeFolder.value === 'archive') {
    list = list.filter(s => s.is_deleted)
  } else if (activeFolder.value === 'hidden') {
    list = list.filter(s => !s.is_deleted && s.status_hidden)
  } else if (activeFolder.value === 'except') {
    list = list.filter(s => !s.is_deleted && (!s.folder_ids || s.folder_ids.length === 0))
  } else if (activeFolder.value !== 'all') {
    const targetFolderId = String(activeFolder.value)
    list = list.filter(s => !s.is_deleted && (s.folder_ids || []).map(String).includes(targetFolderId))
  } else {
    // In 'all' folder: if searching, include archived students; otherwise show active students
    if (!q) {
      list = list.filter(s => !s.is_deleted)
    }
  }

  // 2. Search Query (In-Memory Filter)
  if (q) {
    if (searchMode.value === 'id') {
      list = list.filter(s => (s.id || '').toLowerCase().includes(q))
    } else {
      list = list.filter(s => {
        const idMatch = (s.id || '').toLowerCase().includes(q)
        const nameMatch = (s.full_name || '').toLowerCase().includes(q)
        const koreanNameMatch = (s.korean_name || '').toLowerCase().includes(q)
        const passportMatch = (s.passport || '').toLowerCase().includes(q)
        const phone1Match = (s.phone1 || '').toLowerCase().includes(q)
        const phone2Match = (s.phone2 || '').toLowerCase().includes(q)
        const telegramMatch = (s.telegram_username || '').toLowerCase().includes(q)
        const fatherMatch = (s.father_name || '').toLowerCase().includes(q)
        const motherMatch = (s.mother_name || '').toLowerCase().includes(q)
        const uniMatch = (s.university_1 || '').toLowerCase().includes(q)
        return idMatch || nameMatch || koreanNameMatch || passportMatch || phone1Match || phone2Match || telegramMatch || fatherMatch || motherMatch || uniMatch

      })
    }
  }

  return list
})

const filteredStudents = computed(() => {
  let list = folderScopedStudents.value

  // 3. Multi-Criteria Filters (Tariffs, Levels, Groups, Certs, Scores, Tags, Leads)
  if (selectedTariffs.value.length > 0) {
    const hasNoTariff = selectedTariffs.value.includes('NO_TARIFF') || selectedTariffs.value.includes('No Tariff')
    const cleanTariffs = selectedTariffs.value.filter(t => t !== 'NO_TARIFF' && t !== 'No Tariff')
    list = list.filter(s => {
      if (hasNoTariff && (!s.tariff || cleanTariffs.includes(s.tariff))) return true
      return s.tariff && cleanTariffs.includes(s.tariff)
    })
  }

  if (selectedLevels.value.length > 0) {
    const hasNoLevel = selectedLevels.value.includes('NO_LEVEL') || selectedLevels.value.includes('No Level')
    const cleanLevels = selectedLevels.value.filter(l => l !== 'NO_LEVEL' && l !== 'No Level')
    list = list.filter(s => {
      if (hasNoLevel && (!s.level || cleanLevels.includes(s.level) || cleanLevels.includes(s.level2 || ''))) return true
      return (s.level && cleanLevels.includes(s.level)) || (s.level2 && cleanLevels.includes(s.level2))
    })
  }

  if (selectedGroups.value.length > 0) {
    const hasNoGroup = selectedGroups.value.includes('NO_GROUP') || selectedGroups.value.includes('No Group')
    const cleanGroups = selectedGroups.value.filter(g => g !== 'NO_GROUP' && g !== 'No Group')
    list = list.filter(s => {
      if (hasNoGroup && (!s.student_group || cleanGroups.includes(s.student_group))) return true
      return s.student_group && cleanGroups.includes(s.student_group)
    })
  }

  if (selectedBranches.value.length > 0) {
    const hasNoBranch = selectedBranches.value.includes('NO_BRANCH') || selectedBranches.value.includes('No Branch')
    const cleanBranches = selectedBranches.value.filter(b => b !== 'NO_BRANCH' && b !== 'No Branch').map(b => b.toLowerCase())
    list = list.filter(s => {
      if (hasNoBranch && (!s.office || cleanBranches.includes(s.office.toLowerCase()))) return true
      return !!s.office && cleanBranches.includes(s.office.toLowerCase())
    })
  }

  if (selectedCerts.value.length > 0) {
    list = list.filter(s => {
      return selectedCerts.value.some(c => {
        if (c === 'NO CERTIFICATE') {
          return !s.language_certificate || s.language_certificate === 'NO CERTIFICATE'
        }
        return s.language_certificate === c || s.language_certificate_2 === c || s.language_certificate_3 === c
      })
    })
  }

  if (selectedScores.value.length > 0) {
    const normalizedSelected = selectedScores.value.map(normalizeCertificateScore)
    list = list.filter(s => {
      const studentScores = [s.certificate_score, s.certificate_score_2, s.certificate_score_3]
        .map(normalizeCertificateScore)
        .filter(Boolean)
      return normalizedSelected.some(sc => studentScores.includes(sc))
    })
  }

  if (selectedTags.value.length > 0) {
    list = list.filter(s => {
      const studentTags = Array.isArray(s.task_tags) ? s.task_tags : []
      return selectedTags.value.some(t => studentTags.includes(t))
    })
  }

  if (selectedLeads.value.length > 0) {
    const hasNoLead = selectedLeads.value.includes('NO_LEADBY') || selectedLeads.value.includes('No Lead by')
    const cleanLeads = selectedLeads.value.filter(l => l !== 'NO_LEADBY' && l !== 'No Lead by')
    // lead_by is free-text, so the same source can be saved with different
    // casing (e.g. "Ali Uncle" vs "ALI UNCLE") — compare case-insensitively
    // or a student silently drops out of the filtered results.
    const cleanLeadsLower = cleanLeads.map(l => l.toLowerCase())
    list = list.filter(s => {
      if (hasNoLead && (!s.lead_by || cleanLeadsLower.includes(s.lead_by.toLowerCase()))) return true
      return !!s.lead_by && cleanLeadsLower.includes(s.lead_by.toLowerCase())
    })
  }

  if (selectedMissingDocs.value.length > 0) {
    list = list.filter(s => {
      const missingList = getEffectiveMissingDocs(s)
      return selectedMissingDocs.value.some(d => missingList.includes(d))
    })
  }

  return [...list].sort((a, b) => compareStudentIds(a, b, sortOrder.value))
})

const PAGE_SIZE = 50
const totalCount = computed(() => filteredStudents.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE)))
const students = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredStudents.value.slice(start, start + PAGE_SIZE)
})

// Query: Selected Student Detail with reactive query key & immediate background refetch
const { data: detailStudent } = useQuery({
  queryKey: computed(() => ['student-detail', selectedDetailStudentId.value]),
  queryFn: () => selectedDetailStudentId.value ? studentsApi.getStudentDetail(selectedDetailStudentId.value) : null,
  enabled: computed(() => !!selectedDetailStudentId.value),
  staleTime: 0,
})

const selectedStudent = computed<Student | null>(() => {
  if (!selectedDetailStudentId.value) return null
  const fromRoster = allStudents.value.find(s => s.id === selectedDetailStudentId.value)
  if (detailStudent.value && detailStudent.value.id === selectedDetailStudentId.value) {
    return { ...(fromRoster || {}), ...detailStudent.value }
  }
  return fromRoster || null
})

// Optimistic update helper for 0ms latency UI response
const updateMasterStudentOptimistically = (id: string, updater: (student: Student) => Student) => {
  queryClient.setQueryData<PaginatedResponse<Student> | { results: Student[] } | undefined>(
    ['all-students-master'],
    (oldData) => {
      if (!oldData || !oldData.results) return oldData
      return {
        ...oldData,
        results: oldData.results.map((s) => (s.id === id ? updater({ ...s }) : s)),
      }
    }
  )
  queryClient.setQueryData<Student | undefined>(
    ['student-detail', id],
    (old) => (old ? updater({ ...old }) : undefined)
  )
}

// Mutations with 0ms Instant Optimistic Updates
const createStudentMutation = useMutation({
  mutationFn: (data: Partial<Student>) => studentsApi.createStudent(data),
  onSuccess: (newStudent) => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    // A tariff set at creation writes balance server-side (see
    // recalculate_student_financials); the Payments page keeps its own
    // separate cache of the same student/balance data and must be told too,
    // or it keeps showing pre-creation figures until a full page reload.
    queryClient.invalidateQueries({ queryKey: ['payment-overview-all'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history-all'] })
    isAddModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Student Created',
      message: `Student ${newStudent.full_name} (${newStudent.id}) registered successfully.`
    })
  },
  onError: (err: any) => {
    uiStore.addToast({
      type: 'error',
      title: 'Creation Failed',
      message: err.response?.data?.detail || err.message || 'Failed to create student'
    })
  }
})

const updateStudentMutation = useMutation({
  mutationFn: (data: Partial<Student>) => {
    if (!selectedDetailStudentId.value) throw new Error('No student selected')
    return studentsApi.updateStudent(selectedDetailStudentId.value, data)
  },
  onMutate: async (data) => {
    if (selectedDetailStudentId.value) {
      updateMasterStudentOptimistically(selectedDetailStudentId.value, s => {
        const merged = { ...s, ...data }
        // Assigning/changing a tariff moves debt onto balance server-side
        // (balance = -tariff_price + existing payments/discounts/withdrawals).
        // Estimate that same shift here so the optimistic patch is never a
        // self-contradictory state (new tariff + stale old balance), which
        // is what caused "Payments Done" to flash the tariff price instead
        // of the real (zero) amount paid.
        if ('tariff' in data && data.tariff !== s.tariff) {
          const oldTariffPrice = getTariffPrice(s.tariff, s.language_certificate, options.value?.tariffs || [])
          const newTariffPrice = getTariffPrice(data.tariff as string, (data as any).language_certificate ?? s.language_certificate, options.value?.tariffs || [])
          merged.balance = Number(s.balance || 0) + oldTariffPrice - newTariffPrice
        }
        return merged
      })
    }
  },
  onSuccess: (updatedStudent) => {
    if (updatedStudent && updatedStudent.id) {
      updateMasterStudentOptimistically(updatedStudent.id, () => updatedStudent)
    }
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    queryClient.invalidateQueries({ queryKey: ['student-detail', selectedDetailStudentId.value] })
    // Assigning/changing a tariff (or recording other financial fields here)
    // recalculates balance server-side. The Payments page reads that same
    // balance from its own cache keys, which are otherwise never told this
    // student changed — without this it keeps showing the pre-update balance
    // until a full page reload forces a refetch.
    queryClient.invalidateQueries({ queryKey: ['payment-overview-all'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history-all'] })
    if (selectedDetailStudentId.value) {
      queryClient.invalidateQueries({ queryKey: ['student-payments', selectedDetailStudentId.value] })
    }
    uiStore.addToast({
      type: 'success',
      title: 'Student Updated',
      message: 'Student details updated successfully.'
    })
  }
})

const setColorMutation = useMutation({
  mutationFn: ({ id, color, scope }: { id: string; color: string; scope: 'mine' | 'all' }) => {
    return studentsApi.setColor(id, { row_color: color, scope })
  },
  onMutate: async ({ id, color, scope }) => {
    // 0ms instant UI update
    const patch = scope === 'mine' ? { my_row_color: color } : { row_color: color }
    updateMasterStudentOptimistically(id, s => ({ ...s, ...patch }))
    if (selectedActionStudent.value && selectedActionStudent.value.id === id) {
      selectedActionStudent.value = { ...selectedActionStudent.value, ...patch }
    }
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
  }
})

// X (clear color) button — always wipes both the shared and the acting
// user's own personal color in one action, no scope argument.
const clearColorMutation = useMutation({
  mutationFn: (id: string) => {
    return studentsApi.setColor(id, { row_color: null })
  },
  onMutate: async (id) => {
    const patch = { row_color: null, my_row_color: null }
    updateMasterStudentOptimistically(id, s => ({ ...s, ...patch }))
    if (selectedActionStudent.value && selectedActionStudent.value.id === id) {
      selectedActionStudent.value = { ...selectedActionStudent.value, ...patch }
    }
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
  }
})

const setFoldersMutation = useMutation({
  mutationFn: ({ id, folderIds }: { id: string; folderIds: string[] }) => {
    return studentsApi.setFolders(id, folderIds)
  },
  onMutate: async ({ id, folderIds }) => {
    // 0ms instant UI update
    updateMasterStudentOptimistically(id, s => ({ ...s, folder_ids: folderIds }))
    if (selectedActionStudent.value && selectedActionStudent.value.id === id) {
      selectedActionStudent.value = { ...selectedActionStudent.value, folder_ids: folderIds }
    }
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
  }
})

const toggleTagArray = (tags: string[] | undefined, tagName: string) => {
  const current = Array.isArray(tags) ? [...tags] : []
  const idx = current.indexOf(tagName)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(tagName)
  }
  return current
}

const toggleTagMutation = useMutation({
  mutationFn: ({ id, tagName, scope }: { id: string; tagName: string; scope: 'mine' | 'all' }) => {
    return studentsApi.toggleTag(id, tagName, scope)
  },
  onMutate: async ({ id, tagName, scope }) => {
    // 0ms instant UI update
    updateMasterStudentOptimistically(id, s => {
      // Dual-presence (tag in both scopes) removes both copies at once,
      // regardless of which scope was passed — mirror that optimistically.
      const inAll = Array.isArray(s.task_tags) && s.task_tags.includes(tagName)
      const inMine = Array.isArray(s.my_task_tags) && s.my_task_tags.includes(tagName)
      if (inAll && inMine) {
        return {
          ...s,
          task_tags: toggleTagArray(s.task_tags, tagName),
          my_task_tags: toggleTagArray(s.my_task_tags, tagName),
        }
      }
      return scope === 'mine'
        ? { ...s, my_task_tags: toggleTagArray(s.my_task_tags, tagName) }
        : { ...s, task_tags: toggleTagArray(s.task_tags, tagName) }
    })
    if (selectedActionStudent.value && selectedActionStudent.value.id === id) {
      const s = selectedActionStudent.value
      const inAll = Array.isArray(s.task_tags) && s.task_tags.includes(tagName)
      const inMine = Array.isArray(s.my_task_tags) && s.my_task_tags.includes(tagName)
      if (inAll && inMine) {
        selectedActionStudent.value = {
          ...s,
          task_tags: toggleTagArray(s.task_tags, tagName),
          my_task_tags: toggleTagArray(s.my_task_tags, tagName),
        }
      } else {
        selectedActionStudent.value = scope === 'mine'
          ? { ...s, my_task_tags: toggleTagArray(s.my_task_tags, tagName) }
          : { ...s, task_tags: toggleTagArray(s.task_tags, tagName) }
      }
    }
  },
  onSuccess: (data, variables) => {
    // Server is the source of truth here — the dual-presence removal case
    // changes both arrays server-side in one call.
    updateMasterStudentOptimistically(variables.id, s => ({
      ...s,
      task_tags: data?.task_tags ?? s.task_tags,
      my_task_tags: data?.my_task_tags ?? s.my_task_tags,
    }))
  }
})

const clearAllMutation = useMutation({
  mutationFn: (id: string) => {
    return studentsApi.clearAll(id)
  },
  onMutate: async (id) => {
    // 0ms instant UI update
    const patch = { row_color: null, task_tags: [], my_row_color: null, my_task_tags: [] }
    updateMasterStudentOptimistically(id, s => ({ ...s, ...patch }))
    if (selectedActionStudent.value && selectedActionStudent.value.id === id) {
      selectedActionStudent.value = { ...selectedActionStudent.value, ...patch }
    }
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    isActionsModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Cleared',
      message: 'Color highlight and tags cleared.'
    })
  }
})

const archiveMutation = useMutation({
  mutationFn: (id: string) => studentsApi.archiveStudent(id),
  onMutate: async (id) => {
    updateMasterStudentOptimistically(id, s => ({ ...s, is_deleted: true }))
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    isActionsModalOpen.value = false
    uiStore.addToast({
      type: 'warning',
      title: 'Student Archived',
      message: 'Student moved to archive.'
    })
  }
})

const restoreMutation = useMutation({
  mutationFn: (id: string) => studentsApi.restoreStudent(id),
  onMutate: async (id) => {
    updateMasterStudentOptimistically(id, s => ({ ...s, is_deleted: false }))
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    isActionsModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Student Restored',
      message: 'Student restored to active roster.'
    })
  }
})

const permanentDeleteMutation = useMutation({
  mutationFn: (id: string) => studentsApi.permanentDeleteStudent(id),
  onMutate: async (id) => {
    queryClient.setQueryData<PaginatedResponse<Student> | { results: Student[] } | undefined>(
      ['all-students-master'],
      (oldData) => {
        if (!oldData || !oldData.results) return oldData
        return {
          ...oldData,
          results: oldData.results.filter((s) => s.id !== id),
        }
      }
    )
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    isActionsModalOpen.value = false
    uiStore.addToast({
      type: 'error',
      title: 'Student Permanently Deleted',
      message: 'Student removed completely.'
    })
  }
})

const createFolderMutation = useMutation({
  mutationFn: (name: string) => studentsApi.createFolder(name),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
  }
})

// Export Excel Handler
const handleExportExcel = async () => {
  try {
    dashboardStore.isExcelExporting = true
    await studentsApi.exportExcel({
      search: searchQuery.value,
      search_mode: searchMode.value,
      folder: activeFolder.value,
      tariff: selectedTariffs.value,
      level: selectedLevels.value,
      include_archive: activeFolder.value === 'deleted' || activeFolder.value === 'archive'
    })
    uiStore.addToast({
      type: 'success',
      title: 'Export Started',
      message: 'Students roster spreadsheet downloaded.'
    })
  } catch (err: any) {
    uiStore.addToast({
      type: 'error',
      title: 'Export Failed',
      message: err.message || 'Could not download Excel file.'
    })
  } finally {
    dashboardStore.isExcelExporting = false
  }
}

// Handlers
const openDetail = (id: string) => {
  selectedDetailStudentId.value = id
  isDetailDrawerOpen.value = true
}

const openActions = (student: Student) => {
  selectedActionStudent.value = student
  isActionsModalOpen.value = true
}

const toggleSort = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
}

const handleApplyFilters = (filters: {
  tariffs: string[]
  levels: string[]
  groups: string[]
  branches?: string[]
  certs: string[]
  scores: string[]
  tags: string[]
  leads: string[]
  missingDocs?: string[]
}) => {
  selectedTariffs.value = filters.tariffs
  selectedLevels.value = filters.levels
  selectedGroups.value = filters.groups
  selectedBranches.value = filters.branches || []
  selectedCerts.value = filters.certs
  selectedScores.value = filters.scores
  selectedTags.value = filters.tags
  selectedLeads.value = filters.leads
  selectedMissingDocs.value = filters.missingDocs || []
  currentPage.value = 1
  isFilterPanelOpen.value = false
}

const resetAllFilters = () => {
  searchQuery.value = ''
  selectedTariffs.value = []
  selectedLevels.value = []
  selectedGroups.value = []
  selectedBranches.value = []
  selectedCerts.value = []
  selectedScores.value = []
  selectedTags.value = []
  selectedLeads.value = []
  selectedMissingDocs.value = []
  currentPage.value = 1
}

const activeFolderItem = computed(() => folders.value.find(f => String(f.id) === String(activeFolder.value)))
const activeFolderName = computed(() => {
  if (activeFolder.value === 'all') return 'All'
  if (activeFolder.value === 'except') return 'Except'
  if (activeFolder.value === 'deleted' || activeFolder.value === 'archive') return 'Archive'
  if (activeFolder.value === 'hidden') return 'Hidden'
  return activeFolderItem.value?.name || 'Folder'
})

const handleOpenFolderAdd = () => {
  isFolderAddModalOpen.value = true
}

const handleSaveFolderAdd = async (selectedIds: string[]) => {
  if (selectedIds.length === 0) return
  const folderId = String(activeFolder.value)
  if (!folderId || activeFolder.value === 'all' || activeFolder.value === 'except' || activeFolder.value === 'deleted') return

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

dashboardStore.onExportExcel = handleExportExcel
</script>

<template>
  <div class="space-y-4">
    <!-- Master-Detail Filter Panel Popover (Triggered from Top Navbar) -->
    <StudentFilters
      :is-open="isFilterPanelOpen"
      :options="options"
      :students="folderScopedStudents"
      :selected-tariffs="selectedTariffs"
      :selected-levels="selectedLevels"
      :selected-groups="selectedGroups"
      :selected-branches="selectedBranches"
      :selected-certs="selectedCerts"
      :selected-scores="selectedScores"
      :selected-tags="selectedTags"
      :selected-leads="selectedLeads"
      :selected-missing-docs="selectedMissingDocs"
      :matching-count="totalCount"
      @close="isFilterPanelOpen = false"
      @apply="handleApplyFilters"
    />

    <!-- Active Filter Chips (if any selected) -->
    <div v-if="activeFiltersCount > 0" class="flex flex-wrap items-center gap-1.5 px-1 py-1 select-none text-xs">
      <span class="text-[11px] font-bold text-zinc-500 mr-1">Active Filters:</span>

      <span
        v-for="t in selectedTariffs"
        :key="`t-${t}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-full font-medium"
      >
        <span>Tariff: {{ t === 'NO_TARIFF' ? 'No Tariff' : t }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedTariffs = selectedTariffs.filter(x => x !== t)" />
      </span>

      <span
        v-for="l in selectedLevels"
        :key="`l-${l}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 rounded-full font-medium"
      >
        <span>Level: {{ l === 'NO_LEVEL' ? 'No Level' : l }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedLevels = selectedLevels.filter(x => x !== l)" />
      </span>

      <span
        v-for="g in selectedGroups"
        :key="`g-${g}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 rounded-full font-medium"
      >
        <span>Group: {{ g === 'NO_GROUP' ? 'No Group' : g }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedGroups = selectedGroups.filter(x => x !== g)" />
      </span>

      <span
        v-for="b in selectedBranches"
        :key="`b-${b}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 rounded-full font-medium"
      >
        <span>Branch: {{ b === 'NO_BRANCH' ? 'No Branch' : b }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedBranches = selectedBranches.filter(x => x !== b)" />
      </span>

      <span
        v-for="c in selectedCerts"
        :key="`c-${c}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 rounded-full font-medium"
      >
        <span>Cert: {{ c }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedCerts = selectedCerts.filter(x => x !== c)" />
      </span>

      <span
        v-for="s in selectedScores"
        :key="`s-${s}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 rounded-full font-medium"
      >
        <span>Score: {{ s }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedScores = selectedScores.filter(x => x !== s)" />
      </span>

      <span
        v-for="m in selectedMissingDocs"
        :key="`m-${m}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-800 rounded-full font-medium"
      >
        <span>Missing: {{ m }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedMissingDocs = selectedMissingDocs.filter(x => x !== m)" />
      </span>

      <span
        v-for="tg in selectedTags"
        :key="`tg-${tg}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-full font-medium"
      >
        <span>Tag: {{ tg }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedTags = selectedTags.filter(x => x !== tg)" />
      </span>

      <span
        v-for="lb in selectedLeads"
        :key="`lb-${lb}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 rounded-full font-medium"
      >
        <span>Lead: {{ lb === 'NO_LEADBY' ? 'No Lead by' : lb }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="selectedLeads = selectedLeads.filter(x => x !== lb)" />
      </span>

      <button
        @click="resetAllFilters"
        class="text-xs font-bold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors ml-1 cursor-pointer"
      >
        Clear All
      </button>
    </div>

    <!-- Folders Navigation Bar Strip (Matching Screenshot) -->
    <StudentFoldersManager
      :folders="folders"
      :active-folder="activeFolder"
      :total-count="totalCount"
      :folder-counts="dynamicFolderCounts"
      @select="f => { activeFolder = f; currentPage = 1; }"
      @create-folder="name => createFolderMutation.mutate(name)"
      @open-add-to-folder="handleOpenFolderAdd"
    />

    <!-- Students Table -->
    <StudentTable
      :students="students"
      :is-loading="isLoading"
      :sort-order="sortOrder"
      @toggle-sort="toggleSort"
      @open-detail="openDetail"
      @open-actions="openActions"
    />

    <!-- Pagination Controls -->
    <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 bg-white dark:bg-[#111315] rounded-2xl border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 select-none">
      <div>
        Showing <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min((currentPage - 1) * 50 + 1, totalCount) }}</span> to
        <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min(currentPage * 50, totalCount) }}</span> of
        <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ totalCount }}</span> students
      </div>

      <div class="flex items-center gap-1.5">
        <button
          @click="currentPage = Math.max(1, currentPage - 1)"
          :disabled="currentPage === 1"
          class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed hover:bg-zinc-100 transition-colors"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>

        <span class="px-3 py-1 font-bold text-zinc-800 dark:text-zinc-200">
          Page {{ currentPage }} of {{ totalPages }}
        </span>

        <button
          @click="currentPage = Math.min(totalPages, currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed hover:bg-zinc-100 transition-colors"
        >
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Modals & Drawers -->
    <AddStudentsToFolderModal
      :is-open="isFolderAddModalOpen"
      :folder-id="activeFolder"
      :folder-name="activeFolderName"
      :folders="folders"
      :all-students="allStudents"
      :options="options"
      @close="isFolderAddModalOpen = false"
      @save="handleSaveFolderAdd"
    />

    <AddStudentModal
      :is-open="isAddModalOpen"
      :is-submitting="createStudentMutation.isPending.value"
      :options="options"
      @close="isAddModalOpen = false"
      @submit="data => createStudentMutation.mutate(data)"
    />

    <StudentActionsModal
      :is-open="isActionsModalOpen"
      :student="selectedActionStudent"
      :folders="folders"
      @close="isActionsModalOpen = false"
      @set-color="(c, scope) => selectedActionStudent && setColorMutation.mutate({ id: selectedActionStudent.id, color: c, scope })"
      @clear-color="() => selectedActionStudent && clearColorMutation.mutate(selectedActionStudent.id)"
      @set-folders="fIds => selectedActionStudent && setFoldersMutation.mutate({ id: selectedActionStudent.id, folderIds: fIds })"
      @toggle-tag="(t, scope) => selectedActionStudent && toggleTagMutation.mutate({ id: selectedActionStudent.id, tagName: t, scope })"
      @clear-all="() => selectedActionStudent && clearAllMutation.mutate(selectedActionStudent.id)"
      @archive="() => selectedActionStudent && archiveMutation.mutate(selectedActionStudent.id)"
      @restore="() => selectedActionStudent && restoreMutation.mutate(selectedActionStudent.id)"
      @permanent-delete="() => selectedActionStudent && permanentDeleteMutation.mutate(selectedActionStudent.id)"
    />

    <StudentDetailDrawer
      :is-open="isDetailDrawerOpen"
      :student="selectedStudent || null"
      :options="options"
      @close="isDetailDrawerOpen = false"
      @update-student="data => updateStudentMutation.mutate(data)"
      @archive="() => selectedStudent && archiveMutation.mutate(selectedStudent.id)"
      @restore="() => selectedStudent && restoreMutation.mutate(selectedStudent.id)"
      @permanent-delete="() => selectedStudent && permanentDeleteMutation.mutate(selectedStudent.id)"
      @open-add-payment="id => { isDetailDrawerOpen = false; $router.push({ path: '/payments', query: { student_id: id, open_add: 'true' } }); }"
    />

    <ExportExcelModal
      :is-open="dashboardStore.isExcelModalOpen"
      :students="allStudents"
      :folders="folders"
      :options="options"
      @close="dashboardStore.isExcelModalOpen = false"
      @open-detail="openDetail"
    />
  </div>
</template>
