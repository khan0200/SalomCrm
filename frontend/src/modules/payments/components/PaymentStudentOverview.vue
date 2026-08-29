<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Student } from '@/types'
import {
  Search, Plus, LayoutGrid, Table as TableIcon,
  ChevronDown, ChevronUp, UserX, FileSpreadsheet
} from 'lucide-vue-next'

const props = defineProps<{
  students: Student[]
  totalFilteredCount: number
  isLoading: boolean
  options?: any
  tariffOptions?: string[]
  searchQuery: string
  selectedStatuses: string[]
  selectedTariffs: string[]
  selectedBalances: string[]
  selectedGroups: string[]
  viewMode: 'grid' | 'table'
  sortOrder: 'asc' | 'desc'
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'toggle-status', val: string): void
  (e: 'toggle-all-statuses'): void
  (e: 'toggle-tariff', val: string): void
  (e: 'toggle-all-tariffs'): void
  (e: 'toggle-balance', val: string): void
  (e: 'toggle-all-balances'): void
  (e: 'toggle-group', val: string): void
  (e: 'toggle-all-groups'): void
  (e: 'update:viewMode', val: 'grid' | 'table'): void
  (e: 'toggle-sort'): void
  (e: 'open-add-payment', studentId?: string): void
  (e: 'export-excel'): void
}>()

const isStatusOpen = ref(false)
const isTariffOpen = ref(false)
const isBalanceOpen = ref(false)
const isGroupOpen = ref(false)

const statusRef = ref<HTMLElement | null>(null)
const tariffRef = ref<HTMLElement | null>(null)
const balanceRef = ref<HTMLElement | null>(null)
const groupRef = ref<HTMLElement | null>(null)

const STATUS_FILTER_OPTIONS = ['Active', 'Archive']

