<script setup lang="ts">
import { ref, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useCurrency } from '@/composables/useCurrency'
import type { Payment, Student } from '@/types'
import { Pencil, X, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  payment: Payment | null
  students: Student[]
  paymentMethods: string[]
  paymentReceivers: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const { formatAmountInput, parseAmount } = useCurrency()

const amountInput = ref('')
const method = ref('')
const receivedBy = ref('')
const notes = ref('')
const error = ref<string | null>(null)
const isSubmitting = ref(false)

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

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) {
    emit('close')
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

const allMethods = computed(() => {
  const defaults = props.paymentMethods.length > 0 ? props.paymentMethods : ['Karta J.A', 'Karta Abdulaziz', 'Naqd', 'Karta M.A', 'Bank', 'Discount']
  return Array.from(new Set([...defaults, 'Withdrawal']))
})

const allReceivers = computed(() => {
  const defaults = props.paymentReceivers.length > 0 ? props.paymentReceivers : ['ABDULAZIZ', 'MUSLIHIDDIN', 'BAXTIYOR', 'MUHAMMADALI', 'JASUR', 'ADMIN', 'Discount']
  return Array.from(new Set([...defaults, 'System']))
})

const linkedStudent = computed(() => {
  if (!props.payment?.student_id) return null
  return props.students.find(s => s.id === props.payment?.student_id) || null
})

function formatAmount(val: number | string | null | undefined) {
  if (val === null || val === undefined) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('uz-UZ').format(Math.round(num || 0))
}

watch(() => [props.isOpen, props.payment], ([isOpenVal]) => {
  if (isOpenVal && props.payment) {
    const absVal = Math.abs(Number(props.payment.amount) || 0)
    amountInput.value = formatAmount(absVal)
    method.value = props.payment.method || allMethods.value[0]
    receivedBy.value = props.payment.received_by || allReceivers.value[0]
    notes.value = props.payment.notes || ''
    error.value = null
    isSubmitting.value = false

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

const onAmountChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  amountInput.value = formatAmountInput(target.value)
}

const handleSubmit = () => {
  if (!props.payment) return
  const rawAmount = parseAmount(amountInput.value)
  if (!rawAmount || rawAmount <= 0) {
    error.value = 'Please enter a valid amount!'
    return
  }
  if (!method.value) {
    error.value = 'Please select a payment method!'
    return
  }
  if (!receivedBy.value) {
    error.value = 'Please select who received the payment!'
    return
  }

  const isNegative = Number(props.payment.amount) < 0
  const newAmount = isNegative ? -rawAmount : rawAmount

  isSubmitting.value = true
  emit('submit', {
    amount: newAmount,
    method: method.value,
    received_by: receivedBy.value,
    notes: notes.value.trim()
  })
}
</script>

<template>
  <div
    v-if="isOpen && payment"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none overflow-hidden"
  >
    <div class="fixed inset-0" @click="emit('close')" />

    <!-- Scale wrapper for smaller laptop displays -->
    <div class="relative z-10 flex items-center justify-center pointer-events-auto" :style="{ zoom: modalZoom }">
      <div
        ref="modalPanelRef"
        class="relative w-[565px] max-w-[calc(100vw-2rem)] rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] shadow-2xl overflow-hidden flex flex-col p-4 sm:p-5 gap-3.5 text-xs text-zinc-900 dark:text-zinc-100 animate-page-in"
        @click.stop
      >
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-2.5">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-xl bg-blue-600/10 dark:bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center border border-blue-500/20">
              <Pencil class="h-4 w-4" />
            </div>
            <div class="flex flex-col">
              <h3 class="text-sm font-extrabold text-zinc-900 dark:text-zinc-100 tracking-tight">Edit Payment</h3>
              <span class="text-[10px] text-zinc-400 font-medium">Update transaction details</span>
            </div>
          </div>
          <button
            type="button"
            @click="emit('close')"
            class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
            title="Close (Esc)"
          >
            <X class="h-4 w-4" />
          </button>
        </div>

        <!-- Error Alert -->
        <div
          v-if="error"
          class="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-2"
        >
          <AlertCircle class="w-4 h-4 shrink-0" />
          <span>{{ error }}</span>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="flex flex-col gap-3 text-xs">
          <!-- Student Info (Read-only) -->
          <div>
            <label class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 mb-1 block">Student</label>
            <div class="px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-750 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-700 dark:text-zinc-300 flex items-center justify-between">
              <span class="font-bold uppercase truncate">
                {{ payment.student_id ? `${payment.student_id} — ${payment.student_full_name || payment.student_name}` : 'General payment (No Student)' }}
              </span>
              <span
                v-if="linkedStudent?.is_deleted"
                class="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shrink-0"
              >
                Archive
              </span>
            </div>
          </div>

          <!-- Amount -->
          <div>
            <label class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 mb-1 block">Amount (UZS) *</label>
            <input
              type="text"
              :value="amountInput"
              @input="onAmountChange"
              placeholder="0"
              required
              class="w-full px-3 py-2 text-sm border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 font-mono font-bold"
            />
          </div>

          <!-- Method & Received By -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 mb-1 block">Method</label>
              <select
                v-model="method"
                class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 cursor-pointer font-semibold focus:outline-none focus:border-blue-500"
              >
                <option v-for="m in allMethods" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
            <div>
              <label class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 mb-1 block">Received By</label>
              <select
                v-model="receivedBy"
                class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 cursor-pointer font-semibold focus:outline-none focus:border-blue-500"
              >
                <option v-for="r in allReceivers" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
          </div>

          <!-- Notes -->
          <div>
            <label class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 mb-1 block">Notes</label>
            <textarea
              v-model="notes"
              rows="2"
              placeholder="Edit notes..."
              class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="isSubmitting"
            class="mt-1 w-full py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 shadow-2xs"
          >
            {{ isSubmitting ? 'Saving...' : 'Save Changes' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
