<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useCurrency } from '@/composables/useCurrency'
import type { Student, Payment } from '@/types'
import { CreditCard, X, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  preselectedStudentId?: string | null
  students: Student[]
  payments?: Payment[]
  paymentMethods: string[]
  paymentReceivers: string[]
  notePills: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const { formatAmountInput, parseAmount } = useCurrency()

const amountInput = ref('')
const method = ref('')
const receivedBy = ref('')
const selectedStudentId = ref('')
const studentSearch = ref('')
const notes = ref('')
const error = ref<string | null>(null)
const isSubmitting = ref(false)

const selectedStudent = computed(() => {
  if (!selectedStudentId.value) return null
  return props.students.find(s => s.id === selectedStudentId.value) || null
})

const studentOptions = computed(() => {
  if (!studentSearch.value) return props.students.slice(0, 30)
  const q = studentSearch.value.toLowerCase()
  return props.students.filter(s =>
    (s.id || '').toLowerCase().includes(q) ||
    (s.full_name || '').toLowerCase().includes(q)
  ).slice(0, 30)
})

const recentStudentPayments = computed(() => {
  if (!selectedStudentId.value || !props.payments) return []
  return props.payments
    .filter(p => p.student_id === selectedStudentId.value)
    .slice(0, 5)
})

function formatAmount(val: number | string | null | undefined) {
  if (val === null || val === undefined) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('uz-UZ').format(Math.round(num || 0))
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    selectedStudentId.value = props.preselectedStudentId || ''
    studentSearch.value = ''
    amountInput.value = ''
    method.value = props.paymentMethods[0] || 'Karta J.A'
    receivedBy.value = props.paymentReceivers[0] || 'ABDULAZIZ'
    notes.value = ''
    error.value = null
    isSubmitting.value = false
  }
})

const onAmountChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  amountInput.value = formatAmountInput(target.value)
}

const addNotePill = (pill: string) => {
  const current = notes.value.trim()
  if (pill === 'DISCOUNT') {
    method.value = 'Discount'
    receivedBy.value = 'Discount'
  }
  notes.value = current ? `${current}, ${pill}` : pill
}

