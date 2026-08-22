<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { paymentsApi } from '@/api/payments'
import { studentsApi } from '@/api/students'
import type { Payment, Student } from '@/types'
import { useUiStore } from '@/stores/ui'
import {
  CreditCard, Plus, Minus, Users, Receipt,
  ChevronLeft, ChevronRight, FileSpreadsheet
} from 'lucide-vue-next'

import PaymentStudentOverview from './components/PaymentStudentOverview.vue'
import PaymentHistoryTable from './components/PaymentHistoryTable.vue'
import AddPaymentModal from './components/AddPaymentModal.vue'
import WithdrawModal from './components/WithdrawModal.vue'
import EditPaymentModal from './components/EditPaymentModal.vue'

const queryClient = useQueryClient()
const uiStore = useUiStore()

const ITEMS_PER_PAGE = 32

// Alphanumeric sorting logic matching UniApp2
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

// Balance filtering logic matching UniApp2
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
      return true
  }
}

// Main Page State
const activeTab = ref<'overview' | 'history'>('overview')
const viewMode = ref<'grid' | 'table'>('grid')

// Modals
const isAddModalOpen = ref(false)
const isWithdrawModalOpen = ref(false)
const isEditModalOpen = ref(false)
const preselectedStudentId = ref<string | null>(null)
const editingPayment = ref<Payment | null>(null)

// Overview Tab Filters
const overviewSearch = ref('')
const overviewStatus = ref('all')
const selectedTariff = ref('all')
const selectedBalance = ref('all')
const selectedGroup = ref('all')
const overviewPage = ref(1)

// History Tab Filters
const historySearch = ref('')
const selectedMethod = ref('all')
const selectedReceiver = ref('all')
const historyPage = ref(1)

// Query: Options (Tariffs, Groups)
const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
  staleTime: 1000 * 60 * 10,
})

const options = computed(() => optionsData.value || {
  tariffs: [],
  groups: [],
})

// Query: Payment Student Overview (Load full set into in-memory cache)
const { data: overviewData, isLoading: isOverviewLoading } = useQuery({
  queryKey: ['payment-overview-all'],
  queryFn: () => paymentsApi.getPaymentOverview({ page_size: 1000 }),
  staleTime: 1000 * 60 * 5,
})

const allOverviewStudents = computed<Student[]>(() => overviewData.value?.results || [])

// ── Ultra-Fast Instant In-Memory Filter for Students (0ms Response) ──────────────────────────
const filteredOverviewStudents = computed(() => {
  let list = allOverviewStudents.value

  const q = overviewSearch.value.trim().toLowerCase()
  if (q) {
    list = list.filter(s => {
      const idMatch = (s.id || '').toLowerCase().includes(q)
      const nameMatch = (s.full_name || '').toLowerCase().includes(q)
      const phoneMatch = (s.phone1 || '').toLowerCase().includes(q) || (s.phone2 || '').toLowerCase().includes(q)
      const groupMatch = (s.student_group || '').toLowerCase().includes(q)
      return idMatch || nameMatch || phoneMatch || groupMatch
    })
  }

  if (overviewStatus.value === 'Active') {
    list = list.filter(s => !s.is_deleted)
  } else if (overviewStatus.value === 'Archive') {
    list = list.filter(s => s.is_deleted)
  }

  if (selectedTariff.value !== 'all') {
    if (selectedTariff.value === 'No Tariff') {
      list = list.filter(s => !s.tariff)
    } else {
      list = list.filter(s => s.tariff === selectedTariff.value)
    }
  }

  if (selectedGroup.value !== 'all') {
    if (selectedGroup.value === 'NO GROUP') {
      list = list.filter(s => !s.student_group)
    } else {
      list = list.filter(s => s.student_group === selectedGroup.value)
    }
  }

  if (selectedBalance.value !== 'all') {
    list = list.filter(s => matchesBalanceOption(Number(s.balance || 0), selectedBalance.value))
  }

  return [...list].sort((a, b) => compareStudentIds(a, b, 'asc'))
})

const overviewTotalCount = computed(() => filteredOverviewStudents.value.length)
const overviewTotalPages = computed(() => Math.max(1, Math.ceil(overviewTotalCount.value / ITEMS_PER_PAGE)))
const overviewStudents = computed(() => {
  const start = (overviewPage.value - 1) * ITEMS_PER_PAGE
  return filteredOverviewStudents.value.slice(start, start + ITEMS_PER_PAGE)
})

// Query: Payment History (Load full set into in-memory cache)
const { data: historyData, isLoading: isHistoryLoading } = useQuery({
  queryKey: ['payment-history-all'],
  queryFn: () => paymentsApi.getPaymentHistory({ page_size: 1000 }),
  staleTime: 1000 * 60 * 5,
})

const allPayments = computed<Payment[]>(() => historyData.value?.results || [])

