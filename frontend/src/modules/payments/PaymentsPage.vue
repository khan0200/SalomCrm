<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { paymentsApi } from '@/api/payments'
import { studentsApi } from '@/api/students'
import { settingsApi } from '@/api/settings'
import type { Payment, Student } from '@/types'
import { useUiStore } from '@/stores/ui'
import {
  Users, Receipt, Plus, Minus
} from 'lucide-vue-next'

import PaymentStudentOverview from './components/PaymentStudentOverview.vue'
import PaymentHistoryTable from './components/PaymentHistoryTable.vue'
import AddPaymentModal from './components/AddPaymentModal.vue'
import WithdrawModal from './components/WithdrawModal.vue'
import EditPaymentModal from './components/EditPaymentModal.vue'

const queryClient = useQueryClient()
const uiStore = useUiStore()

const ITEMS_PER_PAGE = 30

const PAYMENT_METHODS_DEFAULT = ['Karta J.A', 'Karta Abdulaziz', 'Naqd', 'Karta M.A', 'Bank', 'Discount']
const RECEIVED_BY_DEFAULT = ['ABDULAZIZ', 'MUSLIHIDDIN', 'BAXTIYOR', 'MUHAMMADALI', 'JASUR', 'ADMIN', 'Discount']
const NOTE_PILLS_DEFAULT = ['Shartnoma uchun', 'Qarz', 'Elchixona uchun', 'Appfee', 'DISCOUNT']

const STATUS_FILTER_OPTIONS = ['Active', 'Archive']
const TARIFF_FILTER_OPTIONS = [
  'E-VISA (TIL SERTIFIKATISIZ)',
  'E-VISA (TIL SERTIFIKATLI)',
  'PREMIUM',
  'REGIONAL VISA',
  'STANDART',
  'VISA PLUS',
  'ZERO RISK',
  'No Tariff'
]
const BALANCE_FILTER_OPTIONS = [
  'Balance < 0 (Debt)',
  'Balance = 0 (Fully Paid)',
  'Balance > 500,000',
  'Balance > 1,000,000',
  'Balance > 2,000,000',
  'Balance > 5,000,000',
  'Balance > 10,000,000'
]

// ── Alphanumeric ID Sorting Logic (Matching UniApp2 1-to-1) ─────────────
const compareStudentIds = (a: Student, b: Student, order: 'asc' | 'desc' = 'asc') => {
  const idA = a.id || ''
  const idB = b.id || ''

  const parseId = (idStr: string) => {
    const str = idStr.trim()
    const match = str.match(/^([A-Za-z\s_-]*)(\d*)$/)
    if (match) {
      return {
        prefix: match[1] || '',
        num: match[2] ? parseInt(match[2], 10) : null
      }
    }
    return { prefix: str, num: null }
  }

  const valA = parseId(idA)
  const valB = parseId(idB)

  const prefixComp = valA.prefix.localeCompare(valB.prefix, undefined, { sensitivity: 'base' })
  if (prefixComp !== 0) {
    return order === 'asc' ? prefixComp : -prefixComp
  }

  if (valA.num !== null && valB.num !== null) {
    return order === 'asc' ? valA.num - valB.num : valB.num - valA.num
  } else if (valA.num !== null) {
    return order === 'asc' ? 1 : -1
  } else if (valB.num !== null) {
    return order === 'asc' ? -1 : 1
  }

  return order === 'asc' ? idA.localeCompare(idB) : idB.localeCompare(idA)
}

// ── Balance Filter Matching (Matching UniApp2 1-to-1) ───────────────────
const matchesBalanceOption = (studentBalance: number, option: string) => {
  switch (option) {
    case 'Balance < 0 (Debt)':
      return studentBalance < 0
    case 'Balance = 0 (Fully Paid)':
      return studentBalance === 0
    case 'Balance > 500,000':
      return studentBalance > 500000
    case 'Balance > 1,000,000':
      return studentBalance > 1000000
    case 'Balance > 2,000,000':
      return studentBalance > 2000000
    case 'Balance > 5,000,000':
      return studentBalance > 5000000
    case 'Balance > 10,000,000':
      return studentBalance > 10000000
    default:
      return false
  }
}

