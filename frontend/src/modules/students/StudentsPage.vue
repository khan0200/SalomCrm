<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import type { Student, Folder } from '@/types'
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
import { useStudentDashboardStore } from '@/stores/studentDashboard'

const queryClient = useQueryClient()
const uiStore = useUiStore()
const dashboardStore = useStudentDashboardStore()

const activeFolder = ref('all')
const currentPage = ref(1)
const sortOrder = ref<'asc' | 'desc'>('asc')
const isExportingExcel = computed(() => dashboardStore.isExcelExporting)

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
const activeFiltersCount = computed(() => dashboardStore.activeFiltersCount)

// Modals / Drawers
const isActionsModalOpen = ref(false)
const selectedActionStudent = ref<Student | null>(null)
const selectedDetailStudentId = ref<string | null>(null)
const isDetailDrawerOpen = ref(false)

// Query: Student Options
const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
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

// Query: Folders
const { data: foldersData } = useQuery({
  queryKey: ['folders'],
  queryFn: () => studentsApi.getFolders(),
})

const folders = computed(() => foldersData.value || [])

// Query: Students Roster
const { data: studentsResponse, isLoading, refetch } = useQuery({
  queryKey: [
    'students',
    currentPage,
    searchQuery,
    searchMode,
    activeFolder,
    sortOrder,
    selectedTariffs,
    selectedLevels,
    selectedGroups,
    selectedCerts,
    selectedScores,
    selectedTags,
    selectedLeads,
  ],
  queryFn: () => studentsApi.getStudents({
    page: currentPage.value,
    page_size: 50,
    search: searchQuery.value,
    search_mode: searchMode.value,
    folder: activeFolder.value,
    sort_by: 'id',
    sort_order: sortOrder.value,
    tariff: selectedTariffs.value,
    level: selectedLevels.value,
    group: selectedGroups.value,
    cert: selectedCerts.value,
    score: selectedScores.value,
    tag: selectedTags.value,
    lead_by: selectedLeads.value,
    include_archive: activeFolder.value === 'deleted' || activeFolder.value === 'archive',
  }),
})

const students = computed(() => studentsResponse.value?.results || [])
const totalPages = computed(() => studentsResponse.value?.total_pages || 1)
const totalCount = computed(() => studentsResponse.value?.count || 0)

// Query: All Students in Folder (for instantaneous client-side filter count calculation)
const { data: allStudentsData } = useQuery({
  queryKey: ['all-students-roster', activeFolder],
  queryFn: () => studentsApi.getStudents({
    page: 1,
    page_size: 2000,
    folder: activeFolder.value,
    include_archive: activeFolder.value === 'deleted' || activeFolder.value === 'archive',
  }),
})

const allStudents = computed(() => allStudentsData.value?.results || students.value)

// Query: Selected Student Detail
const { data: detailStudent } = useQuery({
  queryKey: ['student-detail', selectedDetailStudentId],
  queryFn: () => selectedDetailStudentId.value ? studentsApi.getStudentDetail(selectedDetailStudentId.value) : null,
  enabled: computed(() => !!selectedDetailStudentId.value),
})

// Mutations
const createStudentMutation = useMutation({
  mutationFn: (data: Partial<Student>) => studentsApi.createStudent(data),
  onSuccess: (newStudent) => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
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
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
    queryClient.invalidateQueries({ queryKey: ['student-detail', selectedDetailStudentId.value] })
    uiStore.addToast({
      type: 'success',
      title: 'Student Updated',
      message: 'Student details updated successfully.'
    })
  }
})

const setColorMutation = useMutation({
  mutationFn: ({ id, color }: { id: string; color: string | null }) => {
    return studentsApi.setColor(id, { row_color: color })
  },
  onSuccess: (_data, variables) => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
    if (selectedActionStudent.value && selectedActionStudent.value.id === variables.id) {
      selectedActionStudent.value = { ...selectedActionStudent.value, row_color: variables.color }
    }
  }
})

const setFoldersMutation = useMutation({
  mutationFn: ({ id, folderIds }: { id: string; folderIds: string[] }) => {
    return studentsApi.setFolders(id, folderIds)
  },
  onSuccess: (data, variables) => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
    if (selectedActionStudent.value && selectedActionStudent.value.id === variables.id) {
      selectedActionStudent.value = { ...selectedActionStudent.value, folder_ids: data.folder_ids || variables.folderIds }
    }
  }
})

