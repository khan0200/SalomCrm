<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { Payment, Student } from '@/types'
import {
  DollarSign, TrendingUp, TrendingDown, Users, AlertCircle,
  FileSpreadsheet, Filter, Calendar, Search, ArrowUpRight,
  ArrowDownRight, Percent, Wallet, CreditCard, Lock,
  ChevronDown, ChevronUp, Printer, Copy, Check, X,
  Clock, Tag, RefreshCw
} from 'lucide-vue-next'

const props = defineProps<{
  payments: Payment[]
  students: Student[]
  paymentMethods: string[]
  paymentReceivers: string[]
  isLoading?: boolean
}>()

const emit = defineEmits<{
  (e: 'lock-finance'): void
  (e: 'open-edit-payment', payment: Payment): void
  (e: 'delete-payment', payment: Payment): void
  (e: 'open-add-payment', studentId?: string): void
}>()

const ITEMS_PER_PAGE = 30

// ── Date Filters ──────────────────────────────────────────────────────
type DatePreset = 'all' | 'today' | 'yesterday' | 'this_week' | 'this_month' | 'last_month' | 'this_year' | 'custom'

const selectedDatePreset = ref<DatePreset>('this_month')
const customStartDate = ref('')
const customEndDate = ref('')

// Other Filters
const searchFinance = ref('')
const selectedMethod = ref('all')
const selectedReceiver = ref('all')
const selectedType = ref<'all' | 'payments' | 'withdrawals' | 'discounts'>('all')
const currentPage = ref(1)

// Receipt Modal State
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

// ── Date Range Computation Helpers ─────────────────────────────────────
const getDateRange = (preset: DatePreset): { start: Date | null; end: Date | null } => {
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0)
  const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999)

  switch (preset) {
    case 'today':
      return { start: todayStart, end: todayEnd }

    case 'yesterday': {
      const yStart = new Date(todayStart)
      yStart.setDate(yStart.getDate() - 1)
      const yEnd = new Date(todayEnd)
      yEnd.setDate(yEnd.getDate() - 1)
      return { start: yStart, end: yEnd }
    }

    case 'this_week': {
      // Start of current week (Monday)
      const day = todayStart.getDay()
      const diff = todayStart.getDate() - day + (day === 0 ? -6 : 1)
      const weekStart = new Date(todayStart.setDate(diff))
      return { start: weekStart, end: todayEnd }
    }

    case 'this_month': {
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0, 0)
      return { start: monthStart, end: todayEnd }
    }

    case 'last_month': {
      const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1, 0, 0, 0, 0)
      const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59, 999)
      return { start: lastMonthStart, end: lastMonthEnd }
    }

    case 'this_year': {
      const yearStart = new Date(now.getFullYear(), 0, 1, 0, 0, 0, 0)
      return { start: yearStart, end: todayEnd }
    }

    case 'custom': {
      const start = customStartDate.value ? new Date(`${customStartDate.value}T00:00:00`) : null
      const end = customEndDate.value ? new Date(`${customEndDate.value}T23:59:59.999`) : null
      return { start, end }
    }

    case 'all':
    default:
      return { start: null, end: null }
  }
}

const currentRange = computed(() => getDateRange(selectedDatePreset.value))

// ── Overall Fixed KPI Calculations (Today, This Month, Total Debt) ─────
const todayMetrics = computed(() => {
  const { start, end } = getDateRange('today')
  if (!start || !end) return { collected: 0, count: 0 }

  let total = 0
  let count = 0
  props.payments.forEach(p => {
    if (!p.created_at || p.is_discount || p.is_withdrawal) return
    const d = new Date(p.created_at)
    if (d >= start && d <= end) {
      const amt = Number(p.amount) || 0
      if (amt > 0) {
        total += amt
        count++
      }
    }
  })
  return { collected: total, count }
})

const thisMonthMetrics = computed(() => {
  const { start, end } = getDateRange('this_month')
  if (!start || !end) return { collected: 0, count: 0 }

  let total = 0
  let count = 0
  props.payments.forEach(p => {
    if (!p.created_at || p.is_discount || p.is_withdrawal) return
    const d = new Date(p.created_at)
    if (d >= start && d <= end) {
      const amt = Number(p.amount) || 0
      if (amt > 0) {
        total += amt
        count++
      }
    }
  })
  return { collected: total, count }
})