// ── Ultra-Fast Instant In-Memory Filter for Payment History (0ms Response) ──────────────────────────
const filteredPayments = computed(() => {
  let list = allPayments.value

  const q = historySearch.value.trim().toLowerCase()
  if (q) {
    list = list.filter(p => {
      const nameMatch = (p.student_full_name || p.student_name || '').toLowerCase().includes(q)
      const idMatch = (p.student_id || '').toLowerCase().includes(q)
      const notesMatch = (p.notes || '').toLowerCase().includes(q)
      const methodMatch = (p.method || '').toLowerCase().includes(q)
      const recMatch = (p.received_by || '').toLowerCase().includes(q)
      return nameMatch || idMatch || notesMatch || methodMatch || recMatch
    })
  }

  if (selectedMethod.value !== 'all') {
    list = list.filter(p => p.method === selectedMethod.value)
  }

  if (selectedReceiver.value !== 'all') {
    list = list.filter(p => p.received_by === selectedReceiver.value)
  }

  return list
})

const historyTotalCount = computed(() => filteredPayments.value.length)
const historyTotalPages = computed(() => Math.max(1, Math.ceil(historyTotalCount.value / ITEMS_PER_PAGE)))
const paymentsList = computed(() => {
  const start = (historyPage.value - 1) * ITEMS_PER_PAGE
  return filteredPayments.value.slice(start, start + ITEMS_PER_PAGE)
})

// Reset page on search or filter change
watch([overviewSearch, overviewStatus, selectedTariff, selectedBalance, selectedGroup], () => {
  overviewPage.value = 1
})

watch([historySearch, selectedMethod, selectedReceiver], () => {
  historyPage.value = 1
})