const handleSubmit = () => {
  const numericAmount = parseAmount(amountInput.value)
  if (!numericAmount || numericAmount <= 0) {
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

  const isDiscount = notes.value.toUpperCase().includes('DISCOUNT')
  if (isDiscount && !selectedStudentId.value) {
    error.value = 'Please select a student for the discount!'
    return
  }

  isSubmitting.value = true
  emit('submit', {
    student_id: selectedStudentId.value || null,
    amount: numericAmount,
    method: method.value,
    received_by: receivedBy.value,
    notes: notes.value.trim(),
    is_discount: isDiscount
  })
}
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs select-none"
  >
    <div
      class="bg-white dark:bg-[#181a1d] border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-page-in p-6 flex flex-col gap-4 max-h-[90vh] overflow-y-auto"
      @click.stop
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
        <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <CreditCard class="h-4 w-4 text-blue-600" />
          <span>Add Payment</span>
        </h3>
        <button
          type="button"
          @click="emit('close')"
          class="cursor-pointer text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
        >
          <X class="h-5 w-5" />
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

      <!-- Form Fields -->
      <form @submit.prevent="handleSubmit" class="flex flex-col gap-3.5 text-xs">
        <!-- Amount -->
        <div>
          <label class="text-xs font-semibold text-zinc-500 mb-1 block">Amount (UZS) *</label>
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
            <label class="text-xs font-semibold text-zinc-500 mb-1 block">Method</label>
            <select
              v-model="method"
              class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 cursor-pointer font-semibold focus:outline-none focus:border-blue-500"
            >
              <option v-for="m in paymentMethods" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs font-semibold text-zinc-500 mb-1 block">Received By</label>
            <select
              v-model="receivedBy"
              class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 cursor-pointer font-semibold focus:outline-none focus:border-blue-500"
            >
              <option v-for="r in paymentReceivers" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
        </div>

        <!-- Student Selection (Searchable) -->
        <div>
          <label class="text-xs font-semibold text-zinc-500 mb-1 block">Student (optional)</label>
          <div
            v-if="selectedStudent"
            class="flex items-center justify-between px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850"
          >
            <span class="text-zinc-900 dark:text-zinc-100 font-bold truncate flex items-center gap-2">
              <span class="font-mono text-blue-600">{{ selectedStudent.id }}</span>
              <span>—</span>
              <span class="uppercase">{{ selectedStudent.full_name }}</span>
              <span
                v-if="selectedStudent.is_deleted"
                class="px-1.5 py-0.5 rounded text-[9.5px] font-bold tracking-wider uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shrink-0"
              >
                Archive
              </span>
            </span>
            <button
              type="button"
              @click="selectedStudentId = ''"
              class="cursor-pointer text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-0.5"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <div v-else class="relative">
            <input
              type="text"
              v-model="studentSearch"
              placeholder="Search student by name or ID..."
              class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500"
            />
            <div
              v-if="studentSearch"
              class="mt-1 max-h-40 overflow-y-auto rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-lg divide-y divide-zinc-100 dark:divide-zinc-800"
            >
              <div
                v-for="s in studentOptions"
                :key="s.id"
                @click="selectedStudentId = s.id; studentSearch = ''"
                class="px-3 py-2 text-xs cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-900 dark:text-zinc-100 flex items-center justify-between"
              >
                <div class="flex items-center gap-2">
                  <span class="font-mono font-bold text-blue-600">{{ s.id }}</span>
                  <span>—</span>
                  <span class="font-semibold uppercase">{{ s.full_name }}</span>
                </div>
                <span
                  v-if="s.is_deleted"
                  class="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shrink-0"
                >
                  Archive
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Notes & Note Pills -->
        <div>
          <label class="text-xs font-semibold text-zinc-500 mb-1 block">Notes</label>
          <textarea
            v-model="notes"
            rows="2"
            placeholder="Add note..."
            class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 resize-none"
          />
          <div class="flex flex-wrap gap-1.5 mt-1.5">
            <button
              v-for="pill in notePills"
              :key="pill"
              type="button"
              @click="addNotePill(pill)"
              class="text-[10px] font-semibold px-2 py-0.5 rounded-full border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-750 cursor-pointer text-zinc-600 dark:text-zinc-400 transition-colors"
            >
              {{ pill }}
            </button>
          </div>
        </div>

        <!-- Recent Student Payments Preview -->
        <div v-if="selectedStudent && recentStudentPayments.length > 0" class="border-t border-zinc-100 dark:border-zinc-800 pt-2.5">
          <div class="text-[11px] font-semibold text-zinc-500 mb-1.5">Recent Payments for this student</div>
          <div class="max-h-24 overflow-y-auto flex flex-col gap-1 pr-1">
            <div
              v-for="p in recentStudentPayments"
              :key="p.id"
              class="flex items-center justify-between text-[11px] text-zinc-600 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-850/60 px-2 py-1 rounded-lg"
            >
              <span>{{ p.created_at ? new Date(p.created_at).toLocaleDateString('uz-UZ') : '' }} ({{ p.method }})</span>
              <span
                class="font-mono font-bold"
                :class="Number(p.amount) < 0 ? 'text-rose-500' : 'text-emerald-500'"
              >
                {{ Number(p.amount) < 0 ? '-' : '+' }}{{ formatAmount(Math.abs(Number(p.amount))) }} UZS
              </span>
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isSubmitting"
          class="mt-2 w-full py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 shadow-2xs"
        >
          {{ isSubmitting ? 'Saving...' : 'Save Payment' }}
        </button>
      </form>
    </div>
  </div>
</template>