// Debt analysis across all active students
const debtMetrics = computed(() => {
  let totalDebt = 0
  let debtorCount = 0
  let totalAdvance = 0
  let fullyPaidCount = 0
  let totalActiveStudents = 0

  props.students.forEach(s => {
    if (s.is_deleted) return
    totalActiveStudents++
    const bal = Number(s.balance) || 0
    if (bal < 0) {
      totalDebt += Math.abs(bal)
      debtorCount++
    } else if (bal > 0) {
      totalAdvance += bal
    } else {
      fullyPaidCount++
    }
  })

  return {
    totalDebt,
    debtorCount,
    totalAdvance,
    fullyPaidCount,
    totalActiveStudents
  }
})

// ── Filtered Payments according to selected date range & filters ───────
const filteredPayments = computed(() => {
  const { start, end } = currentRange.value

  return props.payments.filter(p => {
    // 1. Date Range Filter
    if (p.created_at) {
      const d = new Date(p.created_at)
      if (start && d < start) return false
      if (end && d > end) return false
    }

    // 2. Transaction Type Filter
    if (selectedType.value === 'payments') {
      if (p.is_discount || p.is_withdrawal || Number(p.amount) <= 0) return false
    } else if (selectedType.value === 'withdrawals') {
      if (!p.is_withdrawal && Number(p.amount) >= 0) return false
    } else if (selectedType.value === 'discounts') {
      if (!p.is_discount) return false
    }

    // 3. Payment Method Filter
    if (selectedMethod.value !== 'all' && p.method !== selectedMethod.value) {
      return false
    }

    // 4. Receiver Filter
    if (selectedReceiver.value !== 'all' && p.received_by !== selectedReceiver.value) {
      return false
    }

    // 5. Search Query
    if (searchFinance.value.trim()) {
      const q = searchFinance.value.toLowerCase()
      const matchName = (p.student_full_name || p.student_name || '').toLowerCase().includes(q)
      const matchId = (p.student_id || '').toLowerCase().includes(q)
      const matchReceiver = (p.received_by || '').toLowerCase().includes(q)
      const matchNotes = (p.notes || '').toLowerCase().includes(q)
      if (!matchName && !matchId && !matchReceiver && !matchNotes) return false
    }

    return true
  })
})

// Strictly sort payments descending by created_at
const sortedFilteredPayments = computed(() => {
  return [...filteredPayments.value].sort((a, b) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
    return timeB - timeA
  })
})

// ── Selected Period KPI Summary ───────────────────────────────────────
const periodMetrics = computed(() => {
  let totalCollected = 0
  let totalWithdrawals = 0
  let totalDiscounts = 0
  let collectedTxCount = 0
  let withdrawalTxCount = 0
  let discountTxCount = 0

  filteredPayments.value.forEach(p => {
    const amt = Number(p.amount) || 0
    if (p.is_discount) {
      totalDiscounts += Math.abs(amt)
      discountTxCount++
    } else if (p.is_withdrawal || amt < 0) {
      totalWithdrawals += Math.abs(amt)
      withdrawalTxCount++
    } else {
      totalCollected += amt
      collectedTxCount++
    }
  })

  const netCashflow = totalCollected - totalWithdrawals

  return {
    totalCollected,
    totalWithdrawals,
    totalDiscounts,
    netCashflow,
    collectedTxCount,
    withdrawalTxCount,
    discountTxCount,
    totalTxCount: filteredPayments.value.length
  }
})

// ── Method Breakdown for selected period ──────────────────────────────
const methodBreakdown = computed(() => {
  const map = new Map<string, { amount: number; count: number }>()

  filteredPayments.value.forEach(p => {
    if (p.is_discount || p.is_withdrawal) return
    const amt = Number(p.amount) || 0
    if (amt <= 0) return

    const m = p.method || 'Unspecified'
    const existing = map.get(m) || { amount: 0, count: 0 }
    map.set(m, {
      amount: existing.amount + amt,
      count: existing.count + 1
    })
  })

  const total = periodMetrics.value.totalCollected || 1
  return Array.from(map.entries())
    .map(([method, data]) => ({
      method,
      amount: data.amount,
      count: data.count,
      percent: Math.round((data.amount / total) * 100)
    }))
    .sort((a, b) => b.amount - a.amount)
})

