<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import type { Student, Folder, PaginatedResponse } from '@/types'
import { useUiStore } from '@/stores/ui'
import {
  Search, Plus, Filter, ChevronLeft, ChevronRight,
  RefreshCw, Users, Hash, BookOpen, FileSpreadsheet
} from 'lucide-vue-next'

import StudentTable from './components/StudentTable.vue'
import StudentFilters from './components/StudentFilters.vue'
import ActiveFilterChips from '@/components/ActiveFilterChips.vue'
import AddStudentModal from './components/AddStudentModal.vue'
import StudentActionsModal from './components/StudentActionsModal.vue'
import StudentFoldersManager from './components/StudentFoldersManager.vue'
import StudentDetailDrawer from './components/StudentDetailDrawer.vue'
import ExportExcelModal from './components/ExportExcelModal.vue'
import AddStudentsToFolderModal from './components/AddStudentsToFolderModal.vue'
import StudentRosterContextMenu from './components/StudentRosterContextMenu.vue'
import StudentQuickNoteModal from './components/StudentQuickNoteModal.vue'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import { useCustomTags } from '@/composables/useCustomTags'
import { useStudentFiltering } from '@/composables/useStudentFiltering'
import { getTariffPrice } from '@/utils/tariff'

const queryClient = useQueryClient()
const uiStore = useUiStore()
const dashboardStore = useStudentDashboardStore()
const { fetchTags } = useCustomTags()
fetchTags()

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

// Context Menu & Quick Note State
const isContextMenuOpen = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuStudent = ref<Student | null>(null)
const isQuickNoteModalOpen = ref(false)
const quickNoteStudent = ref<Student | null>(null)

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
// No query-level staleTime override - relies on the global default
// (main.ts) so every page reading this same key treats freshness
// identically (was 5min here vs 0 on other pages before).
const { data: allStudentsData, isLoading, refetch } = useQuery({
  queryKey: ['all-students-master'],
  queryFn: () => studentsApi.getStudents({
    page: 1,
    page_size: 5000,
    folder: 'all',
    include_archive: true,
  }),
})

const allStudents = computed<Student[]>(() => allStudentsData.value?.results || [])

// True only when the tenant has never added a single student yet (not when
// filters/search simply return no matches) — used to point brand-new tenants
// at the Settings "Boshlash / Info" tab instead of the generic empty state.
const isNewTenant = computed(() => !isLoading.value && allStudents.value.length === 0)

// Dynamic real-time folder counts calculated from in-memory master roster
const dynamicFolderCounts = computed(() => {
  const list = allStudents.value
  const activeList = list.filter(s => !s.is_deleted)
  const counts: Record<string, number> = {
    all: activeList.length,
    except: activeList.filter(s => !s.folder_ids || s.folder_ids.length === 0).length,
    deleted: list.filter(s => s.is_deleted && !s.is_permanently_deleted).length,
    archive: list.filter(s => s.is_deleted && !s.is_permanently_deleted).length,
    permanently_deleted: list.filter(s => s.is_permanently_deleted).length,
    hidden: activeList.filter(s => s.status_hidden).length,
  }
  for (const f of folders.value) {
    const fId = String(f.id)
    counts[fId] = activeList.filter(s => (s.folder_ids || []).map(String).includes(fId)).length
  }
  return counts
})

// ── Ultra-Fast Instant In-Memory Filter (0ms Latency on Folder Switch & Keystrokes) ──────────
// Folder scope first (not part of the shared composable - Payments has no
// folder concept), then delegate search + the 9 multi-criteria filters to
// useStudentFiltering so both this page and PaymentsPage.vue share one
// filter implementation instead of maintaining duplicate copies.
const folderScoped = computed(() => {
  let list = allStudents.value
  const q = searchQuery.value.trim().toLowerCase()

  if (activeFolder.value === 'permanently_deleted') {
    list = list.filter(s => s.is_permanently_deleted)
  } else if (activeFolder.value === 'deleted' || activeFolder.value === 'archive') {
    list = list.filter(s => s.is_deleted && !s.is_permanently_deleted)
  } else if (activeFolder.value === 'hidden') {
    list = list.filter(s => !s.is_deleted && !s.is_permanently_deleted && s.status_hidden)
  } else if (activeFolder.value === 'except') {
    list = list.filter(s => !s.is_deleted && !s.is_permanently_deleted && (!s.folder_ids || s.folder_ids.length === 0))
  } else if (activeFolder.value !== 'all') {
    const targetFolderId = String(activeFolder.value)
    list = list.filter(s => !s.is_deleted && !s.is_permanently_deleted && (s.folder_ids || []).map(String).includes(targetFolderId))
  } else {
    // In 'all' folder: if searching, include recoverable archived students, but NEVER permanently deleted students; otherwise show active students
    if (!q) {
      list = list.filter(s => !s.is_deleted && !s.is_permanently_deleted)
    } else {
      list = list.filter(s => !s.is_permanently_deleted)
    }
  }

  return list
})

