<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  Search,
  Plus,
  Filter,
  FileSpreadsheet,
  BookOpen,
  X,
  Layers,
  Building2,
  Globe,
  Map,
  ChevronDown,
  Check,
  FileText
} from 'lucide-vue-next'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import { useAuthStore } from '@/stores/auth'
import { PICK_NEEDED_LIST } from '@/composables/useDocumentHelpers'

const route = useRoute()
const dashboardStore = useStudentDashboardStore()
const authStore = useAuthStore()
const searchInputRef = ref<HTMLInputElement | null>(null)

const pathname = computed(() => route.path)

const isStudentOrStatusPage = computed(() => {
  return pathname.value === '/students' || pathname.value === '/status' || pathname.value === '/documents' || pathname.value === '/visacheck'
})

const isMac = computed(() => {
  if (typeof navigator === 'undefined') return false
  return /(Mac|iPhone|iPod|iPad)/i.test(navigator.platform || navigator.userAgent)
})

const isVisaTypeDropdownOpen = ref(false)
const isMissingDocsDropdownOpen = ref(false)
const missingDocsSearchQuery = ref('')

const filteredMissingDocOptions = computed(() => {
  const q = missingDocsSearchQuery.value.trim().toLowerCase()
  if (!q) return PICK_NEEDED_LIST
  return PICK_NEEDED_LIST.filter(doc => doc.toLowerCase().includes(q))
})

const toggleMissingDoc = (doc: string) => {
  const current = [...dashboardStore.selectedMissingDocs]
  if (current.includes(doc)) {
    dashboardStore.selectedMissingDocs = current.filter(d => d !== doc)
  } else {
    dashboardStore.selectedMissingDocs = [...current, doc]
  }
}

const clearMissingDocs = () => {
  dashboardStore.selectedMissingDocs = []
}

const visaTypeOptions = [
  { value: 'all', label: 'All', icon: Layers },
  { value: 'Embassy', label: 'Embassy', icon: Building2 },
  { value: 'E-Visa', label: 'E-Visa', icon: Globe },
  { value: 'Regional', label: 'Regional', icon: Map },
]

const activeVisaTypeOpt = computed(() => {
  return visaTypeOptions.find(o => o.value === dashboardStore.visaTypeFilter) || visaTypeOptions[0]
})

const PAGE_TITLES: Record<string, string> = {
  '/students': 'Students',
  '/status': 'Status Board',
  '/documents': 'Documents',
  '/visacheck': 'Visa Check',
  '/payments': 'Payments',
  '/settings': 'Settings',
  '/tenants': 'Tenants Management',
}

const pageTitle = computed(() => {
  return PAGE_TITLES[pathname.value] || 'Dashboard'
})

const currentDateFormatted = computed(() => {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

// Global Hotkeys: Ctrl+K / Cmd+K to Search, Esc to blur/clear/close
const handleGlobalKeyDown = (e: KeyboardEvent) => {
  // Ctrl+K or Cmd+K
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    if (isStudentOrStatusPage.value && searchInputRef.value) {
      searchInputRef.value.focus()
      searchInputRef.value.select()
    }
    return
  }

  // Escape key handler
  if (e.key === 'Escape') {
    if (document.activeElement === searchInputRef.value) {
      if (dashboardStore.searchQuery) {
        dashboardStore.searchQuery = ''
      }
      searchInputRef.value?.blur()
      return
    }

    // Close top bar modals / panels if open
    if (isMissingDocsDropdownOpen.value) {
      isMissingDocsDropdownOpen.value = false
      return
    }
    if (dashboardStore.isFilterPanelOpen) {
      dashboardStore.isFilterPanelOpen = false
      return
    }
    if (dashboardStore.isAddStudentModalOpen) {
      dashboardStore.isAddStudentModalOpen = false
      return
    }
    if (dashboardStore.isExcelModalOpen) {
      dashboardStore.isExcelModalOpen = false
      return
    }
    if (isVisaTypeDropdownOpen.value) {
      isVisaTypeDropdownOpen.value = false
      return
    }
  }
}

function onDocClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (isVisaTypeDropdownOpen.value && !target.closest('[data-visa-type-menu]')) {
    isVisaTypeDropdownOpen.value = false
  }
  if (isMissingDocsDropdownOpen.value && !target.closest('[data-missing-docs-menu]')) {
    isMissingDocsDropdownOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeyDown)
  document.addEventListener('click', onDocClick)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeyDown)
  document.removeEventListener('click', onDocClick)
})
</script>