// ── Receiver Breakdown for selected period ────────────────────────────
const receiverBreakdown = computed(() => {
  const map = new Map<string, { amount: number; count: number }>()

  filteredPayments.value.forEach(p => {
    if (p.is_discount || p.is_withdrawal) return
    const amt = Number(p.amount) || 0
    if (amt <= 0) return

    const r = p.received_by || 'Unspecified'
    const existing = map.get(r) || { amount: 0, count: 0 }
    map.set(r, {
      amount: existing.amount + amt,
      count: existing.count + 1
    })
  })

  const total = periodMetrics.value.totalCollected || 1
  return Array.from(map.entries())
    .map(([receiver, data]) => ({
      receiver,
      amount: data.amount,
      count: data.count,
      percent: Math.round((data.amount / total) * 100)
    }))
    .sort((a, b) => b.amount - a.amount)
})

// ── Pagination ────────────────────────────────────────────────────────
const totalPages = computed(() => Math.max(1, Math.ceil(sortedFilteredPayments.value.length / ITEMS_PER_PAGE)))
const paginatedPayments = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return sortedFilteredPayments.value.slice(start, start + ITEMS_PER_PAGE)
})

watch([selectedDatePreset, customStartDate, customEndDate, searchFinance, selectedMethod, selectedReceiver, selectedType], () => {
  currentPage.value = 1
})

// Number formatting helper
const formatUZS = (val: number | string | null | undefined) => {
  if (val === null || val === undefined) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('uz-UZ').format(Math.round(num || 0))
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ── Export Financial Report to Excel ─────────────────────────────────
const exportFinanceReportToExcel = async () => {
  if (sortedFilteredPayments.value.length === 0) {
    alert('No transaction records to export in the selected filter range!')
    return
  }

  const XLSX = await import('xlsx-js-style')

  const pad = (n: number) => String(n).padStart(2, '0')
  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  }

  // Summary Rows
  const summaryRows = [
    { A: 'SALOM CRM - FINANCIAL REPORT' },
    { A: `Report Date Range: ${selectedDatePreset.value.toUpperCase()}` },
    { A: `Generated At: ${formatDateTime(new Date().toISOString())}` },
    { A: '' },
    { A: 'METRIC', B: 'AMOUNT (UZS)', C: 'DETAILS' },
    { A: 'Total Collected (Selected Range)', B: periodMetrics.value.totalCollected, C: `${periodMetrics.value.collectedTxCount} payments` },
    { A: 'Total Collected (Today)', B: todayMetrics.value.collected, C: `${todayMetrics.value.count} payments today` },
    { A: 'Total Collected (This Month)', B: thisMonthMetrics.value.collected, C: `${thisMonthMetrics.value.count} payments this month` },
    { A: 'Total Outstanding Debt', B: debtMetrics.value.totalDebt, C: `${debtMetrics.value.debtorCount} active debtor students` },
    { A: 'Total Discounts Given', B: periodMetrics.value.totalDiscounts, C: `${periodMetrics.value.discountTxCount} discounts` },
    { A: 'Total Withdrawals', B: periodMetrics.value.totalWithdrawals, C: `${periodMetrics.value.withdrawalTxCount} withdrawals` },
    { A: 'Net Cashflow', B: periodMetrics.value.netCashflow, C: 'Collected minus Withdrawals' },
    { A: '' },
    { A: 'ITEMIZED FINANCIAL TRANSACTIONS' }
  ]

  const ledgerData = sortedFilteredPayments.value.map((p, index) => {
    let txType = 'Payment'
    if (p.is_withdrawal) txType = 'Withdrawal'
    else if (p.is_discount) txType = 'Discount'

    return {
      No: index + 1,
      'Transaction ID': p.id ? String(p.id).toUpperCase() : '',
      'Student ID': p.student_id || '—',
      'Student Name': p.student_full_name || p.student_name || 'General Payment',
      'Type': txType,
      'Payment Method': p.method || '—',
      'Received By': p.received_by || '—',
      'Amount (UZS)': Number(p.amount) || 0,
      'Date & Time': formatDateTime(p.created_at),
      'Notes': p.notes || ''
    }
  })

  const wb = XLSX.utils.book_new()

  // 1. Transactions Sheet
  const ws = XLSX.utils.json_to_sheet(ledgerData)
  ws['!cols'] = [
    { wch: 6 },   // No
    { wch: 22 },  // ID
    { wch: 15 },  // Student ID
    { wch: 30 },  // Student Name
    { wch: 15 },  // Type
    { wch: 18 },  // Method
    { wch: 18 },  // Received By
    { wch: 18 },  // Amount
    { wch: 22 },  // Date
    { wch: 35 }   // Notes
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'Transactions Ledger')

  // 2. Summary Sheet
  const wsSummary = XLSX.utils.json_to_sheet(summaryRows, { skipHeader: true })
  wsSummary['!cols'] = [{ wch: 35 }, { wch: 22 }, { wch: 35 }]
  XLSX.utils.book_append_sheet(wb, wsSummary, 'Financial KPI Summary')

  const dateStr = new Date().toISOString().split('T')[0]
  const filename = `Finance_Report_${selectedDatePreset.value}_${dateStr}.xlsx`
  XLSX.writeFile(wb, filename)
}
</script>

