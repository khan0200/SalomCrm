<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { X, Folder, FileText, CheckSquare, CheckCircle2 } from 'lucide-vue-next'
import type { Student } from '@/types'
import { useDocumentHelpers } from '@/composables/useDocumentHelpers'
import { useCurrency } from '@/composables/useCurrency'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  isOpen: boolean
  student: Student | null
  updating: boolean
  paymentsDone: number | null
  paymentsDoneLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toggle-pick', studentId: string, pill: string): void
  (e: 'toggle-mc', studentId: string): void
  (e: 'update-count', studentId: string, field: string, value: number): void
}>()

const authStore = useAuthStore()

const {
  getEffectiveMissingDocs, getDocRemainingCount, PICK_NEEDED_LIST, HAND_COUNT_DOCS
} = useDocumentHelpers()

const { formatCurrency } = useCurrency()

const modalPanelRef = ref<HTMLElement | null>(null)
const modalZoom = ref(1)

// Never shrink past this — below ~62% the 10px labels stop being readable.
const MIN_ZOOM = 0.62
// Breathing room around the panel at full size.
const VIEWPORT_MARGIN = 40

// Scale wrapper: the modal keeps one fixed design at every size — on screens
// too short to fit it (e.g. 1366x768, 1280x800) the whole thing is zoomed down
// proportionally instead of reflowing, so it looks identical everywhere.
const recalcZoom = () => {
  const el = modalPanelRef.value
  if (!el) return

  // Measure at natural size, then scale to fit.
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

    // Round to 3dp to avoid sub-pixel jitter on resize.
    modalZoom.value = fit >= 1 ? 1 : Math.max(MIN_ZOOM, Math.round(fit * 1000) / 1000)
  })
}

let resizeObserver: ResizeObserver | null = null

