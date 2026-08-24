<script setup lang="ts">
import { ref, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
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
  const numericAmount = parseAmount(amountInput.value)
  if (!numericAmount || numericAmount <= 0) {
    error.value = 'Please enter a valid amount!'
    return
  }
  if (!selectedStudentId.value) {
    error.value = 'Please select a student for the withdrawal!'
    return
  }
  if (!reason.value.trim()) {
    error.value = 'Please enter a reason for withdrawal!'
    return
  }

  isSubmitting.value = true
  emit('submit', {
    student_id: selectedStudentId.value,
    amount: numericAmount,
    reason: reason.value.trim()
  })
}
</script>

<template>
  <div
    v-if="isOpen"
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
            <div class="w-8 h-8 rounded-xl bg-rose-500/10 dark:bg-rose-500/15 text-rose-600 dark:text-rose-400 flex items-center justify-center border border-rose-500/20">
              <Wallet class="h-4 w-4" />
            </div>
            <div class="flex flex-col">
              <h3 class="text-sm font-extrabold text-zinc-900 dark:text-zinc-100 tracking-tight">Withdraw Payment</h3>
              <span class="text-[10px] text-zinc-400 font-medium">Process a student balance withdrawal</span>
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
          <!-- Amount -->
          <div>
            <label class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 mb-1 block">
              Amount (UZS) <span class="text-rose-500">*</span>
            </label>
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
            <label class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 mb-1 block">
              Student <span class="text-rose-500">*</span>
            </label>
            <div
              v-if="selectedStudent"
              class="flex items-center justify-between px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-xl bg-zinc-50 dark:bg-zinc-850"
            >
              <span class="text-zinc-900 dark:text-zinc-100 font-bold truncate flex items-center gap-2">
                <span class="font-mono text-blue-600 dark:text-blue-400 font-bold">{{ selectedStudent.id }}</span>
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
                    <span class="font-mono font-bold text-blue-600 dark:text-blue-400">{{ s.id }}</span>
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
            <label class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 mb-1 block">Reason *</label>
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
            class="mt-1 w-full py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 shadow-2xs"
          >
            {{ isSubmitting ? 'Saving...' : 'Confirm Withdrawal' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