// ── Main Page State ───────────────────────────────────────────────────
const activeTab = ref<'students' | 'history'>('students')
const viewMode = ref<'grid' | 'table'>('table')
const sortOrder = ref<'asc' | 'desc'>('asc')

// Students Tab Filter State (Multi-Select Arrays)
const studentSearch = ref('')
const selectedStatuses = ref<string[]>([])
const selectedTariffs = ref<string[]>([])
const selectedBalances = ref<string[]>([])
const selectedGroups = ref<string[]>([])
const studentsPage = ref(1)

// History Tab Filter State
const historySearch = ref('')
const selectedMethod = ref('all')
const selectedReceiver = ref('all')
const historyPage = ref(1)

// Modals State
const isAddModalOpen = ref(false)
const isWithdrawModalOpen = ref(false)
const isEditModalOpen = ref(false)
const preselectedStudentId = ref<string | null>(null)
const editingPayment = ref<Payment | null>(null)

// ── Settings Data (Methods, Receivers, Note Pills) ─────────────────────
const paymentMethods = ref<string[]>(PAYMENT_METHODS_DEFAULT)
const paymentReceivers = ref<string[]>(RECEIVED_BY_DEFAULT)
const notePills = ref<string[]>(NOTE_PILLS_DEFAULT)

onMounted(async () => {
  try {
    const [methodsRes, receiversRes, notesRes] = await Promise.allSettled([
      settingsApi.getPaymentMethods(),
      settingsApi.getPaymentReceivers(),
      settingsApi.getPaymentNotes()
    ])
    if (methodsRes.status === 'fulfilled' && methodsRes.value.length > 0) {
      paymentMethods.value = methodsRes.value.map(m => m.name)
    }
    if (receiversRes.status === 'fulfilled' && receiversRes.value.length > 0) {
      paymentReceivers.value = receiversRes.value.map(r => r.name)
    }
    if (notesRes.status === 'fulfilled' && notesRes.value.length > 0) {
      notePills.value = notesRes.value.map(n => n.name)
    }
  } catch (err) {
    console.error('Error loading settings options:', err)
  }
})

// ── Queries ───────────────────────────────────────────────────────────
const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
  staleTime: 1000 * 60 * 10,
})

const options = computed(() => optionsData.value || {
  tariffs: [],
  groups: [],
})

const { data: overviewData, isLoading: isOverviewLoading } = useQuery({
  queryKey: ['payment-overview-all'],
  queryFn: () => paymentsApi.getPaymentOverview({ page_size: 2500, status: 'all' }),
  staleTime: 1000 * 60 * 5,
})

const allStudents = computed<Student[]>(() => overviewData.value?.results || [])

const { data: historyData, isLoading: isHistoryLoading } = useQuery({
  queryKey: ['payment-history-all'],
  queryFn: () => paymentsApi.getPaymentHistory({ page_size: 2000 }),
  staleTime: 1000 * 60 * 5,
})

const allPayments = computed<Payment[]>(() => historyData.value?.results || [])

// ── Multi-Select Handlers ─────────────────────────────────────────────
const toggleStatus = (val: string) => {
  if (selectedStatuses.value.includes(val)) {
    selectedStatuses.value = selectedStatuses.value.filter(s => s !== val)
  } else {
    selectedStatuses.value.push(val)
  }
}
const toggleAllStatuses = () => {
  if (selectedStatuses.value.length === STATUS_FILTER_OPTIONS.length) {
    selectedStatuses.value = []
  } else {
    selectedStatuses.value = [...STATUS_FILTER_OPTIONS]
  }
}

const toggleTariff = (val: string) => {
  if (selectedTariffs.value.includes(val)) {
    selectedTariffs.value = selectedTariffs.value.filter(t => t !== val)
  } else {
    selectedTariffs.value.push(val)
  }
}
const toggleAllTariffs = () => {
  if (selectedTariffs.value.length === TARIFF_FILTER_OPTIONS.length) {
    selectedTariffs.value = []
  } else {
    selectedTariffs.value = [...TARIFF_FILTER_OPTIONS]
  }
}

