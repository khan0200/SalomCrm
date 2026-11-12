<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import {
  ChevronDown, ChevronRight, Check, Search, X, RotateCcw
} from 'lucide-vue-next'
import { studentsApi } from '@/api/students'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import { useCustomTags } from '@/composables/useCustomTags'
import { useCurrency } from '@/composables/useCurrency'
import { getTariffPrice } from '@/utils/tariff'

const dashboardStore = useStudentDashboardStore()
const { formatCurrency } = useCurrency()
const { tagsRegistry, getTagIcon, fetchTags } = useCustomTags()

const dropdownContainerRef = ref<HTMLElement | null>(null)

// Open dropdown name: 'tariff' | 'level' | 'group' | 'cert' | 'tag' | 'coordinator' | null
const openDropdown = ref<string | null>(null)
const openSubMenu = ref<string | null>(null) // 'TOPIK' | 'IELTS' | 'CEFR' | null

// Search inputs inside popovers
const searchQueries = ref<Record<string, string>>({
  tariff: '',
  level: '',
  group: '',
  cert: '',
  tag: '',
  coordinator: '',
})

onMounted(() => {
  fetchTags()
  document.addEventListener('click', handleDocumentClick)
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
  document.removeEventListener('keydown', handleKeyDown)
})

const handleDocumentClick = (e: MouseEvent) => {
  if (!dropdownContainerRef.value) return
  if (!dropdownContainerRef.value.contains(e.target as Node)) {
    closeAll()
  }
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    closeAll()
  }
}

const closeAll = () => {
  openDropdown.value = null
  openSubMenu.value = null
}

const toggleDropdown = (name: string) => {
  if (openDropdown.value === name) {
    closeAll()
  } else {
    openDropdown.value = name
    openSubMenu.value = null
  }
}

// ── Query options from API ──
const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
  staleTime: 1000 * 60 * 10,
})

// ── 1. TARIFF OPTIONS ──
const tariffRawOptions = computed<string[]>(() => {
  const list = optionsData.value?.tariffs || []
  return ['NO_TARIFF', ...list.map((t: any) => t.name)]
})

const filteredTariffs = computed(() => {
  const q = (searchQueries.value.tariff || '').trim().toLowerCase()
  if (!q) return tariffRawOptions.value
  return tariffRawOptions.value.filter(t => {
    const label = t === 'NO_TARIFF' ? 'no tariff' : t.toLowerCase()
    return label.includes(q)
  })
})

const getTariffLabel = (opt: string) => {
  if (opt === 'NO_TARIFF') return 'No Tariff'
  const price = getTariffPrice(opt, null, optionsData.value?.tariffs || [])
  return price > 0 ? `${opt} (${formatCurrency(price)})` : opt
}

// ── 2. LEVEL OPTIONS ──
const levelRawOptions = computed<string[]>(() => {
  const list = optionsData.value?.levels || []
  const base = ['NO_LEVEL', ...list]
  return Array.from(new Set(base))
})

const filteredLevels = computed(() => {
  const q = (searchQueries.value.level || '').trim().toLowerCase()
  if (!q) return levelRawOptions.value
  return levelRawOptions.value.filter(l => {
    const label = l === 'NO_LEVEL' ? 'no level' : l.toLowerCase()
    return label.includes(q)
  })
})

const getLevelLabel = (opt: string) => {
  if (opt === 'NO_LEVEL') return 'No Level'
  return opt
}

// ── 3. GROUP OPTIONS ──
const groupRawOptions = computed<string[]>(() => {
  const list = optionsData.value?.groups || []
  return ['NO_GROUP', ...list]
})

const filteredGroups = computed(() => {
  const q = (searchQueries.value.group || '').trim().toLowerCase()
  if (!q) return groupRawOptions.value
  return groupRawOptions.value.filter(g => {
    const label = g === 'NO_GROUP' ? 'no group' : g.toLowerCase()
    return label.includes(q)
  })
})

