<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { statusApi } from '@/api/status'
import { studentsApi } from '@/api/students'
import type { Student } from '@/types'
import { useUiStore } from '@/stores/ui'
import {
  CheckSquare, Search, EyeOff, Calendar, FileText,
  ChevronLeft, ChevronRight, Layers, Clock
} from 'lucide-vue-next'

import StatusGeneralTable from './components/StatusGeneralTable.vue'
import StatusKdbTable from './components/StatusKdbTable.vue'
import KdbDatePickerModal from './components/KdbDatePickerModal.vue'
import EmbassyDocumentsDrawer from './components/EmbassyDocumentsDrawer.vue'

const queryClient = useQueryClient()
const uiStore = useUiStore()

// State
const activeTab = ref<'general' | 'kdb'>('general')
const searchQuery = ref('')
const activeFolder = ref('all')
const showHidden = ref(false)
const currentPage = ref(1)

// Selected student for modals
const selectedKdbStudent = ref<Student | null>(null)
const isKdbModalOpen = ref(false)
const selectedEmbassyStudent = ref<Student | null>(null)
const isEmbassyDrawerOpen = ref(false)

// Query: Folders
const { data: foldersData } = useQuery({
  queryKey: ['folders'],
  queryFn: () => studentsApi.getFolders(),
})

const folders = computed(() => foldersData.value || [])

// Query: Status Students
const { data: statusResponse, isLoading } = useQuery({
  queryKey: [
    'status-students',
    activeTab,
    currentPage,
    searchQuery,
    activeFolder,
    showHidden,
  ],
  queryFn: () => statusApi.getStatusStudents({
    page: currentPage.value,
    page_size: 30,
    search: searchQuery.value,
    folder: activeFolder.value,
    sort_by: activeTab.value === 'kdb' ? 'left' : 'id',
    sort_order: 'asc',
    show_hidden: showHidden.value,
  }),
})

const students = computed(() => statusResponse.value?.results || [])
const totalPages = computed(() => statusResponse.value?.total_pages || 1)
const totalCount = computed(() => statusResponse.value?.count || 0)

// Mutations
const updateKdbMutation = useMutation({
  mutationFn: ({ id, data }: { id: string; data: any }) => statusApi.quickUpdate(id, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['status-students'] })
    queryClient.invalidateQueries({ queryKey: ['students'] })
    isKdbModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'KDB Dates Saved',
      message: 'Deposit put and take dates updated.'
    })
  }
})

const updateEmbassyMutation = useMutation({
  mutationFn: ({ id, data }: { id: string; data: any }) => statusApi.updateEmbassyDrawer(id, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['status-students'] })
    queryClient.invalidateQueries({ queryKey: ['students'] })
    isEmbassyDrawerOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Embassy Record Saved',
      message: 'Visa documents and sponsorship records updated.'
    })
  }
})

// Handlers
const openKdbModal = (student: Student) => {
  selectedKdbStudent.value = student
  isKdbModalOpen.value = true
}

const openEmbassyDrawer = (student: Student) => {
  selectedEmbassyStudent.value = student
  isEmbassyDrawerOpen.value = true
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header & Tab Switcher -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <CheckSquare class="w-5 h-5 text-brand-500" />
          <span>Status Board & Embassy Tracking</span>
        </h1>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
          Monitor admission invoices, Certificate of Admission (COA), KDB bank deposits, and embassy sponsorship docs.
        </p>
      </div>

      <!-- Tab Buttons -->
      <div class="flex items-center gap-1.5 p-1 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl select-none text-xs">
        <button
          @click="activeTab = 'general'"
          class="px-3.5 py-1.5 rounded-xl font-bold transition-all cursor-pointer flex items-center gap-1.5"
          :class="activeTab === 'general' ? 'bg-brand-500 text-white shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
        >
          <Layers class="w-4 h-4" />
          <span>General Status</span>
        </button>
        <button
          @click="activeTab = 'kdb'"
          class="px-3.5 py-1.5 rounded-xl font-bold transition-all cursor-pointer flex items-center gap-1.5"
          :class="activeTab === 'kdb' ? 'bg-brand-500 text-white shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
        >
          <Clock class="w-4 h-4" />
          <span>KDB Deposit Tracking</span>
        </button>
      </div>
    </div>

    <!-- Search & Filter Controls -->
    <div class="p-3 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs select-none">
      <div class="relative flex-1 min-w-[240px]">
        <Search class="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by student name, ID, or phone..."
          class="w-full pl-9 pr-3 py-1.5 rounded-xl bg-zinc-50 dark:bg-zinc-800 border-transparent focus:border-brand-500 focus:bg-white dark:focus:bg-zinc-800 focus:ring-2 focus:ring-brand-500/20 outline-none text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400"
        />
      </div>

      <!-- Folder Pills -->
      <div class="flex items-center gap-1.5 overflow-x-auto">
        <button
          @click="activeFolder = 'all'"
          class="px-2.5 py-1 rounded-lg border font-bold transition-all cursor-pointer"
          :class="activeFolder === 'all' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 border-transparent' : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'"
        >
          All Folders
        </button>
        <button
          v-for="f in folders"
          :key="f.id"
          @click="activeFolder = f.id"
          class="px-2.5 py-1 rounded-lg border font-bold transition-all cursor-pointer"
          :class="activeFolder === f.id ? 'bg-brand-500 text-white border-brand-500' : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'"
        >
          {{ f.name }}
        </button>
      </div>

      <!-- Show Hidden Toggle -->
      <label class="flex items-center gap-1.5 font-bold text-zinc-600 dark:text-zinc-400 cursor-pointer ml-auto">
        <input
          v-model="showHidden"
          type="checkbox"
          class="w-4 h-4 rounded text-brand-500 focus:ring-brand-500 cursor-pointer"
        />
        <span>Show Hidden</span>
      </label>
    </div>

    <!-- Active Table View -->
    <StatusGeneralTable
      v-if="activeTab === 'general'"
      :students="students"
      :is-loading="isLoading"
      @open-kdb-modal="openKdbModal"
      @open-embassy-drawer="openEmbassyDrawer"
    />

    <StatusKdbTable
      v-else
      :students="students"
      :is-loading="isLoading"
      @open-kdb-modal="openKdbModal"
      @open-embassy-drawer="openEmbassyDrawer"
    />

    <!-- Pagination -->
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
    <KdbDatePickerModal
      :is-open="isKdbModalOpen"
      :student="selectedKdbStudent"
      @close="isKdbModalOpen = false"
      @save="data => selectedKdbStudent && updateKdbMutation.mutate({ id: selectedKdbStudent.id, data })"
    />

    <EmbassyDocumentsDrawer
      :is-open="isEmbassyDrawerOpen"
      :student="selectedEmbassyStudent"
      @close="isEmbassyDrawerOpen = false"
      @save="data => selectedEmbassyStudent && updateEmbassyMutation.mutate({ id: selectedEmbassyStudent.id, data })"
    />
  </div>
</template>