const toggleBalance = (val: string) => {
  if (selectedBalances.value.includes(val)) {
    selectedBalances.value = selectedBalances.value.filter(b => b !== val)
  } else {
    selectedBalances.value.push(val)
  }
}
const toggleAllBalances = () => {
  if (selectedBalances.value.length === BALANCE_FILTER_OPTIONS.length) {
    selectedBalances.value = []
  } else {
    selectedBalances.value = [...BALANCE_FILTER_OPTIONS]
  }
}

const ALL_GROUP_OPTIONS = computed(() => {
  const set = new Set<string>()
  allStudents.value.forEach(s => { if (s.student_group) set.add(s.student_group) })
  const list = Array.from(set)
  if (!list.includes('2026 BAHOR')) list.push('2026 BAHOR')
  if (!list.includes('2026 KUZ')) list.push('2026 KUZ')
  if (!list.includes('2027 BAHOR')) list.push('2027 BAHOR')
  return ['No Group', ...list.sort()]
})

const toggleGroup = (val: string) => {
  if (selectedGroups.value.includes(val)) {
    selectedGroups.value = selectedGroups.value.filter(g => g !== val)
  } else {
    selectedGroups.value.push(val)
  }
}
const toggleAllGroups = () => {
  if (selectedGroups.value.length === ALL_GROUP_OPTIONS.value.length) {
    selectedGroups.value = []
  } else {
    selectedGroups.value = [...ALL_GROUP_OPTIONS.value]
  }
}

// ── Filtered & Sorted Students ────────────────────────────────────────
const filteredStudents = computed(() => {
  return allStudents.value.filter(s => {
    if (studentSearch.value) {
      const q = studentSearch.value.toLowerCase()
      const matches = (s.id || '').toLowerCase().includes(q) || (s.full_name || '').toLowerCase().includes(q)
      if (!matches) return false
    }

    if (selectedStatuses.value.length > 0 && selectedStatuses.value.length < STATUS_FILTER_OPTIONS.length) {
      if (selectedStatuses.value.includes('Active') && s.is_deleted) return false
      if (selectedStatuses.value.includes('Archive') && !s.is_deleted) return false
    }

    if (selectedTariffs.value.length > 0) {
      let matchesTariff = false
      for (const selected of selectedTariffs.value) {
        if (selected === 'No Tariff' && !s.tariff) {
          matchesTariff = true
          break
        } else if (selected === 'E-VISA (TIL SERTIFIKATLI)' && s.tariff === 'E-VISA' && s.language_certificate && s.language_certificate !== 'NO CERTIFICATE') {
          matchesTariff = true
          break
        } else if (selected === 'E-VISA (TIL SERTIFIKATISIZ)' && s.tariff === 'E-VISA' && (!s.language_certificate || s.language_certificate === 'NO CERTIFICATE')) {
          matchesTariff = true
          break
        } else if (s.tariff === selected) {
          matchesTariff = true
          break
        }
      }
      if (!matchesTariff) return false
    }

    if (selectedBalances.value.length > 0) {
      let matchesBalance = false
      const bal = Number(s.balance) || 0
      for (const selected of selectedBalances.value) {
        if (matchesBalanceOption(bal, selected)) {
          matchesBalance = true
          break
        }
      }
      if (!matchesBalance) return false
    }

    if (selectedGroups.value.length > 0) {
      let matchesGroup = false
      for (const selected of selectedGroups.value) {
        if (selected === 'No Group' && !s.student_group) {
          matchesGroup = true
          break
        } else if (s.student_group === selected) {
          matchesGroup = true
          break
        }
      }
      if (!matchesGroup) return false
    }

    return true
  })
})

const sortedStudents = computed(() => {
  return [...filteredStudents.value].sort((a, b) => {
    // Archived students always sort after active ones, regardless of ID order
    const aArchived = a.is_deleted ? 1 : 0
    const bArchived = b.is_deleted ? 1 : 0
    if (aArchived !== bArchived) return aArchived - bArchived
    return compareStudentIds(a, b, sortOrder.value)
  })
})

