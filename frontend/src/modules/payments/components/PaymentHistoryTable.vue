<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { Payment } from '@/types'
import {
  Search, FileSpreadsheet, Pencil, Trash2, Printer,
  Receipt, X, User, LayoutGrid, Table as TableIcon,
  Copy, Check, Clock, ArrowDownLeft, ArrowUpRight, Tag
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

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
const copiedField = ref<string | null>(null)

const handleCopy = (field: string, text?: string | number | null) => {
  if (!text) return
  navigator.clipboard.writeText(String(text))
  copiedField.value = field
  setTimeout(() => {
    if (copiedField.value === field) copiedField.value = null
  }, 1600)
}

// ── Responsive Zoom Scaling for Laptop Screens ─────────────────────────
const modalPanelRef = ref<HTMLElement | null>(null)
const modalZoom = ref(1)
const MIN_ZOOM = 0.65
const VIEWPORT_MARGIN = 32

const recalcZoom = () => {
  const el = modalPanelRef.value
  if (!el) return

  const prev = modalZoom.value
  modalZoom.value = 1

  nextTick(() => {
    if (!modalPanelRef.value) {
      modalZoom.value = prev
      return
    }
    const naturalH = modalPanelRef.value.offsetHeight
    const naturalW = modalPanelRef.value.offsetWidth
    if (!naturalH || !naturalW) {
      modalZoom.value = prev
      return
    }

    const availH = window.innerHeight - VIEWPORT_MARGIN
    const availW = window.innerWidth - VIEWPORT_MARGIN
    const fit = Math.min(availH / naturalH, availW / naturalW)

    modalZoom.value = fit >= 1 ? 1 : Math.max(MIN_ZOOM, Math.round(fit * 1000) / 1000)
  })
}

let resizeObserver: ResizeObserver | null = null

watch(() => viewingPayment.value, (val) => {
  if (val) {
    nextTick(() => {
      recalcZoom()
      if (modalPanelRef.value && typeof ResizeObserver !== 'undefined') {
        resizeObserver?.disconnect()
        resizeObserver = new ResizeObserver(() => {
          if (modalZoom.value === 1) recalcZoom()
        })
        resizeObserver.observe(modalPanelRef.value)
      }
    })
  } else {
    resizeObserver?.disconnect()
    resizeObserver = null
  }
})

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && viewingPayment.value) {
    viewingPayment.value = null
  }
}

onMounted(() => {
  window.addEventListener('resize', recalcZoom)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', recalcZoom)
  window.removeEventListener('keydown', handleKeydown)
  resizeObserver?.disconnect()
})

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

