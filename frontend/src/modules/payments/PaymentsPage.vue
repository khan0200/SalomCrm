<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { paymentsApi } from '@/api/payments'
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
const overviewStatus = ref('Active')
const selectedTariffs = ref<string[]>([])
const selectedBalances = ref<string[]>([])
const overviewPage = ref(1)

// History Tab Filters
const historySearch = ref('')
const selectedMethod = ref('all')
const selectedReceiver = ref('all')
const historyPage = ref(1)

// Query: Payment Student Overview
const { data: overviewData, isLoading: isOverviewLoading } = useQuery({
  queryKey: [
    'payment-overview',
    overviewPage,
    overviewSearch,
    overviewStatus,
    selectedTariffs,
    selectedBalances,
  ],
  queryFn: () => paymentsApi.getPaymentOverview({
    page: overviewPage.value,
    page_size: 30,
    search: overviewSearch.value,
    status: overviewStatus.value,
    tariff: selectedTariffs.value,
    balance: selectedBalances.value,
  }),
  enabled: computed(() => activeTab.value === 'overview'),
})

const overviewStudents = computed(() => overviewData.value?.results || [])
const overviewTotalPages = computed(() => overviewData.value?.total_pages || 1)
const overviewTotalCount = computed(() => overviewData.value?.count || 0)

// Query: Payment History
const { data: historyData, isLoading: isHistoryLoading } = useQuery({
  queryKey: [
    'payment-history',
    historyPage,
    historySearch,
    selectedMethod,
    selectedReceiver,
  ],
  queryFn: () => paymentsApi.getPaymentHistory({
    page: historyPage.value,
    page_size: 30,
    search: historySearch.value,
    method: selectedMethod.value,
    received_by: selectedReceiver.value,
  }),
  enabled: computed(() => activeTab.value === 'history'),
})

const paymentsList = computed(() => historyData.value?.results || [])
const historyTotalPages = computed(() => historyData.value?.total_pages || 1)
const historyTotalCount = computed(() => historyData.value?.count || 0)

// Mutations
const createPaymentMutation = useMutation({
  mutationFn: (data: any) => paymentsApi.createPayment(data),
  onSuccess: (res) => {
    queryClient.invalidateQueries({ queryKey: ['payment-overview'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history'] })
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
    queryClient.invalidateQueries({ queryKey: ['payment-overview'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history'] })
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
    queryClient.invalidateQueries({ queryKey: ['payment-overview'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history'] })
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
    queryClient.invalidateQueries({ queryKey: ['payment-overview'] })
    queryClient.invalidateQueries({ queryKey: ['payment-history'] })
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
    <!-- Header with Tab Switcher & Quick Add Buttons -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <CreditCard class="w-5 h-5 text-brand-500" />
          <span>Payments & Financial Ledger</span>
        </h1>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
          Track student tariffs, balances, discounts, payment history, and withdrawals.
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-2.5">
        <button
          @click="openWithdraw()"
          class="px-3.5 py-2 rounded-xl border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 hover:bg-rose-100"
        >
          <Minus class="w-4 h-4" />
          <span>Withdraw</span>
        </button>

        <button
          @click="openAddPayment()"
          class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/25 transition-all cursor-pointer flex items-center gap-1.5"
        >
          <Plus class="w-4 h-4" />
          <span>Add Payment</span>
        </button>
      </div>
    </div>

    <!-- Tab Switcher Navigation -->
    <div class="flex items-center gap-2 border-b border-zinc-200 dark:border-zinc-800 pb-2 select-none text-xs">
      <button
        @click="activeTab = 'overview'"
        class="px-4 py-2 rounded-xl font-bold transition-all cursor-pointer flex items-center gap-2"
        :class="activeTab === 'overview' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
      >
        <Users class="w-4 h-4" />
        <span>Student Overview</span>
      </button>

      <button
        @click="activeTab = 'history'"
        class="px-4 py-2 rounded-xl font-bold transition-all cursor-pointer flex items-center gap-2"
        :class="activeTab === 'history' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
      >
        <Receipt class="w-4 h-4" />
        <span>Payment History</span>
      </button>
    </div>

    <!-- TAB 1: Student Financial Overview -->
    <div v-if="activeTab === 'overview'">
      <PaymentStudentOverview
        :students="overviewStudents"
        :is-loading="isOverviewLoading"
        v-model:search-query="overviewSearch"
        v-model:selected-tariffs="selectedTariffs"
        v-model:selected-balances="selectedBalances"
        v-model:selected-status="overviewStatus"
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