const studentsTotalPages = computed(() => Math.max(1, Math.ceil(sortedStudents.value.length / ITEMS_PER_PAGE)))
const paginatedStudents = computed(() => {
  const start = (studentsPage.value - 1) * ITEMS_PER_PAGE
  return sortedStudents.value.slice(start, start + ITEMS_PER_PAGE)
})

// ── Filtered Payments ─────────────────────────────────────────────────
const filteredPayments = computed(() => {
  return allPayments.value.filter(p => {
    if (historySearch.value) {
      const q = historySearch.value.toLowerCase()
      const matches =
        (p.student_full_name || p.student_name || '').toLowerCase().includes(q) ||
        (p.student_id || '').toLowerCase().includes(q) ||
        (p.notes || '').toLowerCase().includes(q)
      if (!matches) return false
    }
    if (selectedMethod.value !== 'all' && p.method !== selectedMethod.value) return false
    if (selectedReceiver.value !== 'all' && p.received_by !== selectedReceiver.value) return false
    return true
  })
})

// Strictly sort payments by Date and Time descending (latest always on top, even for archived students)
const sortedPayments = computed(() => {
  return [...filteredPayments.value].sort((a, b) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
    return timeB - timeA
  })
})

const historyTotalPages = computed(() => Math.max(1, Math.ceil(sortedPayments.value.length / ITEMS_PER_PAGE)))
const paginatedPayments = computed(() => {
  const start = (historyPage.value - 1) * ITEMS_PER_PAGE
  return sortedPayments.value.slice(start, start + ITEMS_PER_PAGE)
})

watch([studentSearch, selectedStatuses, selectedTariffs, selectedBalances, selectedGroups, sortOrder], () => {
  studentsPage.value = 1
})

watch([historySearch, selectedMethod, selectedReceiver], () => {
  historyPage.value = 1
})

// ── Optimistic Cache Helpers ──────────────────────────────────────────
const injectPaymentToCache = (payment: Payment) => {
  // Immediately add the new payment to the history cache
  queryClient.setQueryData(['payment-history-all'], (old: any) => {
    if (!old) return old
    return { ...old, results: [payment, ...(old.results || [])] }
  })
  // Also inject into student-specific payment cache if open
  if (payment.student_id) {
    queryClient.setQueryData(['student-payments', payment.student_id], (old: any) => {
      if (!old) return old
      return { ...old, results: [payment, ...(old.results || [])] }
    })
  }
}

const removePaymentFromCache = (paymentId: string) => {
  queryClient.setQueryData(['payment-history-all'], (old: any) => {
    if (!old) return old
    return { ...old, results: (old.results || []).filter((p: Payment) => p.id !== paymentId) }
  })
  // Remove from all student-specific caches
  queryClient.getQueriesData({ queryKey: ['student-payments'] }).forEach(([key, data]: any) => {
    if (data?.results) {
      queryClient.setQueryData(key, { ...data, results: data.results.filter((p: Payment) => p.id !== paymentId) })
    }
  })
}

const backgroundRefreshAll = () => {
  queryClient.invalidateQueries({ queryKey: ['payment-overview-all'] })
  queryClient.invalidateQueries({ queryKey: ['payment-history-all'] })
  queryClient.invalidateQueries({ queryKey: ['students'] })
  queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
  queryClient.invalidateQueries({ queryKey: ['student-payments'] })
}

// Patches the Balance/Discount columns on the overview table (this page's own
// list) the instant a payment/discount/withdrawal is submitted, mirroring the
// same formula the backend applies in recalculate_student_financials:
// balance = (payments + discount) - tariff - withdrawals. This must run
// silently in the background — the API call itself is still in flight, this
// only updates what the user sees while it completes.
const patchOverviewBalance = (studentId: string, balanceDelta: number, discountDelta: number = 0) => {
  queryClient.setQueryData(['payment-overview-all'], (old: any) => {
    if (!old?.results) return old
    return {
      ...old,
      results: old.results.map((s: Student) =>
        s.id === studentId
          ? {
              ...s,
              balance: Number(s.balance || 0) + balanceDelta,
              discount: Number(s.discount || 0) + discountDelta,
            }
          : s
      ),
    }
  })
}

