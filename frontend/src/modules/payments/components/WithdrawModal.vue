<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useCurrency } from '@/composables/useCurrency'
import type { Student } from '@/types'
import { Wallet, X, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  preselectedStudentId?: string | null
  students: Student[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const { formatAmountInput, parseAmount } = useCurrency()

const amountInput = ref('')
const selectedStudentId = ref('')
const studentSearch = ref('')
const reason = ref('')
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

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    selectedStudentId.value = props.preselectedStudentId || ''
    studentSearch.value = ''
    amountInput.value = ''
    reason.value = ''
    error.value = null
    isSubmitting.value = false
  }
})

const onAmountChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  amountInput.value = formatAmountInput(target.value)
}

const handleSubmit = () => {
  const numericAmount = parseAmount(amountInput.value)
  if (!numericAmount || numericAmount <= 0) {
    error.value = 'Please enter a valid amount!'
    return
  }
  if (!reason.value.trim()) {
    error.value = 'Please enter a reason for withdrawal!'
    return
  }

  isSubmitting.value = true
  emit('submit', {
    student_id: selectedStudentId.value || null,
    amount: numericAmount,
    reason: reason.value.trim()
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
          <Wallet class="h-4 w-4 text-rose-500" />
          <span>Withdraw Payment</span>
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

      <!-- Form -->
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
            class="w-full px-3 py-2 text-sm border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-rose-500 font-mono font-bold"
          />
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
              class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-rose-500"
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

        <!-- Reason -->
        <div>
          <label class="text-xs font-semibold text-zinc-500 mb-1 block">Reason *</label>
          <textarea
            v-model="reason"
            rows="2"
            required
            placeholder="Enter reason for withdrawal..."
            class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-rose-500 resize-none"
          />
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isSubmitting"
          class="mt-2 w-full py-2.5 rounded-xl bg-rose-500 text-white font-bold text-xs hover:bg-rose-600 active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 shadow-2xs"
        >
          {{ isSubmitting ? 'Saving...' : 'Confirm Withdrawal' }}
        </button>
      </form>
    </div>
  </div>
</template>
