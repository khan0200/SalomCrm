<script setup lang="ts">
import { computed } from 'vue'
import type { Student } from '@/types'
import { useCurrency } from '@/composables/useCurrency'
import {
  Search, Plus, Minus, LayoutGrid, Table as TableIcon,
  Users, ChevronDown, UserX
} from 'lucide-vue-next'

const props = defineProps<{
  students: Student[]
  isLoading: boolean
  options?: any
  searchQuery: string
  selectedStatus: string
  selectedTariff: string
  selectedBalance: string
  selectedGroup: string
  viewMode: 'grid' | 'table'
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'update:selectedStatus', val: string): void
  (e: 'update:selectedTariff', val: string): void
  (e: 'update:selectedBalance', val: string): void
  (e: 'update:selectedGroup', val: string): void
  (e: 'update:viewMode', val: 'grid' | 'table'): void
  (e: 'open-add-payment', studentId: string): void
  (e: 'open-withdraw', studentId: string): void
}>()

const { formatCurrency } = useCurrency()

const STATUS_OPTIONS = [
  { label: 'All Statuses', value: 'all' },
  { label: 'Active', value: 'Active' },
  { label: 'Archive / Deleted', value: 'Archive' },
]

const TARIFF_OPTIONS = [
  'STANDART', 'PREMIUM', 'VISA PLUS', 'E-VISA', 'REGIONAL VISA', 'ZERO RISK', 'No Tariff'
]

const BALANCE_OPTIONS = [
  'Balance < 0 (Debt)',
  'Balance = 0 (Fully Paid)',
  'Balance > 500,000',
  'Balance > 1,000,000',
  'Balance > 2,000,000',
  'Balance > 5,000,000',
  'Balance > 10,000,000',
]

const groupList = computed(() => {
  const custom = (props.options?.groups || []).map((g: any) => typeof g === 'string' ? g : g.name)
  const defaults = ['2026 KUZ', '2027 BAHOR', '2026 BAHOR', '2025 KUZ', 'NO GROUP']
  return Array.from(new Set([...custom, ...defaults])).filter(Boolean)
})
</script>