const availableTariffs = computed<string[]>(() => {
  if (props.tariffOptions && props.tariffOptions.length > 0) {
    return props.tariffOptions
  }
  const custom = (props.options?.tariffs || []).map((t: any) => typeof t === 'string' ? t : (t?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  props.students.forEach(s => { if (s.tariff) set.add(s.tariff) })
  const list = Array.from(set).filter(t => t !== 'No Tariff' && t !== 'NO_TARIFF').sort()
  return [...list, 'No Tariff']
})

const BALANCE_FILTER_OPTIONS = [
  'Balance < 0 (Debt)',
  'Balance = 0 (Fully Paid)',
  'Balance > 500,000',
  'Balance > 1,000,000',
  'Balance > 2,000,000',
  'Balance > 5,000,000',
  'Balance > 10,000,000'
]

const ALL_GROUP_OPTIONS = computed(() => {
  const custom = (props.options?.groups || []).map((g: any) => typeof g === 'string' ? g : (g?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  props.students.forEach(s => { if (s.student_group) set.add(s.student_group) })
  const unique = Array.from(set).filter(Boolean).sort()
  return ['No Group', ...unique]
})

function formatAmount(val: number | string | null | undefined) {
  if (val === null || val === undefined) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('uz-UZ').format(Math.round(num || 0))
}

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as Node
  if (statusRef.value && !statusRef.value.contains(target)) isStatusOpen.value = false
  if (tariffRef.value && !tariffRef.value.contains(target)) isTariffOpen.value = false
  if (balanceRef.value && !balanceRef.value.contains(target)) isBalanceOpen.value = false
  if (groupRef.value && !groupRef.value.contains(target)) isGroupOpen.value = false
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})
</script>

<template>
  <div class="flex flex-col gap-4 select-none text-xs">
    <!-- ── Filter Bar matching UniApp2 ────────────────────────────────── -->
    <div class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-3 shadow-2xs flex flex-wrap gap-2.5 items-center">
      <!-- Search Input -->
      <div class="relative flex-1 min-w-[200px]">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400 pointer-events-none" />
        <input
          type="text"
          :value="searchQuery"
          @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
          placeholder="Search by name or ID..."
          class="w-full pl-9 pr-4 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>

      <!-- 1. Status Filter Dropdown -->
      <div class="relative" ref="statusRef">
        <button
          type="button"
          @click="isStatusOpen = !isStatusOpen; isTariffOpen = false; isBalanceOpen = false; isGroupOpen = false"
          class="px-3.5 py-2 text-xs border rounded-full text-zinc-700 dark:text-zinc-200 cursor-pointer flex items-center justify-between gap-2 min-w-[125px] select-none transition-all shadow-2xs font-semibold"
          :class="isStatusOpen
            ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
            : 'border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 hover:border-blue-400'"
        >
          <span class="truncate max-w-[130px]">
            {{ selectedStatuses.length === 0 || selectedStatuses.length === STATUS_FILTER_OPTIONS.length
              ? 'All Statuses'
              : selectedStatuses.join(', ') }}
          </span>
          <ChevronDown
            class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200"
            :class="isStatusOpen ? 'rotate-180 text-blue-600' : ''"
          />
        </button>

        <div
          v-if="isStatusOpen"
          class="absolute left-0 mt-1.5 w-44 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 overflow-y-auto"
        >
          <div
            @click="emit('toggle-all-statuses')"
            class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200"
          >
            <input
              type="checkbox"
              :checked="selectedStatuses.length === STATUS_FILTER_OPTIONS.length"
              class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span>Select All</span>
          </div>
          <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />
          <div
            v-for="opt in STATUS_FILTER_OPTIONS"
            :key="opt"
            @click="emit('toggle-status', opt)"
            class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-medium text-zinc-700 dark:text-zinc-300"
          >
            <input
              type="checkbox"
              :checked="selectedStatuses.includes(opt)"
              class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span>{{ opt }}</span>
          </div>
        </div>
      </div>

      <!-- 2. Tariff Filter Dropdown -->
      <div class="relative" ref="tariffRef">
        <button
          type="button"
          @click="isTariffOpen = !isTariffOpen; isStatusOpen = false; isBalanceOpen = false; isGroupOpen = false"
          class="px-3.5 py-2 text-xs border rounded-full text-zinc-700 dark:text-zinc-200 cursor-pointer flex items-center justify-between gap-2 min-w-[130px] select-none transition-all shadow-2xs font-semibold"
          :class="isTariffOpen
            ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
            : 'border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 hover:border-blue-400'"
        >
          <span class="truncate max-w-[140px]">
            {{ selectedTariffs.length === 0 || selectedTariffs.length === availableTariffs.length
              ? 'All Tariffs'
              : selectedTariffs.join(', ') }}
          </span>
          <ChevronDown
            class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200"
            :class="isTariffOpen ? 'rotate-180 text-blue-600' : ''"
          />
        </button>

        <div
          v-if="isTariffOpen"
          class="absolute left-0 mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 overflow-y-auto"
        >
          <div
            @click="emit('toggle-all-tariffs')"
            class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200"
          >
            <input
              type="checkbox"
              :checked="selectedTariffs.length === availableTariffs.length"
              class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span>Select All</span>
          </div>
          <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />
          <div
            v-for="opt in availableTariffs"
            :key="opt"
            @click="emit('toggle-tariff', opt)"
            class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-medium text-zinc-700 dark:text-zinc-300"
          >
            <input
              type="checkbox"
              :checked="selectedTariffs.includes(opt)"
              class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span class="truncate">{{ opt }}</span>
          </div>
        </div>
      </div>

      <!-- 3. Balance Filter Dropdown -->
      <div class="relative" ref="balanceRef">
        <button
          type="button"
          @click="isBalanceOpen = !isBalanceOpen; isStatusOpen = false; isTariffOpen = false; isGroupOpen = false"
          class="px-3.5 py-2 text-xs border rounded-full text-zinc-700 dark:text-zinc-200 cursor-pointer flex items-center justify-between gap-2 min-w-[130px] select-none transition-all shadow-2xs font-semibold"
          :class="isBalanceOpen
            ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
            : 'border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 hover:border-blue-400'"
        >
          <span class="truncate max-w-[140px]">
            {{ selectedBalances.length === 0 || selectedBalances.length === BALANCE_FILTER_OPTIONS.length
              ? 'All Balances'
              : selectedBalances.join(', ') }}
          </span>
          <ChevronDown
            class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200"
            :class="isBalanceOpen ? 'rotate-180 text-blue-600' : ''"
          />
        </button>

        <div
          v-if="isBalanceOpen"
          class="absolute left-0 mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 overflow-y-auto"
        >
          <div
            @click="emit('toggle-all-balances')"
            class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200"
          >
            <input
              type="checkbox"
              :checked="selectedBalances.length === BALANCE_FILTER_OPTIONS.length"
              class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span>Select All</span>
          </div>
          <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />
          <div
            v-for="opt in BALANCE_FILTER_OPTIONS"
            :key="opt"
            @click="emit('toggle-balance', opt)"
            class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-medium text-zinc-700 dark:text-zinc-300"
          >
            <input
              type="checkbox"
              :checked="selectedBalances.includes(opt)"
              class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span class="truncate">{{ opt }}</span>
          </div>
        </div>
      </div>

      <!-- 4. Group Filter Dropdown -->
      <div class="relative" ref="groupRef">
        <button
          type="button"
          @click="isGroupOpen = !isGroupOpen; isStatusOpen = false; isTariffOpen = false; isBalanceOpen = false"
          class="px-3.5 py-2 text-xs border rounded-full text-zinc-700 dark:text-zinc-200 cursor-pointer flex items-center justify-between gap-2 min-w-[130px] select-none transition-all shadow-2xs font-semibold"
          :class="isGroupOpen
            ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
            : 'border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 hover:border-blue-400'"
        >
          <span class="truncate max-w-[140px]">
            {{ selectedGroups.length === 0 || selectedGroups.length === ALL_GROUP_OPTIONS.length
              ? 'All Groups'
              : selectedGroups.join(', ') }}
          </span>
          <ChevronDown
            class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200"
            :class="isGroupOpen ? 'rotate-180 text-blue-600' : ''"
          />
        </button>

        <div
          v-if="isGroupOpen"
          class="absolute left-0 mt-1.5 w-56 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 overflow-y-auto"
        >
          <div
            @click="emit('toggle-all-groups')"
            class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200"
          >
            <input
              type="checkbox"
              :checked="selectedGroups.length === ALL_GROUP_OPTIONS.length"
              class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span>Select All</span>
          </div>
          <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />
          <div
            v-for="opt in ALL_GROUP_OPTIONS"
            :key="opt"
            @click="emit('toggle-group', opt)"
            class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-medium text-zinc-700 dark:text-zinc-300"
          >
            <input
              type="checkbox"
              :checked="selectedGroups.includes(opt)"
              class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span class="truncate">{{ opt }}</span>
          </div>
        </div>
      </div>

      <!-- Actions: Export Excel + View Mode Switcher -->
      <div class="flex items-center gap-2 ml-auto">
        <button
          type="button"
          @click="emit('export-excel')"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg border border-emerald-300 dark:border-emerald-700/60 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-all cursor-pointer shadow-2xs"
          title="Download Filtered Students Excel"
        >
          <FileSpreadsheet class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <span>Export Excel</span>
        </button>

        <!-- View Mode Switcher -->
        <div class="flex items-center gap-1 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-100 dark:bg-zinc-850 p-1">
          <button
            type="button"
            @click="emit('update:viewMode', 'grid')"
            class="p-1.5 rounded-md transition-all cursor-pointer"
            :class="viewMode === 'grid'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100'"
            title="Grid View (Cards)"
          >
            <LayoutGrid class="h-4 w-4" />
          </button>
          <button
            type="button"
            @click="emit('update:viewMode', 'table')"
            class="p-1.5 rounded-md transition-all cursor-pointer"
            :class="viewMode === 'table'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100'"
            title="Table View"
          >
            <TableIcon class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Student Count -->
    <div class="text-xs text-zinc-500 dark:text-zinc-400 italic px-1">
      <span v-if="isLoading" class="inline-block h-3 w-24 rounded bg-zinc-200 dark:bg-zinc-800 animate-pulse align-middle" />
      <template v-else>{{ totalFilteredCount }} students</template>
    </div>

    <!-- ── Loading Skeleton: Grid View ─────────────────────────────────────── -->
    <div v-if="isLoading && viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <div
        v-for="i in 9"
        :key="i"
        class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] p-4 shadow-sm animate-pulse"
      >
        <div class="flex items-start justify-between gap-2 mb-3">
          <div class="h-3.5 w-1/2 rounded bg-zinc-200 dark:bg-zinc-800" />
          <div class="h-3 w-12 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
        <div class="h-3 w-1/3 rounded bg-zinc-100 dark:bg-zinc-800/70 mb-4" />
        <div class="flex items-center gap-2 mb-3">
          <div class="h-5 w-20 rounded bg-zinc-100 dark:bg-zinc-800/70" />
          <div class="h-5 w-16 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
        <div class="pt-3 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between">
          <div class="h-3 w-24 rounded bg-zinc-100 dark:bg-zinc-800/70" />
          <div class="h-3 w-14 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
      </div>
    </div>

    <!-- ── Loading Skeleton: Table View ────────────────────────────────────── -->
    <div v-else-if="isLoading" class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60 text-[12px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300 select-none">
              <th class="px-5 py-3.5 w-[30%]">Student / Full Name</th>
              <th class="px-5 py-3.5 w-[14%]">Group</th>
              <th class="px-5 py-3.5 w-[22%]">Tariff</th>
              <th class="px-5 py-3.5 w-[18%]">Balance</th>
              <th class="px-5 py-3.5 w-[12%]">Discount</th>
              <th class="px-5 py-3.5 text-center w-24">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
            <tr v-for="i in 12" :key="i" class="animate-pulse">
              <td class="px-5 py-3.5">
                <div class="h-3.5 w-3/5 rounded bg-zinc-200 dark:bg-zinc-800 mb-1.5" />
                <div class="h-2.5 w-1/3 rounded bg-zinc-100 dark:bg-zinc-800/70" />
              </td>
              <td class="px-5 py-3.5"><div class="h-3 w-16 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-5 py-3.5"><div class="h-3 w-24 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-5 py-3.5"><div class="h-3 w-20 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-5 py-3.5"><div class="h-3 w-14 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-5 py-3.5">
                <div class="flex items-center justify-center gap-1.5">
                  <div class="h-6 w-6 rounded-md bg-zinc-100 dark:bg-zinc-800/70" />
                  <div class="h-6 w-6 rounded-md bg-zinc-100 dark:bg-zinc-800/70" />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── 1. Grid View (UniApp2 Student Cards 1-to-1) ────────────────────── -->
    <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <button
        v-for="student in students"
        :key="student.id"
        type="button"
        @click="emit('open-add-payment', student.id)"
        class="text-left rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] p-4 shadow-sm hover:bg-zinc-50 dark:hover:bg-zinc-850/80 transition-all cursor-pointer w-full hover:-translate-y-0.5 group"
      >
        <!-- Card Header: Full Name + Archive Badge -->
        <div class="flex items-center justify-between gap-2">
          <div class="font-bold text-[17px] uppercase text-zinc-900 dark:text-zinc-100 truncate tracking-wide group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {{ student.full_name }}
          </div>
          <span
            v-if="student.is_deleted"
            class="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shrink-0"
          >
            Archive
          </span>
        </div>

        <!-- Badges Row -->
        <div class="flex flex-wrap gap-1.5 mt-3">
          <!-- Blue ID Badge -->
          <span class="text-[13px] font-bold px-2 py-1 rounded-[6px] bg-[#0066cc] text-white font-mono shadow-2xs">
            {{ student.id }}
          </span>

          <!-- Green Tariff Badge with Certificate Suffix -->
          <span
            v-if="student.tariff"
            class="text-[13px] font-bold px-2.5 py-1 rounded-[6px] bg-[#10b981] text-white uppercase shadow-2xs"
          >
            {{ student.tariff }}
            <template v-if="student.tariff === 'E-VISA'">
              {{ (student.language_certificate && student.language_certificate !== 'NO CERTIFICATE')
                ? ' (TIL SERTIFIKATLI)'
                : ' (TIL SERTIFIKATISIZ)' }}
            </template>
          </span>

          <!-- Balance Badge (Red if < 0 debt, Green if >= 0) -->
          <span
            class="text-[13px] font-bold px-2.5 py-1 rounded-[6px] text-white shadow-2xs font-mono"
            :class="(Number(student.balance) || 0) < 0 ? 'bg-[#ef4444]' : 'bg-[#10b981]'"
          >
            {{ (Number(student.balance) || 0) > 0 ? '+' : '' }}{{ formatAmount(student.balance) }}
          </span>

          <!-- Discount Badge (Pink #be185d if exists) -->
          <span
            v-if="student.discount !== null && student.discount !== undefined && Number(student.discount) > 0"
            class="text-[13px] font-bold px-2.5 py-1 rounded-[6px] bg-[#be185d] text-white font-mono shadow-2xs"
          >
            {{ formatAmount(student.discount) }}
          </span>
        </div>
      </button>
    </div>

    <!-- ── 2. Table View (UniApp2 Table 1-to-1) ────────────────────────────── -->
    <div v-else class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60 text-[12px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300 select-none">
              <!-- Student / Full Name (Sortable) -->
              <th
                @click="emit('toggle-sort')"
                class="px-5 py-3.5 cursor-pointer select-none hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors w-[30%]"
              >
                <span class="flex items-center gap-1.5 font-bold text-[12.5px] uppercase tracking-wider text-zinc-700 dark:text-zinc-200">
                  Student / Full Name
                  <ChevronDown v-if="sortOrder === 'asc'" class="h-3.5 w-3.5 text-blue-600" />
                  <ChevronUp v-else class="h-3.5 w-3.5 text-blue-600" />
                </span>
              </th>
              <th class="px-5 py-3.5 w-[14%]">Group</th>
              <th class="px-5 py-3.5 w-[22%]">Tariff</th>
              <th class="px-5 py-3.5 w-[18%]">Balance</th>
              <th class="px-5 py-3.5 w-[12%]">Discount</th>
              <th class="px-5 py-3.5 text-center w-24">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800 text-[13.5px]">
            <tr
              v-for="student in students"
              :key="student.id"
              class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors text-zinc-800 dark:text-zinc-200"
            >
              <!-- Student: Full Name on top, ID below -->
              <td class="px-5 py-3">
                <div class="flex flex-col gap-0.5">
                  <div class="flex items-center gap-2">
                    <span class="font-bold uppercase tracking-wide text-zinc-900 dark:text-zinc-100 truncate">
                      {{ student.full_name }}
                    </span>
                    <span
                      v-if="student.is_deleted"
                      class="px-1.5 py-0.5 rounded text-[9.5px] font-bold tracking-wider uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shrink-0"
                    >
                      Archive
                    </span>
                  </div>
                  <div class="flex items-center gap-1">
                    <span class="font-mono text-[11px] font-bold text-[#0066cc] dark:text-blue-400 tracking-wider">
                      {{ student.id }}
                    </span>
                  </div>
                </div>
              </td>

              <!-- Group -->
              <td class="px-5 py-3.5 text-[13.5px] font-medium text-zinc-500 dark:text-zinc-400 uppercase">
                {{ student.student_group || '—' }}
              </td>

              <!-- Tariff -->
              <td class="px-5 py-3.5">
                <span
                  v-if="student.tariff"
                  class="inline-flex px-2 py-0.5 rounded-[4px] text-[12px] font-bold bg-[#10b981] text-white uppercase shadow-2xs"
                >
                  {{ student.tariff }}
                  <template v-if="student.tariff === 'E-VISA'">
                    {{ (student.language_certificate && student.language_certificate !== 'NO CERTIFICATE')
                      ? ' (TIL SERTIFIKATLI)'
                      : ' (TIL SERTIFIKATISIZ)' }}
                  </template>
                </span>
                <span v-else class="text-zinc-400">—</span>
              </td>

              <!-- Balance -->
              <td class="px-5 py-3.5 font-mono font-bold">
                <span
                  class="inline-flex px-2 py-0.5 rounded-[4px] text-[12.5px] font-bold text-white shadow-2xs"
                  :class="(Number(student.balance) || 0) < 0 ? 'bg-[#ef4444]' : 'bg-[#10b981]'"
                >
                  {{ (Number(student.balance) || 0) > 0 ? '+' : '' }}{{ formatAmount(student.balance) }} UZS
                </span>
              </td>

              <!-- Discount -->
              <td class="px-5 py-3.5">
                <span
                  v-if="student.discount !== null && student.discount !== undefined && Number(student.discount) > 0"
                  class="inline-flex px-2 py-0.5 rounded-[4px] text-[12px] font-bold font-mono bg-[#be185d] text-white shadow-2xs"
                >
                  {{ formatAmount(student.discount) }} UZS
                </span>
                <span v-else class="text-zinc-400">—</span>
              </td>

              <!-- Actions -->
              <td class="px-5 py-3.5 text-center">
                <button
                  type="button"
                  @click="emit('open-add-payment', student.id)"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-all cursor-pointer shadow-2xs"
                >
                  <Plus class="h-3.5 w-3.5 stroke-[2.5]" />
                  <span>Pay</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="students.length === 0 && !isLoading"
      class="rounded-xl border border-zinc-200 dark:border-zinc-800 border-dashed bg-white dark:bg-[#111315] py-16 px-6 text-center space-y-3"
    >
      <div class="w-14 h-14 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center mx-auto text-zinc-400">
        <UserX class="h-7 w-7" />
      </div>
      <p class="font-bold text-sm text-zinc-800 dark:text-zinc-200">No students found</p>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        {{ searchQuery
          ? 'No students match your search or filters. Try adjusting them.'
          : 'No students are available for this view yet.' }}
      </p>
    </div>
  </div>
</template>