const filterCriteria = computed(() => ({
  searchQuery: searchQuery.value,
  searchMode: searchMode.value,
  selectedTariffs: selectedTariffs.value,
  selectedLevels: selectedLevels.value,
  selectedGroups: selectedGroups.value,
  selectedBranches: selectedBranches.value,
  selectedCerts: selectedCerts.value,
  selectedScores: selectedScores.value,
  selectedTags: selectedTags.value,
  selectedLeads: selectedLeads.value,
  selectedMissingDocs: selectedMissingDocs.value,
}))

const { searchedStudents: folderScopedStudents, filteredStudents: multiCriteriaFiltered } = useStudentFiltering(folderScoped, filterCriteria)

const filteredStudents = computed(() => [...multiCriteriaFiltered.value].sort((a, b) => compareStudentIds(a, b, sortOrder.value)))

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

// Mirrors FIELD_STAMP_EXCLUDE in apps/students/serializers.py - bookkeeping
// and computed columns that never carry a user-visible "Updated at" date.
const FIELD_STAMP_EXCLUDE = new Set([
  'tenant', 'created_by', 'created_at', 'updated_at', 'field_updated_at',
  'balance', 'discount', 'payment_id', 'workflow_stage', 'is_deleted',
  'is_permanently_deleted', 'permanently_deleted_at', 'jarayon_updated_at',
  'status_hidden', 'row_color', 'folder_ids',
])