<template>
  <!-- 1-to-1 Top Navbar for /students, /status, /documents, /visacheck -->
  <header
    v-if="isStudentOrStatusPage"
    class="flex flex-col md:flex-row flex-shrink-0 items-stretch md:items-center justify-between gap-2.5 md:gap-3 lg:gap-4 px-3 sm:px-4 md:px-6 h-auto py-2.5 md:h-14 md:py-0 border-b border-zinc-200/80 dark:border-zinc-800 bg-white/95 dark:bg-[#111315]/95 backdrop-blur-md sticky top-0 z-30 shadow-2xs"
  >
    <!-- Left Column: Filter Button or Visa Type -->
    <div class="flex-shrink-0 flex items-center gap-2 justify-start">
      <!-- Visa Type Dropdown on /visacheck -->
      <div v-if="pathname === '/visacheck'" class="relative" data-visa-type-menu>
        <button
          type="button"
          @click.stop="isVisaTypeDropdownOpen = !isVisaTypeDropdownOpen"
          class="flex items-center justify-center gap-2 px-3 lg:px-4 h-[34px] md:h-[36px] rounded-full border text-xs md:text-sm font-bold select-none cursor-pointer transition-all duration-200 shadow-xs hover:shadow-md outline-none whitespace-nowrap shrink-0 border-zinc-300 dark:border-zinc-700 bg-zinc-100/90 dark:bg-zinc-900 text-zinc-800 dark:text-zinc-100 hover:bg-zinc-200/80 dark:hover:bg-zinc-800"
        >
          <component :is="activeVisaTypeOpt.icon" class="size-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>{{ activeVisaTypeOpt.label }}</span>
          <span class="text-[11px] font-bold rounded-md px-1.5 py-0.5 min-w-[1.25rem] text-center bg-[#0B4133] text-white">
            {{ dashboardStore.visaTypeCounts?.[dashboardStore.visaTypeFilter] ?? 0 }}
          </span>
          <ChevronDown class="size-3.5 text-zinc-400" />
        </button>

        <Transition
          enter-active-class="transition duration-100 ease-out"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition duration-75 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="isVisaTypeDropdownOpen"
            class="absolute left-0 mt-1 w-52 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xl py-2 z-50 text-xs"
          >
            <button
              v-for="opt in visaTypeOptions"
              :key="opt.value"
              type="button"
              @click="dashboardStore.visaTypeFilter = opt.value as any; isVisaTypeDropdownOpen = false"
              class="w-full text-left px-3.5 py-2.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 flex items-center justify-between text-zinc-800 dark:text-zinc-200 font-semibold cursor-pointer transition-colors"
            >
              <div class="flex items-center gap-2">
                <component :is="opt.icon" class="size-4 text-zinc-400" />
                <span>{{ opt.label }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span
                  class="text-[10px] font-bold rounded px-1.5 py-0.5 text-center"
                  :class="dashboardStore.visaTypeFilter === opt.value
                    ? 'bg-[#0B4133] text-white'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400'"
                >
                  {{ dashboardStore.visaTypeCounts?.[opt.value] ?? 0 }}
                </span>
                <Check v-if="dashboardStore.visaTypeFilter === opt.value" class="size-3.5 text-emerald-500" />
              </div>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Filter Button on other pages -->
      <div v-else class="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          @click="dashboardStore.isFilterPanelOpen = !dashboardStore.isFilterPanelOpen"
          class="flex items-center justify-center gap-1.5 px-3 lg:px-3.5 h-[34px] md:h-[36px] rounded-full border text-xs md:text-sm font-semibold select-none cursor-pointer transition-all duration-200 shadow-xs hover:shadow-md outline-none whitespace-nowrap shrink-0"
          :class="[
            dashboardStore.isFilterPanelOpen || dashboardStore.activeFiltersCount > 0
              ? 'border-blue-500 bg-blue-50/80 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold ring-2 ring-blue-500/20'
              : 'border-zinc-200 dark:border-zinc-700/80 bg-zinc-100/80 dark:bg-zinc-900 text-zinc-700 dark:text-zinc-200 hover:bg-zinc-200/70 dark:hover:bg-zinc-800'
          ]"
        >
          <Filter class="h-4 w-4" />
          <span>Filter{{ dashboardStore.activeFiltersCount > 0 ? ` (${dashboardStore.activeFiltersCount})` : '' }}</span>
        </button>
      </div>
    </div>

    <!-- Center Column: Search Bar + (on /documents) Missing Docs Filter -->
    <div class="flex items-center justify-center gap-2 z-30 w-full md:flex-1 md:min-w-0 max-w-full md:max-w-[420px] lg:max-w-[480px] xl:max-w-[540px] mx-0 md:mx-2 lg:mx-4">
      <div
        class="relative flex-1 flex items-center rounded-full border border-zinc-200 dark:border-zinc-700/80 bg-zinc-100/90 dark:bg-zinc-900 backdrop-blur-md shadow-xs hover:border-zinc-300 dark:hover:border-zinc-600 dark:hover:bg-zinc-850 transition-all duration-200 ease-out h-[36px] md:h-[38px] focus-within:border-blue-500 dark:focus-within:border-blue-500 focus-within:bg-white dark:focus-within:bg-zinc-900 focus-within:ring-2 focus-within:ring-blue-500/20"
      >
        <div class="relative flex items-center w-full h-full rounded-full pl-3 sm:pl-3.5 pr-2 bg-transparent gap-2">
          <Search class="h-4 w-4 text-zinc-400 dark:text-zinc-400 flex-shrink-0" />
          <input
            ref="searchInputRef"
            type="text"
            :placeholder="dashboardStore.searchMode === 'id' ? 'Search ID (e.g. G54)...' : 'Search by name, ID, passport...'"
            v-model="dashboardStore.searchQuery"
            class="w-full bg-transparent text-xs md:text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-400 py-1.5 border-none focus:outline-none ring-0 outline-none font-medium"
          />

          <!-- Clear Button -->
          <button
            v-if="dashboardStore.searchQuery"
            type="button"
            @click="dashboardStore.searchQuery = ''"
            class="p-0.5 rounded-full text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors"
            title="Clear search"
          >
            <X class="size-3.5" />
          </button>

          <!-- Hotkey Badge (Visible on xl+ screens) -->
          <div class="hidden xl:flex items-center gap-1 shrink-0 select-none">
            <kbd class="inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold text-zinc-500 dark:text-zinc-400 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded shadow-2xs font-mono">
              {{ isMac ? '⌘K' : 'Ctrl+K' }}
            </kbd>
          </div>

          <div class="flex items-center shrink-0 border-l border-zinc-200 dark:border-zinc-700/80 pl-1.5 pr-0.5 py-0.5">
            <select
              v-model="dashboardStore.searchMode"
              class="bg-transparent text-xs font-bold text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white cursor-pointer focus:outline-none border-none py-1 pr-1"
            >
              <option value="all" class="bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 font-medium">All</option>
              <option value="id" class="bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 font-medium">ID only</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Dedicated Missing Documents Dropdown Trigger (on right of searchbar on /documents) -->
      <div v-if="pathname === '/documents'" class="relative shrink-0" data-missing-docs-menu>
        <button
          type="button"
          @click.stop="isMissingDocsDropdownOpen = !isMissingDocsDropdownOpen"
          class="flex items-center justify-center gap-1.5 px-2.5 sm:px-3 h-[36px] md:h-[38px] rounded-full border text-xs font-semibold select-none cursor-pointer transition-all duration-200 shadow-xs hover:shadow-md outline-none whitespace-nowrap"
          :class="[
            dashboardStore.selectedMissingDocs.length > 0 || isMissingDocsDropdownOpen
              ? 'border-orange-500 bg-orange-50/90 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 font-bold ring-2 ring-orange-500/20'
              : 'border-zinc-200 dark:border-zinc-700/80 bg-zinc-100/90 dark:bg-zinc-900 text-zinc-700 dark:text-zinc-200 hover:bg-zinc-200/70 dark:hover:bg-zinc-800'
          ]"
        >
          <FileText class="h-4 w-4 text-orange-500 dark:text-orange-400 shrink-0" />
          <span class="hidden sm:inline">Missing Docs</span>
          <span
            v-if="dashboardStore.selectedMissingDocs.length > 0"
            class="text-[10px] font-bold rounded-full px-1.5 py-0.2 min-w-[1.2rem] text-center bg-orange-500 text-white"
          >
            {{ dashboardStore.selectedMissingDocs.length }}
          </span>
          <ChevronDown class="size-3.5 text-zinc-400 transition-transform" :class="isMissingDocsDropdownOpen ? 'rotate-180' : ''" />
        </button>

        <Transition
          enter-active-class="transition duration-100 ease-out"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition duration-75 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="isMissingDocsDropdownOpen"
            class="absolute right-0 mt-1.5 w-64 max-h-[380px] rounded-2xl bg-white dark:bg-[#15171a] border border-zinc-200 dark:border-zinc-800 shadow-2xl z-50 text-xs flex flex-col overflow-hidden animate-page-in"
          >
            <!-- Search inside missing docs -->
            <div class="p-2 border-b border-zinc-100 dark:border-zinc-800">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-400" />
                <input
                  v-model="missingDocsSearchQuery"
                  type="text"
                  placeholder="Search missing docs..."
                  class="w-full pl-8 pr-2.5 py-1.5 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-lg border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:border-orange-500"
                  @click.stop
                />
              </div>
            </div>

            <!-- List of Missing Doc Checkboxes -->
            <div class="overflow-y-auto max-h-[240px] p-1.5 space-y-0.5 scrollbar-thin">
              <label
                v-for="doc in filteredMissingDocOptions"
                :key="doc"
                class="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800/80 cursor-pointer transition-colors select-none"
                @click.stop
              >
                <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-200">{{ doc }}</span>
                <input
                  type="checkbox"
                  :checked="dashboardStore.selectedMissingDocs.includes(doc)"
                  @change="toggleMissingDoc(doc)"
                  class="h-4 w-4 rounded border-zinc-300 text-orange-600 focus:ring-orange-500 cursor-pointer"
                />
              </label>
            </div>

            <!-- Footer with Clear button -->
            <div class="p-2 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/60 dark:bg-zinc-850/40">
              <span class="text-[11px] text-zinc-400 font-medium">
                {{ dashboardStore.selectedMissingDocs.length }} selected
              </span>
              <button
                v-if="dashboardStore.selectedMissingDocs.length > 0"
                type="button"
                @click="clearMissingDocs"
                class="text-[11px] font-bold text-rose-600 dark:text-rose-400 hover:underline cursor-pointer"
              >
                Clear all
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Right Column: Action Buttons -->
    <div class="flex items-center gap-1.5 sm:gap-2 lg:gap-2.5 justify-end shrink-0 mt-1 md:mt-0">
      <!-- Admissions Link Button (Hidden on /visacheck and /documents) -->
      <a
        v-if="pathname !== '/visacheck' && pathname !== '/documents'"
        href="https://www.salomkorea.uz/#admission"
        target="_blank"
        rel="noopener noreferrer"
        class="flex items-center justify-center gap-1.5 px-2.5 sm:px-3 lg:px-3.5 h-[34px] rounded-full border border-blue-600/30 bg-blue-50 hover:bg-blue-100/70 text-blue-700 dark:bg-blue-950/20 dark:border-blue-800/40 dark:text-blue-400 text-xs font-semibold select-none cursor-pointer transition-all duration-300 shadow-[0_8px_30px_rgba(0,0,0,0.06)] hover:shadow-md outline-none shrink-0 whitespace-nowrap"
        title="Admissions University Portal"
      >
        <BookOpen class="h-4 w-4 text-blue-500 shrink-0" />
        <span class="hidden xl:inline">Admissions</span>
      </a>

      <!-- Excel Download Button (Hidden on /visacheck and /documents) -->
      <button
        v-if="pathname !== '/visacheck' && pathname !== '/documents'"
        type="button"
        @click="dashboardStore.isExcelModalOpen = true"
        class="flex items-center justify-center gap-1.5 px-2.5 sm:px-3 lg:px-3.5 h-[34px] rounded-full border border-emerald-600/30 bg-emerald-50 hover:bg-emerald-100/70 text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-800/40 dark:text-emerald-400 text-xs font-semibold select-none cursor-pointer transition-all duration-300 shadow-[0_8px_30px_rgba(0,0,0,0.06)] hover:shadow-md outline-none shrink-0 whitespace-nowrap"
        title="Export Roster to Excel"
      >
        <FileSpreadsheet class="h-4 w-4 shrink-0" />
        <span class="hidden 2xl:inline">Export Excel</span>
        <span class="hidden lg:inline 2xl:hidden">Export</span>
      </button>

      <!-- Add Student Button (Hidden on /documents and for Tenant Staff) -->
      <button
        v-if="pathname !== '/documents' && authStore.canEdit"
        type="button"
        @click="dashboardStore.isAddStudentModalOpen = true"
        class="flex-1 md:flex-initial flex items-center justify-center gap-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 px-3 sm:px-3.5 lg:px-4 py-1.5 text-xs md:text-sm font-bold text-white shadow-md shadow-blue-500/25 transition-all cursor-pointer select-none h-8 md:h-[34px] shrink-0 whitespace-nowrap"
      >
        <Plus class="h-4 w-4 shrink-0" />
        <span>Add<span class="hidden sm:inline"> Student</span></span>
      </button>
    </div>
  </header>

  <!-- Clean Title Header for Other Pages (/payments, /settings, /tenants) - Hidden on /extract -->
  <header
    v-else-if="!pathname.includes('/extract')"
    class="flex h-14 flex-shrink-0 items-center justify-between gap-4 px-6 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-[#111315]/80 backdrop-blur-md sticky top-0 z-20 shadow-2xs"
  >
    <div>
      <h1 class="text-base font-bold text-zinc-900 dark:text-zinc-100">{{ pageTitle }}</h1>
      <p class="text-[11px] text-zinc-400 dark:text-zinc-500">{{ currentDateFormatted }}</p>
    </div>
  </header>
</template>
