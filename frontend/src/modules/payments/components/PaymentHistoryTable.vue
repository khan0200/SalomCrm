<script setup lang="ts">
import { ref } from 'vue'
import type { Payment } from '@/types'
import { useCurrency } from '@/composables/useCurrency'
import {
  Search, FileSpreadsheet, Pencil, Trash2, Printer,
  Calendar, Receipt, Loader2, User, ChevronDown, LayoutGrid, Table as TableIcon
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
const viewMode = ref<'grid' | 'table'>('grid')

const PAYMENT_METHODS = ['all', 'Karta J.A', 'Karta Abdulaziz', 'Naqd', 'Karta M.A', 'Bank', 'Discount', 'Withdrawal']
const RECEIVED_BY_OPTIONS = ['all', 'ABDULAZIZ', 'MUSLIHIDDIN', 'BAXTIYOR', 'MUHAMMADALI', 'JASUR', 'ADMIN']

const formatCardDateTime = (dateStr: string) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

const handlePrint = (p: Payment) => {
  const printWindow = window.open('', '_blank', 'width=600,height=700')
  if (!printWindow) return

  const studentName = p.student_full_name || p.student_name || 'General'
  const dateFormatted = formatCardDateTime(p.created_at)
  const sign = p.is_withdrawal ? '-' : '+'
  const amountFormatted = `${sign}${Number(p.amount).toLocaleString('en-US')} UZS`
  const paymentType = p.is_withdrawal ? 'WITHDRAWAL / REFUND' : (p.is_discount ? 'DISCOUNT' : 'STUDENT PAYMENT')

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Payment Receipt - ${studentName}</title>
        <style>
          body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; color: #1e293b; }
          .receipt { border: 2px solid #e2e8f0; border-radius: 12px; padding: 24px; max-width: 480px; margin: auto; }
          .header { text-align: center; border-bottom: 2px dashed #cbd5e1; padding-bottom: 16px; margin-bottom: 16px; }
          .title { font-size: 20px; font-weight: 800; text-transform: uppercase; margin: 0; color: #0f172a; }
          .subtitle { font-size: 12px; color: #64748b; margin-top: 4px; }
          .row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 13px; }
          .label { color: #64748b; font-weight: 600; text-transform: uppercase; font-size: 11px; }
          .value { font-weight: 700; color: #0f172a; }
          .amount-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center; margin: 16px 0; }
          .amount-label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
          .amount-value { font-size: 22px; font-weight: 900; color: #059669; font-family: monospace; margin-top: 4px; }
          .footer { text-align: center; font-size: 11px; color: #94a3b8; margin-top: 20px; border-top: 1px solid #f1f5f9; padding-top: 12px; }
        </style>
      </head>
      <body>
        <div class="receipt">
          <div class="header">
            <h1 class="title">Official Payment Receipt</h1>
            <div class="subtitle">${paymentType}</div>
          </div>
          <div class="row"><span class="label">Date & Time</span><span class="value">${dateFormatted}</span></div>
          <div class="row"><span class="label">Student Name</span><span class="value">${studentName}</span></div>
          <div class="row"><span class="label">Student ID</span><span class="value">${p.student_id || '—'}</span></div>
          <div class="row"><span class="label">Payment Method</span><span class="value">${p.method}</span></div>
          <div class="row"><span class="label">Received By</span><span class="value">${p.received_by}</span></div>
          <div class="row"><span class="label">Registered By</span><span class="value">${p.created_by_name || 'System Admin'}</span></div>
          ${p.notes ? `<div class="row"><span class="label">Notes</span><span class="value">${p.notes}</span></div>` : ''}
          <div class="amount-box">
            <div class="amount-label">Total Amount</div>
            <div class="amount-value">${amountFormatted}</div>
          </div>
          <div class="footer">Thank you! Generated automatically by CRM System.</div>
        </div>
        <script>window.onload = function() { window.print(); }<\/script>
      </body>
    </html>
  `)
  printWindow.document.close()
}
</script>

<template>
  <div class="space-y-4 text-xs select-none">
    <!-- 1. Search & Filter Bar Card -->
    <div class="p-2.5 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 shadow-2xs flex flex-wrap items-center gap-2.5">
      <!-- Search Input -->
      <div class="relative flex-1 min-w-[220px]">
        <Search class="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          :value="searchQuery"
          @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
          type="text"
          placeholder="Search payments by student name, ID, or notes..."
          class="w-full pl-9 pr-3 py-2 rounded-xl bg-[#f8fafc] dark:bg-zinc-800/80 border border-zinc-200/80 dark:border-zinc-700/80 focus:border-blue-500 focus:bg-white dark:focus:bg-zinc-800 focus:ring-2 focus:ring-blue-500/20 outline-none text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 text-xs font-medium transition-all"
        />
      </div>

      <!-- Filter Dropdowns Row -->
      <div class="flex flex-wrap items-center gap-2">
        <!-- Method Dropdown -->
        <div class="relative">
          <select
            :value="selectedMethod"
            @change="emit('update:selectedMethod', ($event.target as HTMLSelectElement).value)"
            class="appearance-none bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600 rounded-xl pl-3.5 pr-8 py-2 text-xs font-semibold text-zinc-700 dark:text-zinc-200 outline-none cursor-pointer transition-colors shadow-2xs"
          >
            <option value="all">All Methods</option>
            <option v-for="m in PAYMENT_METHODS.filter(m => m !== 'all')" :key="m" :value="m">{{ m }}</option>
          </select>
          <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        <!-- Receiver Dropdown -->
        <div class="relative">
          <select
            :value="selectedReceiver"
            @change="emit('update:selectedReceiver', ($event.target as HTMLSelectElement).value)"
            class="appearance-none bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600 rounded-xl pl-3.5 pr-8 py-2 text-xs font-semibold text-zinc-700 dark:text-zinc-200 outline-none cursor-pointer transition-colors shadow-2xs"
          >
            <option value="all">All Receivers</option>
            <option v-for="r in RECEIVED_BY_OPTIONS.filter(r => r !== 'all')" :key="r" :value="r">{{ r }}</option>
          </select>
          <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        <!-- Export to Excel Button -->
        <button
          type="button"
          @click="emit('export-excel')"
          class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-2xs transition-all cursor-pointer active:scale-98"
          title="Export Payment History to Excel (.xlsx)"
        >
          <FileSpreadsheet class="w-4 h-4" />
          <span>Export Excel</span>
        </button>

        <!-- View Mode Grid / Table Switcher -->
        <div class="flex items-center gap-1 border border-zinc-200 dark:border-zinc-700 rounded-xl p-0.5 bg-zinc-50 dark:bg-zinc-800 shadow-2xs">
          <button
            type="button"
            @click="viewMode = 'grid'"
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
            @click="viewMode = 'table'"
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

    <!-- 2. SKELETON LOADING STATE -->
    <div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="i in 6"
        :key="`skel-pay-${i}`"
        class="p-4 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs flex flex-col justify-between gap-3.5 animate-pulse"
      >
        <div class="flex items-center justify-between">
          <div class="h-5 w-40 bg-zinc-200 dark:bg-zinc-800 rounded" />
          <div class="h-4 w-24 bg-zinc-100 dark:bg-zinc-800 rounded" />
        </div>
        <div class="flex items-center gap-2">
          <div class="h-6 w-20 bg-zinc-200 dark:bg-zinc-800 rounded-md" />
          <div class="h-6 w-24 bg-zinc-100 dark:bg-zinc-800 rounded-md" />
          <div class="h-6 w-20 bg-zinc-100 dark:bg-zinc-800 rounded-md" />
        </div>
        <div class="h-4 w-32 bg-zinc-100 dark:bg-zinc-800 rounded" />
        <div class="h-4 w-48 bg-zinc-100 dark:bg-zinc-800 rounded" />
        <div class="flex items-center gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
          <div class="h-8 flex-1 bg-zinc-100 dark:bg-zinc-800 rounded-xl" />
          <div class="h-8 flex-1 bg-zinc-100 dark:bg-zinc-800 rounded-xl" />
          <div class="h-8 flex-1 bg-zinc-100 dark:bg-zinc-800 rounded-xl" />
        </div>
      </div>
    </div>

    <!-- 3. EMPTY STATE -->
    <div
      v-else-if="payments.length === 0"
      class="p-12 text-center rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
    >
      <Receipt class="w-10 h-10 mx-auto text-zinc-300 dark:text-zinc-700 mb-3" />
      <h3 class="font-bold text-sm text-zinc-800 dark:text-zinc-200">No payment records found</h3>
      <p class="text-xs text-zinc-400 mt-1">Try adjusting your search query or filter options.</p>
    </div>

    <!-- 4. GRID / CARD VIEW (Matching Screenshot 100%) -->
    <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="p in payments"
        :key="p.id"
        class="p-4 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xs hover:shadow-md hover:border-blue-500/30 transition-all flex flex-col justify-between gap-3 group"
      >
        <!-- Top Row: Student Name & DateTime -->
        <div>
          <div class="flex items-start justify-between gap-2 mb-2">
            <h3 class="font-bold text-[13.5px] text-zinc-900 dark:text-zinc-100 uppercase tracking-wide truncate" :title="p.student_full_name || p.student_name || 'General Payment'">
              {{ p.student_full_name || p.student_name || 'General Payment' }}
            </h3>
            <span class="text-[11.5px] text-zinc-400 dark:text-zinc-400 font-mono whitespace-nowrap">
              {{ formatCardDateTime(p.created_at) }}
            </span>
          </div>

          <!-- Badges Row: Amount, Method, Receiver (Matching Screenshot) -->
          <div class="flex flex-wrap items-center gap-1.5 mt-2">
            <!-- Amount Badge -->
            <span
              class="px-2.5 py-1 rounded-lg text-xs font-bold font-mono shadow-2xs"
              :class="p.is_withdrawal
                ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60'
                : (p.is_discount
                  ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/60'
                  : 'bg-[#e6f8ef] dark:bg-emerald-950/40 text-[#00875a] dark:text-emerald-400 border border-[#a3e635]/70 dark:border-emerald-800/60')"
            >
              {{ p.is_withdrawal ? '-' : '+' }}{{ formatCurrency(Math.abs(p.amount)) }}
            </span>

            <!-- Method Badge -->
            <span class="px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase bg-blue-50/70 dark:bg-blue-950/30 text-zinc-700 dark:text-zinc-300 border border-blue-200/80 dark:border-blue-800/60 shadow-2xs">
              {{ p.method }}
            </span>

            <!-- Receiver Badge -->
            <span class="px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase bg-blue-50/70 dark:bg-blue-950/30 text-zinc-700 dark:text-zinc-300 border border-blue-200/80 dark:border-blue-800/60 shadow-2xs">
              {{ p.received_by }}
            </span>
          </div>
        </div>

        <!-- Middle Section: Registered By & Notes -->
        <div class="space-y-1.5 py-2 border-t border-zinc-100 dark:border-zinc-800/80">
          <!-- Registered By Row -->
          <div class="flex items-center gap-1.5 text-xs">
            <User class="w-3.5 h-3.5 text-zinc-400" />
            <span class="text-zinc-400 font-medium">Registered by:</span>
            <span class="font-bold text-zinc-800 dark:text-zinc-200 uppercase">
              {{ p.created_by_name || 'BAXTIYOR' }}
            </span>
          </div>

          <!-- Notes Row (Italic) -->
          <div class="pt-0.5">
            <p v-if="p.notes" class="italic text-xs text-zinc-500 dark:text-zinc-400 truncate" :title="p.notes">
              {{ p.notes }}
            </p>
            <p v-else class="italic text-xs text-zinc-300 dark:text-zinc-600">
              No notes
            </p>
          </div>
        </div>

        <!-- Bottom Action Buttons: Edit, Delete, Print (Matching Screenshot) -->
        <div class="flex items-center gap-2 pt-1 border-t border-zinc-100 dark:border-zinc-800/80">
          <!-- Edit Button -->
          <button
            type="button"
            @click="emit('open-edit', p)"
            class="flex-1 py-1.5 px-3 rounded-xl bg-white hover:bg-zinc-50 active:scale-98 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-bold text-xs flex items-center justify-center gap-1.5 shadow-2xs transition-all cursor-pointer"
          >
            <Pencil class="w-3.5 h-3.5" />
            <span>Edit</span>
          </button>

          <!-- Delete Button -->
          <button
            type="button"
            @click="emit('delete-payment', p)"
            class="flex-1 py-1.5 px-3 rounded-xl bg-white hover:bg-rose-50 active:scale-98 dark:bg-zinc-800 border border-rose-200 dark:border-rose-800/60 text-rose-600 dark:text-rose-400 font-bold text-xs flex items-center justify-center gap-1.5 shadow-2xs transition-all cursor-pointer"
          >
            <Trash2 class="w-3.5 h-3.5" />
            <span>Delete</span>
          </button>

          <!-- Print Button -->
          <button
            type="button"
            @click="handlePrint(p)"
            class="flex-1 py-1.5 px-3 rounded-xl bg-white hover:bg-zinc-50 active:scale-98 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-bold text-xs flex items-center justify-center gap-1.5 shadow-2xs transition-all cursor-pointer"
          >
            <Printer class="w-3.5 h-3.5" />
            <span>Print</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 5. TABLE VIEW (Alternative) -->
    <div v-else class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-xs">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/60 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            <th class="px-4 py-3">Date & Time</th>
            <th class="px-4 py-3">Student</th>
            <th class="px-4 py-3">Method</th>
            <th class="px-4 py-3">Received By</th>
            <th class="px-4 py-3">Registered By</th>
            <th class="px-4 py-3">Notes</th>
            <th class="px-4 py-3 text-right">Amount</th>
            <th class="px-4 py-3 text-right w-24">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100 dark:divide-zinc-850">
          <tr
            v-for="p in payments"
            :key="p.id"
            class="hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 transition-colors"
          >
            <td class="px-4 py-3 whitespace-nowrap text-zinc-500 font-mono text-[11.5px]">
              {{ formatCardDateTime(p.created_at) }}
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <span
                  v-if="p.student_id"
                  class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-[#1868db]/10 text-[#1868db] dark:text-blue-400 border border-[#1868db]/20"
                >
                  {{ p.student_id }}
                </span>
                <span class="font-bold text-zinc-900 dark:text-zinc-100 uppercase">
                  {{ p.student_full_name || p.student_name || 'General' }}
                </span>
              </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
              <span class="px-2 py-0.5 rounded-md text-[11px] font-bold bg-blue-50 dark:bg-blue-950/30 text-zinc-700 dark:text-zinc-300 border border-blue-200/80 dark:border-blue-800/60">
                {{ p.method }}
              </span>
            </td>
            <td class="px-4 py-3 whitespace-nowrap font-bold text-zinc-700 dark:text-zinc-300 uppercase">
              {{ p.received_by }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-zinc-500 font-medium uppercase">
              {{ p.created_by_name || 'BAXTIYOR' }}
            </td>
            <td class="px-4 py-3 text-zinc-500 italic truncate max-w-[180px]" :title="p.notes || ''">
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
                class="text-[#00875a] dark:text-emerald-400"
              >
                +{{ formatCurrency(p.amount) }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1">
                <button
                  type="button"
                  @click="emit('open-edit', p)"
                  class="p-1.5 rounded-lg text-zinc-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors cursor-pointer"
                  title="Edit Payment"
                >
                  <Pencil class="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  @click="emit('delete-payment', p)"
                  class="p-1.5 rounded-lg text-zinc-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
                  title="Delete Payment"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  @click="handlePrint(p)"
                  class="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                  title="Print Receipt"
                >
                  <Printer class="w-3.5 h-3.5" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