const toggleTagMutation = useMutation({
  mutationFn: ({ id, tagName }: { id: string; tagName: string }) => {
    return studentsApi.toggleTag(id, tagName)
  },
  onSuccess: (data, variables) => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
    if (selectedActionStudent.value && selectedActionStudent.value.id === variables.id) {
      selectedActionStudent.value = { ...selectedActionStudent.value, task_tags: data.task_tags }
    }
  }
})

const clearAllMutation = useMutation({
  mutationFn: (id: string) => {
    return studentsApi.clearAll(id)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
    if (selectedActionStudent.value) {
      selectedActionStudent.value = { ...selectedActionStudent.value, row_color: null, task_tags: [] }
    }
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
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
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
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
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
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
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
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    queryClient.invalidateQueries({ queryKey: ['student-options'] })
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] })
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
  certs: string[]
  scores: string[]
  tags: string[]
  leads: string[]
}) => {
  selectedTariffs.value = filters.tariffs
  selectedLevels.value = filters.levels
  selectedGroups.value = filters.groups
  selectedCerts.value = filters.certs
  selectedScores.value = filters.scores
  selectedTags.value = filters.tags
  selectedLeads.value = filters.leads
  currentPage.value = 1
  isFilterPanelOpen.value = false
}

const resetAllFilters = () => {
  searchQuery.value = ''
  selectedTariffs.value = []
  selectedLevels.value = []
  selectedGroups.value = []
  selectedCerts.value = []
  selectedScores.value = []
  selectedTags.value = []
  selectedLeads.value = []
  currentPage.value = 1
}

dashboardStore.onExportExcel = handleExportExcel
</script>

<template>
  <div class="space-y-4">
    <!-- Master-Detail Filter Panel Popover (Triggered from Top Navbar) -->
    <StudentFilters
      :is-open="isFilterPanelOpen"
      :options="options"
      :students="allStudents"
      :selected-tariffs="selectedTariffs"
      :selected-levels="selectedLevels"
      :selected-groups="selectedGroups"
      :selected-certs="selectedCerts"
      :selected-scores="selectedScores"
      :selected-tags="selectedTags"
      :selected-leads="selectedLeads"
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
      :folder-counts="options.folder_counts"
      @select="f => { activeFolder = f; currentPage = 1; }"
      @create-folder="name => createFolderMutation.mutate(name)"
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
    <AddStudentModal
      :is-open="isAddModalOpen"
      :options="options"
      @close="isAddModalOpen = false"
      @submit="data => createStudentMutation.mutate(data)"
    />

    <StudentActionsModal
      :is-open="isActionsModalOpen"
      :student="selectedActionStudent"
      :folders="folders"
      @close="isActionsModalOpen = false"
      @set-color="c => selectedActionStudent && setColorMutation.mutate({ id: selectedActionStudent.id, color: c })"
      @set-folders="fIds => selectedActionStudent && setFoldersMutation.mutate({ id: selectedActionStudent.id, folderIds: fIds })"
      @toggle-tag="t => selectedActionStudent && toggleTagMutation.mutate({ id: selectedActionStudent.id, tagName: t })"
      @clear-all="() => selectedActionStudent && clearAllMutation.mutate(selectedActionStudent.id)"
      @archive="() => selectedActionStudent && archiveMutation.mutate(selectedActionStudent.id)"
      @restore="() => selectedActionStudent && restoreMutation.mutate(selectedActionStudent.id)"
      @permanent-delete="() => selectedActionStudent && permanentDeleteMutation.mutate(selectedActionStudent.id)"
    />

    <StudentDetailDrawer
      :is-open="isDetailDrawerOpen"
      :student="detailStudent || null"
      :options="options"
      @close="isDetailDrawerOpen = false"
      @update-student="data => updateStudentMutation.mutate(data)"
      @archive="() => detailStudent && archiveMutation.mutate(detailStudent.id)"
      @restore="() => detailStudent && restoreMutation.mutate(detailStudent.id)"
      @permanent-delete="() => detailStudent && permanentDeleteMutation.mutate(detailStudent.id)"
      @open-add-payment="id => { isDetailDrawerOpen = false; $router.push({ path: '/payments', query: { student_id: id, open_add: 'true' } }); }"
    />

    <ExportExcelModal
      :is-open="dashboardStore.isExcelModalOpen"
      :students="allStudents"
      :folders="folders"
      :options="options"
      @close="dashboardStore.isExcelModalOpen = false"
    />
  </div>
</template>