// ── Mutations ─────────────────────────────────────────────────────────
const createPaymentMutation = useMutation({
  mutationFn: (data: any) => paymentsApi.createPayment(data),
  onMutate: (data: any) => {
    // Give the new row a stable id so onSuccess can find and replace this
    // exact record (recomputing "now" a second time, as before, could miss
    // it and leave a duplicate until the next full refetch).
    const tempId = `temp-${Date.now()}`
    const tempPayment: Payment = {
      id: tempId,
      student_id: data.student_id,
      student_full_name: allStudents.value.find(s => s.id === data.student_id)?.full_name || null,
      student_name: null,
      amount: data.amount,
      method: data.method,
      received_by: data.received_by,
      notes: data.notes,
      is_discount: data.is_discount || false,
      is_withdrawal: false,
      created_by_name: null,
      created_at: new Date().toISOString(),
    }
    injectPaymentToCache(tempPayment)
    // Silently update Balance/Discount on the overview table right away —
    // the Save Payment button's spinner covers the actual network request,
    // this just keeps the table from looking stale while that's in flight.
    patchOverviewBalance(data.student_id, data.amount, data.is_discount ? data.amount : 0)
    return { tempId }
  },
  onSuccess: (res, _vars, context) => {
    if (context?.tempId) removePaymentFromCache(context.tempId)
    backgroundRefreshAll()
    isAddModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Payment Recorded',
      message: `Payment of ${new Intl.NumberFormat('uz-UZ').format(res.amount)} UZS recorded.`
    })
  },
  onError: (err: any, _vars, context) => {
    if (context?.tempId) removePaymentFromCache(context.tempId)
    backgroundRefreshAll()
    uiStore.addToast({
      type: 'error',
      title: 'Payment Failed',
      message: err.response?.data?.detail || err.message || 'Failed to save payment.'
    })
  }
})

const withdrawMutation = useMutation({
  mutationFn: (data: any) => paymentsApi.createWithdrawal(data),
  onMutate: (data: any) => {
    const tempId = `temp-${Date.now()}`
    const tempPayment: Payment = {
      id: tempId,
      student_id: data.student_id,
      student_full_name: allStudents.value.find(s => s.id === data.student_id)?.full_name || null,
      student_name: null,
      amount: -Math.abs(data.amount),
      method: data.method,
      received_by: data.received_by,
      notes: data.notes || data.reason,
      is_discount: false,
      is_withdrawal: true,
      created_by_name: null,
      created_at: new Date().toISOString(),
    }
    injectPaymentToCache(tempPayment)
    // Withdrawal increases debt, so it's a negative shift on balance.
    patchOverviewBalance(data.student_id, -Math.abs(data.amount))
    return { tempId }
  },
  onSuccess: (res, _vars, context) => {
    if (context?.tempId) removePaymentFromCache(context.tempId)
    backgroundRefreshAll()
    isWithdrawModalOpen.value = false
    uiStore.addToast({
      type: 'warning',
      title: 'Withdrawal Recorded',
      message: `Withdrawal of ${new Intl.NumberFormat('uz-UZ').format(Math.abs(res.amount))} UZS recorded.`
    })
  },
  onError: (err: any, _vars, context) => {
    if (context?.tempId) removePaymentFromCache(context.tempId)
    backgroundRefreshAll()
    uiStore.addToast({
      type: 'error',
      title: 'Withdrawal Failed',
      message: err.response?.data?.detail || err.message || 'Failed to process withdrawal.'
    })
  }
})