const getGroupLabel = (opt: string) => {
  if (opt === 'NO_GROUP') return 'No Group'
  return opt
}

// ── 4. CERTIFICATE OPTIONS & SUB-MENUS ──
const certRawOptions = [
  'NO CERTIFICATE',
  'EXPECTED',
  'TOPIK',
  'IELTS',
  'CEFR',
  'SKA',
  'TOEFL',
  'SAT'
]

const CERT_SUB_SCORES: Record<string, string[]> = {
  TOPIK: ['1', '2', '3', '4', '5', '6', 'EXPECTED'],
  IELTS: ['5.0', '5.5', '6.0', '6.5', '7.0', '7.5', '8.0', '8.5', '9.0', 'EXPECTED'],
  CEFR: ['B1', 'B2', 'C1', 'C2', 'EXPECTED'],
}

const filteredCerts = computed(() => {
  const q = (searchQueries.value.cert || '').trim().toLowerCase()
  if (!q) return certRawOptions
  return certRawOptions.filter(c => c.toLowerCase().includes(q))
})

const getCertLabel = (opt: string) => {
  if (opt === 'NO CERTIFICATE') return 'No Certificate'
  if (opt === 'EXPECTED') return 'Expected'
  return opt
}

// ── 5. TAGS OPTIONS ──
const tagRawOptions = computed<string[]>(() => {
  const list = tagsRegistry.value.map(t => t.name)
  return ['NO_TAGS', ...list]
})

const filteredTags = computed(() => {
  const q = (searchQueries.value.tag || '').trim().toLowerCase()
  if (!q) return tagRawOptions.value
  return tagRawOptions.value.filter(t => {
    const label = t === 'NO_TAGS' ? 'no tags' : t.toLowerCase()
    return label.includes(q)
  })
})

const getTagLabel = (opt: string) => {
  if (opt === 'NO_TAGS') return 'No Tags'
  return `${getTagIcon(opt)} ${opt}`
}

// ── 6. COORDINATOR OPTIONS ──
const coordinatorRawOptions = computed<string[]>(() => {
  const coordSet = new Set<string>()
  ;(optionsData.value?.coordinators || []).forEach((c: any) => {
    const name = typeof c === 'string' ? c.trim() : (c?.name || '').trim()
    if (name && name !== 'NO_COORDINATOR' && name !== 'No Coordinator') coordSet.add(name)
  })
  return ['NO_COORDINATOR', ...Array.from(coordSet).sort((a, b) => a.localeCompare(b))]
})

const filteredCoordinators = computed(() => {
  const q = (searchQueries.value.coordinator || '').trim().toLowerCase()
  if (!q) return coordinatorRawOptions.value
  return coordinatorRawOptions.value.filter(co => {
    const label = co === 'NO_COORDINATOR' ? 'no coordinator' : co.toLowerCase()
    return label.includes(q)
  })
})

const getCoordinatorLabel = (opt: string) => {
  if (opt === 'NO_COORDINATOR') return 'No Coordinator'
  return opt
}

// ── Checkbox Helper Logic: All checked by default ──
const isOptionChecked = (opt: string, selectedList: string[]): boolean => {
  if (selectedList.includes('__NONE__')) return false
  if (selectedList.length === 0) return true
  return selectedList.includes(opt)
}

const isAllChecked = (selectedList: string[], allOptions: string[]): boolean => {
  if (selectedList.includes('__NONE__')) return false
  if (selectedList.length === 0) return true
  return allOptions.every(o => selectedList.includes(o))
}

