<script setup lang="ts">
import { ref } from 'vue'
import type { Payment } from '@/types'
import { useCurrency } from '@/composables/useCurrency'
import {
  Search, FileSpreadsheet, Edit3, Trash2,
  Calendar, Receipt, Loader2, ArrowUpRight, ArrowDownRight
} from 'lucide-vue-next'

const props = defineProps<{
  payments: Payment[]
  isLoading: boolean
  searchQuery: string
  selectedMethod: string
  selectedReceiver: string
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'update:selectedMethod', val: string): void
  (e: 'update:selectedReceiver', val: string): void
  (e: 'export-excel'): void
  (e: 'open-edit', payment: Payment): void
  (e: 'delete-payment', payment: Payment): void
}>()

const { formatCurrency } = useCurrency()

const PAYMENT_METHODS = ['all', 'Karta J.A', 'Karta Abdulaziz', 'Naqd', 'Karta M.A', 'Bank', 'Discount', 'Withdrawal']
const RECEIVED_BY_OPTIONS = ['all', 'ABDULAZIZ', 'MUSLIHIDDIN', 'BAXTIYOR', 'MUHAMMADALI', 'JASUR', 'ADMIN']

const formatDate = (dateStr: string) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div class="space-y-4 text-xs select-none">
    <!-- Filter & Export Toolbar -->
    <div class="p-3 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-xs flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2.5 flex-1 min-w-[240px]">
        <div class="relative flex-1">
          <Search class="w-4 h-4 text-zinc-400 dark:text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            :value="searchQuery"
            @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
            type="text"
            placeholder="Search payments by student name, ID, or notes..."
            class="w-full pl-9 pr-3 py-1.5 rounded-xl bg-zinc-100/90 dark:bg-zinc-800/90 border border-zinc-200 dark:border-zinc-700/80 focus:border-blue-500 focus:bg-white dark:focus:bg-zinc-800 focus:ring-2 focus:ring-blue-500/20 outline-none text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-400 transition-all font-medium"
          />
        </div>

        <!-- Method Filter -->
        <select
          :value="selectedMethod"
          @change="emit('update:selectedMethod', ($event.target as HTMLSelectElement).value)"
          class="px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 font-bold text-zinc-700 dark:text-zinc-300 outline-none cursor-pointer"
        >
          <option value="all">All Methods</option>
          <option v-for="m in PAYMENT_METHODS.filter(m => m !== 'all')" :key="m" :value="m">{{ m }}</option>
        </select>

        <!-- Receiver Filter -->
        <select
          :value="selectedReceiver"
          @change="emit('update:selectedReceiver', ($event.target as HTMLSelectElement).value)"
          class="px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 font-bold text-zinc-700 dark:text-zinc-300 outline-none cursor-pointer"
        >
          <option value="all">All Receivers</option>
          <option v-for="r in RECEIVED_BY_OPTIONS.filter(r => r !== 'all')" :key="r" :value="r">{{ r }}</option>
        </select>
      </div>

      <!-- Export to Excel Button -->
      <button
        @click="emit('export-excel')"
        class="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
        title="Export Payment History to Excel (.xlsx)"
      >
        <FileSpreadsheet class="w-4 h-4" />
        <span>Export Excel</span>
      </button>
    </div>

    <!-- Payments History Table -->
    <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-xs">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/60 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            <th class="px-4 py-3">Date & Time</th>
            <th class="px-4 py-3">Student</th>
            <th class="px-4 py-3">Method</th>
            <th class="px-4 py-3">Received By</th>
            <th class="px-4 py-3">Notes</th>
            <th class="px-4 py-3 text-right">Amount</th>
            <th class="px-4 py-3 text-right w-20">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100 dark:divide-zinc-850">
          <tr v-if="isLoading">
            <td colspan="7" class="p-12 text-center text-zinc-400">
              <Loader2 class="w-6 h-6 animate-spin mx-auto text-brand-500 mb-2" />
              <span>Loading payment records...</span>
            </td>
          </tr>

          <tr v-else-if="payments.length === 0">
            <td colspan="7" class="p-12 text-center text-zinc-400">
              <Receipt class="w-8 h-8 mx-auto text-zinc-300 dark:text-zinc-700 mb-2" />
              <p class="font-bold text-sm text-zinc-700 dark:text-zinc-300">No payment records found</p>
            </td>
          </tr>

          <tr
            v-else
            v-for="p in payments"
            :key="p.id"
            class="hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 transition-colors"
          >
            <td class="px-4 py-3 whitespace-nowrap text-zinc-500 font-mono text-[11.5px]">
              {{ formatDate(p.created_at) }}
            </td>

            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <span
                  v-if="p.student_id"
                  class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20"
                >
                  {{ p.student_id }}
                </span>
                <span class="font-bold text-zinc-900 dark:text-zinc-100">
                  {{ p.student_full_name || p.student_name || 'General Payment' }}
                </span>
              </div>
            </td>

            <td class="px-4 py-3 whitespace-nowrap">
              <span class="px-2 py-0.5 rounded-full text-[10.5px] font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                {{ p.method }}
              </span>
            </td>

            <td class="px-4 py-3 whitespace-nowrap font-bold text-zinc-700 dark:text-zinc-300">
              {{ p.received_by }}
            </td>

            <td class="px-4 py-3 text-zinc-500 truncate max-w-[200px]" :title="p.notes || ''">
              {{ p.notes || '—' }}
            </td>

            <td class="px-4 py-3 text-right font-mono font-black whitespace-nowrap">
              <span
                v-if="p.is_withdrawal"
                class="text-rose-600 dark:text-rose-400"
              >
                -{{ formatCurrency(Math.abs(p.amount)) }}
              </span>
              <span
                v-else-if="p.is_discount"
                class="text-amber-600 dark:text-amber-400"
              >
                +{{ formatCurrency(p.amount) }} (Discount)
              </span>
              <span
                v-else
                class="text-emerald-600 dark:text-emerald-400"
              >
                +{{ formatCurrency(p.amount) }}
              </span>
            </td>

            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1">
                <button
                  @click="emit('open-edit', p)"
                  class="p-1.5 rounded-lg text-zinc-400 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-950/30 transition-colors cursor-pointer"
                  title="Edit Payment"
                >
                  <Edit3 class="w-3.5 h-3.5" />
                </button>
                <button
                  @click="emit('delete-payment', p)"
                  class="p-1.5 rounded-lg text-zinc-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
                  title="Delete Payment"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
