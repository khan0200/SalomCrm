<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { useCurrency } from '@/composables/useCurrency'
import { MinusCircle, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  preselectedStudentId?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const { formatAmountInput, parseAmount } = useCurrency()

const studentId = ref('')
const amountInput = ref('')
const reason = ref('')
const error = ref<string | null>(null)
const isSubmitting = ref(false)

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    studentId.value = props.preselectedStudentId || ''
    amountInput.value = ''
    reason.value = ''
    error.value = null
  }
})

const onAmountChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  amountInput.value = formatAmountInput(target.value)
}

const handleSubmit = () => {
  const numericAmount = parseAmount(amountInput.value)
  if (!numericAmount || numericAmount <= 0) {
    error.value = 'Please enter a valid withdrawal amount.'
    return
  }
  if (!reason.value.trim()) {
    error.value = 'Please enter a withdrawal reason.'
    return
  }

  isSubmitting.value = true
  emit('submit', {
    student_id: studentId.value ? studentId.value.trim().toUpperCase() : null,
    amount: numericAmount,
    reason: reason.value.trim()
  })
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Record Fund Withdrawal"
    subtitle="Record a refund or fund withdrawal (deducts from student balance)."
    max-width="max-w-md"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-4 text-xs">
      <div v-if="error" class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 flex items-center gap-2 font-semibold">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">Student ID (Optional)</label>
        <input
          v-model="studentId"
          type="text"
          placeholder="e.g. UB120"
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold uppercase focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 outline-none"
        />
      </div>

      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
          Withdrawal Amount (UZS) <span class="text-rose-500">*</span>
        </label>
        <div class="relative">
          <input
            :value="amountInput"
            @input="onAmountChange"
            type="text"
            placeholder="0"
            required
            class="w-full px-3 py-2 pr-12 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold text-base text-rose-600 dark:text-rose-400 focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 outline-none"
          />
          <span class="absolute right-3.5 top-1/2 -translate-y-1/2 text-[11px] font-bold text-zinc-400">UZS</span>
        </div>
      </div>

      <div>
        <label class="block font-bold text-zinc-700 dark:text-zinc-300 mb-1">
          Reason for Withdrawal <span class="text-rose-500">*</span>
        </label>
        <input
          v-model="reason"
          type="text"
          placeholder="e.g. Visa cancelled refund, Overpayment return"
          required
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 outline-none"
        />
      </div>

      <div class="pt-4 flex items-center justify-end gap-2.5 border-t border-zinc-100 dark:border-zinc-800">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold transition-all shadow-md shadow-rose-600/25 cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
        >
          <MinusCircle class="w-4 h-4" />
          <span>Confirm Withdrawal</span>
        </button>
      </div>
    </form>
  </BaseModal>
</template>
