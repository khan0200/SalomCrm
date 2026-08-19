<script setup lang="ts">
import { ref } from 'vue'
import type { Student } from '@/types'
import { useCurrency } from '@/composables/useCurrency'
import {
  Search, Plus, Minus, LayoutGrid, Table as TableIcon,
  CreditCard, CheckCircle2, AlertCircle, Filter, ArrowUpRight
} from 'lucide-vue-next'

const props = defineProps<{
  students: Student[]
  isLoading: boolean
  searchQuery: string
  selectedTariffs: string[]
  selectedBalances: string[]
  selectedStatus: string
  viewMode: 'grid' | 'table'
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'update:selectedTariffs', val: string[]): void
  (e: 'update:selectedBalances', val: string[]): void
  (e: 'update:selectedStatus', val: string): void
  (e: 'update:viewMode', val: 'grid' | 'table'): void
  (e: 'open-add-payment', studentId: string): void
  (e: 'open-withdraw', studentId: string): void
}>()

const { formatCurrency } = useCurrency()

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

const toggleItem = (list: string[], item: string, emitName: any) => {
  const next = list.includes(item) ? list.filter(i => i !== item) : [...list, item]
  emit(emitName, next)
}
</script>

<template>
  <div class="space-y-4 text-xs select-none">
    <!-- Filter Controls Bar -->
    <div class="p-3 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-xs flex flex-wrap items-center justify-between gap-3">
      <!-- Search & Status -->
      <div class="flex items-center gap-2.5 flex-1 min-w-[260px]">
        <div class="relative flex-1">
          <Search class="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            :value="searchQuery"
            @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
            type="text"
            placeholder="Search student by name, ID, or phone..."
            class="w-full pl-9 pr-3 py-1.5 rounded-xl bg-zinc-50 dark:bg-zinc-800 border-transparent focus:border-brand-500 focus:bg-white dark:focus:bg-zinc-800 focus:ring-2 focus:ring-brand-500/20 outline-none text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400"
          />
        </div>

        <!-- Status Filter -->
        <select
          :value="selectedStatus"
          @change="emit('update:selectedStatus', ($event.target as HTMLSelectElement).value)"
          class="px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 font-bold text-zinc-700 dark:text-zinc-300 outline-none cursor-pointer"
        >
          <option value="Active">Active Students</option>
          <option value="Archive">Archive / Deleted</option>
        </select>
      </div>

      <!-- View Mode Grid/Table Switcher -->
      <div class="flex items-center gap-1 border border-zinc-200 dark:border-zinc-700 rounded-xl p-1 bg-zinc-50 dark:bg-zinc-800">
        <button
          @click="emit('update:viewMode', 'grid')"
          class="p-1.5 rounded-lg font-bold transition-all cursor-pointer"
          :class="viewMode === 'grid' ? 'bg-white dark:bg-zinc-700 text-brand-600 dark:text-brand-400 shadow-2xs' : 'text-zinc-400 hover:text-zinc-600'"
          title="Grid View"
        >
          <LayoutGrid class="w-4 h-4" />
        </button>
        <button
          @click="emit('update:viewMode', 'table')"
          class="p-1.5 rounded-lg font-bold transition-all cursor-pointer"
          :class="viewMode === 'table' ? 'bg-white dark:bg-zinc-700 text-brand-600 dark:text-brand-400 shadow-2xs' : 'text-zinc-400 hover:text-zinc-600'"
          title="Table View"
        >
          <TableIcon class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Multi-select Filter Pills (Tariffs & Balance) -->
    <div class="flex flex-wrap items-center gap-1.5">
      <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 mr-1">Tariff:</span>
      <button
        v-for="t in TARIFF_OPTIONS"
        :key="t"
        @click="toggleItem(selectedTariffs, t, 'update:selectedTariffs')"
        class="px-2.5 py-1 rounded-lg text-[10.5px] font-bold border transition-all cursor-pointer"
        :class="selectedTariffs.includes(t) ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50'"
      >
        {{ t }}
      </button>

      <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 ml-3 mr-1">Balance:</span>
      <button
        v-for="b in BALANCE_OPTIONS"
        :key="b"
        @click="toggleItem(selectedBalances, b, 'update:selectedBalances')"
        class="px-2.5 py-1 rounded-lg text-[10.5px] font-bold border transition-all cursor-pointer"
        :class="selectedBalances.includes(b) ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50'"
      >
        {{ b }}
      </button>
    </div>

    <!-- 1. GRID VIEW -->
    <div v-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
      <div
        v-for="s in students"
        :key="s.id"
        class="p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs hover:border-brand-500/50 transition-all flex flex-col justify-between gap-3 group"
      >
        <!-- Header -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20">
              {{ s.id }}
            </span>
            <span class="text-[10px] font-bold text-zinc-400 uppercase truncate max-w-[120px]">
              {{ s.tariff || 'No Tariff' }}
            </span>
          </div>

          <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 truncate" :title="s.full_name">
            {{ s.full_name }}
          </h3>
          <p v-if="s.student_group" class="text-[11px] text-zinc-400 mt-0.5">{{ s.student_group }}</p>
        </div>

        <!-- Financial Position Section -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-100 dark:border-zinc-800 space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-[10.5px] font-bold text-zinc-400 uppercase">Balance</span>
            <span
              class="font-mono font-black text-xs"
              :class="s.balance < 0 ? 'text-rose-600 dark:text-rose-400' : (s.balance === 0 ? 'text-zinc-800 dark:text-zinc-200' : 'text-emerald-600 dark:text-emerald-400')"
            >
              {{ formatCurrency(s.balance) }}
            </span>
          </div>

          <div v-if="s.discount > 0" class="flex items-center justify-between text-[11px]">
            <span class="text-zinc-400 font-medium">Discount</span>
            <span class="font-mono font-bold text-amber-600 dark:text-amber-400">{{ formatCurrency(s.discount) }}</span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center gap-2 pt-1">
          <button
            @click="emit('open-add-payment', s.id)"
            class="flex-1 py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center justify-center gap-1 shadow-2xs transition-colors cursor-pointer"
          >
            <Plus class="w-3.5 h-3.5" />
            <span>Pay</span>
          </button>
          <button
            @click="emit('open-withdraw', s.id)"
            class="py-1.5 px-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 font-bold transition-colors cursor-pointer"
            title="Withdraw / Refund"
          >
            <Minus class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>

    <!-- 2. TABLE VIEW -->
    <div v-else class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-xs">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/60 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            <th class="px-4 py-3 w-16">ID</th>
            <th class="px-4 py-3">Full Name</th>
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
            <td class="px-4 py-3 font-mono font-bold text-brand-600 dark:text-brand-400">{{ s.id }}</td>
            <td class="px-4 py-3 font-bold text-zinc-900 dark:text-zinc-100">{{ s.full_name }}</td>
            <td class="px-4 py-3 font-semibold text-zinc-500">{{ s.tariff || 'No Tariff' }}</td>
            <td class="px-4 py-3 text-right font-mono font-bold text-amber-600 dark:text-amber-400">
              {{ s.discount > 0 ? formatCurrency(s.discount) : '—' }}
            </td>
            <td
              class="px-4 py-3 text-right font-mono font-black"
              :class="s.balance < 0 ? 'text-rose-600 dark:text-rose-400' : (s.balance === 0 ? 'text-zinc-700 dark:text-zinc-300' : 'text-emerald-600 dark:text-emerald-400')"
            >
              {{ formatCurrency(s.balance) }}
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1.5">
                <button
                  @click="emit('open-add-payment', s.id)"
                  class="p-1.5 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 hover:bg-emerald-100 font-bold transition-colors cursor-pointer"
                  title="Add Payment"
                >
                  <Plus class="w-3.5 h-3.5" />
                </button>
                <button
                  @click="emit('open-withdraw', s.id)"
                  class="p-1.5 rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 hover:bg-rose-100 font-bold transition-colors cursor-pointer"
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