const editPaymentMutation = useMutation({
  mutationFn: (data: any) => {
    if (!editingPayment.value) throw new Error('No payment selected')
    return paymentsApi.updatePayment(editingPayment.value.id, data)
  },
  onMutate: (data: any) => {
    if (!editingPayment.value) return
    const paymentId = editingPayment.value.id
    const studentId = editingPayment.value.student_id
    const wasDiscount = editingPayment.value.is_discount
    const isWithdrawal = editingPayment.value.is_withdrawal
    const oldSignedAmount = Number(editingPayment.value.amount) || 0
    const updatedAmount = isWithdrawal ? -Math.abs(data.amount) : Math.abs(data.amount)

    // Optimistically update the payment in history cache
    queryClient.setQueryData(['payment-history-all'], (old: any) => {
      if (!old) return old
      return {
        ...old,
        results: (old.results || []).map((p: Payment) =>
          p.id === paymentId
            ? { ...p, amount: updatedAmount, method: data.method, received_by: data.received_by, notes: data.notes ?? p.notes }
            : p
        )
      }
    })
    // Update student-specific caches
    queryClient.getQueriesData({ queryKey: ['student-payments'] }).forEach(([key, cacheData]: any) => {
      if (cacheData?.results?.some((p: Payment) => p.id === paymentId)) {
        queryClient.setQueryData(key, {
          ...cacheData,
          results: cacheData.results.map((p: Payment) =>
            p.id === paymentId
              ? { ...p, amount: updatedAmount, method: data.method, received_by: data.received_by, notes: data.notes ?? p.notes }
              : p
          )
        })
      }
    })
    // Shift the overview Balance/Discount columns by exactly the change in
    // this payment's amount (balance moves by the same signed delta the
    // ledger sum would; discount only if this payment is a discount row).
    if (studentId) {
      const balanceDelta = updatedAmount - oldSignedAmount
      const discountDelta = wasDiscount ? balanceDelta : 0
      patchOverviewBalance(studentId, balanceDelta, discountDelta)
    }
  },
  onSuccess: () => {
    backgroundRefreshAll()
    isEditModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Payment Updated',
      message: 'Payment updated and student balance recalculated.'
    })
  },
  onError: (err: any) => {
    backgroundRefreshAll()
    uiStore.addToast({
      type: 'error',
      title: 'Update Failed',
      message: err.response?.data?.detail || err.message || 'Failed to update payment.'
    })
  }
})

const deletePaymentMutation = useMutation({
  mutationFn: (id: string) => paymentsApi.deletePayment(id),
  onMutate: (id: string) => {
    // Optimistically remove the payment from cache immediately
    removePaymentFromCache(id)
  },
  onSuccess: () => {
    backgroundRefreshAll()
    uiStore.addToast({
      type: 'error',
      title: 'Payment Deleted',
      message: 'Payment deleted and student balance rolled back.'
    })
  },
  onError: (err: any) => {
    backgroundRefreshAll()
    uiStore.addToast({
      type: 'error',
      title: 'Delete Failed',
      message: err.response?.data?.detail || err.message || 'Failed to delete payment.'
    })
  }
})

// ── Modals & Actions ──────────────────────────────────────────────────
const openAddModal = (studentId?: string) => {
  preselectedStudentId.value = studentId || null
  isAddModalOpen.value = true
}

const openWithdrawModal = (studentId?: string) => {
  preselectedStudentId.value = studentId || null
  isWithdrawModalOpen.value = true
}

const openEditModal = (payment: Payment) => {
  editingPayment.value = payment
  isEditModalOpen.value = true
}

const handleDeletePayment = (payment: Payment) => {
  const name = payment.student_full_name || payment.student_name || 'General'
  const absAmount = new Intl.NumberFormat('uz-UZ').format(Math.abs(Number(payment.amount)))
  if (confirm(`Are you sure you want to delete this payment of ${absAmount} UZS for ${name}?`)) {
    deletePaymentMutation.mutate(payment.id)
  }
}