const updateStudentMutation = useMutation({
  mutationFn: (data: Partial<Student>) => {
    if (!selectedDetailStudentId.value) throw new Error('No student selected')
    return studentsApi.updateStudent(selectedDetailStudentId.value, data)
  },
  onMutate: async (data) => {
    if (selectedDetailStudentId.value) {
      updateMasterStudentOptimistically(selectedDetailStudentId.value, s => {
        const merged = { ...s, ...data }
        // Stamp the per-field edit dates locally so the drawer's "Updated at"
        // ghost text appears the moment the user saves, instead of waiting a
        // few seconds for the PATCH to come back. The server recomputes the
        // same thing authoritatively and onSuccess overwrites this with its
        // response, so a failed request simply rolls back with the value.
        const today = new Date().toLocaleDateString('en-CA')
        const stamps = { ...((s as any).field_updated_at || {}) }
        for (const key of Object.keys(data)) {
          if (FIELD_STAMP_EXCLUDE.has(key)) continue
          if ((data as any)[key] !== (s as any)[key]) stamps[key] = today
        }
        ;(merged as any).field_updated_at = stamps
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
    queryClient.invalidateQueries({ queryKey: ['payment-history-all'] })
    if (selectedDetailStudentId.value) {
      queryClient.invalidateQueries({ queryKey: ['student-payments', selectedDetailStudentId.value] })
    }
    uiStore.addToast({
      type: 'success',
      title: 'Student Updated',
      message: 'Student details updated successfully.'
    })
  },
  onError: (err: any) => {
    // Without this the optimistic patch stayed on screen and the request
    // failed silently - a rejected Student ID rename looked like it worked
    // until the page was reloaded. Refetching restores the server's truth.
    const data = err?.response?.data
    const message =
      (typeof data?.id === 'string' && data.id) ||
      (Array.isArray(data?.id) && data.id[0]) ||
      data?.detail ||
      err?.message ||
      'Could not save the change.'
    uiStore.addToast({ type: 'error', title: 'Update Failed', message })
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    if (selectedDetailStudentId.value) {
      queryClient.invalidateQueries({ queryKey: ['student-detail', selectedDetailStudentId.value] })
    }
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

// Note: "permanent delete" no longer removes the student from the roster -
// the record's data is never lost. It just moves into its own "Permanently
// Deleted" sub-tab of Archive, so the optimistic update flips the flag
// instead of filtering the row out of the in-memory master list.
const permanentDeleteMutation = useMutation({
  mutationFn: (id: string) => studentsApi.permanentDeleteStudent(id),
  onMutate: async (id) => {
    updateMasterStudentOptimistically(id, s => ({ ...s, is_deleted: true, is_permanently_deleted: true }))
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    isActionsModalOpen.value = false
    uiStore.addToast({
      type: 'error',
      title: 'Student Permanently Deleted',
      message: 'Moved to the Permanently Deleted tab. Data is retained, not erased.'
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

const handleContextMenu = (student: Student, event: MouseEvent) => {
  contextMenuStudent.value = student
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  isContextMenuOpen.value = true
}

const handleOpenQuickNotes = (student: Student) => {
  quickNoteStudent.value = student
  isQuickNoteModalOpen.value = true
}

const handleSaveQuickNotes = async (notes: string, student: Student) => {
  const trimmed = notes.trim()
  // 0ms instant optimistic update across caches and open modals
  updateMasterStudentOptimistically(student.id, s => ({ ...s, quick_notes: trimmed || null }))
  if (selectedActionStudent.value && selectedActionStudent.value.id === student.id) {
    selectedActionStudent.value = { ...selectedActionStudent.value, quick_notes: trimmed || null }
  }
  if (contextMenuStudent.value && contextMenuStudent.value.id === student.id) {
    contextMenuStudent.value = { ...contextMenuStudent.value, quick_notes: trimmed || null }
  }
  if (quickNoteStudent.value && quickNoteStudent.value.id === student.id) {
    quickNoteStudent.value = { ...quickNoteStudent.value, quick_notes: trimmed || null }
  }
  try {
    await studentsApi.updateStudent(student.id, { quick_notes: trimmed })
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['student-detail', student.id] })
    uiStore.addToast({
      type: 'success',
      title: 'Quick Note Saved',
      message: `Note updated for ${student.full_name}`
    })
  } catch (err: any) {
    uiStore.addToast({
      type: 'error',
      title: 'Failed to Save Note',
      message: err?.response?.data?.detail || 'Could not save note'
    })
    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
  }
}

const handleToggleFolderFromContextMenu = (folderId: string, student: Student) => {
  const strId = String(folderId)
  const current = [...(student.folder_ids || []).map(String)]
  const idx = current.indexOf(strId)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(strId)
  }
  setFoldersMutation.mutate({ id: student.id, folderIds: current })
  if (contextMenuStudent.value && contextMenuStudent.value.id === student.id) {
    contextMenuStudent.value = { ...contextMenuStudent.value, folder_ids: current }
  }
}

const handleClearFoldersFromContextMenu = (student: Student) => {
  setFoldersMutation.mutate({ id: student.id, folderIds: [] })
  if (contextMenuStudent.value && contextMenuStudent.value.id === student.id) {
    contextMenuStudent.value = { ...contextMenuStudent.value, folder_ids: [] }
  }
}

const handleToggleTagFromContextMenu = (tagName: string, student: Student) => {
  toggleTagMutation.mutate({ id: student.id, tagName, scope: 'all' })
  if (contextMenuStudent.value && contextMenuStudent.value.id === student.id) {
    const inAll = (contextMenuStudent.value.task_tags || []).includes(tagName)
    const inMine = (contextMenuStudent.value.my_task_tags || []).includes(tagName)
    let newTags = [...(contextMenuStudent.value.task_tags || [])]
    if (inAll || inMine) {
      newTags = newTags.filter(t => t !== tagName)
    } else {
      newTags.push(tagName)
    }
    contextMenuStudent.value = { ...contextMenuStudent.value, task_tags: newTags }
  }
}

const handleOpenActionsFromContextMenu = (student: Student) => {
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
    <ActiveFilterChips />

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
      :is-new-tenant="isNewTenant"
      @toggle-sort="toggleSort"
      @open-detail="openDetail"
      @open-actions="openActions"
      @open-notes="handleOpenQuickNotes"
      @contextmenu="handleContextMenu"
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
      :all-students="allStudents"
      @close="isActionsModalOpen = false"
      @set-color="(c, scope) => selectedActionStudent && setColorMutation.mutate({ id: selectedActionStudent.id, color: c, scope })"
      @clear-color="() => selectedActionStudent && clearColorMutation.mutate(selectedActionStudent.id)"
      @set-folders="fIds => selectedActionStudent && setFoldersMutation.mutate({ id: selectedActionStudent.id, folderIds: fIds })"
      @toggle-tag="(t, scope) => selectedActionStudent && toggleTagMutation.mutate({ id: selectedActionStudent.id, tagName: t, scope })"
      @update-quick-notes="notes => selectedActionStudent && handleSaveQuickNotes(notes, selectedActionStudent)"
      @clear-all="() => selectedActionStudent && clearAllMutation.mutate(selectedActionStudent.id)"
      @archive="() => selectedActionStudent && archiveMutation.mutate(selectedActionStudent.id)"
      @restore="() => selectedActionStudent && restoreMutation.mutate(selectedActionStudent.id)"
      @permanent-delete="() => selectedActionStudent && permanentDeleteMutation.mutate(selectedActionStudent.id)"
    />

    <!-- Student Right-Click Context Menu -->
    <StudentRosterContextMenu
      :is-open="isContextMenuOpen"
      :x="contextMenuX"
      :y="contextMenuY"
      :student="contextMenuStudent"
      :folders="folders"
      @close="isContextMenuOpen = false"
      @quick-notes="handleOpenQuickNotes"
      @open-actions="handleOpenActionsFromContextMenu"
      @toggle-folder="handleToggleFolderFromContextMenu"
      @clear-folders="handleClearFoldersFromContextMenu"
      @toggle-tag="handleToggleTagFromContextMenu"
    />

    <!-- Quick Note Modal -->
    <StudentQuickNoteModal
      :is-open="isQuickNoteModalOpen"
      :student="quickNoteStudent"
      :all-students="allStudents"
      @close="isQuickNoteModalOpen = false"
      @save="handleSaveQuickNotes"
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
      :current-folder="activeFolder"
      @close="dashboardStore.isExcelModalOpen = false"
      @open-detail="openDetail"
    />
  </div>
</template>