const toggleOption = (opt: string, currentSelected: string[], allOptions: string[]): string[] => {
  if (currentSelected.length === 0) {
    // Unchecking an option from "all checked" default
    return allOptions.filter(o => o !== opt)
  }

  if (currentSelected.includes('__NONE__')) {
    // Checking first option from "none checked"
    return [opt]
  }

  const isChecked = currentSelected.includes(opt)
  if (isChecked) {
    const next = currentSelected.filter(o => o !== opt)
    if (next.length === 0) return ['__NONE__']
    return next
  } else {
    const next = [...currentSelected, opt]
    if (allOptions.every(o => next.includes(o))) {
      return [] // All checked -> reset to []
    }
    return next
  }
}

const toggleSelectAll = (currentSelected: string[], allOptions: string[]): string[] => {
  if (isAllChecked(currentSelected, allOptions)) {
    return ['__NONE__']
  } else {
    return []
  }
}

// ── Sub-Scores Logic for Certificate ──
const isSubScoreChecked = (cert: string, score: string): boolean => {
  const allowed = dashboardStore.selectedCertScores?.[cert]
  if (!allowed || allowed.length === 0) return true
  if (allowed.includes('__NONE__')) return false
  return allowed.includes(score)
}

const isAllSubScoresChecked = (cert: string): boolean => {
  const allScores = CERT_SUB_SCORES[cert] || []
  const allowed = dashboardStore.selectedCertScores?.[cert]
  if (!allowed || allowed.length === 0) return true
  if (allowed.includes('__NONE__')) return false
  return allScores.every(s => allowed.includes(s))
}

const toggleSubScore = (cert: string, score: string) => {
  const allScores = CERT_SUB_SCORES[cert] || []
  const current = dashboardStore.selectedCertScores?.[cert] || []
  let nextScores: string[]

  if (current.length === 0) {
    nextScores = allScores.filter(s => s !== score)
  } else if (current.includes('__NONE__')) {
    nextScores = [score]
  } else {
    if (current.includes(score)) {
      nextScores = current.filter(s => s !== score)
      if (nextScores.length === 0) nextScores = ['__NONE__']
    } else {
      nextScores = [...current, score]
      if (allScores.every(s => nextScores.includes(s))) {
        nextScores = [] // All checked
      }
    }
  }

  const updated = { ...(dashboardStore.selectedCertScores || {}) }
  if (nextScores.length === 0) {
    delete updated[cert]
  } else {
    updated[cert] = nextScores
  }
  dashboardStore.selectedCertScores = updated
}

const toggleAllSubScores = (cert: string) => {
  const updated = { ...(dashboardStore.selectedCertScores || {}) }
  if (isAllSubScoresChecked(cert)) {
    updated[cert] = ['__NONE__']
  } else {
    delete updated[cert]
  }
  dashboardStore.selectedCertScores = updated
}

// Count of checked options for button badge
const getCheckedCount = (selectedList: string[], allOptions: string[]): number => {
  if (selectedList.includes('__NONE__')) return 0
  if (selectedList.length === 0) return allOptions.length
  return selectedList.filter(o => allOptions.includes(o)).length
}

// Whether dimension is actively filtering
const isTariffFiltered = computed(() => dashboardStore.selectedTariffs.length > 0)
const isLevelFiltered = computed(() => dashboardStore.selectedLevels.length > 0)
const isGroupFiltered = computed(() => dashboardStore.selectedGroups.length > 0)
const isCertFiltered = computed(() => (
  dashboardStore.selectedCerts.length > 0 ||
  Object.keys(dashboardStore.selectedCertScores || {}).length > 0
))
const isTagFiltered = computed(() => dashboardStore.selectedTags.length > 0)
const isCoordinatorFiltered = computed(() => (dashboardStore.selectedCoordinators || []).length > 0)

const hasAnyQuickFilter = computed(() => (
  isTariffFiltered.value ||
  isLevelFiltered.value ||
  isGroupFiltered.value ||
  isCertFiltered.value ||
  isTagFiltered.value ||
  isCoordinatorFiltered.value
))