// ── Excel Export with xlsx-js-style matching UniApp2 ─────────────────
const exportPaymentHistoryToExcel = async () => {
  if (sortedPayments.value.length === 0) {
    alert('No payments to export!')
    return
  }

  const XLSX = await import('xlsx-js-style')

  const pad = (n: number) => String(n).padStart(2, '0')
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  }

  const excelData = sortedPayments.value.map((p, index) => {
    let txType = 'Standard Payment'
    if (p.is_withdrawal) {
      txType = 'Withdrawal'
    } else if (p.is_discount) {
      txType = 'Discount'
    }

    return {
      No: index + 1,
      'Payment ID': p.id ? String(p.id).toUpperCase() : '',
      'Student ID': p.student_id || '—',
      'Student Name': p.student_full_name || p.student_name || 'General Payment',
      'Amount (UZS)': p.amount !== undefined ? Number(p.amount) : '',
      'Transaction Type': txType,
      'Payment Method': p.method || '',
      'Received By': p.received_by || '',
      'Date & Time': formatDate(p.created_at),
      Notes: p.notes || ''
    }
  })

  const colWidths = [
    { wch: 5 },   // No
    { wch: 20 },  // Payment ID
    { wch: 15 },  // Student ID
    { wch: 30 },  // Student Name
    { wch: 18 },  // Amount (UZS)
    { wch: 18 },  // Transaction Type
    { wch: 18 },  // Payment Method
    { wch: 18 },  // Received By
    { wch: 22 },  // Date & Time
    { wch: 35 }   // Notes
  ]

  const ws = XLSX.utils.json_to_sheet(excelData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Payment History')
  ws['!cols'] = colWidths

  const dateStr = new Date().toISOString().split('T')[0]
  const filename = `Payment_History_Export_${dateStr}.xlsx`

  XLSX.writeFile(wb, filename)
}
</script>