const handleDeleteFromModal = () => {
  if (viewingPayment.value) {
    const p = viewingPayment.value
    viewingPayment.value = null
    emit('delete-payment', p)
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
  const companyName = authStore.currentTenant?.name?.toUpperCase() || 'SALOM CRM'

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
  <div class="company-name">${companyName}</div>
  <div class="company-sub">PAYMENT RECEIPT</div>
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
  <div class="footer">★ RAHMAT! THANK YOU! ★</div>
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
      <span v-if="isLoading" class="inline-block h-3 w-24 rounded bg-zinc-200 dark:bg-zinc-800 animate-pulse align-middle" />
      <template v-else>{{ totalFilteredCount }} payments</template>
    </div>

    <!-- ── Loading Skeleton: Grid View ────────────────────────────────── -->
    <div v-if="isLoading && viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
      <div
        v-for="i in 12"
        :key="i"
        class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] p-3.5 shadow-2xs flex flex-col gap-3 animate-pulse"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="h-3.5 w-2/3 rounded bg-zinc-200 dark:bg-zinc-800" />
          <div class="h-2.5 w-12 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
        <div class="flex items-center gap-1.5 flex-wrap">
          <div class="h-5 w-24 rounded bg-zinc-100 dark:bg-zinc-800/70" />
          <div class="h-5 w-14 rounded bg-zinc-100 dark:bg-zinc-800/70" />
          <div class="h-5 w-16 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
        <div class="pt-2 border-t border-zinc-100 dark:border-zinc-800/80">
          <div class="h-3 w-1/2 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
      </div>
    </div>

    <!-- ── Loading Skeleton: Table View ───────────────────────────────── -->
    <div v-else-if="isLoading" class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60 text-[12px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300 select-none">
              <th class="px-4 py-3.5 w-[145px] whitespace-nowrap">Date &amp; Time / ID</th>
              <th class="px-4 py-3.5 w-[22%] min-w-[180px]">Student</th>
              <th class="px-4 py-3.5 w-[130px] whitespace-nowrap">Amount</th>
              <th class="px-4 py-3.5 w-[95px] whitespace-nowrap">Method</th>
              <th class="px-4 py-3.5 w-[110px] whitespace-nowrap">Received By</th>
              <th class="px-4 py-3.5 w-[110px] whitespace-nowrap">Registered By</th>
              <th class="px-4 py-3.5 w-auto min-w-[200px]">Notes</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
            <tr v-for="i in 12" :key="i" class="animate-pulse">
              <td class="px-4 py-3 whitespace-nowrap">
                <div class="h-3 w-20 rounded bg-zinc-200 dark:bg-zinc-800 mb-1.5" />
                <div class="h-2.5 w-14 rounded bg-zinc-100 dark:bg-zinc-800/70" />
              </td>
              <td class="px-4 py-3"><div class="h-3 w-4/5 rounded bg-zinc-200 dark:bg-zinc-800" /></td>
              <td class="px-4 py-3 whitespace-nowrap"><div class="h-5 w-24 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-4 py-3 whitespace-nowrap"><div class="h-3 w-14 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-4 py-3 whitespace-nowrap"><div class="h-3 w-16 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-4 py-3 whitespace-nowrap"><div class="h-3 w-16 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-4 py-3"><div class="h-3 w-3/4 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── 1. Grid View ──────────────────────────────────────────────── -->
    <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
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
              <th class="px-4 py-3.5 w-[145px] whitespace-nowrap">Date &amp; Time / ID</th>
              <th class="px-4 py-3.5 w-[22%] min-w-[180px]">Student</th>
              <th class="px-4 py-3.5 w-[130px] whitespace-nowrap">Amount</th>
              <th class="px-4 py-3.5 w-[95px] whitespace-nowrap">Method</th>
              <th class="px-4 py-3.5 w-[110px] whitespace-nowrap">Received By</th>
              <th class="px-4 py-3.5 w-[110px] whitespace-nowrap">Registered By</th>
              <th class="px-4 py-3.5 w-auto min-w-[200px]">Notes</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800 text-[13px]">
            <tr
              v-for="payment in payments"
              :key="payment.id"
              @click="viewingPayment = payment"
              class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors text-zinc-800 dark:text-zinc-200 cursor-pointer"
            >
              <!-- Date & Time on top, Payment ID below -->
              <td class="px-4 py-3 whitespace-nowrap">
                <div class="flex flex-col gap-0.5">
                  <span class="font-mono text-[12px] font-semibold text-zinc-900 dark:text-zinc-100 whitespace-nowrap">
                    {{ formatTimestamp(payment.created_at) }}
                  </span>
                  <span class="font-mono font-bold text-[10.5px] uppercase text-zinc-400 dark:text-zinc-500 select-all tracking-wider">
                    #{{ String(payment.id).slice(0, 8) }}
                  </span>
                </div>
              </td>

              <!-- Student: Full Name on top, Student ID below -->
              <td class="px-4 py-3">
                <div class="flex flex-col gap-0.5">
                  <span
                    class="font-bold uppercase tracking-wide text-zinc-900 dark:text-zinc-100 text-[13px] truncate"
                    :title="payment.student_full_name || payment.student_name || 'General Payment'"
                  >
                    {{ payment.student_full_name || payment.student_name || 'General Payment' }}
                  </span>
                  <div class="flex items-center gap-1">
                    <span v-if="payment.student_id" class="font-mono text-blue-600 dark:text-blue-400 font-bold text-[11px] tracking-wider">
                      {{ payment.student_id }}
                    </span>
                    <span v-else class="text-[10.5px] text-zinc-400 italic">
                      General Payment
                    </span>
                  </div>
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
              <td class="px-4 py-3 whitespace-nowrap">
                <span class="inline-flex px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase tracking-wider bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                  {{ payment.method }}
                </span>
              </td>

              <!-- Received By -->
              <td class="px-4 py-3 font-semibold uppercase text-zinc-700 dark:text-zinc-300 text-xs whitespace-nowrap">
                {{ payment.received_by }}
              </td>

              <!-- Registered By -->
              <td class="px-4 py-3 font-bold uppercase text-zinc-800 dark:text-zinc-200 text-xs whitespace-nowrap">
                {{ payment.created_by_name || payment.received_by || 'Staff' }}
              </td>

              <!-- Notes (Takes all remaining table width) -->
              <td class="px-4 py-3 text-xs text-zinc-600 dark:text-zinc-300 leading-relaxed" :title="payment.notes || ''">
                <span v-if="payment.notes" class="line-clamp-2">{{ payment.notes }}</span>
                <span v-else class="text-zinc-400 dark:text-zinc-600 italic">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="payments.length === 0 && !isLoading"
      class="rounded-xl border border-zinc-200 dark:border-zinc-800 border-dashed bg-white dark:bg-[#111315] py-16 px-6 text-center space-y-3"
    >
      <div class="w-14 h-14 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center mx-auto text-zinc-400">
        <Receipt class="h-7 w-7" />
      </div>
      <p class="font-bold text-sm text-zinc-800 dark:text-zinc-200">No payments found</p>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        {{ searchQuery || selectedMethod !== 'all' || selectedReceiver !== 'all'
          ? 'No payments match your filters. Try adjusting your search or filters.'
          : 'No payments have been recorded yet.' }}
      </p>
    </div>

    <!-- ── Payment Details Modal (+10% width, Auto-Fit Zoom Scaling) ───────────────────────── -->
    <div
      v-if="viewingPayment"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none overflow-hidden"
    >
      <div class="fixed inset-0" @click="viewingPayment = null" />

      <!-- Scale wrapper for smaller laptop displays -->
      <div class="relative z-10 flex items-center justify-center pointer-events-auto" :style="{ zoom: modalZoom }">
        <div
          ref="modalPanelRef"
          class="relative w-[565px] max-w-[calc(100vw-2rem)] rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl overflow-hidden flex flex-col p-4 sm:p-5 gap-3.5 text-xs text-zinc-900 dark:text-zinc-100 animate-page-in"
          @click.stop
        >
          <!-- 1. Header -->
          <div class="flex items-start justify-between gap-3">
            <div class="flex flex-col gap-0.5 min-w-0">
              <h3 class="text-[15px] font-bold text-zinc-900 dark:text-zinc-100 tracking-tight leading-tight">
                Payment Details
              </h3>
              <button
                type="button"
                @click="handleCopy('id', viewingPayment.id)"
                class="group inline-flex items-center gap-1 self-start font-mono text-[10.5px] font-medium text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors cursor-pointer"
                :title="'Click to copy full ID: ' + viewingPayment.id"
              >
                <span>#{{ String(viewingPayment.id).replace(/-/g, '').slice(-8).toUpperCase() }}</span>
                <Check v-if="copiedField === 'id'" class="w-3 h-3 text-emerald-500" />
                <Copy v-else class="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            </div>

            <button
              type="button"
              @click="viewingPayment = null"
              class="w-7 h-7 shrink-0 rounded-full flex items-center justify-center text-zinc-400 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors cursor-pointer active:scale-90"
              title="Close (Esc)"
            >
              <X class="h-3.5 w-3.5" />
            </button>
          </div>

          <!-- 2. Hero Amount -->
          <div
            class="rounded-2xl px-4 py-4 flex flex-col items-center gap-2.5 text-center"
            :class="Number(viewingPayment.amount) < 0
              ? 'bg-rose-500/8 dark:bg-rose-500/12'
              : viewingPayment.is_discount
                ? 'bg-pink-500/8 dark:bg-pink-500/12'
                : 'bg-emerald-500/8 dark:bg-emerald-500/12'"
          >
            <!-- Type pill -->
            <span
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
              :class="Number(viewingPayment.amount) < 0
                ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
                : viewingPayment.is_discount
                  ? 'bg-pink-500/15 text-pink-700 dark:text-pink-300'
                  : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'"
            >
              <ArrowDownLeft v-if="Number(viewingPayment.amount) < 0" class="w-3 h-3" />
              <ArrowUpRight v-else class="w-3 h-3" />
              <span>{{ Number(viewingPayment.amount) < 0 ? 'Withdrawal' : (viewingPayment.is_discount ? 'Discount' : 'Payment') }}</span>
            </span>

            <!-- Amount -->
            <button
              type="button"
              @click="handleCopy('amount', formatAmount(Math.abs(Number(viewingPayment.amount))))"
              class="group flex items-baseline justify-center gap-1.5 cursor-pointer transition-transform active:scale-[0.98]"
              title="Click to copy amount"
            >
              <span
                class="font-mono text-[30px] leading-none font-bold tracking-tight tabular-nums"
                :class="Number(viewingPayment.amount) < 0
                  ? 'text-rose-600 dark:text-rose-400'
                  : viewingPayment.is_discount
                    ? 'text-pink-600 dark:text-pink-400'
                    : 'text-emerald-600 dark:text-emerald-400'"
              >
                {{ Number(viewingPayment.amount) < 0 ? '−' : '+' }}{{ formatAmount(Math.abs(Number(viewingPayment.amount))) }}
              </span>
              <span class="font-mono text-[13px] font-semibold text-zinc-400 dark:text-zinc-500">UZS</span>
              <Check v-if="copiedField === 'amount'" class="w-3.5 h-3.5 text-emerald-500 self-center ml-0.5" />
              <Copy v-else class="w-3.5 h-3.5 text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity self-center ml-0.5" />
            </button>

            <!-- Method · Receiver -->
            <div class="flex items-center justify-center gap-1.5 text-[11px] text-zinc-500 dark:text-zinc-400 font-medium flex-wrap">
              <span class="font-semibold text-zinc-700 dark:text-zinc-300">{{ viewingPayment.method || '—' }}</span>
              <span class="text-zinc-300 dark:text-zinc-600">·</span>
              <span>received by</span>
              <span class="font-semibold text-zinc-700 dark:text-zinc-300">{{ viewingPayment.received_by || '—' }}</span>
            </div>
          </div>

          <!-- 3. Grouped Detail List (iOS inset-grouped style) -->
          <div class="rounded-2xl bg-zinc-50 dark:bg-zinc-850/60 divide-y divide-zinc-200/70 dark:divide-zinc-800 overflow-hidden">
            <!-- Student -->
            <div class="flex items-center justify-between gap-3 px-3.5 py-2.5">
              <span class="text-[11.5px] text-zinc-500 dark:text-zinc-400 shrink-0">Student</span>
              <div class="flex items-center gap-2 min-w-0">
                <span
                  class="text-[12.5px] font-semibold text-zinc-900 dark:text-zinc-100 truncate text-right"
                  :title="viewingPayment.student_full_name || viewingPayment.student_name || 'General Payment'"
                >
                  {{ viewingPayment.student_full_name || viewingPayment.student_name || 'General Payment' }}
                </span>
                <button
                  v-if="viewingPayment.student_id"
                  type="button"
                  @click="handleCopy('student', viewingPayment.student_id)"
                  class="group inline-flex items-center gap-1 shrink-0 px-1.5 py-0.5 rounded-md font-mono text-[10.5px] font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 transition-colors cursor-pointer"
                  title="Click to copy Student ID"
                >
                  <span>{{ viewingPayment.student_id }}</span>
                  <Check v-if="copiedField === 'student'" class="w-2.5 h-2.5 text-emerald-500" />
                  <Copy v-else class="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              </div>
            </div>

            <!-- Registered by -->
            <div class="flex items-center justify-between gap-3 px-3.5 py-2.5">
              <span class="text-[11.5px] text-zinc-500 dark:text-zinc-400 shrink-0">Registered by</span>
              <span class="text-[12.5px] font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                {{ viewingPayment.created_by_name || viewingPayment.received_by || 'Staff' }}
              </span>
            </div>

            <!-- Date -->
            <div class="flex items-center justify-between gap-3 px-3.5 py-2.5">
              <span class="text-[11.5px] text-zinc-500 dark:text-zinc-400 shrink-0">Date &amp; time</span>
              <span class="font-mono text-[12px] font-medium text-zinc-700 dark:text-zinc-300 tabular-nums">
                {{ formatTimestamp(viewingPayment.created_at) || '—' }}
              </span>
            </div>

            <!-- Notes -->
            <div class="px-3.5 py-2.5 flex flex-col gap-1">
              <div class="flex items-center justify-between gap-3">
                <span class="text-[11.5px] text-zinc-500 dark:text-zinc-400">Notes</span>
                <button
                  v-if="viewingPayment.notes"
                  type="button"
                  @click="handleCopy('notes', viewingPayment.notes)"
                  class="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 flex items-center gap-1 cursor-pointer shrink-0"
                  title="Copy notes"
                >
                  <Check v-if="copiedField === 'notes'" class="w-3 h-3 text-emerald-500" />
                  <Copy v-else class="w-2.5 h-2.5" />
                </button>
              </div>
              <p
                class="text-[12.5px] leading-relaxed whitespace-pre-wrap"
                :class="viewingPayment.notes
                  ? 'text-zinc-800 dark:text-zinc-200'
                  : 'text-zinc-400 dark:text-zinc-500 italic'"
              >
                {{ viewingPayment.notes || 'No notes attached.' }}
              </p>
            </div>
          </div>

          <!-- 4. Actions -->
          <div class="flex flex-col gap-2 pt-0.5">
            <!-- Primary -->
            <button
              type="button"
              @click="viewingPayment = null"
              class="w-full py-2.5 text-[13px] font-semibold rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-all cursor-pointer active:scale-[0.99] shadow-sm shadow-blue-600/25"
            >
              Done
            </button>

            <!-- Secondary row -->
            <div class="flex items-center gap-2">
              <button
                type="button"
                @click="viewingPayment && printReceipt(viewingPayment)"
                class="flex-1 flex items-center justify-center gap-1.5 py-2 text-[12px] font-semibold rounded-xl bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-200 transition-all cursor-pointer active:scale-[0.98]"
                title="Print 80mm Thermal Receipt"
              >
                <Printer class="h-3.5 w-3.5" />
                <span>Print</span>
              </button>

              <button
                type="button"
                @click="handleEditFromModal"
                class="flex-1 flex items-center justify-center gap-1.5 py-2 text-[12px] font-semibold rounded-xl bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-200 transition-all cursor-pointer active:scale-[0.98]"
                title="Edit Payment"
              >
                <Pencil class="h-3.5 w-3.5" />
                <span>Edit</span>
              </button>

              <button
                type="button"
                @click="handleDeleteFromModal"
                class="flex-1 flex items-center justify-center gap-1.5 py-2 text-[12px] font-semibold rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 transition-all cursor-pointer active:scale-[0.98]"
                title="Delete Payment"
              >
                <Trash2 class="h-3.5 w-3.5" />
                <span>Delete</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
