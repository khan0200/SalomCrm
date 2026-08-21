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
  Check
} from 'lucide-vue-next'
import { useStudentDashboardStore } from '@/stores/studentDashboard'

const route = useRoute()
const dashboardStore = useStudentDashboardStore()
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
  if (isVisaTypeDropdownOpen.value) {
    const target = e.target as HTMLElement
    if (!target.closest('[data-visa-type-menu]')) {
      isVisaTypeDropdownOpen.value = false
    }
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
    class="flex flex-col md:flex-row flex-shrink-0 items-stretch md:items-center justify-between gap-3 md:gap-4 px-4 md:px-6 h-auto py-2.5 md:h-14 md:py-0 border-b border-zinc-200/80 dark:border-zinc-800 bg-white/95 dark:bg-[#111315]/95 backdrop-blur-md sticky top-0 z-30 shadow-2xs"
  >
    <!-- Left Side: Visa Type Dropdown on /visacheck OR Filter Button on other pages -->
    <div v-if="pathname === '/visacheck'" class="flex-shrink-0 relative" data-visa-type-menu>
      <button
        type="button"
        @click.stop="isVisaTypeDropdownOpen = !isVisaTypeDropdownOpen"
        class="flex items-center justify-center gap-2 px-3.5 lg:px-4 h-[34px] md:h-[36px] rounded-full border text-xs md:text-sm font-bold select-none cursor-pointer transition-all duration-200 shadow-xs hover:shadow-md outline-none whitespace-nowrap shrink-0 border-zinc-300 dark:border-zinc-700 bg-zinc-100/90 dark:bg-zinc-900 text-zinc-800 dark:text-zinc-100 hover:bg-zinc-200/80 dark:hover:bg-zinc-800"
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
    <div v-else class="flex-shrink-0 flex items-center gap-2 flex-wrap">
      <button
        type="button"
        @click="dashboardStore.isFilterPanelOpen = !dashboardStore.isFilterPanelOpen"
        class="flex items-center justify-center gap-1.5 px-3 lg:px-4 h-[34px] md:h-[36px] rounded-full border text-xs md:text-sm font-semibold select-none cursor-pointer transition-all duration-200 shadow-xs hover:shadow-md outline-none whitespace-nowrap shrink-0"
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

    <!-- Center: Sleek Search Bar -->
    <div class="flex items-center gap-2.5 z-30 w-full h-auto md:flex-1 md:min-w-0 md:mx-3 max-w-full md:max-w-[480px]">
      <div
        class="relative flex-1 flex items-center rounded-full border border-zinc-200 dark:border-zinc-700/80 bg-zinc-100/90 dark:bg-zinc-900 backdrop-blur-md shadow-xs hover:border-zinc-300 dark:hover:border-zinc-600 dark:hover:bg-zinc-850 transition-all duration-200 ease-out h-[38px] md:h-[40px] focus-within:border-blue-500 dark:focus-within:border-blue-500 focus-within:bg-white dark:focus-within:bg-zinc-900 focus-within:ring-2 focus-within:ring-blue-500/20"
      >
        <div class="relative flex items-center w-full h-full rounded-full pl-3.5 md:pl-4 pr-2.5 bg-transparent gap-2">
          <Search class="h-4 w-4 text-zinc-400 dark:text-zinc-400 flex-shrink-0" />
          <input
            ref="searchInputRef"
            type="text"
            :placeholder="dashboardStore.searchMode === 'id' ? 'Search ID (e.g. G54)...' : 'Search by name, ID, passport...'"
            v-model="dashboardStore.searchQuery"
            class="w-full bg-transparent text-[14px] md:text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-400 py-2 border-none focus:outline-none ring-0 outline-none font-medium"
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

          <!-- Hotkey Badge -->
          <div class="hidden sm:flex items-center gap-1 shrink-0 select-none">
            <kbd class="inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold text-zinc-500 dark:text-zinc-400 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded shadow-2xs font-mono">
              {{ isMac ? '⌘K' : 'Ctrl+K' }}
            </kbd>
          </div>

          <div class="flex items-center shrink-0 border-l border-zinc-200 dark:border-zinc-700/80 pl-2 pr-0.5 py-0.5">
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
    </div>

    <!-- Right Side Actions -->
    <div class="flex items-center gap-2 md:gap-2.5 justify-end z-10 w-full md:w-auto md:shrink-0 mt-1 md:mt-0">
      <!-- Admissions Link Button (Hidden on /visacheck) -->
      <a
        v-if="pathname !== '/visacheck'"
        href="https://www.salomkorea.uz/#admission"
        target="_blank"
        rel="noopener noreferrer"
        class="flex items-center justify-center gap-1.5 px-3 lg:px-4 h-[34px] rounded-full border border-blue-600/30 bg-blue-50 hover:bg-blue-100/70 text-blue-700 dark:bg-blue-950/20 dark:border-blue-800/40 dark:text-blue-400 text-xs md:text-sm font-semibold select-none cursor-pointer transition-all duration-300 shadow-[0_8px_30px_rgba(0,0,0,0.06)] hover:shadow-md outline-none shrink-0 whitespace-nowrap"
        title="Admissions University Portal"
      >
        <BookOpen class="h-4.5 w-4.5 text-blue-500 shrink-0" />
        <span class="hidden sm:inline md:hidden lg:inline">Admissions</span>
      </a>

      <!-- Excel Download Button (Hidden on /visacheck) -->
      <button
        v-if="pathname !== '/visacheck'"
        type="button"
        @click="dashboardStore.isExcelModalOpen = true"
        class="flex items-center justify-center gap-1.5 px-3 lg:px-4 h-[34px] rounded-full border border-emerald-600/30 bg-emerald-50 hover:bg-emerald-100/70 text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-800/40 dark:text-emerald-400 text-xs md:text-sm font-semibold select-none cursor-pointer transition-all duration-300 shadow-[0_8px_30px_rgba(0,0,0,0.06)] hover:shadow-md outline-none shrink-0 whitespace-nowrap"
        title="Export Roster to Excel"
      >
        <FileSpreadsheet class="h-4.5 w-4.5 shrink-0" />
        <span class="hidden sm:inline md:hidden lg:inline">Export Excel</span>
      </button>

      <!-- Add Student Button -->
      <button
        type="button"
        @click="dashboardStore.isAddStudentModalOpen = true"
        class="flex-1 md:flex-initial flex items-center justify-center gap-1.5 lg:gap-2 rounded-xl bg-blue-600 hover:bg-blue-700 px-3.5 lg:px-4 py-1.5 text-xs md:text-sm font-bold text-white shadow-md shadow-blue-500/25 transition-all cursor-pointer select-none h-8 md:h-[34px] shrink-0 whitespace-nowrap"
      >
        <Plus class="h-4 w-4 shrink-0" />
        <span>Add<span class="sm:inline md:hidden lg:inline"> Student</span></span>
      </button>
    </div>
  </header>

  <!-- Clean Title Header for Other Pages (/payments, /settings, /tenants) -->
  <header
    v-else
    class="flex h-14 flex-shrink-0 items-center justify-between gap-4 px-6 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-[#111315]/80 backdrop-blur-md sticky top-0 z-20 shadow-2xs"
  >
    <div>
      <h1 class="text-base font-bold text-zinc-900 dark:text-zinc-100">{{ pageTitle }}</h1>
      <p class="text-[11px] text-zinc-400 dark:text-zinc-500">{{ currentDateFormatted }}</p>
    </div>
  </header>
</template>