<template>
  <div class="flex flex-col gap-5 select-none text-xs">
    <!-- ── Top Header Banner with Lock & Export ─────────────────────────── -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-transparent dark:from-blue-950/40 dark:via-indigo-950/30 dark:to-transparent border border-blue-200/60 dark:border-blue-900/40 rounded-2xl p-4 shadow-2xs">
      <div class="flex items-center gap-3">
        <div class="h-10 w-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
          <DollarSign class="h-5 w-5 stroke-[2.5]" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h2 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
              Executive Financial Overview
            </h2>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              Authorized
            </span>
          </div>
          <p class="text-[11px] text-zinc-500 dark:text-zinc-400">
            Real-time analytics, revenue collection, outstanding debt, and cashier reconciliations.
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="exportFinanceReportToExcel"
          class="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl border border-emerald-300 dark:border-emerald-700/60 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-all cursor-pointer shadow-2xs"
          title="Export Filtered Financial Report to Excel"
        >
          <FileSpreadsheet class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <span>Export Excel</span>
        </button>

        <button
          type="button"
          @click="emit('lock-finance')"
          class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all cursor-pointer shadow-2xs"
          title="Lock Finance Dashboard Session"
        >
          <Lock class="h-3.5 w-3.5 text-amber-500" />
          <span>Lock Tab</span>
        </button>
      </div>
    </div>

    <!-- ── KPI Cards Grid ──────────────────────────────────────────────── -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
      <!-- 1. Total Collected (Today & This Month) -->
      <div class="rounded-2xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs flex flex-col justify-between relative overflow-hidden">
        <div class="flex items-start justify-between">
          <div>
            <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Total Collected
            </span>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 font-mono tracking-tight">
                {{ formatUZS(thisMonthMetrics.collected) }}
              </span>
              <span class="text-[11px] font-bold text-zinc-400 font-mono">UZS</span>
            </div>
            <span class="text-[10.5px] font-semibold text-blue-600 dark:text-blue-400">
              This Month ({{ thisMonthMetrics.count }} payments)
            </span>
          </div>
          <div class="h-9 w-9 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <TrendingUp class="h-4.5 w-4.5" />
          </div>
        </div>

        <div class="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px]">
          <span class="text-zinc-500 dark:text-zinc-400">Today:</span>
          <span class="font-bold text-emerald-600 dark:text-emerald-400 font-mono">
            +{{ formatUZS(todayMetrics.collected) }} UZS
          </span>
        </div>
      </div>

      <!-- 2. Total Outstanding Debt -->
      <div class="rounded-2xl border border-red-200/60 dark:border-red-950/50 bg-white dark:bg-[#111315] p-4 shadow-2xs flex flex-col justify-between relative overflow-hidden">
        <div class="flex items-start justify-between">
          <div>
            <span class="text-[11px] font-bold uppercase tracking-wider text-red-600 dark:text-red-400">
              Outstanding Debt
            </span>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-xl font-extrabold text-red-600 dark:text-red-400 font-mono tracking-tight">
                -{{ formatUZS(debtMetrics.totalDebt) }}
              </span>
              <span class="text-[11px] font-bold text-zinc-400 font-mono">UZS</span>
            </div>
            <span class="text-[10.5px] font-semibold text-zinc-500 dark:text-zinc-400">
              Across {{ debtMetrics.debtorCount }} debtor students
            </span>
          </div>
          <div class="h-9 w-9 rounded-xl bg-red-500/10 text-red-600 dark:text-red-400 flex items-center justify-center">
            <AlertCircle class="h-4.5 w-4.5" />
          </div>
        </div>

        <div class="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px]">
          <span class="text-zinc-500 dark:text-zinc-400">Fully Paid:</span>
          <span class="font-bold text-zinc-700 dark:text-zinc-300 font-mono">
            {{ debtMetrics.fullyPaidCount }} of {{ debtMetrics.totalActiveStudents }} active
          </span>
        </div>
      </div>

      <!-- 3. Total Discounts Given -->
      <div class="rounded-2xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs flex flex-col justify-between relative overflow-hidden">
        <div class="flex items-start justify-between">
          <div>
            <span class="text-[11px] font-bold uppercase tracking-wider text-pink-600 dark:text-pink-400">
              Discounts Given
            </span>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-xl font-extrabold text-pink-600 dark:text-pink-400 font-mono tracking-tight">
                {{ formatUZS(periodMetrics.totalDiscounts) }}
              </span>
              <span class="text-[11px] font-bold text-zinc-400 font-mono">UZS</span>
            </div>
            <span class="text-[10.5px] font-semibold text-zinc-500 dark:text-zinc-400">
              In selected period ({{ periodMetrics.discountTxCount }} promos)
            </span>
          </div>
          <div class="h-9 w-9 rounded-xl bg-pink-500/10 text-pink-600 dark:text-pink-400 flex items-center justify-center">
            <Percent class="h-4.5 w-4.5" />
          </div>
        </div>

        <div class="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px]">
          <span class="text-zinc-500 dark:text-zinc-400">Selected Type:</span>
          <span class="font-bold text-zinc-700 dark:text-zinc-300 capitalize">
            {{ selectedType }}
          </span>
        </div>
      </div>

      <!-- 4. Total Withdrawals & Net Cashflow -->
      <div class="rounded-2xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs flex flex-col justify-between relative overflow-hidden">
        <div class="flex items-start justify-between">
          <div>
            <span class="text-[11px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
              Total Withdrawals
            </span>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-xl font-extrabold text-amber-600 dark:text-amber-400 font-mono tracking-tight">
                -{{ formatUZS(periodMetrics.totalWithdrawals) }}
              </span>
              <span class="text-[11px] font-bold text-zinc-400 font-mono">UZS</span>
            </div>
            <span class="text-[10.5px] font-semibold text-zinc-500 dark:text-zinc-400">
              {{ periodMetrics.withdrawalTxCount }} refunds/deductions
            </span>
          </div>
          <div class="h-9 w-9 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center">
            <TrendingDown class="h-4.5 w-4.5" />
          </div>
        </div>

        <div class="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px]">
          <span class="text-zinc-500 dark:text-zinc-400">Net Period Cashflow:</span>
          <span
            class="font-bold font-mono"
            :class="periodMetrics.netCashflow >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'"
          >
            {{ periodMetrics.netCashflow >= 0 ? '+' : '' }}{{ formatUZS(periodMetrics.netCashflow) }} UZS
          </span>
        </div>
      </div>
    </div>

    <!-- ── Filter Controls Bar ─────────────────────────────────────────── -->
    <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs space-y-3">
      <!-- Row 1: Date Range Presets -->
      <div class="flex flex-wrap items-center justify-between gap-2.5">
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 mr-1 flex items-center gap-1">
            <Calendar class="h-3.5 w-3.5" />
            <span>Range:</span>
          </span>
          <button
            v-for="preset in [
              { key: 'today', label: 'Today' },
              { key: 'yesterday', label: 'Yesterday' },
              { key: 'this_week', label: 'This Week' },
              { key: 'this_month', label: 'This Month' },
              { key: 'last_month', label: 'Last Month' },
              { key: 'this_year', label: 'This Year' },
              { key: 'all', label: 'All Time' },
              { key: 'custom', label: 'Custom Range' }
            ]"
            :key="preset.key"
            type="button"
            @click="selectedDatePreset = preset.key as DatePreset"
            class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer select-none shrink-0"
            :class="selectedDatePreset === preset.key
              ? 'bg-blue-600 text-white shadow-xs'
              : 'border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'"
          >
            {{ preset.label }}
          </button>
        </div>
      </div>

      <!-- Custom Date Pickers (Shown if Custom Range is active) -->
      <div v-if="selectedDatePreset === 'custom'" class="flex flex-wrap items-center gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800 animate-in fade-in duration-150">
        <div class="flex items-center gap-2">
          <label class="text-[11px] font-bold text-zinc-500 dark:text-zinc-400">From:</label>
          <input
            type="date"
            v-model="customStartDate"
            class="rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 px-2.5 py-1 text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-[11px] font-bold text-zinc-500 dark:text-zinc-400">To:</label>
          <input
            type="date"
            v-model="customEndDate"
            class="rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 px-2.5 py-1 text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <!-- Row 2: Search + Method + Receiver + Type Dropdowns -->
      <div class="flex flex-wrap items-center gap-2.5 pt-2 border-t border-zinc-100 dark:border-zinc-800">
        <!-- Search Input -->
        <div class="relative flex-1 min-w-[200px]">
          <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400 pointer-events-none" />
          <input
            type="text"
            v-model="searchFinance"
            placeholder="Search by student name, ID, receiver, notes..."
            class="w-full pl-9 pr-4 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <!-- Payment Method Filter -->
        <div class="relative min-w-[140px]">
          <select
            v-model="selectedMethod"
            class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 font-semibold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="all">All Methods</option>
            <option v-for="m in paymentMethods" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>

        <!-- Receiver Filter -->
        <div class="relative min-w-[140px]">
          <select
            v-model="selectedReceiver"
            class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 font-semibold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="all">All Receivers</option>
            <option v-for="r in paymentReceivers" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>

        <!-- Transaction Type Filter -->
        <div class="relative min-w-[150px]">
          <select
            v-model="selectedType"
            class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 font-semibold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="all">All Transaction Types</option>
            <option value="payments">Payments Only (+)</option>
            <option value="withdrawals">Withdrawals Only (-)</option>
            <option value="discounts">Discounts Only</option>
          </select>
        </div>
      </div>
    </div>

    <!-- ── Breakdown Sections: Method & Cashier Breakdown ──────────────── -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Method Breakdown Card -->
      <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <CreditCard class="h-4 w-4 text-blue-600" />
            <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              Payment Channels Distribution
            </h3>
          </div>
          <span class="text-[11px] font-bold text-zinc-500">
            Total: {{ formatUZS(periodMetrics.totalCollected) }} UZS
          </span>
        </div>

        <div v-if="methodBreakdown.length === 0" class="py-6 text-center text-zinc-400">
          No payment collections recorded in this period.
        </div>
        <div v-else class="space-y-2.5">
          <div
            v-for="item in methodBreakdown"
            :key="item.method"
            class="p-2 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-100 dark:border-zinc-800/80 flex flex-col gap-1.5"
          >
            <div class="flex items-center justify-between text-xs font-bold">
              <span class="text-zinc-800 dark:text-zinc-200 uppercase">{{ item.method }}</span>
              <div class="flex items-center gap-2 font-mono">
                <span class="text-zinc-900 dark:text-zinc-100">{{ formatUZS(item.amount) }} UZS</span>
                <span class="text-[10.5px] text-zinc-400 font-sans">({{ item.count }} tx / {{ item.percent }}%)</span>
              </div>
            </div>
            <!-- Progress Bar -->
            <div class="h-1.5 w-full rounded-full bg-zinc-200 dark:bg-zinc-750 overflow-hidden">
              <div
                class="h-full rounded-full bg-blue-600 transition-all duration-300"
                :style="{ width: `${item.percent}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Receiver / Cashier Breakdown Card -->
      <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <Users class="h-4 w-4 text-emerald-600" />
            <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              Cashier & Receiver Breakdown
            </h3>
          </div>
          <span class="text-[11px] font-bold text-zinc-500">
            {{ receiverBreakdown.length }} active receivers
          </span>
        </div>

        <div v-if="receiverBreakdown.length === 0" class="py-6 text-center text-zinc-400">
          No cashier records in this period.
        </div>
        <div v-else class="space-y-2.5">
          <div
            v-for="item in receiverBreakdown"
            :key="item.receiver"
            class="p-2 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-100 dark:border-zinc-800/80 flex flex-col gap-1.5"
          >
            <div class="flex items-center justify-between text-xs font-bold">
              <span class="text-zinc-800 dark:text-zinc-200 uppercase">{{ item.receiver }}</span>
              <div class="flex items-center gap-2 font-mono">
                <span class="text-zinc-900 dark:text-zinc-100">{{ formatUZS(item.amount) }} UZS</span>
                <span class="text-[10.5px] text-zinc-400 font-sans">({{ item.count }} tx / {{ item.percent }}%)</span>
              </div>
            </div>
            <!-- Progress Bar -->
            <div class="h-1.5 w-full rounded-full bg-zinc-200 dark:bg-zinc-750 overflow-hidden">
              <div
                class="h-full rounded-full bg-emerald-600 transition-all duration-300"
                :style="{ width: `${item.percent}%` }"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Financial Transactions Ledger Table ─────────────────────────── -->
    <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <div class="px-5 py-3.5 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-800 dark:text-zinc-200">
            Financial Transactions Ledger
          </h3>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-mono">
            {{ sortedFilteredPayments.length }} records
          </span>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60 text-[11.5px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300 select-none">
              <th class="px-4 py-3 w-12 text-center">No</th>
              <th class="px-4 py-3 w-[24%]">Student / Full Name</th>
              <th class="px-4 py-3 w-[14%]">Type</th>
              <th class="px-4 py-3 w-[16%]">Method / Channel</th>
              <th class="px-4 py-3 w-[14%]">Received By</th>
              <th class="px-4 py-3 w-[16%] text-right">Amount</th>
              <th class="px-4 py-3 w-[16%]">Date & Time</th>
              <th class="px-4 py-3 text-center w-16">Receipt</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800 text-[13px]">
            <tr
              v-for="(p, idx) in paginatedPayments"
              :key="p.id"
              class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors text-zinc-800 dark:text-zinc-200"
            >
              <!-- Index -->
              <td class="px-4 py-3 text-center text-zinc-400 font-mono text-[11px]">
                {{ (currentPage - 1) * ITEMS_PER_PAGE + idx + 1 }}
              </td>

              <!-- Student Full Name & ID -->
              <td class="px-4 py-3">
                <div class="flex flex-col gap-0.5">
                  <span class="font-bold uppercase tracking-wide text-zinc-900 dark:text-zinc-100 truncate">
                    {{ p.student_full_name || p.student_name || 'General Payment' }}
                  </span>
                  <span class="font-mono text-[11px] font-bold text-[#0066cc] dark:text-blue-400">
                    {{ p.student_id || '—' }}
                  </span>
                </div>
              </td>

              <!-- Transaction Type Badge -->
              <td class="px-4 py-3">
                <span
                  v-if="p.is_withdrawal"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-[5px] text-[11px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                >
                  <ArrowDownRight class="h-3 w-3" />
                  <span>Withdrawal</span>
                </span>
                <span
                  v-else-if="p.is_discount"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-[5px] text-[11px] font-bold bg-pink-500/10 text-pink-600 dark:text-pink-400 border border-pink-500/20"
                >
                  <Percent class="h-3 w-3" />
                  <span>Discount</span>
                </span>
                <span
                  v-else
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-[5px] text-[11px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                >
                  <ArrowUpRight class="h-3 w-3" />
                  <span>Payment</span>
                </span>
              </td>

              <!-- Method -->
              <td class="px-4 py-3 font-semibold uppercase text-zinc-700 dark:text-zinc-300">
                {{ p.method || '—' }}
              </td>

              <!-- Receiver -->
              <td class="px-4 py-3 font-medium uppercase text-zinc-500 dark:text-zinc-400">
                {{ p.received_by || '—' }}
              </td>

              <!-- Amount -->
              <td class="px-4 py-3 text-right font-mono font-extrabold text-[13.5px]">
                <span
                  :class="p.is_withdrawal ? 'text-amber-600 dark:text-amber-400' : p.is_discount ? 'text-pink-600 dark:text-pink-400' : 'text-emerald-600 dark:text-emerald-400'"
                >
                  {{ p.is_withdrawal ? '-' : p.is_discount ? '' : '+' }}{{ formatUZS(Math.abs(Number(p.amount))) }} UZS
                </span>
              </td>

              <!-- Date & Time -->
              <td class="px-4 py-3 text-zinc-500 dark:text-zinc-400 font-mono text-[11.5px]">
                {{ formatDate(p.created_at) }}
              </td>

              <!-- Receipt View -->
              <td class="px-4 py-3 text-center">
                <button
                  type="button"
                  @click="viewingPayment = p"
                  class="p-1.5 rounded-lg text-zinc-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 transition-colors cursor-pointer"
                  title="View / Print Receipt"
                >
                  <Printer class="h-4 w-4" />
                </button>
              </td>
            </tr>

            <!-- Empty State -->
            <tr v-if="paginatedPayments.length === 0">
              <td colspan="8" class="px-6 py-12 text-center text-zinc-400">
                No financial transactions matching the selected filters.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div v-if="totalPages > 1" class="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
        <span class="text-xs text-zinc-500 font-mono">
          Page {{ currentPage }} of {{ totalPages }} ({{ sortedFilteredPayments.length }} records)
        </span>
        <div class="flex items-center gap-1.5">
          <button
            :disabled="currentPage === 1"
            @click="currentPage--"
            class="px-3 py-1 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 disabled:opacity-40 cursor-pointer text-zinc-700 dark:text-zinc-300"
          >
            Prev
          </button>
          <button
            :disabled="currentPage === totalPages"
            @click="currentPage++"
            class="px-3 py-1 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 disabled:opacity-40 cursor-pointer text-zinc-700 dark:text-zinc-300"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- ── Receipt Modal ───────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="viewingPayment"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none"
      >
        <div class="relative w-full max-w-lg rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] p-6 shadow-2xl space-y-4">
          <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
            <div class="flex items-center gap-2">
              <Printer class="h-5 w-5 text-blue-600" />
              <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                Official Payment Receipt
              </h3>
            </div>
            <button
              type="button"
              @click="viewingPayment = null"
              class="p-1 rounded-lg text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 cursor-pointer"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <div class="space-y-2.5 text-xs">
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Receipt ID:</span>
              <span class="font-mono font-bold">{{ viewingPayment.id }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Student ID:</span>
              <span class="font-mono font-bold text-blue-600">{{ viewingPayment.student_id || '—' }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Student Name:</span>
              <span class="font-bold uppercase">{{ viewingPayment.student_full_name || viewingPayment.student_name || 'General' }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Amount:</span>
              <span class="font-mono font-extrabold text-sm text-emerald-600 dark:text-emerald-400">
                {{ formatUZS(Math.abs(Number(viewingPayment.amount))) }} UZS
              </span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Payment Channel:</span>
              <span class="font-bold uppercase">{{ viewingPayment.method }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Cashier / Receiver:</span>
              <span class="font-bold uppercase">{{ viewingPayment.received_by }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Date & Time:</span>
              <span class="font-mono">{{ formatDate(viewingPayment.created_at) }}</span>
            </div>
            <div v-if="viewingPayment.notes" class="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500 block mb-1">Notes:</span>
              <p class="font-medium text-zinc-800 dark:text-zinc-200">{{ viewingPayment.notes }}</p>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
            <button
              type="button"
              @click="window.print()"
              class="flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-colors cursor-pointer"
            >
              <Printer class="h-4 w-4" />
              <span>Print Receipt</span>
            </button>
            <button
              type="button"
              @click="viewingPayment = null"
              class="px-4 py-2 text-xs font-bold rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
