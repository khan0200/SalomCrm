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

// Match color based on the design: APOSTILLE -> orange, BIRTH CERTIFICATE -> yellow-orange
const getMissingRowColor = (doc: string) => {
  if (doc === 'APOSTILLE') return '#ea580c'
  if (doc === 'BIRTH CERTIFICATE') return '#f59e0b'
  if (doc === 'MARRIAGE CERTIFICATE') return '#2563eb'
  if (doc === 'AJRASHGANLIK') return '#ec4899'
  if (doc === 'Foreign passport') return '#ea580c'
  if (doc === 'FULL OK') return '#10b981'
  return '#6b7280'
}

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
        <div class="fixed inset-0 bg-black/50" @click="emit('close')" />

        <!-- Scale wrapper -->
        <div class="relative z-10" :style="{ zoom: modalZoom }">
          <div
            ref="modalPanelRef"
            class="relative w-[986px] max-w-[calc(100vw-2rem)] rounded-2xl border border-zinc-300 dark:border-zinc-700 bg-[var(--surface-elevated)] p-5 shadow-2xl flex flex-col gap-4"
          >
            <!-- Close Button -->
            <button
              :disabled="updating"
              @click="emit('close')"
              class="absolute right-4 top-4 rounded-full p-1.5 text-[var(--foreground-muted)] hover:bg-zinc-200 dark:hover:bg-zinc-700 hover:text-[var(--foreground)] transition-all cursor-pointer disabled:opacity-50 border border-zinc-300 dark:border-zinc-700"
            >
              <X class="h-4 w-4" />
            </button>

            <!-- Header -->
            <div class="flex items-center gap-3 pr-12">
              <div class="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-sm">
                <Folder class="h-[18px] w-[18px]" />
              </div>
              <div class="min-w-0">
                <h2 class="text-[15px] font-extrabold text-[var(--foreground)] select-all uppercase tracking-wide leading-tight truncate">
                  Documents: {{ student.full_name }}
                </h2>
                <p class="text-[11px] text-[var(--foreground-muted)] font-medium">Manage student documents</p>
              </div>
            </div>

            <!-- Student Info Strip -->
            <div class="px-3.5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-[var(--background)] flex items-center gap-x-5 gap-y-2 flex-wrap select-text">
              <div class="min-w-0">
                <span class="block text-[9px] uppercase font-bold text-[var(--foreground-muted)] tracking-wider leading-none mb-0.5">Student ID</span>
                <span class="text-[13px] font-extrabold text-[#007aff] font-mono leading-tight">{{ student.id }}</span>
              </div>
              <div class="w-px h-7 bg-zinc-200 dark:bg-zinc-700 shrink-0" />
              <div class="min-w-0">
                <span class="block text-[9px] uppercase font-bold text-[var(--foreground-muted)] tracking-wider leading-none mb-1">Status</span>
                <span v-if="student.is_deleted" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase bg-rose-500/10 text-rose-600 border border-rose-500/20 leading-none">
                  <span class="w-1.5 h-1.5 rounded-full bg-rose-500" /> Deleted
                </span>
                <span v-else class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 leading-none">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Active
                </span>
              </div>
              <div class="w-px h-7 bg-zinc-200 dark:bg-zinc-700 shrink-0" />
              <div class="min-w-0">
                <span class="block text-[9px] uppercase font-bold text-[var(--foreground-muted)] tracking-wider leading-none mb-0.5">Group</span>
                <span class="text-[13px] font-bold text-[var(--foreground)] uppercase leading-tight whitespace-nowrap">{{ student.student_group || 'No Group' }}</span>
              </div>
              <div class="w-px h-7 bg-zinc-200 dark:bg-zinc-700 shrink-0" />
              <div class="min-w-0 flex-1">
                <span class="block text-[9px] uppercase font-bold text-[var(--foreground-muted)] tracking-wider leading-none mb-0.5">Edu-Level</span>
                <span class="text-[13px] font-bold text-[var(--foreground)] uppercase leading-tight block truncate" :title="eduLevel">{{ eduLevel }}</span>
              </div>
              <div class="w-px h-7 bg-zinc-200 dark:bg-zinc-700 shrink-0" />
              <div class="min-w-0">
                <span class="block text-[9px] uppercase font-bold text-[var(--foreground-muted)] tracking-wider leading-none mb-0.5">Office</span>
                <span class="text-[13px] font-bold text-[var(--foreground)] uppercase leading-tight whitespace-nowrap">{{ (student as any).office || '—' }}</span>
              </div>
              <template v-if="authStore.canAccessPayments">
                <div class="w-px h-7 bg-zinc-200 dark:bg-zinc-700 shrink-0" />
                <div class="min-w-0">
                  <span class="block text-[9px] uppercase font-bold text-[var(--foreground-muted)] tracking-wider leading-none mb-0.5">Payments Done</span>
                  <span v-if="paymentsDoneLoading" class="inline-block h-3 w-20 rounded bg-zinc-200 dark:bg-zinc-700 animate-pulse" />
                  <span v-else class="text-[13px] font-extrabold text-emerald-600 dark:text-emerald-400 leading-tight whitespace-nowrap">
                    {{ formatCurrency(paymentsDone ?? 0) }}
                  </span>
                </div>
              </template>
            </div>

            <!-- Split cards grid for Missing & Pick needed -->
            <div class="grid grid-cols-1 md:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] gap-3.5">
              <!-- Missing Documents Column -->
              <div class="border border-zinc-300 dark:border-zinc-700 rounded-xl p-3.5 flex flex-col gap-2.5 bg-[var(--surface-elevated)]">
                <h3 class="text-[12px] font-bold text-[var(--foreground)] flex items-center gap-1.5 uppercase tracking-wide">
                  <FileText class="h-4 w-4 text-rose-500" />
                  Missing documents
                  <span v-if="missingDocs.length" class="ml-auto text-[10px] font-extrabold text-white bg-rose-500 rounded-full px-1.5 py-0.5 leading-none">
                    {{ missingDocs.length }}
                  </span>
                </h3>

                <div class="flex flex-col gap-1.5 overflow-y-auto max-h-[268px] pr-1">
                  <span v-if="missingDocs.length === 0" class="text-[11px] text-[var(--foreground-muted)] italic font-semibold py-2">
                    No missing documents specified.
                  </span>
                  <div
                    v-for="doc in missingDocs"
                    :key="doc"
                    class="flex items-center justify-between pl-2.5 pr-1.5 py-2 rounded-lg text-[11px] font-bold text-white shadow-sm w-full transition-all"
                    :style="{ backgroundColor: getMissingRowColor(doc) }"
                  >
                    <div class="flex items-center gap-1.5 min-w-0">
                      <FileText class="h-3.5 w-3.5 text-white shrink-0" />
                      <span class="truncate uppercase tracking-wide">{{ doc }}</span>
                    </div>
                    <button
                      v-if="authStore.canEdit"
                      type="button"
                      :disabled="updating"
                      @click="emit('toggle-pick', student.id, doc)"
                      class="p-1 hover:bg-white/20 rounded-md transition-all cursor-pointer disabled:opacity-50 text-white shrink-0"
                      title="Remove document"
                    >
                      <X class="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              <!-- Pick Needed Column -->
              <div class="border border-zinc-300 dark:border-zinc-700 rounded-xl p-3.5 flex flex-col gap-2.5 bg-[var(--surface-elevated)]">
                <h3 class="text-[12px] font-bold text-[var(--foreground)] flex items-center gap-1.5 uppercase tracking-wide">
                  <CheckSquare class="h-4 w-4 text-emerald-500" />
                  Pick needed
                </h3>

                <div class="flex flex-wrap gap-1.5 overflow-y-auto max-h-[268px] pr-1 content-start">
                  <button
                    v-for="pill in PICK_NEEDED_LIST"
                    :key="pill"
                    type="button"
                    :disabled="updating || !authStore.canEdit"
                    @click="emit('toggle-pick', student.id, pill)"
                    class="px-2.5 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wide border transition-all hover:scale-[1.03] active:scale-95 disabled:opacity-50 whitespace-nowrap h-[26px] inline-flex items-center"
                    :class="[
                      authStore.canEdit ? 'cursor-pointer' : 'cursor-default',
                      isPillActive(pill)
                        ? 'text-white shadow-sm border-transparent'
                        : (pill === 'FULL OK'
                            ? 'border-emerald-500/40 text-emerald-600 bg-emerald-500/5 hover:bg-emerald-500/10'
                            : 'border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 hover:border-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800')
                    ]"
                    :style="isPillActive(pill)
                      ? { backgroundColor: getPillActiveColor(pill), borderColor: getPillActiveColor(pill) }
                      : {}"
                  >
                    {{ pill }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Physical Copies In Hand -->
            <div class="border border-[var(--border)] rounded-2xl p-5 flex flex-col gap-4 bg-[var(--surface-elevated)]">
              <h3 class="text-sm font-bold text-[var(--foreground)] flex items-center gap-2">
                <Folder class="h-[18px] w-[18px] text-blue-500" />
                Physical Copies In Hand (Override)
              </h3>

              <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                <div
                  v-for="item in counters"
                  :key="item.key"
                  class="relative rounded-2xl border border-[var(--border)] bg-gray-50 dark:bg-zinc-950 p-4 flex flex-col items-center justify-between min-h-[100px] select-none shadow-sm"
                >
                  <!-- MC enable/disable toggle -->
                  <div v-if="item.label === 'MC'" class="absolute top-3 right-3 z-10 flex items-center">
                    <label class="relative inline-flex items-center" :class="authStore.canEdit ? 'cursor-pointer' : 'cursor-default'">
                      <input
                        type="checkbox"
                        :checked="student.has_mc !== false"
                        :disabled="updating || !authStore.canEdit"
                        @change="emit('toggle-mc', student.id)"
                        class="sr-only peer"
                      />
                      <div class="w-8 h-[18px] bg-gray-200 peer-focus:outline-none rounded-full dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3.5 after:w-3.5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600" />
                    </label>
                  </div>

                  <span class="text-[10px] uppercase font-bold text-[var(--foreground-muted)] tracking-wider mb-2">{{ item.label }}</span>

                  <div class="flex items-center justify-between w-full mt-2 px-1">
                    <button
                      type="button"
                      :disabled="item.isDisabled || item.remaining <= 0"
                      @click="emit('update-count', student.id, item.key, item.remaining - 1)"
                      class="h-8 w-8 rounded-full border border-gray-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 flex items-center justify-center hover:bg-gray-100 dark:hover:bg-zinc-700 active:scale-95 disabled:opacity-40 disabled:pointer-events-none cursor-pointer transition-all text-sm font-bold shadow-sm"
                    >
                      -
                    </button>

                    <span
                      class="font-extrabold text-base w-12 text-center"
                      :class="item.isMcDisabled
                        ? 'text-gray-400 dark:text-gray-600'
                        : (item.remaining > 0 ? 'text-[#007aff]' : 'text-gray-700 dark:text-gray-300')"
                    >
                      {{ item.isMcDisabled ? 'N/A' : item.remaining }}
                    </span>

                    <button
                      type="button"
                      :disabled="item.isDisabled"
                      @click="emit('update-count', student.id, item.key, item.remaining + 1)"
                      class="h-8 w-8 rounded-full border border-gray-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 flex items-center justify-center hover:bg-gray-100 dark:hover:bg-zinc-700 active:scale-95 disabled:opacity-40 disabled:pointer-events-none cursor-pointer transition-all text-sm font-bold shadow-sm"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="flex justify-end mt-2">
              <button
                type="button"
                @click="emit('close')"
                class="bg-[#007aff] hover:bg-blue-600 text-white rounded-full px-6 py-2.5 flex items-center gap-2 font-bold text-sm shadow-md active:scale-[0.96] transition-all cursor-pointer"
              >
                <CheckCircle2 class="h-[18px] w-[18px]" />
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
