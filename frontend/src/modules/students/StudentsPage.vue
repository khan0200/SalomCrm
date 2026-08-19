<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import { paymentsApi } from '@/api/payments'
import type { Student, Folder } from '@/types'
import { useUiStore } from '@/stores/ui'
import {
  Search, Plus, Filter, ChevronLeft, ChevronRight,
  RefreshCw, Users, Hash
} from 'lucide-vue-next'

import StudentTable from './components/StudentTable.vue'
import StudentFilters from './components/StudentFilters.vue'
import AddStudentModal from './components/AddStudentModal.vue'
import StudentActionsModal from './components/StudentActionsModal.vue'
import StudentFoldersManager from './components/StudentFoldersManager.vue'
import StudentDetailDrawer from './components/StudentDetailDrawer.vue'

const queryClient = useQueryClient()
const uiStore = useUiStore()

// State
const searchQuery = ref('')
const searchMode = ref<'all' | 'id'>('all')
const activeFolder = ref('all')
const currentPage = ref(1)
const sortOrder = ref<'asc' | 'desc'>('asc')
const isFilterPanelOpen = ref(false)

// Modals / Drawers
const isAddModalOpen = ref(false)
const isActionsModalOpen = ref(false)
const selectedActionStudent = ref<Student | null>(null)
const selectedDetailStudentId = ref<string | null>(null)
const isDetailDrawerOpen = ref(false)

// Multi-select filters
const selectedTariffs = ref<string[]>([])
const selectedLevels = ref<string[]>([])
const selectedGroups = ref<string[]>([])
const selectedCerts = ref<string[]>([])
const selectedLeads = ref<string[]>([])

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
    selectedLeads,
  ],
  queryFn: () => studentsApi.getStudents({
    page: currentPage.value,
    page_size: 30,
    search: searchQuery.value,
    search_mode: searchMode.value,
    folder: activeFolder.value,
    sort_by: 'id',
    sort_order: sortOrder.value,
    tariff: selectedTariffs.value,
    level: selectedLevels.value,
    group: selectedGroups.value,
    cert: selectedCerts.value,
    lead_by: selectedLeads.value,
    include_archive: activeFolder.value === 'deleted',
  }),
})

const students = computed(() => studentsResponse.value?.results || [])
const totalPages = computed(() => studentsResponse.value?.total_pages || 1)
const totalCount = computed(() => studentsResponse.value?.count || 0)

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
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    isActionsModalOpen.value = false
  }
})

const setFoldersMutation = useMutation({
  mutationFn: ({ id, folderIds }: { id: string; folderIds: string[] }) => {
    return studentsApi.setFolders(id, folderIds)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
    isActionsModalOpen.value = false
  }
})

const archiveMutation = useMutation({
  mutationFn: (id: string) => studentsApi.archiveStudent(id),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })
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
  }
})

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

const resetAllFilters = () => {
  searchQuery.value = ''
  selectedTariffs.value = []
  selectedLevels.value = []
  selectedGroups.value = []
  selectedCerts.value = []
  selectedLeads.value = []
  currentPage.value = 1
}
</script>

<template>
  <div class="space-y-4">
    <!-- Top Header Bar -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <Users class="w-5 h-5 text-brand-500" />
          <span>Students Roster</span>
        </h1>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
          Manage enrolled students, applications, document checklists, and tariffs.
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-2.5">
        <button
          @click="isFilterPanelOpen = !isFilterPanelOpen"
          class="px-3.5 py-2 rounded-xl border text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5"
          :class="isFilterPanelOpen ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
        >
          <Filter class="w-4 h-4" />
          <span>Filter</span>
        </button>

        <button
          @click="isAddModalOpen = true"
          class="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold shadow-md shadow-brand-500/25 transition-all cursor-pointer flex items-center gap-1.5"
        >
          <Plus class="w-4 h-4" />
          <span>Add Student</span>
        </button>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="flex items-center gap-2.5 p-2 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-xs">
      <div class="relative flex-1">
        <Search class="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="searchMode === 'id' ? 'Search by exact Student ID (e.g. UB120)...' : 'Search by ID, Full Name, Passport, Phone, or Parents...'"
          class="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-zinc-50 dark:bg-zinc-800/80 border-transparent focus:border-brand-500 focus:bg-white dark:focus:bg-zinc-800 focus:ring-2 focus:ring-brand-500/20 outline-none transition-all text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400"
        />
      </div>

      <!-- Search Mode Switcher (All vs ID) -->
      <button
        @click="searchMode = searchMode === 'all' ? 'id' : 'all'"
        class="px-3 py-2 rounded-xl border text-xs font-bold transition-all cursor-pointer flex items-center gap-1 shrink-0"
        :class="searchMode === 'id' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 border-transparent' : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300'"
        :title="searchMode === 'id' ? 'Searching ID only' : 'Searching across all fields'"
      >
        <Hash class="w-3.5 h-3.5" />
        <span>{{ searchMode === 'id' ? 'ID Only' : 'All Fields' }}</span>
      </button>
    </div>

    <!-- Folders Navigation Bar -->
    <StudentFoldersManager
      :folders="folders"
      :active-folder="activeFolder"
      @select="f => { activeFolder = f; currentPage = 1; }"
      @create-folder="name => createFolderMutation.mutate(name)"
    />

    <!-- Filter Drawer / Panel (Expandable) -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform -translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform -translate-y-2 opacity-0"
    >
      <StudentFilters
        v-if="isFilterPanelOpen"
        :options="options"
        v-model:selected-tariffs="selectedTariffs"
        v-model:selected-levels="selectedLevels"
        v-model:selected-groups="selectedGroups"
        v-model:selected-certs="selectedCerts"
        v-model:selected-leads="selectedLeads"
        @reset="resetAllFilters"
      />
    </transition>

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
    <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 select-none">
      <div>
        Showing <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min((currentPage - 1) * 30 + 1, totalCount) }}</span> to
        <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min(currentPage * 30, totalCount) }}</span> of
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
      @open-add-payment="id => { isDetailDrawerOpen = false; $router.push({ path: '/payments', query: { student_id: id, open_add: 'true' } }); }"
    />
  </div>
</template>
