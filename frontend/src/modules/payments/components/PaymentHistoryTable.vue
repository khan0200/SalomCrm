<script setup lang="ts">
import { ref } from 'vue'
import type { Payment } from '@/types'
import {
  Search, FileSpreadsheet, Pencil, Trash2, Printer,
  Receipt, X, User, LayoutGrid, Table as TableIcon
} from 'lucide-vue-next'

const props = defineProps<{
  payments: Payment[]
  totalFilteredCount: number
  isLoading: boolean
  searchQuery: string
  selectedMethod: string
  selectedReceiver: string
  paymentMethods: string[]
  paymentReceivers: string[]
  viewMode: 'grid' | 'table'
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'update:selectedMethod', val: string): void
  (e: 'update:selectedReceiver', val: string): void
  (e: 'update:viewMode', val: 'grid' | 'table'): void
  (e: 'open-edit', payment: Payment): void
  (e: 'delete-payment', payment: Payment): void
  (e: 'export-excel'): void
}>()

const viewingPayment = ref<Payment | null>(null)

function formatAmount(val: number | string | null | undefined) {
  if (val === null || val === undefined) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('uz-UZ').format(Math.round(num || 0))
}

const formatTimestamp = (dateStr?: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleString('uz-UZ', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleEditFromModal = () => {
  if (viewingPayment.value) {
    const p = viewingPayment.value
    viewingPayment.value = null
    emit('open-edit', p)
  }
}

// ── 80mm Thermal Receipt Generator matching UniApp2 1-to-1 ─────────────────────────
const printReceipt = (payment: Payment) => {
  const amount = Number(payment.amount) || 0
  const isWithdrawal = amount < 0
  const absAmount = Math.abs(amount)
  const amountFormatted = formatAmount(absAmount) + ' UZS'
  const amountSign = isWithdrawal ? '-' : '+'
  const amountLabel = isWithdrawal ? 'WITHDRAWAL' : 'PAYMENT'

  const dateObj = payment.created_at ? new Date(payment.created_at) : new Date()
  const dateStr = dateObj.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })
  const timeStr = dateObj.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })

  const receiptNo = payment.id ? String(payment.id).replace(/-/g, '').slice(-8).toUpperCase() : 'N/A'
  const studentName = payment.student_full_name || payment.student_name || ''
  const studentLine = payment.student_id && studentName
    ? `${payment.student_id} — ${studentName}`
    : (studentName || 'General Payment')
  const notesLine = payment.notes || ''
  const methodLine = payment.method || '—'
  const receiverLine = payment.received_by || '—'

  const receiptHTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Receipt #${receiptNo}</title>