// Mutations
const createPaymentMutation = useMutation({
  mutationFn: (data: any) => paymentsApi.createPayment(data),
  onSuccess: (res) => {
    queryClient.invalidateQueries({ queryKey: ['payment-overview-all'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history-all'] })
    queryClient.invalidateQueries({ queryKey: ['students'] })
    isAddModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Payment Recorded',
      message: `Payment of ${res.amount} UZS recorded successfully.`
    })
  },
  onError: (err: any) => {
    uiStore.addToast({
      type: 'error',
      title: 'Payment Failed',
      message: err.response?.data?.detail || err.message || 'Failed to record payment'
    })
  }
})

const withdrawMutation = useMutation({
  mutationFn: (data: any) => paymentsApi.createWithdrawal(data),
  onSuccess: (res) => {
    queryClient.invalidateQueries({ queryKey: ['payment-overview-all'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history-all'] })
    queryClient.invalidateQueries({ queryKey: ['students'] })
    isWithdrawModalOpen.value = false
    uiStore.addToast({
      type: 'warning',
      title: 'Withdrawal Recorded',
      message: `Withdrawal of ${Math.abs(res.amount)} UZS recorded.`
    })
  }
})

const editPaymentMutation = useMutation({
  mutationFn: (data: any) => {
    if (!editingPayment.value) throw new Error('No payment selected')
    return paymentsApi.updatePayment(editingPayment.value.id, data)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['payment-overview-all'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history-all'] })
    queryClient.invalidateQueries({ queryKey: ['students'] })
    isEditModalOpen.value = false
    uiStore.addToast({
      type: 'success',
      title: 'Payment Updated',
      message: 'Payment updated and student balance recalculated.'
    })
  }
})

const deletePaymentMutation = useMutation({
  mutationFn: (id: string) => paymentsApi.deletePayment(id),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['payment-overview-all'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history-all'] })
    queryClient.invalidateQueries({ queryKey: ['students'] })
    uiStore.addToast({
      type: 'error',
      title: 'Payment Deleted',
      message: 'Payment removed and student balance rolled back.'
    })
  }
})

// Handlers
const openAddPayment = (studentId?: string) => {
  preselectedStudentId.value = studentId || null
  isAddModalOpen.value = true
}

const openWithdraw = (studentId?: string) => {
  preselectedStudentId.value = studentId || null
  isWithdrawModalOpen.value = true
}

const openEdit = (p: Payment) => {
  editingPayment.value = p
  isEditModalOpen.value = true
}

const deletePayment = (p: Payment) => {
  if (confirm(`Are you sure you want to delete payment of ${p.amount} UZS for ${p.student_full_name || p.student_name || 'General'}?`)) {
    deletePaymentMutation.mutate(p.id)
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Navigation Tabs & Primary Action Buttons Row -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 select-none">
      <!-- Left: Tab Switcher Pills -->
      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="activeTab = 'overview'"
          class="px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 shadow-xs"
          :class="activeTab === 'overview'
            ? 'bg-[#1868db] text-white shadow-blue-500/20'
            : 'bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-750'"
        >
          <Users class="w-4 h-4" />
          <span>Students</span>
        </button>

        <button
          type="button"
          @click="activeTab = 'history'"
          class="px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 shadow-xs"
          :class="activeTab === 'history'
            ? 'bg-[#1868db] text-white shadow-blue-500/20'
            : 'bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-750'"
        >
          <Receipt class="w-4 h-4" />
          <span>Payment History</span>
        </button>
      </div>

      <!-- Right: Action Buttons -->
      <div class="flex items-center gap-2.5">
        <button
          type="button"
          @click="openAddPayment()"
          class="px-4 py-2 rounded-xl bg-[#1868db] hover:bg-[#1557bf] text-white text-xs font-bold shadow-xs transition-all cursor-pointer flex items-center gap-1.5 active:scale-98"
        >
          <Plus class="w-4 h-4" />
          <span>Add Payment</span>
        </button>

        <button
          type="button"
          @click="openWithdraw()"
          class="px-4 py-2 rounded-xl bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-750 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 text-xs font-bold shadow-2xs transition-all cursor-pointer flex items-center gap-1.5 active:scale-98"
        >
          <Minus class="w-4 h-4" />
          <span>Withdraw</span>
        </button>
      </div>
    </div>

    <!-- TAB 1: Student Financial Overview -->
    <div v-if="activeTab === 'overview'">
      <PaymentStudentOverview
        :students="overviewStudents"
        :is-loading="isOverviewLoading"
        :options="options"
        v-model:search-query="overviewSearch"
        v-model:selected-status="overviewStatus"
        v-model:selected-tariff="selectedTariff"
        v-model:selected-balance="selectedBalance"
        v-model:selected-group="selectedGroup"
        v-model:view-mode="viewMode"
        @open-add-payment="openAddPayment"
        @open-withdraw="openWithdraw"
      />

      <!-- Overview Pagination -->
      <div v-if="overviewTotalPages > 1" class="flex items-center justify-between px-4 py-3 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 mt-4 select-none">
        <div>
          Showing <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min((overviewPage - 1) * 30 + 1, overviewTotalCount) }}</span> to
          <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min(overviewPage * 30, overviewTotalCount) }}</span> of
          <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ overviewTotalCount }}</span> students
        </div>
        <div class="flex items-center gap-1.5">
          <button
            @click="overviewPage = Math.max(1, overviewPage - 1)"
            :disabled="overviewPage === 1"
            class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed hover:bg-zinc-100 transition-colors"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <span class="px-3 py-1 font-bold text-zinc-800 dark:text-zinc-200">Page {{ overviewPage }} of {{ overviewTotalPages }}</span>
          <button
            @click="overviewPage = Math.min(overviewTotalPages, overviewPage + 1)"
            :disabled="overviewPage === overviewTotalPages"
            class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed hover:bg-zinc-100 transition-colors"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- TAB 2: Payment History -->
    <div v-if="activeTab === 'history'">
      <PaymentHistoryTable
        :payments="paymentsList"
        :is-loading="isHistoryLoading"
        v-model:search-query="historySearch"
        v-model:selected-method="selectedMethod"
        v-model:selected-receiver="selectedReceiver"
        @export-excel="() => paymentsApi.exportExcel()"
        @open-edit="openEdit"
        @delete-payment="deletePayment"
      />

      <!-- History Pagination -->
      <div v-if="historyTotalPages > 1" class="flex items-center justify-between px-4 py-3 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 mt-4 select-none">
        <div>
          Showing <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min((historyPage - 1) * 30 + 1, historyTotalCount) }}</span> to
          <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ Math.min(historyPage * 30, historyTotalCount) }}</span> of
          <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ historyTotalCount }}</span> payments
        </div>
        <div class="flex items-center gap-1.5">
          <button
            @click="historyPage = Math.max(1, historyPage - 1)"
            :disabled="historyPage === 1"
            class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed hover:bg-zinc-100 transition-colors"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <span class="px-3 py-1 font-bold text-zinc-800 dark:text-zinc-200">Page {{ historyPage }} of {{ historyTotalPages }}</span>
          <button
            @click="historyPage = Math.min(historyTotalPages, historyPage + 1)"
            :disabled="historyPage === historyTotalPages"
            class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed hover:bg-zinc-100 transition-colors"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <AddPaymentModal
      :is-open="isAddModalOpen"
      :preselected-student-id="preselectedStudentId"
      @close="isAddModalOpen = false"
      @submit="data => createPaymentMutation.mutate(data)"
    />

    <WithdrawModal
      :is-open="isWithdrawModalOpen"
      :preselected-student-id="preselectedStudentId"
      @close="isWithdrawModalOpen = false"
      @submit="data => withdrawMutation.mutate(data)"
    />

    <EditPaymentModal
      :is-open="isEditModalOpen"
      :payment="editingPayment"
      @close="isEditModalOpen = false"
      @submit="data => editPaymentMutation.mutate(data)"
    />
  </div>
</template>