<template>
  <div class="space-y-4 text-xs select-none">
    <!-- 1. Search & Filter Bar Card (Matching Reference Screenshot) -->
    <div class="p-2.5 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 shadow-2xs flex flex-wrap items-center gap-2.5">
      <!-- Search Input Box -->
      <div class="relative flex-1 min-w-[220px]">
        <Search class="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          :value="searchQuery"
          @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
          type="text"
          placeholder="Search by name or ID..."
          class="w-full pl-9 pr-3 py-2 rounded-xl bg-[#f8fafc] dark:bg-zinc-800/80 border border-zinc-200/80 dark:border-zinc-700/80 focus:border-blue-500 focus:bg-white dark:focus:bg-zinc-800 focus:ring-2 focus:ring-blue-500/20 outline-none text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 text-xs font-medium transition-all"
        />
      </div>

      <!-- Filter Dropdowns Row (Pill Style with Chevron) -->
      <div class="flex flex-wrap items-center gap-2">
        <!-- 1. All Statuses Dropdown -->
        <div class="relative">
          <select
            :value="selectedStatus"
            @change="emit('update:selectedStatus', ($event.target as HTMLSelectElement).value)"
            class="appearance-none bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600 rounded-xl pl-3.5 pr-8 py-2 text-xs font-semibold text-zinc-700 dark:text-zinc-200 outline-none cursor-pointer transition-colors shadow-2xs"
          >
            <option v-for="st in STATUS_OPTIONS" :key="st.value" :value="st.value">
              {{ st.label }}
            </option>
          </select>
          <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        <!-- 2. All Tariffs Dropdown -->
        <div class="relative">
          <select
            :value="selectedTariff"
            @change="emit('update:selectedTariff', ($event.target as HTMLSelectElement).value)"
            class="appearance-none bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600 rounded-xl pl-3.5 pr-8 py-2 text-xs font-semibold text-zinc-700 dark:text-zinc-200 outline-none cursor-pointer transition-colors shadow-2xs"
          >
            <option value="all">All Tariffs</option>
            <option v-for="t in TARIFF_OPTIONS" :key="t" :value="t">{{ t }}</option>
          </select>
          <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        <!-- 3. All Balances Dropdown -->
        <div class="relative">
          <select
            :value="selectedBalance"
            @change="emit('update:selectedBalance', ($event.target as HTMLSelectElement).value)"
            class="appearance-none bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600 rounded-xl pl-3.5 pr-8 py-2 text-xs font-semibold text-zinc-700 dark:text-zinc-200 outline-none cursor-pointer transition-colors shadow-2xs"
          >
            <option value="all">All Balances</option>
            <option v-for="b in BALANCE_OPTIONS" :key="b" :value="b">{{ b }}</option>
          </select>
          <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        <!-- 4. All Groups Dropdown -->
        <div class="relative">
          <select
            :value="selectedGroup"
            @change="emit('update:selectedGroup', ($event.target as HTMLSelectElement).value)"
            class="appearance-none bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600 rounded-xl pl-3.5 pr-8 py-2 text-xs font-semibold text-zinc-700 dark:text-zinc-200 outline-none cursor-pointer transition-colors shadow-2xs"
          >
            <option value="all">All Groups</option>
            <option v-for="g in groupList" :key="g" :value="g">{{ g }}</option>
          </select>
          <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        <!-- View Mode Grid / Table Switcher (Matching Screenshot) -->
        <div class="flex items-center gap-1 border border-zinc-200 dark:border-zinc-700 rounded-xl p-0.5 bg-zinc-50 dark:bg-zinc-800 shadow-2xs ml-auto">
          <button
            type="button"
            @click="emit('update:viewMode', 'grid')"
            class="p-1.5 rounded-lg font-bold transition-all cursor-pointer"
            :class="viewMode === 'grid'
              ? 'bg-[#1868db] text-white shadow-xs'
              : 'text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'"
            title="Grid View"
          >
            <LayoutGrid class="w-4 h-4" />
          </button>
          <button
            type="button"
            @click="emit('update:viewMode', 'table')"
            class="p-1.5 rounded-lg font-bold transition-all cursor-pointer"
            :class="viewMode === 'table'
              ? 'bg-[#1868db] text-white shadow-xs'
              : 'text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'"
            title="Table View"
          >
            <TableIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- 2. SKELETON LOADING STATE (When Loading) -->
    <div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
      <div
        v-for="i in 8"
        :key="`skel-${i}`"
        class="p-4 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs flex flex-col justify-between gap-3 animate-pulse"
      >
        <div>
          <div class="flex items-center justify-between mb-2">
            <div class="h-5 w-12 bg-zinc-200 dark:bg-zinc-800 rounded-md" />
            <div class="h-4 w-20 bg-zinc-100 dark:bg-zinc-800 rounded" />
          </div>
          <div class="h-5 w-3/4 bg-zinc-200 dark:bg-zinc-800 rounded mb-1.5" />
          <div class="h-3.5 w-1/3 bg-zinc-100 dark:bg-zinc-800 rounded" />
        </div>
        <div class="h-12 bg-zinc-100 dark:bg-zinc-800/60 rounded-xl" />
        <div class="flex items-center gap-2 pt-1">
          <div class="h-8 flex-1 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
          <div class="h-8 w-10 bg-zinc-100 dark:bg-zinc-800 rounded-xl" />
        </div>
      </div>
    </div>

    <!-- 3. EMPTY STATE -->
    <div
      v-else-if="students.length === 0"
      class="p-12 text-center rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
    >
      <UserX class="w-10 h-10 mx-auto text-zinc-300 dark:text-zinc-700 mb-3" />
      <h3 class="font-bold text-sm text-zinc-800 dark:text-zinc-200">No students found</h3>
      <p class="text-xs text-zinc-400 mt-1">Try adjusting your search query or filter options.</p>
    </div>

    <!-- 4. GRID VIEW (Matching Reference Screenshot 100%) -->
    <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
      <div
        v-for="s in students"
        :key="s.id"
        class="p-4 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs hover:shadow-md hover:border-blue-500/40 transition-all flex flex-col justify-between gap-3 group"
      >
        <!-- Card Header: ID Badge & Tariff -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <!-- Student ID Badge -->
            <span class="px-2 py-0.5 rounded-md text-[11px] font-mono font-bold bg-[#eef4ff] dark:bg-blue-950/40 text-[#1868db] dark:text-blue-400 border border-blue-200/80 dark:border-blue-800/60 shadow-2xs">
              {{ s.id }}
            </span>
            <!-- Tariff Name -->
            <span class="text-[11px] font-bold text-zinc-400 dark:text-zinc-400 uppercase tracking-wide truncate max-w-[130px]" :title="s.tariff || ''">
              {{ s.tariff || 'No Tariff' }}
            </span>
          </div>

          <!-- Full Name -->
          <h3 class="font-extrabold text-sm text-zinc-900 dark:text-zinc-100 uppercase tracking-wide truncate" :title="s.full_name">
            {{ s.full_name }}
          </h3>
          <!-- Group Subtitle -->
          <p class="text-[11.5px] font-bold text-zinc-400 dark:text-zinc-400 uppercase mt-0.5 truncate">
            {{ s.student_group || 'No Group' }}
          </p>
        </div>

        <!-- Financial Balance Container (Matching Screenshot) -->
        <div class="p-3 bg-[#f8fafc] dark:bg-zinc-800/60 rounded-xl border border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
          <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-400">
            BALANCE
          </span>
          <span
            class="font-mono font-extrabold text-sm tracking-tight"
            :class="s.balance < 0 ? 'text-[#ff1853]' : (s.balance === 0 ? 'text-zinc-800 dark:text-zinc-200' : 'text-[#00b074]')"
          >
            {{ formatCurrency(s.balance) }}
          </span>
        </div>

        <!-- Action Buttons Row (Matching Screenshot) -->
        <div class="flex items-center gap-2 pt-0.5">
          <!-- + Pay Button -->
          <button
            type="button"
            @click="emit('open-add-payment', s.id)"
            class="flex-1 py-2 px-3 rounded-xl bg-[#00b074] hover:bg-[#009663] active:scale-98 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-2xs transition-all cursor-pointer"
          >
            <Plus class="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Pay</span>
          </button>

          <!-- — (Withdraw / Refund) Button -->
          <button
            type="button"
            @click="emit('open-withdraw', s.id)"
            class="py-2 px-3 rounded-xl bg-white hover:bg-zinc-50 active:scale-98 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:text-rose-600 font-bold shadow-2xs transition-all cursor-pointer"
            title="Withdraw / Refund"
          >
            <Minus class="w-3.5 h-3.5 stroke-[2.5]" />
          </button>
        </div>
      </div>
    </div>

    <!-- 5. TABLE VIEW -->
    <div v-else class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-xs">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/60 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            <th class="px-4 py-3 w-16">ID</th>
            <th class="px-4 py-3">Full Name</th>
            <th class="px-4 py-3">Group</th>
            <th class="px-4 py-3">Tariff</th>
            <th class="px-4 py-3 text-right">Discount</th>
            <th class="px-4 py-3 text-right">Balance</th>
            <th class="px-4 py-3 text-right w-24">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100 dark:divide-zinc-850">
          <tr
            v-for="s in students"
            :key="s.id"
            class="hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 transition-colors"
          >
            <td class="px-4 py-3 font-mono font-bold text-[#1868db] dark:text-blue-400">{{ s.id }}</td>
            <td class="px-4 py-3 font-bold text-zinc-900 dark:text-zinc-100 uppercase">{{ s.full_name }}</td>
            <td class="px-4 py-3 font-semibold text-zinc-400 uppercase">{{ s.student_group || '—' }}</td>
            <td class="px-4 py-3 font-semibold text-zinc-500 uppercase">{{ s.tariff || 'No Tariff' }}</td>
            <td class="px-4 py-3 text-right font-mono font-bold text-amber-600 dark:text-amber-400">
              {{ s.discount > 0 ? formatCurrency(s.discount) : '—' }}
            </td>
            <td
              class="px-4 py-3 text-right font-mono font-extrabold"
              :class="s.balance < 0 ? 'text-[#ff1853]' : (s.balance === 0 ? 'text-zinc-700 dark:text-zinc-300' : 'text-[#00b074]')"
            >
              {{ formatCurrency(s.balance) }}
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1.5">
                <button
                  type="button"
                  @click="emit('open-add-payment', s.id)"
                  class="p-1.5 rounded-lg bg-emerald-50 text-[#00b074] dark:bg-emerald-950/40 dark:text-emerald-300 hover:bg-emerald-100 font-bold transition-colors cursor-pointer"
                  title="Add Payment"
                >
                  <Plus class="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  @click="emit('open-withdraw', s.id)"
                  class="p-1.5 rounded-lg bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-300 hover:bg-rose-100 font-bold transition-colors cursor-pointer"
                  title="Withdraw"
                >
                  <Minus class="w-3.5 h-3.5" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