<style>
  @page { size: 80mm auto; margin: 2mm; }
  html, body { font-family: 'Courier New', Courier, monospace; font-size: 11px; width: 74mm; color: #000; background: #fff; margin: 0; padding: 0; }
  .receipt { padding: 3mm 3mm 4mm 3mm; }
  .company-name { font-size: 14px; font-weight: 900; letter-spacing: 2px; text-align: center; margin-bottom: 0.5mm; }
  .company-sub { font-size: 9px; text-align: center; margin-bottom: 2mm; letter-spacing: 1px; }
  .divider { border: none; border-top: 1px dashed #000; margin: 1.5mm 0; }
  .divider-solid { border: none; border-top: 1px solid #000; margin: 1.5mm 0; }
  .row { display: flex; justify-content: space-between; margin: 1mm 0; font-size: 10.5px; }
  .row .label { color: #333; flex-shrink: 0; margin-right: 2mm; }
  .row .value { text-align: right; word-break: break-word; max-width: 50mm; }
  .row .bold { font-weight: 700; }
  .amount-box { border: 1px solid #000; padding: 2mm 2mm; text-align: center; margin: 2mm 0; }
  .amount-label { font-size: 9px; letter-spacing: 1px; margin-bottom: 0.5mm; }
  .amount-value { font-size: 18px; font-weight: 900; letter-spacing: 1px; }
  .receipt-no { font-size: 9px; color: #555; text-align: center; margin-bottom: 1mm; }
  .footer { text-align: center; font-size: 9px; margin-top: 2mm; letter-spacing: 1px; }
  .notes-row { border: 1px dashed #555; padding: 1mm 2mm; margin: 1mm 0; font-size: 10px; word-break: break-word; }
</style>
</head>
<body>
<div class="receipt">
  <div class="company-name">SALOM CRM</div>
  <div class="company-sub">UNIBRIDGE EDUCATIONAL SERVICES</div>
  <hr class="divider-solid">
  <div class="receipt-no">Receipt #${receiptNo}</div>
  <div class="row"><span class="label">Date:</span><span class="value bold">${dateStr}</span></div>
  <div class="row"><span class="label">Time:</span><span class="value">${timeStr}</span></div>
  <hr class="divider">
  <div class="row"><span class="label">Student:</span><span class="value bold">${studentLine}</span></div>
  <hr class="divider">
  <div class="amount-box">
    <div class="amount-label">${amountLabel}</div>
    <div class="amount-value">${amountSign}${amountFormatted}</div>
  </div>
  <hr class="divider">
  <div class="row"><span class="label">Method:</span><span class="value">${methodLine}</span></div>
  <div class="row"><span class="label">Received by:</span><span class="value">${receiverLine}</span></div>
  ${notesLine ? `<div class="notes-row"><span style="font-size:9px; letter-spacing:1px; color:#444;">NOTE: </span>${notesLine}</div>` : ''}
  <hr class="divider-solid">
  <div class="footer">★ RAHMAT! THANK YOU! ★<br><span style="font-size:8px; color:#555;">unibridge.uz</span></div>
</div>
</body>
</html>`

  const printWin = window.open('', '_blank', 'width=400,height=600,toolbar=0,location=0,menubar=0')
  if (!printWin) {
    alert('Please allow pop-ups to print the receipt!')
    return
  }
  printWin.document.write(receiptHTML)
  printWin.document.close()
  printWin.onload = () => {
    setTimeout(() => {
      printWin.focus()
      printWin.print()
      printWin.onafterprint = () => printWin.close()
    }, 300)
  }
}
</script>

<template>
  <div class="flex flex-col gap-4 select-none text-xs">
    <!-- Filter bar -->
    <div class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-3 shadow-2xs flex flex-wrap gap-2.5 items-center">
      <div class="relative flex-1 min-w-[220px]">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400 pointer-events-none" />
        <input
          type="text"
          :value="searchQuery"
          @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
          placeholder="Search by name, ID, or notes..."
          class="w-full pl-9 pr-4 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>

      <!-- Method Filter -->
      <select
        :value="selectedMethod"
        @change="emit('update:selectedMethod', ($event.target as HTMLSelectElement).value)"
        class="px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-700 dark:text-zinc-200 cursor-pointer shadow-2xs font-semibold focus:outline-none"
      >
        <option value="all">All Methods</option>
        <option v-for="m in paymentMethods" :key="m" :value="m">{{ m }}</option>
        <option value="Withdrawal">Withdrawal</option>
      </select>

      <!-- Receiver Filter -->
      <select
        :value="selectedReceiver"
        @change="emit('update:selectedReceiver', ($event.target as HTMLSelectElement).value)"
        class="px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-700 dark:text-zinc-200 cursor-pointer shadow-2xs font-semibold focus:outline-none"
      >
        <option value="all">All Receivers</option>
        <option v-for="r in paymentReceivers" :key="r" :value="r">{{ r }}</option>
      </select>

      <!-- Export Excel Button -->
      <button
        type="button"
        @click="emit('export-excel')"
        class="flex items-center gap-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 hover:bg-zinc-50 dark:hover:bg-zinc-800 px-3.5 py-2 text-xs font-bold text-zinc-800 dark:text-zinc-200 transition-all cursor-pointer shadow-2xs"
        title="Download Payment History as Excel"
      >
        <FileSpreadsheet class="h-4 w-4 text-emerald-600 dark:text-emerald-500" />
        <span>Export Excel</span>
      </button>

      <!-- View Mode Switcher -->
      <div class="flex items-center gap-1 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-100 dark:bg-zinc-850 p-1 ml-auto">
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

    <!-- Payments Count -->
    <div class="text-xs text-zinc-500 dark:text-zinc-400 italic px-1">
      {{ totalFilteredCount }} payments
    </div>

    <!-- ── 1. Grid View ──────────────────────────────────────────────── -->
    <div v-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
      <div
        v-for="payment in payments"
        :key="payment.id"
        @click="viewingPayment = payment"
        class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] p-3.5 shadow-2xs hover:-translate-y-0.5 hover:shadow-md hover:border-blue-500/40 transition-all duration-200 cursor-pointer flex flex-col justify-between h-full gap-3 group"
      >
        <div class="flex flex-col gap-2.5">
          <!-- Header Row: Student Name + Timestamp -->
          <div class="flex items-start justify-between gap-2 overflow-hidden">
            <span
              class="font-bold text-[13px] uppercase tracking-wide text-[#1868db] dark:text-blue-400 truncate flex-1"
              :title="payment.student_full_name || payment.student_name || 'General Payment'"
            >
              {{ payment.student_full_name || payment.student_name || 'General Payment' }}
            </span>
            <span class="text-[10px] font-medium text-zinc-400 whitespace-nowrap pt-0.5 font-mono">
              {{ formatTimestamp(payment.created_at) }}
            </span>
          </div>

          <!-- Amount & Badges Row -->
          <div class="flex items-center gap-1.5 flex-wrap">
            <!-- Amount Badge -->
            <span
              class="inline-flex items-center px-2 py-0.5 rounded-[4px] text-[12px] font-extrabold font-mono"
              :class="Number(payment.amount) < 0
                ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/25'
                : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25'"
            >
              {{ Number(payment.amount) < 0 ? '-' : '+' }}{{ formatAmount(Math.abs(Number(payment.amount))) }}
            </span>

            <!-- Method Badge -->
            <span class="inline-flex items-center px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase tracking-wider bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
              {{ payment.method }}
            </span>

            <!-- Receiver Badge -->
            <span class="inline-flex items-center px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase tracking-wider bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
              {{ payment.received_by }}
            </span>
          </div>

          <!-- Registered By Section -->
          <div class="pt-2 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center gap-1.5 text-[11.5px]">
            <User class="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <span class="text-zinc-400 dark:text-zinc-500 font-medium">Registered by:</span>
            <span class="font-bold text-zinc-800 dark:text-zinc-200 uppercase tracking-tight">
              {{ payment.created_by_name || payment.received_by || 'Staff' }}
            </span>
          </div>

          <!-- Notes Section -->
          <div v-if="payment.notes" class="pt-1.5 border-t border-zinc-100 dark:border-zinc-800">
            <div class="text-[11px] text-zinc-500 dark:text-zinc-400 leading-normal italic truncate" :title="payment.notes">
              {{ payment.notes }}
            </div>
          </div>
        </div>

        <!-- Actions Footer -->
        <div class="flex items-center gap-2 pt-2.5 border-t border-zinc-100 dark:border-zinc-800">
          <button
            type="button"
            @click.stop="emit('open-edit', payment)"
            class="flex-1 flex items-center justify-center gap-1 py-1.5 text-xs font-semibold rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-all cursor-pointer shadow-2xs"
          >
            <Pencil class="h-3.5 w-3.5" />
            <span>Edit</span>
          </button>
          <button
            type="button"
            @click.stop="emit('delete-payment', payment)"
            class="flex-1 flex items-center justify-center gap-1 py-1.5 text-xs font-bold rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50/60 dark:bg-rose-950/20 text-rose-600 dark:text-rose-400 hover:bg-rose-600 hover:text-white transition-all cursor-pointer shadow-2xs"
          >
            <Trash2 class="h-3.5 w-3.5" />
            <span>Delete</span>
          </button>
          <button
            type="button"
            @click.stop="printReceipt(payment)"
            class="flex-1 flex items-center justify-center gap-1 py-1.5 text-xs font-semibold rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-all cursor-pointer shadow-2xs"
          >
            <Printer class="h-3.5 w-3.5" />
            <span>Print</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ── 2. Table View ──────────────────────────────────────────────── -->
    <div v-else class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60 text-[12px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300 select-none">
              <th class="px-4 py-3.5 w-24">Payment ID</th>
              <th class="px-4 py-3.5 w-36">Date & Time</th>
              <th class="px-4 py-3.5">Student</th>
              <th class="px-4 py-3.5">Amount</th>
              <th class="px-4 py-3.5">Method</th>
              <th class="px-4 py-3.5">Received By</th>
              <th class="px-4 py-3.5">Registered By</th>
              <th class="px-4 py-3.5">Notes</th>
              <th class="px-4 py-3.5 text-center w-28">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800 text-[13px]">
            <tr
              v-for="payment in payments"
              :key="payment.id"
              @click="viewingPayment = payment"
              class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors text-zinc-800 dark:text-zinc-200 cursor-pointer"
            >
              <!-- Payment ID -->
              <td class="px-4 py-3 font-mono font-bold text-[11px] uppercase text-zinc-500 select-all">
                {{ String(payment.id).slice(0, 8) }}
              </td>

              <!-- Date & Time -->
              <td class="px-4 py-3 font-mono text-[11.5px] text-zinc-500 dark:text-zinc-400 whitespace-nowrap">
                {{ formatTimestamp(payment.created_at) }}
              </td>

              <!-- Student -->
              <td class="px-4 py-3 font-bold uppercase tracking-wide">
                <div class="flex items-center gap-1.5 min-w-0">
                  <span v-if="payment.student_id" class="font-mono text-blue-600 font-bold shrink-0">
                    {{ payment.student_id }} —
                  </span>
                  <span class="truncate text-zinc-900 dark:text-zinc-100">
                    {{ payment.student_full_name || payment.student_name || 'General Payment' }}
                  </span>
                </div>
              </td>

              <!-- Amount -->
              <td class="px-4 py-3 font-mono font-bold whitespace-nowrap">
                <span
                  class="inline-flex px-2 py-0.5 rounded-[4px] text-[12px] font-extrabold"
                  :class="Number(payment.amount) < 0
                    ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/25'
                    : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25'"
                >
                  {{ Number(payment.amount) < 0 ? '-' : '+' }}{{ formatAmount(Math.abs(Number(payment.amount))) }} UZS
                </span>
              </td>

              <!-- Method -->
              <td class="px-4 py-3">
                <span class="inline-flex px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase tracking-wider bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                  {{ payment.method }}
                </span>
              </td>

              <!-- Received By -->
              <td class="px-4 py-3 font-semibold uppercase text-zinc-700 dark:text-zinc-300 text-xs">
                {{ payment.received_by }}
              </td>

              <!-- Registered By -->
              <td class="px-4 py-3 font-bold uppercase text-zinc-800 dark:text-zinc-200 text-xs">
                {{ payment.created_by_name || payment.received_by || 'Staff' }}
              </td>

              <!-- Notes -->
              <td class="px-4 py-3 text-xs text-zinc-500 dark:text-zinc-400 max-w-[180px] truncate" :title="payment.notes || ''">
                {{ payment.notes || '—' }}
              </td>

              <!-- Actions -->
              <td class="px-4 py-3 text-center" @click.stop>
                <div class="flex items-center justify-center gap-1">
                  <button
                    type="button"
                    @click="emit('open-edit', payment)"
                    class="p-1 rounded-md text-zinc-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 transition-colors cursor-pointer"
                    title="Edit"
                  >
                    <Pencil class="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    @click="emit('delete-payment', payment)"
                    class="p-1 rounded-md text-zinc-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                    title="Delete"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    @click="printReceipt(payment)"
                    class="p-1 rounded-md text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                    title="Print"
                  >
                    <Printer class="h-3.5 w-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="payments.length === 0 && !isLoading"
      class="rounded-xl border border-zinc-200 dark:border-zinc-800 border-dashed bg-white dark:bg-[#111315] p-12 text-center text-xs text-zinc-500 dark:text-zinc-400"
    >
      No payments match your filters.
    </div>

    <!-- ── Payment Details Modal matching UniApp2 1-to-1 ───────────────────────── -->
    <div
      v-if="viewingPayment"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs select-none"
    >
      <div
        class="bg-white dark:bg-[#181a1d] border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-page-in p-6 flex flex-col gap-4 max-h-[90vh] overflow-y-auto"
        @click.stop
      >
        <!-- Modal Header -->
        <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
          <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Receipt class="h-4 w-4 text-blue-600" />
            <span>Payment Details</span>
          </h3>
          <button
            type="button"
            @click="viewingPayment = null"
            class="cursor-pointer text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
          >
            <X class="h-5 w-5" />
          </button>
        </div>

        <div class="flex flex-col gap-3.5 text-xs">
          <!-- Payment ID -->
          <div class="flex items-center justify-between text-xs border-b border-zinc-100 dark:border-zinc-800 pb-2">
            <span class="text-zinc-500 font-semibold">Payment ID</span>
            <span class="font-mono text-zinc-900 dark:text-zinc-100 bg-zinc-50 dark:bg-zinc-850 px-2 py-0.5 rounded border border-zinc-200 dark:border-zinc-700 select-all uppercase font-bold text-[11px]">
              {{ viewingPayment.id }}
            </span>
          </div>

          <!-- Student Details -->
          <div class="flex flex-col gap-1">
            <span class="text-xs font-semibold text-zinc-500">Student</span>
            <div class="px-3 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 flex flex-col gap-0.5">
              <div v-if="viewingPayment.student_id" class="flex items-center gap-2">
                <span class="text-sm font-bold text-zinc-900 dark:text-zinc-100 uppercase">
                  {{ viewingPayment.student_full_name || viewingPayment.student_name }}
                </span>
              </div>
              <span v-if="viewingPayment.student_id" class="text-xs font-semibold text-zinc-500">
                ID: <span class="text-blue-600 font-mono font-bold">{{ viewingPayment.student_id }}</span>
              </span>
              <span v-else class="text-xs text-zinc-500 italic">
                General Payment (No Student Linked)
              </span>
            </div>
          </div>

          <!-- Amount and Type -->
          <div class="grid grid-cols-2 gap-3">
            <div class="flex flex-col gap-1">
              <span class="text-xs font-semibold text-zinc-500">Amount</span>
              <div class="px-3 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 font-mono">
                <span
                  class="text-base font-extrabold"
                  :class="Number(viewingPayment.amount) < 0 ? 'text-rose-500' : 'text-emerald-500'"
                >
                  {{ Number(viewingPayment.amount) < 0 ? '-' : '+' }}{{ formatAmount(Math.abs(Number(viewingPayment.amount))) }} UZS
                </span>
              </div>
            </div>

            <div class="flex flex-col gap-1">
              <span class="text-xs font-semibold text-zinc-500">Transaction Type</span>
              <div class="px-3 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 flex items-center">
                <span
                  v-if="viewingPayment.is_withdrawal"
                  class="inline-flex px-2.5 py-1 rounded-md text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 uppercase"
                >
                  Withdrawal
                </span>
                <span
                  v-else-if="viewingPayment.is_discount"
                  class="inline-flex px-2.5 py-1 rounded-md text-xs font-bold bg-pink-500/15 text-pink-600 dark:text-pink-400 uppercase"
                >
                  Discount
                </span>
                <span
                  v-else
                  class="inline-flex px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 uppercase"
                >
                  Standard Payment
                </span>
              </div>
            </div>
          </div>

          <!-- Method and Receiver -->
          <div class="grid grid-cols-2 gap-3">
            <div class="flex flex-col gap-1">
              <span class="text-xs font-semibold text-zinc-500">Payment Method</span>
              <div class="px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 text-xs font-bold text-zinc-800 dark:text-zinc-200">
                {{ viewingPayment.method }}
              </div>
            </div>

            <div class="flex flex-col gap-1">
              <span class="text-xs font-semibold text-zinc-500">Received By</span>
              <div class="px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 text-xs font-bold text-zinc-800 dark:text-zinc-200">
                {{ viewingPayment.received_by }}
              </div>
            </div>
          </div>

          <!-- Registered By -->
          <div class="flex flex-col gap-1">
            <span class="text-xs font-semibold text-zinc-500">Registered By</span>
            <div class="px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 text-xs font-bold text-zinc-800 dark:text-zinc-200 uppercase">
              {{ viewingPayment.created_by_name || viewingPayment.received_by || 'Staff' }}
            </div>
          </div>

          <!-- Timestamp -->
          <div class="flex flex-col gap-1">
            <span class="text-xs font-semibold text-zinc-500">Timestamp</span>
            <div class="px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 text-xs font-medium text-zinc-800 dark:text-zinc-200 font-mono">
              {{ viewingPayment.created_at ? new Date(viewingPayment.created_at).toLocaleString('uz-UZ') : '—' }}
            </div>
          </div>

          <!-- Notes -->
          <div class="flex flex-col gap-1">
            <span class="text-xs font-semibold text-zinc-500">Notes / Description</span>
            <div class="px-3 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 text-xs text-zinc-800 dark:text-zinc-200 min-h-[50px] whitespace-pre-wrap">
              {{ viewingPayment.notes || 'No notes attached.' }}
            </div>
          </div>
        </div>

        <!-- Actions Footer -->
        <div class="flex items-center gap-2 mt-2 pt-3 border-t border-zinc-100 dark:border-zinc-800">
          <button
            type="button"
            @click="handleEditFromModal"
            class="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-bold rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-all cursor-pointer text-zinc-800 dark:text-zinc-200 shadow-2xs"
          >
            <Pencil class="h-3.5 w-3.5" />
            <span>Edit</span>
          </button>
          <button
            type="button"
            @click="viewingPayment && printReceipt(viewingPayment)"
            class="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-bold rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-750 transition-all cursor-pointer text-zinc-800 dark:text-zinc-200 shadow-2xs"
          >
            <Printer class="h-3.5 w-3.5" />
            <span>Print</span>
          </button>
          <button
            type="button"
            @click="viewingPayment = null"
            class="flex-1 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-all cursor-pointer shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