const resetQuickFilters = () => {
  dashboardStore.selectedTariffs = []
  dashboardStore.selectedLevels = []
  dashboardStore.selectedGroups = []
  dashboardStore.selectedCerts = []
  dashboardStore.selectedCertScores = {}
  dashboardStore.selectedScores = []
  dashboardStore.selectedTags = []
  dashboardStore.selectedCoordinators = []
}
</script>

<template>
  <div ref="dropdownContainerRef" class="flex-1 flex items-center justify-center min-w-0 px-1 overflow-visible relative z-30">
    <div class="flex items-center gap-1 sm:gap-1.5 py-1 max-w-full overflow-visible">

      <!-- 1. TARIFF DROPDOWN -->
      <div class="relative shrink-0" :class="openDropdown === 'tariff' ? 'z-50' : 'z-20'">
        <button
          type="button"
          @click.stop="toggleDropdown('tariff')"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] md:text-[11px] font-bold uppercase tracking-wider transition-all border select-none cursor-pointer h-7"
          :class="[
            isTariffFiltered
              ? 'bg-blue-50 dark:bg-blue-950/50 border-blue-400 dark:border-blue-600 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/20'
              : 'bg-white dark:bg-[#141619] border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-850',
            openDropdown === 'tariff' ? 'ring-2 ring-blue-500/30' : ''
          ]"
        >
          <span>TARIFF</span>
          <span
            v-if="isTariffFiltered"
            class="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-blue-600 text-white leading-none"
          >
            {{ getCheckedCount(dashboardStore.selectedTariffs, tariffRawOptions) }}
          </span>
          <ChevronDown class="size-3 text-zinc-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'tariff' }" />
        </button>

        <!-- Popover -->
        <Transition
          enter-active-class="transition duration-100 ease-out"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition duration-75 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="openDropdown === 'tariff'"
            class="absolute left-0 top-full mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl z-50 text-xs flex flex-col overflow-hidden animate-page-in"
          >
            <div class="p-2 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/70 dark:bg-zinc-900/60">
              <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Tariff Filter</span>
              <label class="flex items-center gap-1.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="isAllChecked(dashboardStore.selectedTariffs, tariffRawOptions)"
                  @change="dashboardStore.selectedTariffs = toggleSelectAll(dashboardStore.selectedTariffs, tariffRawOptions)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span>Select All</span>
              </label>
            </div>

            <div v-if="tariffRawOptions.length > 5" class="p-1.5 border-b border-zinc-100 dark:border-zinc-800">
              <div class="relative">
                <Search class="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-zinc-400" />
                <input
                  v-model="searchQueries.tariff"
                  type="text"
                  placeholder="Search tariff..."
                  class="w-full pl-6 pr-2 py-1 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500"
                  @click.stop
                />
              </div>
            </div>

            <div class="overflow-y-auto max-h-56 p-1 space-y-0.5 scrollbar-thin">
              <label
                v-for="opt in filteredTariffs"
                :key="opt"
                class="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800/70 cursor-pointer transition-colors select-none"
                @click.stop
              >
                <div class="flex items-center gap-2 min-w-0">
                  <input
                    type="checkbox"
                    :checked="isOptionChecked(opt, dashboardStore.selectedTariffs)"
                    @change="dashboardStore.selectedTariffs = toggleOption(opt, dashboardStore.selectedTariffs, tariffRawOptions)"
                    class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">{{ getTariffLabel(opt) }}</span>
                </div>
              </label>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 2. LEVEL DROPDOWN -->
      <div class="relative shrink-0" :class="openDropdown === 'level' ? 'z-50' : 'z-20'">
        <button
          type="button"
          @click.stop="toggleDropdown('level')"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] md:text-[11px] font-bold uppercase tracking-wider transition-all border select-none cursor-pointer h-7"
          :class="[
            isLevelFiltered
              ? 'bg-blue-50 dark:bg-blue-950/50 border-blue-400 dark:border-blue-600 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/20'
              : 'bg-white dark:bg-[#141619] border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-850',
            openDropdown === 'level' ? 'ring-2 ring-blue-500/30' : ''
          ]"
        >
          <span>LEVEL</span>
          <span
            v-if="isLevelFiltered"
            class="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-blue-600 text-white leading-none"
          >
            {{ getCheckedCount(dashboardStore.selectedLevels, levelRawOptions) }}
          </span>
          <ChevronDown class="size-3 text-zinc-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'level' }" />
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
            v-if="openDropdown === 'level'"
            class="absolute left-0 top-full mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl z-50 text-xs flex flex-col overflow-hidden animate-page-in"
          >
            <div class="p-2 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/70 dark:bg-zinc-900/60">
              <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Level Filter</span>
              <label class="flex items-center gap-1.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="isAllChecked(dashboardStore.selectedLevels, levelRawOptions)"
                  @change="dashboardStore.selectedLevels = toggleSelectAll(dashboardStore.selectedLevels, levelRawOptions)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span>Select All</span>
              </label>
            </div>

            <div v-if="levelRawOptions.length > 6" class="p-1.5 border-b border-zinc-100 dark:border-zinc-800">
              <div class="relative">
                <Search class="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-zinc-400" />
                <input
                  v-model="searchQueries.level"
                  type="text"
                  placeholder="Search level..."
                  class="w-full pl-6 pr-2 py-1 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500"
                  @click.stop
                />
              </div>
            </div>

            <div class="overflow-y-auto max-h-56 p-1 space-y-0.5 scrollbar-thin">
              <label
                v-for="opt in filteredLevels"
                :key="opt"
                class="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800/70 cursor-pointer transition-colors select-none"
                @click.stop
              >
                <div class="flex items-center gap-2 min-w-0">
                  <input
                    type="checkbox"
                    :checked="isOptionChecked(opt, dashboardStore.selectedLevels)"
                    @change="dashboardStore.selectedLevels = toggleOption(opt, dashboardStore.selectedLevels, levelRawOptions)"
                    class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">{{ getLevelLabel(opt) }}</span>
                </div>
              </label>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 3. GROUP DROPDOWN -->
      <div class="relative shrink-0" :class="openDropdown === 'group' ? 'z-50' : 'z-20'">
        <button
          type="button"
          @click.stop="toggleDropdown('group')"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] md:text-[11px] font-bold uppercase tracking-wider transition-all border select-none cursor-pointer h-7"
          :class="[
            isGroupFiltered
              ? 'bg-blue-50 dark:bg-blue-950/50 border-blue-400 dark:border-blue-600 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/20'
              : 'bg-white dark:bg-[#141619] border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-850',
            openDropdown === 'group' ? 'ring-2 ring-blue-500/30' : ''
          ]"
        >
          <span>GROUP</span>
          <span
            v-if="isGroupFiltered"
            class="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-blue-600 text-white leading-none"
          >
            {{ getCheckedCount(dashboardStore.selectedGroups, groupRawOptions) }}
          </span>
          <ChevronDown class="size-3 text-zinc-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'group' }" />
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
            v-if="openDropdown === 'group'"
            class="absolute left-0 top-full mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl z-50 text-xs flex flex-col overflow-hidden animate-page-in"
          >
            <div class="p-2 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/70 dark:bg-zinc-900/60">
              <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Group Filter</span>
              <label class="flex items-center gap-1.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="isAllChecked(dashboardStore.selectedGroups, groupRawOptions)"
                  @change="dashboardStore.selectedGroups = toggleSelectAll(dashboardStore.selectedGroups, groupRawOptions)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span>Select All</span>
              </label>
            </div>

            <div class="p-1.5 border-b border-zinc-100 dark:border-zinc-800">
              <div class="relative">
                <Search class="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-zinc-400" />
                <input
                  v-model="searchQueries.group"
                  type="text"
                  placeholder="Search group..."
                  class="w-full pl-6 pr-2 py-1 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500"
                  @click.stop
                />
              </div>
            </div>

            <div class="overflow-y-auto max-h-56 p-1 space-y-0.5 scrollbar-thin">
              <label
                v-for="opt in filteredGroups"
                :key="opt"
                class="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800/70 cursor-pointer transition-colors select-none"
                @click.stop
              >
                <div class="flex items-center gap-2 min-w-0">
                  <input
                    type="checkbox"
                    :checked="isOptionChecked(opt, dashboardStore.selectedGroups)"
                    @change="dashboardStore.selectedGroups = toggleOption(opt, dashboardStore.selectedGroups, groupRawOptions)"
                    class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">{{ getGroupLabel(opt) }}</span>
                </div>
              </label>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 4. CERTIFICATE DROPDOWN (WITH MINI SIDE MODAL MENU) -->
      <div class="relative shrink-0" :class="openDropdown === 'cert' ? 'z-50' : 'z-20'">
        <button
          type="button"
          @click.stop="toggleDropdown('cert')"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] md:text-[11px] font-bold uppercase tracking-wider transition-all border select-none cursor-pointer h-7"
          :class="[
            isCertFiltered
              ? 'bg-blue-50 dark:bg-blue-950/50 border-blue-400 dark:border-blue-600 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/20'
              : 'bg-white dark:bg-[#141619] border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-850',
            openDropdown === 'cert' ? 'ring-2 ring-blue-500/30' : ''
          ]"
        >
          <span>CERTIFICATE</span>
          <span
            v-if="isCertFiltered"
            class="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-blue-600 text-white leading-none"
          >
            {{ getCheckedCount(dashboardStore.selectedCerts, certRawOptions) }}
          </span>
          <ChevronDown class="size-3 text-zinc-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'cert' }" />
        </button>

        <!-- Popover -->
        <Transition
          enter-active-class="transition duration-100 ease-out"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition duration-75 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="openDropdown === 'cert'"
            class="absolute left-0 top-full mt-1.5 w-64 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl z-50 text-xs flex flex-col overflow-visible animate-page-in"
          >
            <div class="p-2 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/70 dark:bg-zinc-900/60 rounded-t-xl">
              <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Certificate Filter</span>
              <label class="flex items-center gap-1.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="isAllChecked(dashboardStore.selectedCerts, certRawOptions)"
                  @change="dashboardStore.selectedCerts = toggleSelectAll(dashboardStore.selectedCerts, certRawOptions)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span>Select All</span>
              </label>
            </div>

            <div class="p-1 space-y-0.5">
              <div
                v-for="opt in filteredCerts"
                :key="opt"
                class="relative"
                @mouseenter="CERT_SUB_SCORES[opt] ? openSubMenu = opt : null"
              >
                <div
                  class="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800/70 cursor-pointer transition-colors select-none"
                  :class="[openSubMenu === opt ? 'bg-zinc-100 dark:bg-zinc-800' : '']"
                  @click.stop
                >
                  <label class="flex items-center gap-2 min-w-0 cursor-pointer flex-1">
                    <input
                      type="checkbox"
                      :checked="isOptionChecked(opt, dashboardStore.selectedCerts)"
                      @change="dashboardStore.selectedCerts = toggleOption(opt, dashboardStore.selectedCerts, certRawOptions)"
                      class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                    />
                    <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">{{ getCertLabel(opt) }}</span>
                  </label>

                  <!-- Right side: Chevron & Sub-score indicator for TOPIK / IELTS / CEFR -->
                  <div v-if="CERT_SUB_SCORES[opt]" class="flex items-center gap-1.5 ml-2">
                    <span
                      v-if="dashboardStore.selectedCertScores?.[opt]?.length"
                      class="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300"
                    >
                      {{ dashboardStore.selectedCertScores[opt].includes('__NONE__') ? '0' : dashboardStore.selectedCertScores[opt].length }}/{{ CERT_SUB_SCORES[opt].length }}
                    </span>
                    <button
                      type="button"
                      @click.stop="openSubMenu = openSubMenu === opt ? null : opt"
                      class="p-0.5 rounded hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 cursor-pointer"
                      :title="`${opt} score filter`"
                    >
                      <ChevronRight class="size-3.5" />
                    </button>
                  </div>
                </div>

                <!-- Mini Side Modal Menu for Scores (TOPIK / IELTS / CEFR) -->
                <div
                  v-if="CERT_SUB_SCORES[opt] && openSubMenu === opt"
                  class="absolute left-full top-0 ml-1.5 w-44 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl p-2 z-[60] text-xs animate-page-in"
                  @click.stop
                >
                  <div class="flex items-center justify-between pb-1.5 mb-1.5 border-b border-zinc-100 dark:border-zinc-800">
                    <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">{{ opt }} Scores</span>
                    <label class="flex items-center gap-1 text-[10px] font-semibold text-blue-600 dark:text-blue-400 cursor-pointer">
                      <input
                        type="checkbox"
                        :checked="isAllSubScoresChecked(opt)"
                        @change="toggleAllSubScores(opt)"
                        class="h-3 w-3 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      />
                      <span>All</span>
                    </label>
                  </div>

                  <div class="space-y-0.5 max-h-52 overflow-y-auto scrollbar-thin">
                    <label
                      v-for="sc in CERT_SUB_SCORES[opt]"
                      :key="sc"
                      class="flex items-center justify-between px-2 py-1 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-800/80 cursor-pointer transition-colors"
                      @click.stop
                    >
                      <div class="flex items-center gap-2">
                        <input
                          type="checkbox"
                          :checked="isSubScoreChecked(opt, sc)"
                          @change="toggleSubScore(opt, sc)"
                          class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                        />
                        <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
                          {{ sc === 'EXPECTED' ? 'Expected' : (opt === 'TOPIK' ? `Level ${sc}` : sc) }}
                        </span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 5. TAGS DROPDOWN -->
      <div class="relative shrink-0" :class="openDropdown === 'tag' ? 'z-50' : 'z-20'">
        <button
          type="button"
          @click.stop="toggleDropdown('tag')"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] md:text-[11px] font-bold uppercase tracking-wider transition-all border select-none cursor-pointer h-7"
          :class="[
            isTagFiltered
              ? 'bg-blue-50 dark:bg-blue-950/50 border-blue-400 dark:border-blue-600 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/20'
              : 'bg-white dark:bg-[#141619] border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-850',
            openDropdown === 'tag' ? 'ring-2 ring-blue-500/30' : ''
          ]"
        >
          <span>TAGS</span>
          <span
            v-if="isTagFiltered"
            class="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-blue-600 text-white leading-none"
          >
            {{ getCheckedCount(dashboardStore.selectedTags, tagRawOptions) }}
          </span>
          <ChevronDown class="size-3 text-zinc-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'tag' }" />
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
            v-if="openDropdown === 'tag'"
            class="absolute left-0 top-full mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl z-50 text-xs flex flex-col overflow-hidden animate-page-in"
          >
            <div class="p-2 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/70 dark:bg-zinc-900/60">
              <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Tags Filter</span>
              <label class="flex items-center gap-1.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="isAllChecked(dashboardStore.selectedTags, tagRawOptions)"
                  @change="dashboardStore.selectedTags = toggleSelectAll(dashboardStore.selectedTags, tagRawOptions)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span>Select All</span>
              </label>
            </div>

            <div v-if="tagRawOptions.length > 5" class="p-1.5 border-b border-zinc-100 dark:border-zinc-800">
              <div class="relative">
                <Search class="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-zinc-400" />
                <input
                  v-model="searchQueries.tag"
                  type="text"
                  placeholder="Search tags..."
                  class="w-full pl-6 pr-2 py-1 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500"
                  @click.stop
                />
              </div>
            </div>

            <div class="overflow-y-auto max-h-56 p-1 space-y-0.5 scrollbar-thin">
              <label
                v-for="opt in filteredTags"
                :key="opt"
                class="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800/70 cursor-pointer transition-colors select-none"
                @click.stop
              >
                <div class="flex items-center gap-2 min-w-0">
                  <input
                    type="checkbox"
                    :checked="isOptionChecked(opt, dashboardStore.selectedTags)"
                    @change="dashboardStore.selectedTags = toggleOption(opt, dashboardStore.selectedTags, tagRawOptions)"
                    class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">{{ getTagLabel(opt) }}</span>
                </div>
              </label>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 6. KORDINATOR DROPDOWN -->
      <div class="relative shrink-0" :class="openDropdown === 'coordinator' ? 'z-50' : 'z-20'">
        <button
          type="button"
          @click.stop="toggleDropdown('coordinator')"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] md:text-[11px] font-bold uppercase tracking-wider transition-all border select-none cursor-pointer h-7"
          :class="[
            isCoordinatorFiltered
              ? 'bg-blue-50 dark:bg-blue-950/50 border-blue-400 dark:border-blue-600 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/20'
              : 'bg-white dark:bg-[#141619] border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-850',
            openDropdown === 'coordinator' ? 'ring-2 ring-blue-500/30' : ''
          ]"
        >
          <span>KORDINATOR</span>
          <span
            v-if="isCoordinatorFiltered"
            class="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-blue-600 text-white leading-none"
          >
            {{ getCheckedCount(dashboardStore.selectedCoordinators, coordinatorRawOptions) }}
          </span>
          <ChevronDown class="size-3 text-zinc-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'coordinator' }" />
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
            v-if="openDropdown === 'coordinator'"
            class="absolute left-0 sm:right-0 sm:left-auto top-full mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl z-50 text-xs flex flex-col overflow-hidden animate-page-in"
          >
            <div class="p-2 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/70 dark:bg-zinc-900/60">
              <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Kordinator Filter</span>
              <label class="flex items-center gap-1.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="isAllChecked(dashboardStore.selectedCoordinators, coordinatorRawOptions)"
                  @change="dashboardStore.selectedCoordinators = toggleSelectAll(dashboardStore.selectedCoordinators, coordinatorRawOptions)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span>Select All</span>
              </label>
            </div>

            <div v-if="coordinatorRawOptions.length > 5" class="p-1.5 border-b border-zinc-100 dark:border-zinc-800">
              <div class="relative">
                <Search class="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-zinc-400" />
                <input
                  v-model="searchQueries.coordinator"
                  type="text"
                  placeholder="Search kordinator..."
                  class="w-full pl-6 pr-2 py-1 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500"
                  @click.stop
                />
              </div>
            </div>

            <div class="overflow-y-auto max-h-56 p-1 space-y-0.5 scrollbar-thin">
              <label
                v-for="opt in filteredCoordinators"
                :key="opt"
                class="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800/70 cursor-pointer transition-colors select-none"
                @click.stop
              >
                <div class="flex items-center gap-2 min-w-0">
                  <input
                    type="checkbox"
                    :checked="isOptionChecked(opt, dashboardStore.selectedCoordinators)"
                    @change="dashboardStore.selectedCoordinators = toggleOption(opt, dashboardStore.selectedCoordinators, coordinatorRawOptions)"
                    class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">{{ getCoordinatorLabel(opt) }}</span>
                </div>
              </label>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Quick Reset Button (Visible when any quick dropdown is actively filtering) -->
      <button
        v-if="hasAnyQuickFilter"
        type="button"
        @click="resetQuickFilters"
        class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer select-none h-7 shrink-0 ml-0.5"
        title="Reset quick filters to all checked"
      >
        <RotateCcw class="size-3" />
        <span class="hidden xl:inline">Reset</span>
      </button>

    </div>
  </div>
</template>