<template>
  <div class="flex flex-col gap-4 select-none">
    <!-- Header row: tab switcher + actions -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <!-- Left: Tab Switcher (UniApp2 1-to-1) -->
      <div class="flex items-center gap-1 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-1 shadow-2xs">
        <button
          type="button"
          @click="activeTab = 'students'"
          class="flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-bold transition-all cursor-pointer select-none"
          :class="activeTab === 'students'
            ? 'bg-blue-600 text-white shadow-xs'
            : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-850 hover:text-zinc-900 dark:hover:text-zinc-100'"
        >
          <Users class="h-4 w-4" />
          <span>Students</span>
        </button>
        <button
          type="button"
          @click="activeTab = 'history'"
          class="flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-bold transition-all cursor-pointer select-none"
          :class="activeTab === 'history'
            ? 'bg-blue-600 text-white shadow-xs'
            : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-850 hover:text-zinc-900 dark:hover:text-zinc-100'"
        >
          <Receipt class="h-4 w-4" />
          <span>Payment History</span>
        </button>
      </div>

      <!-- Right: Action Buttons -->
      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="openAddModal()"
          class="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 active:scale-[0.97] transition-all cursor-pointer shadow-2xs shadow-blue-500/20"
        >
          <Plus class="h-4 w-4 stroke-[2.5]" />
          <span>Add Payment</span>
        </button>
        <button
          type="button"
          @click="openWithdrawModal()"
          class="flex items-center gap-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 px-4 py-2 text-xs font-bold text-zinc-800 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-800 active:scale-[0.97] transition-all cursor-pointer shadow-2xs"
        >
          <Minus class="h-4 w-4 stroke-[2.5]" />
          <span>Withdraw</span>
        </button>
      </div>
    </div>

    <!-- ── Tab 1: Students Overview ──────────────────────────────────── -->
    <div v-if="activeTab === 'students'">
      <PaymentStudentOverview
        :students="paginatedStudents"
        :total-filtered-count="sortedStudents.length"
        :is-loading="isOverviewLoading"
        :options="options"
        :search-query="studentSearch"
        :selected-statuses="selectedStatuses"
        :selected-tariffs="selectedTariffs"
        :selected-balances="selectedBalances"
        :selected-groups="selectedGroups"
        :view-mode="viewMode"
        :sort-order="sortOrder"
        @update:search-query="studentSearch = $event"
        @toggle-status="toggleStatus"
        @toggle-all-statuses="toggleAllStatuses"
        @toggle-tariff="toggleTariff"
        @toggle-all-tariffs="toggleAllTariffs"
        @toggle-balance="toggleBalance"
        @toggle-all-balances="toggleAllBalances"
        @toggle-group="toggleGroup"
        @toggle-all-groups="toggleAllGroups"
        @update:view-mode="viewMode = $event"
        @toggle-sort="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
        @open-add-payment="openAddModal"
      />

      <!-- Pagination -->
      <div v-if="studentsTotalPages > 1" class="flex items-center justify-center gap-2 mt-4">
        <button
          :disabled="studentsPage === 1"
          @click="studentsPage--"
          class="px-3 py-1.5 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 disabled:opacity-40 cursor-pointer text-zinc-700 dark:text-zinc-300 shadow-2xs"
        >
          Prev
        </button>
        <span class="text-xs text-zinc-500 font-mono">{{ studentsPage }} / {{ studentsTotalPages }}</span>
        <button
          :disabled="studentsPage === studentsTotalPages"
          @click="studentsPage++"
          class="px-3 py-1.5 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 disabled:opacity-40 cursor-pointer text-zinc-700 dark:text-zinc-300 shadow-2xs"
        >
          Next
        </button>
      </div>
    </div>

    <!-- ── Tab 2: Payment History ────────────────────────────────────── -->
    <div v-else>
      <PaymentHistoryTable
        :payments="paginatedPayments"
        :total-filtered-count="sortedPayments.length"
        :is-loading="isHistoryLoading"
        :search-query="historySearch"
        :selected-method="selectedMethod"
        :selected-receiver="selectedReceiver"
        :payment-methods="paymentMethods"
        :payment-receivers="paymentReceivers"
        :view-mode="viewMode"
        @update:search-query="historySearch = $event"
        @update:selected-method="selectedMethod = $event"
        @update:selected-receiver="selectedReceiver = $event"
        @update:view-mode="viewMode = $event"
        @open-edit="openEditModal"
        @delete-payment="handleDeletePayment"
        @export-excel="exportPaymentHistoryToExcel"
      />

      <!-- Pagination -->
      <div v-if="historyTotalPages > 1" class="flex items-center justify-center gap-2 mt-4">
        <button
          :disabled="historyPage === 1"
          @click="historyPage--"
          class="px-3 py-1.5 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 disabled:opacity-40 cursor-pointer text-zinc-700 dark:text-zinc-300 shadow-2xs"
        >
          Prev
        </button>
        <span class="text-xs text-zinc-500 font-mono">{{ historyPage }} / {{ historyTotalPages }}</span>
        <button
          :disabled="historyPage === historyTotalPages"
          @click="historyPage++"
          class="px-3 py-1.5 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 disabled:opacity-40 cursor-pointer text-zinc-700 dark:text-zinc-300 shadow-2xs"
        >
          Next
        </button>
      </div>
    </div>

    <!-- ── Modals ────────────────────────────────────────────────────── -->
    <!-- Add Payment Modal -->
    <AddPaymentModal
      :is-open="isAddModalOpen"
      :is-submitting="createPaymentMutation.isPending.value"
      :preselected-student-id="preselectedStudentId"
      :students="allStudents"
      :payments="allPayments"
      :payment-methods="paymentMethods"
      :payment-receivers="paymentReceivers"
      :note-pills="notePills"
      @close="isAddModalOpen = false"
      @submit="createPaymentMutation.mutate($event)"
    />

    <!-- Withdraw Modal -->
    <WithdrawModal
      :is-open="isWithdrawModalOpen"
      :is-submitting="withdrawMutation.isPending.value"
      :preselected-student-id="preselectedStudentId"
      :students="allStudents"
      @close="isWithdrawModalOpen = false"
      @submit="withdrawMutation.mutate($event)"
    />

    <!-- Edit Payment Modal -->
    <EditPaymentModal
      :is-open="isEditModalOpen"
      :is-submitting="editPaymentMutation.isPending.value"
      :payment="editingPayment"
      :students="allStudents"
      :payment-methods="paymentMethods"
      :payment-receivers="paymentReceivers"
      @close="isEditModalOpen = false"
      @submit="editPaymentMutation.mutate($event)"
    />
  </div>
</template>