watch(() => props.isOpen, (open) => {
  if (open) {
    nextTick(() => {
      recalcZoom()
      // Content can grow after open (payments total resolving, longer lists),
      // so re-fit whenever the panel's own size changes.
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

onMounted(() => window.addEventListener('resize', recalcZoom))
onUnmounted(() => {
  window.removeEventListener('resize', recalcZoom)
  resizeObserver?.disconnect()
})

const missingDocs = computed(() => props.student ? getEffectiveMissingDocs(props.student) : [])

const eduLevel = computed(() => {
  if (!props.student) return 'No Level'
  return [props.student.level, props.student.level2].filter(Boolean).join(', ') || 'No Level'
})

const isPillActive = (pill: string) => {
  const pick = props.student?.pick_needed || []
  return pick.includes(pill)
}

const getPillActiveColor = (pill: string) => {
  if (pill === 'APOSTILLE' || pill === 'Foreign passport') return '#ea580c'
  if (pill === 'BIRTH CERTIFICATE') return '#f59e0b'
  if (pill === 'MARRIAGE CERTIFICATE') return '#2563eb'
  if (pill === 'AJRASHGANLIK') return '#ec4899'
  if (pill === 'FULL OK') return '#10b981'
  return '#4b5563'
}

const counters = computed(() => {
  if (!props.student) return []
  const s = props.student
  const list = missingDocs.value
  return HAND_COUNT_DOCS.map(item => {
    const isMissing = !list.includes('FULL OK') && list.includes(item.name)
    const isMcDisabled = item.label === 'MC' && s.has_mc === false
    const remaining = getDocRemainingCount(s, item.name)
    return {
      ...item,
      isMissing,
      isMcDisabled,
      remaining,
      isDisabled: isMissing || isMcDisabled || props.updating || !authStore.canEdit,
    }
  })
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-[220ms] ease-out"
      enter-from-class="opacity-0"
      leave-active-class="transition-all duration-[220ms] ease-out"
      leave-to-class="opacity-0"
    >
      <div v-if="isOpen && student" class="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-auto">
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/50 backdrop-blur-[2px]" @click="emit('close')" />

        <!-- Scale wrapper -->
        <div class="relative z-10" :style="{ zoom: modalZoom }">
          <div
            ref="modalPanelRef"
            class="relative w-[820px] max-w-[calc(100vw-2rem)] rounded-[28px] border border-[var(--border)] bg-[var(--surface-elevated)] shadow-2xl flex flex-col overflow-hidden"
          >
            <!-- Header -->
            <div class="px-6 pt-6 pb-5 flex items-start gap-3.5 border-b border-[var(--border)]">
              <div class="w-10 h-10 rounded-2xl bg-blue-500/12 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
                <Folder class="h-5 w-5" />
              </div>
              <div class="min-w-0 flex-1 pt-0.5">
                <h2 class="text-[15px] font-bold text-[var(--foreground)] leading-tight truncate">
                  {{ student.full_name }}
                </h2>
                <p class="text-[12px] text-[var(--foreground-muted)] mt-0.5">Document checklist</p>
              </div>
              <button
                :disabled="updating"
                @click="emit('close')"
                class="w-8 h-8 shrink-0 rounded-full flex items-center justify-center text-[var(--foreground-muted)] bg-[var(--surface)] hover:bg-zinc-200 dark:hover:bg-zinc-700 hover:text-[var(--foreground)] transition-all cursor-pointer disabled:opacity-50"
              >
                <X class="h-4 w-4" />
              </button>
            </div>

            <!-- Scrollable body -->
            <div class="px-6 py-5 flex flex-col gap-5 overflow-y-auto max-h-[min(76vh,700px)]">
              <!-- Student Info Strip (iOS grouped-list style) -->
              <div class="rounded-2xl bg-[var(--surface)] border border-[var(--border)] overflow-hidden">
                <div class="grid grid-cols-2 sm:grid-cols-3 divide-x divide-y divide-[var(--border)] [&>*:nth-child(3n)]:border-r-0 sm:[&>*:nth-child(2n)]:border-r">
                  <div class="px-4 py-3">
                    <span class="block text-[10px] uppercase font-semibold text-[var(--foreground-muted)] tracking-wide mb-0.5">Student ID</span>
                    <span class="text-[13px] font-bold text-blue-600 dark:text-blue-400 font-mono">{{ student.id }}</span>
                  </div>
                  <div class="px-4 py-3">
                    <span class="block text-[10px] uppercase font-semibold text-[var(--foreground-muted)] tracking-wide mb-0.5">Status</span>
                    <span v-if="student.is_deleted" class="inline-flex items-center gap-1.5 text-[13px] font-bold text-rose-600 dark:text-rose-400">
                      <span class="w-1.5 h-1.5 rounded-full bg-rose-500" /> Deleted
                    </span>
                    <span v-else class="inline-flex items-center gap-1.5 text-[13px] font-bold text-emerald-600 dark:text-emerald-400">
                      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Active
                    </span>
                  </div>
                  <div class="px-4 py-3">
                    <span class="block text-[10px] uppercase font-semibold text-[var(--foreground-muted)] tracking-wide mb-0.5">Group</span>
                    <span class="text-[13px] font-semibold text-[var(--foreground)] truncate block">{{ student.student_group || '—' }}</span>
                  </div>
                  <div class="px-4 py-3">
                    <span class="block text-[10px] uppercase font-semibold text-[var(--foreground-muted)] tracking-wide mb-0.5">Edu-Level</span>
                    <span class="text-[13px] font-semibold text-[var(--foreground)] truncate block" :title="eduLevel">{{ eduLevel }}</span>
                  </div>
                  <div class="px-4 py-3">
                    <span class="block text-[10px] uppercase font-semibold text-[var(--foreground-muted)] tracking-wide mb-0.5">Office</span>
                    <span class="text-[13px] font-semibold text-[var(--foreground)] truncate block">{{ (student as any).office || '—' }}</span>
                  </div>
                  <div v-if="authStore.canAccessPayments" class="px-4 py-3">
                    <span class="block text-[10px] uppercase font-semibold text-[var(--foreground-muted)] tracking-wide mb-0.5">Payments Done</span>
                    <span v-if="paymentsDoneLoading" class="inline-block h-3.5 w-16 rounded bg-zinc-200 dark:bg-zinc-700 animate-pulse" />
                    <span v-else class="text-[13px] font-bold text-emerald-600 dark:text-emerald-400">
                      {{ formatCurrency(paymentsDone ?? 0) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Document Checklist: one list, each pill IS the missing-doc state.
                   The old layout showed the same 22 items twice — once as
                   "Missing Documents" (whichever pills are toggled on) and
                   again as "Pick Needed" (all 22, with active ones filled in).
                   A toggled-on pill already means "required/missing"; there is
                   nothing a second list could say that this one doesn't. -->
              <div class="rounded-2xl bg-[var(--surface)] border border-[var(--border)] p-4 flex flex-col gap-3">
                <div class="flex items-center justify-between">
                  <h3 class="text-[12px] font-bold text-[var(--foreground)] uppercase tracking-wide flex items-center gap-1.5">
                    <FileText class="h-3.5 w-3.5 text-[var(--foreground-muted)]" />
                    Document Checklist
                  </h3>
                  <span
                    class="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full"
                    :class="missingDocs.includes('FULL OK') || missingDocs.length === 0
                      ? 'bg-emerald-500/12 text-emerald-600 dark:text-emerald-400'
                      : 'bg-rose-500/12 text-rose-600 dark:text-rose-400'"
                  >
                    {{ missingDocs.includes('FULL OK') || missingDocs.length === 0
                      ? 'Complete'
                      : `${missingDocs.length} missing` }}
                  </span>
                </div>

                <div class="flex flex-wrap gap-1.5">
                  <button
                    v-for="pill in PICK_NEEDED_LIST"
                    :key="pill"
                    type="button"
                    :disabled="updating || !authStore.canEdit"
                    @click="emit('toggle-pick', student.id, pill)"
                    class="px-3 py-1.5 rounded-full text-[11px] font-semibold uppercase tracking-wide border transition-all active:scale-95 disabled:opacity-50 whitespace-nowrap inline-flex items-center gap-1.5"
                    :class="[
                      authStore.canEdit ? 'cursor-pointer' : 'cursor-default',
                      isPillActive(pill)
                        ? 'text-white shadow-sm border-transparent'
                        : (pill === 'FULL OK'
                            ? 'border-emerald-500/40 text-emerald-600 dark:text-emerald-400 bg-emerald-500/5 hover:bg-emerald-500/10'
                            : 'border-[var(--border)] text-[var(--foreground-muted)] bg-[var(--surface-elevated)] hover:border-zinc-400 dark:hover:border-zinc-600')
                    ]"
                    :style="isPillActive(pill)
                      ? { backgroundColor: getPillActiveColor(pill), borderColor: getPillActiveColor(pill) }
                      : {}"
                  >
                    <X v-if="isPillActive(pill) && authStore.canEdit" class="h-3 w-3 opacity-70" />
                    {{ pill }}
                  </button>
                </div>
              </div>

              <!-- Physical Copies In Hand -->
              <div class="rounded-2xl bg-[var(--surface)] border border-[var(--border)] p-4 flex flex-col gap-3.5">
                <h3 class="text-[12px] font-bold text-[var(--foreground)] uppercase tracking-wide flex items-center gap-1.5">
                  <CheckSquare class="h-3.5 w-3.5 text-[var(--foreground-muted)]" />
                  Physical Copies In Hand
                </h3>

                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div
                    v-for="item in counters"
                    :key="item.key"
                    class="relative rounded-2xl bg-[var(--surface-elevated)] px-3 py-3.5 flex flex-col items-center gap-2.5 select-none"
                  >
                    <!-- MC enable/disable toggle -->
                    <label
                      v-if="item.label === 'MC'"
                      class="absolute top-2.5 right-2.5"
                      :class="authStore.canEdit ? 'cursor-pointer' : 'cursor-default'"
                    >
                      <input
                        type="checkbox"
                        :checked="student.has_mc !== false"
                        :disabled="updating || !authStore.canEdit"
                        @change="emit('toggle-mc', student.id)"
                        class="sr-only peer"
                      />
                      <div class="w-7 h-4 bg-zinc-300 dark:bg-zinc-700 rounded-full peer-checked:bg-blue-500 transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-3" />
                    </label>

                    <span class="text-[10px] uppercase font-semibold text-[var(--foreground-muted)] tracking-wide">{{ item.label }}</span>

                    <div class="flex items-center gap-3">
                      <button
                        type="button"
                        :disabled="item.isDisabled || item.remaining <= 0"
                        @click="emit('update-count', student.id, item.key, item.remaining - 1)"
                        class="h-7 w-7 rounded-full bg-[var(--surface)] border border-[var(--border)] text-[var(--foreground-muted)] flex items-center justify-center hover:bg-zinc-100 dark:hover:bg-zinc-800 active:scale-90 disabled:opacity-30 disabled:pointer-events-none cursor-pointer transition-all text-sm font-bold"
                      >
                        −
                      </button>

                      <span
                        class="font-bold text-[15px] w-8 text-center tabular-nums"
                        :class="item.isMcDisabled
                          ? 'text-[var(--foreground-subtle)]'
                          : (item.remaining > 0 ? 'text-blue-600 dark:text-blue-400' : 'text-[var(--foreground-muted)]')"
                      >
                        {{ item.isMcDisabled ? '—' : item.remaining }}
                      </span>

                      <button
                        type="button"
                        :disabled="item.isDisabled"
                        @click="emit('update-count', student.id, item.key, item.remaining + 1)"
                        class="h-7 w-7 rounded-full bg-[var(--surface)] border border-[var(--border)] text-[var(--foreground-muted)] flex items-center justify-center hover:bg-zinc-100 dark:hover:bg-zinc-800 active:scale-90 disabled:opacity-30 disabled:pointer-events-none cursor-pointer transition-all text-sm font-bold"
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-[var(--border)] flex justify-end">
              <button
                type="button"
                @click="emit('close')"
                class="bg-blue-600 hover:bg-blue-700 text-white rounded-full px-6 py-2.5 flex items-center gap-2 font-bold text-[13px] shadow-sm active:scale-[0.97] transition-all cursor-pointer"
              >
                <CheckCircle2 class="h-4 w-4" />
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
