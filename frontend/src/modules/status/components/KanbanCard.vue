<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { Student } from '@/types'
import type { WorkflowStage } from '../utils/statusWorkflow'
import { useAuthStore } from '@/stores/auth'
import { useUniversityStatuses } from '@/composables/useUniversityStatuses'
import { CheckCircle2, ArrowLeft, Eye, ChevronDown, GraduationCap } from 'lucide-vue-next'

const props = defineProps<{
  student: Student
  stageKey: WorkflowStage
  universityOptions: string[]
  universityStatusOptions: string[]
  // Bumped whenever ChooseUniversityModal closes without a selection, to
  // force the Invoice <select> to remount - a native <select> keeps
  // whatever option the user clicked in the DOM even if the bound :value
  // never actually changed (e.g. picking "Paid" opens the modal, Cancel is
  // pressed, student.invoice stays at its old value), so Vue's patch never
  // reconciles it back without a key change.
  invoiceSelectResetKey?: number
}>()

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
  (e: 'open-actions', event: MouseEvent): void
  (e: 'open-embassy'): void
  (e: 'open-detail'): void
  (e: 'update-university', slot: number, name: string): void
  (e: 'update-university-status', slot: number, status: string): void
  (e: 'update-invoice-status', currentStatus: string | null, newStatus: string): void
  (e: 'update-coa-status', status: string | null): void
  (e: 'update-visa-status', status: string | null): void
  (e: 'revert-to-coa'): void
}>()

const authStore = useAuthStore()
const { getStatusBadgeClass } = useUniversityStatuses()
const cardRoot = ref<HTMLElement | null>(null)
const universitiesExpanded = ref(false)

const getLevelBadgeClass = (level?: string | null) => {
  switch (level?.toUpperCase()) {
    case 'COLLEGE': return 'bg-[#6554c0] text-white'
    case 'LANGUAGE COURSE': return 'bg-[#ffab00] text-zinc-900'
    case 'MASTERS': return 'bg-[#00875a] text-white'
    case 'MASTER NO CERTIFICATE': return 'bg-[#00875a] text-white'
    case 'BACHELOR': return 'bg-[#0052cc] text-white'
    default: return 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300'
  }
}

// All configured certificates (not just the first), same pattern as
// StudentRow.vue's `certs` - a student can hold up to 3.
const certs = computed(() => {
  const list = [
    { type: props.student.language_certificate, score: props.student.certificate_score },
    { type: props.student.language_certificate_2, score: props.student.certificate_score_2 },
    { type: props.student.language_certificate_3, score: props.student.certificate_score_3 },
  ]
  return list.filter(c => c.type && c.type !== 'NO CERTIFICATE')
})

const handleCardClick = (e: MouseEvent) => {
  if (e.metaKey || e.ctrlKey) {
    window.open(`/students/${props.student.id}/extract`, '_blank')
  } else {
    emit('click', e)
  }
}

const handleContextMenu = (e: MouseEvent) => {
  e.preventDefault()
  emit('open-actions', e)
}

// University status options come from Settings (UniversityStatusOption),
// so the Kanban dropdowns always match whatever a manager configured there
// instead of a hardcoded list. Falls back to the original defaults only if
// Settings has no options configured yet.
const FALLBACK_STATUS_OPTIONS = ['Chosen', 'Applying', 'Applied', 'Accepted', 'Failed']
const statusOptions = computed(() =>
  props.universityStatusOptions.length > 0 ? props.universityStatusOptions : FALLBACK_STATUS_OPTIONS
)

const uniName = (slot: number) => (props.student as any)[`university_${slot}`] || ''
const uniStatus = (slot: number) => {
  const val = (props.student as any)[`university_${slot}_status`]
  return val && val.trim() ? val : 'Not Applied'
}

const chosenUniversitySlots = computed(() =>
  Array.from({ length: 5 }, (_, index) => index + 1)
    .filter(slot => {
      const name = (props.student as any)[`university_${slot}`]
      return typeof name === 'string' && name.trim()
    })
)

const visibleUniversitySlots = computed(() =>
  universitiesExpanded.value
    ? chosenUniversitySlots.value
    : (chosenUniversitySlots.value.length > 0 ? [chosenUniversitySlots.value[0]] : [1])
)

// The card height follows the university rows' own enter/leave transition
// (max-height), so the body keeps `height: auto` and the arrow is never clipped.
const toggleUniversities = () => {
  if (chosenUniversitySlots.value.length > 1) {
    universitiesExpanded.value = !universitiesExpanded.value
  }
}

const closeUniversitiesOnOutsideClick = (event: MouseEvent) => {
  if (cardRoot.value && !cardRoot.value.contains(event.target as Node)) {
    universitiesExpanded.value = false
  }
}

onMounted(() => document.addEventListener('click', closeUniversitiesOnOutsideClick))
onUnmounted(() => document.removeEventListener('click', closeUniversitiesOnOutsideClick))

// ── Invoice column: accepted university + invoice/coa selects ───────────
const acceptedUniversities = computed(() => {
  const list: { slot: number; name: string }[] = []
  for (let i = 1; i <= 5; i++) {
    const status = (props.student as any)[`university_${i}_status`]
    if (typeof status === 'string' && status.trim().toUpperCase() === 'ACCEPTED') {
      const name = (props.student as any)[`university_${i}`]
      list.push({ slot: i, name: name && name.trim() ? name.trim() : `University ${i}` })
    }
  }
  return list
})

const getCoaBadgeClass = (status: string | null | undefined) => {
  const val = status || 'NOT TAKEN'
  if (val === 'TAKEN') return 'bg-emerald-600 dark:bg-emerald-500 text-white font-bold border-transparent'
  if (val === 'MISTAKE') return 'bg-amber-500 text-white font-bold border-transparent'
  if (val === 'CANCELLED') return 'bg-rose-600 dark:bg-rose-500 text-white font-bold border-transparent'
  return 'bg-zinc-400 dark:bg-zinc-500 text-white font-semibold border-transparent'
}

const getInvoiceBadgeClass = (status: string | null | undefined) => {
  const val = status || 'NOT TAKEN'
  if (val === 'PAID') return 'bg-emerald-600 dark:bg-emerald-500 text-white font-bold border-transparent'
  if (val === 'TAKEN') return 'bg-violet-600 dark:bg-violet-500 text-white font-bold border-transparent'
  if (val === 'CANCELLED') return 'bg-rose-600 dark:bg-rose-500 text-white font-bold border-transparent'
  return 'bg-zinc-400 dark:bg-zinc-500 text-white font-semibold border-transparent'
}

// Full-text equivalents of the badge classes above, used as `title` so the
// truncated <select> still exposes its full selected value on hover - the
// invoice/COA/visa selects don't have this already, unlike the university
// name/status selects elsewhere in this file which all do.
const COA_LABELS: Record<string, string> = {
  'NOT TAKEN': 'Not Taken', TAKEN: 'Taken', MISTAKE: 'Mistake', CANCELLED: 'Cancelled',
}
const getCoaTitle = (status: string | null | undefined) => COA_LABELS[status || 'NOT TAKEN'] || 'Not Taken'

const invoiceTitle = computed(() => {
  const val = props.student.invoice || 'NOT TAKEN'
  if (val === 'PAID') return props.student.invoice_university ? `Paid: ${props.student.invoice_university}` : 'Paid'
  const labels: Record<string, string> = { 'NOT TAKEN': 'Not Taken', TAKEN: 'Taken', CANCELLED: 'Cancelled' }
  return labels[val] || 'Not Taken'
})

// ── VISA column: 3-state outcome selector, legacy CANCELLED = Rejected ──
const isVisaActive = (status: 'APPLIED' | 'APPROVED' | 'REJECTED') => {
  const current = props.student.embassy
  if (status === 'REJECTED') return current === 'REJECTED' || current === 'CANCELLED'
  return current === status
}

// Title for the COA-column "Visa" <select> (Applied / Not Yet toggle) - a
// full-text fallback for its truncated badge styling, same reasoning as
// invoiceTitle/getCoaTitle above.
const visaCoaSelectTitle = computed(() => isVisaActive('APPLIED') ? 'Applied' : 'Not Yet')

const visaCardClass = computed(() => {
  if (isVisaActive('APPROVED')) {
    return 'border-emerald-500 dark:border-emerald-400 bg-emerald-50/60 dark:bg-emerald-950/30'
  }
  if (isVisaActive('REJECTED')) {
    return 'border-rose-500 dark:border-rose-400 bg-rose-50/60 dark:bg-rose-950/30'
  }
  if (isVisaActive('APPLIED')) {
    return 'border-sky-500 dark:border-sky-400 bg-sky-50/60 dark:bg-sky-950/30'
  }
  return 'border-teal-500 dark:border-teal-400 bg-white dark:bg-zinc-900'
})

const handleSetVisaStatus = (status: 'APPLIED' | 'APPROVED' | 'REJECTED') => {
  emit('update-visa-status', isVisaActive(status) ? null : status)
}

const stageCardClass = computed(() => {
  if (props.stageKey === 'visa') return visaCardClass.value
  
  const baseBg = 'bg-white dark:bg-zinc-900'
  switch (props.stageKey) {
    case 'student': return `border-zinc-400 dark:border-zinc-500 ${baseBg}`
    case 'apply': return `border-blue-500 dark:border-blue-400 ${baseBg}`
    case 'invoice': return `border-violet-500 dark:border-violet-400 ${baseBg}`
    case 'coa': return `border-amber-500 dark:border-amber-400 ${baseBg}`
    default: return `border-zinc-400 dark:border-zinc-500 ${baseBg}`
  }
})

// "Back to COA" asks for inline confirmation first - the button splits into
// Yes/No instead of acting immediately, since reverting from VISA loses the
// visa outcome.
const isConfirmingRevertToCoa = ref(false)
const confirmRevertToCoa = () => {
  isConfirmingRevertToCoa.value = false
  emit('revert-to-coa')
}
</script>

<template>
  <div
    ref="cardRoot"
    class="kanban-card group rounded-md border border-dashed p-2.5 shadow-md hover:shadow-lg transition-[box-shadow,transform] duration-200 cursor-pointer"
    :class="stageCardClass"
    @click="handleCardClick"
    @contextmenu="handleContextMenu"
  >
    <!-- Header: ID + name, details button -->
    <div class="flex items-center gap-1.5 mb-1.5 min-w-0">
      <span class="text-[9px] font-bold tabular-nums text-[#087cff] bg-[#087cff]/10 px-1.5 py-0.5 rounded-md shrink-0">
        {{ student.id }}
      </span>
      <span class="flex-1 min-w-0 text-[10.5px] font-semibold uppercase tracking-tight text-zinc-900 dark:text-zinc-100 truncate leading-tight">
        {{ student.full_name }}
      </span>
      <button
        type="button"
        title="View student details"
        @click.stop="emit('open-detail')"
        class="flex items-center justify-center w-5 h-5 -mr-0.5 rounded-full text-zinc-400 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer shrink-0"
      >
        <Eye class="w-3.5 h-3.5" />
      </button>
    </div>

    <!-- Meta: level/cert badges + universities toggle (replaces the old bottom arrow) -->
    <div class="flex items-center justify-between gap-1 mb-2">
      <div class="flex flex-wrap items-center gap-1 min-w-0">
        <span
          v-if="student.level"
          class="inline-flex items-center px-1.5 py-px rounded-full text-[8px] font-bold uppercase tracking-wide"
          :class="getLevelBadgeClass(student.level)"
        >
          {{ student.level }}
        </span>
        <span
          v-for="(cert, idx) in certs"
          :key="`${cert.type}-${idx}`"
          class="inline-flex items-center gap-0.5 px-1.5 py-px rounded-full text-[8px] font-bold"
          :class="cert.type === 'TOPIK'
            ? 'bg-rose-500/10 text-rose-600 dark:bg-rose-400/15 dark:text-rose-300'
            : 'bg-blue-500/10 text-blue-600 dark:bg-blue-400/15 dark:text-blue-300'"
        >
          <span>{{ cert.type }}</span>
          <span v-if="cert.score" class="opacity-80 tabular-nums">{{ cert.score }}</span>
        </span>
        <span v-if="!student.level && certs.length === 0" class="text-[9px] text-zinc-400 dark:text-zinc-500">—</span>
      </div>
      <button
        v-if="chosenUniversitySlots.length > 1"
        type="button"
        :title="universitiesExpanded ? 'Hide universities' : 'Show all universities'"
        @click.stop="toggleUniversities"
        class="flex items-center gap-0.5 h-4 pl-1.5 pr-1 rounded-full text-[8.5px] font-semibold tabular-nums transition-colors cursor-pointer shrink-0"
        :class="universitiesExpanded
          ? 'bg-[#087cff]/10 text-[#087cff]'
          : 'bg-zinc-100 text-zinc-500 hover:text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200'"
      >
        <GraduationCap class="w-3 h-3" />
        {{ chosenUniversitySlots.length }}
        <ChevronDown
          class="w-3 h-3 transition-transform duration-300 ease-out"
          :class="universitiesExpanded ? 'rotate-180' : 'rotate-0'"
        />
      </button>
    </div>

    <!-- Stage-specific body -->
    <div class="overflow-hidden -mx-0.5">
    <div class="flex flex-col gap-1.5" @click.stop>
      <!-- STUDENT: university selector + Not Applied/Applied -->
      <template v-if="stageKey === 'student'">
        <TransitionGroup name="university-row" tag="div" class="flex flex-col gap-1.5">
        <div v-for="slot in visibleUniversitySlots" :key="slot" class="university-card-row flex items-center gap-1.5">
          <select
            :value="uniName(slot)"
            :disabled="!authStore.canEdit"
            :title="uniName(slot)"
            @change="emit('update-university', slot, ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-1.5 py-0.5 text-[9px] font-semibold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 focus:outline-none truncate"
            :class="authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90'"
          >
            <option value="" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">University {{ slot }}</option>
            <option v-for="uni in universityOptions" :key="uni" :value="uni" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ uni }}</option>
          </select>
          <select
            :value="uniStatus(slot)"
            :disabled="!authStore.canEdit || !uniName(slot)"
            @change="emit('update-university-status', slot, ($event.target as HTMLSelectElement).value)"
            class="kanban-status-select py-0.5 text-[8.5px] font-bold uppercase rounded-full border focus:outline-none shrink-0 min-w-[62px] w-fit max-w-[88px] truncate"
            :class="[getStatusBadgeClass(uniStatus(slot)), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option v-for="opt in statusOptions" :key="opt" :value="opt" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ opt }}</option>
          </select>
        </div>
        </TransitionGroup>
      </template>

      <!-- APPLY: both slots, full status range. Empty slot gets a university
           name picker (same as Student column) instead of just a label,
           so a second university can still be added from here. -->
      <template v-else-if="stageKey === 'apply'">
        <TransitionGroup name="university-row" tag="div" class="flex flex-col gap-1.5">
        <div v-for="slot in visibleUniversitySlots" :key="slot" class="university-card-row flex items-center gap-1.5">
          <select
            v-if="!uniName(slot)"
            :value="uniName(slot)"
            :disabled="!authStore.canEdit"
            @change="emit('update-university', slot, ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-1.5 py-0.5 text-[9px] font-semibold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 focus:outline-none truncate"
            :class="authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90'"
          >
            <option value="" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">University {{ slot }}</option>
            <option v-for="uni in universityOptions" :key="uni" :value="uni" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ uni }}</option>
          </select>
          <span v-else class="flex-1 min-w-0 text-[9px] font-semibold text-zinc-700 dark:text-zinc-300 truncate" :title="uniName(slot)">
            {{ uniName(slot) }}
          </span>
          <select
            :value="uniStatus(slot)"
            :disabled="!authStore.canEdit || !uniName(slot)"
            @change="emit('update-university-status', slot, ($event.target as HTMLSelectElement).value)"
            class="kanban-status-select py-0.5 text-[8.5px] font-bold uppercase rounded-full border focus:outline-none shrink-0 min-w-[62px] w-fit max-w-[88px] truncate"
            :class="[getStatusBadgeClass(uniStatus(slot)), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option v-for="opt in statusOptions" :key="opt" :value="opt" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ opt }}</option>
          </select>
        </div>
        </TransitionGroup>
      </template>

      <!-- INVOICE: both slots shown, status editable. Empty slot gets a
           university name picker (same as Apply/Student columns) instead
           of being hidden, so a second university can be added here too. -->
      <template v-else-if="stageKey === 'invoice'">
        <TransitionGroup name="university-row" tag="div" class="flex flex-col gap-1.5">
        <div v-for="slot in visibleUniversitySlots" :key="slot" class="university-card-row flex items-center gap-1.5">
          <CheckCircle2
            v-if="uniStatus(slot).trim().toUpperCase() === 'ACCEPTED'"
            class="w-3 h-3 text-emerald-600 dark:text-emerald-400 shrink-0"
          />
          <select
            v-if="!uniName(slot)"
            :value="uniName(slot)"
            :disabled="!authStore.canEdit"
            @change="emit('update-university', slot, ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-1.5 py-0.5 text-[9px] font-semibold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 focus:outline-none truncate"
            :class="authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90'"
          >
            <option value="" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">University {{ slot }}</option>
            <option v-for="uni in universityOptions" :key="uni" :value="uni" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ uni }}</option>
          </select>
          <span v-else class="flex-1 min-w-0 text-[9px] font-semibold text-zinc-700 dark:text-zinc-300 truncate" :title="uniName(slot)">
            {{ uniName(slot) }}
          </span>
          <select
            :value="uniStatus(slot)"
            :disabled="!authStore.canEdit || !uniName(slot)"
            @change="emit('update-university-status', slot, ($event.target as HTMLSelectElement).value)"
            class="kanban-status-select py-0.5 text-[8.5px] font-bold uppercase rounded-full border focus:outline-none shrink-0 min-w-[62px] w-fit max-w-[88px] truncate"
            :class="[getStatusBadgeClass(uniStatus(slot)), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option v-for="opt in statusOptions" :key="opt" :value="opt" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ opt }}</option>
          </select>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-[8.5px] font-bold uppercase text-zinc-400 dark:text-zinc-500 shrink-0 w-10">Invoice</span>
          <select
            :key="`invoice-select-${student.id}-${student.invoice}-${invoiceSelectResetKey}`"
            :value="student.invoice || 'NOT TAKEN'"
            :disabled="!authStore.canEdit"
            :title="invoiceTitle"
            @change="emit('update-invoice-status', student.invoice || 'NOT TAKEN', ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-2 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wider border focus:outline-none shadow-2xs truncate"
            :class="[getInvoiceBadgeClass(student.invoice), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option value="NOT TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Taken</option>
            <option value="TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Taken</option>
            <option value="PAID" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ student.invoice === 'PAID' && student.invoice_university ? `Paid: ${student.invoice_university}` : 'Paid' }}</option>
            <option value="CANCELLED" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Cancelled</option>
          </select>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-[8.5px] font-bold uppercase text-zinc-400 dark:text-zinc-500 shrink-0 w-10">COA</span>
          <select
            :value="student.coa || 'NOT TAKEN'"
            :disabled="!authStore.canEdit"
            :title="getCoaTitle(student.coa)"
            @change="emit('update-coa-status', ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-2 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wider border focus:outline-none shadow-2xs truncate"
            :class="[getCoaBadgeClass(student.coa), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option value="NOT TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Taken</option>
            <option value="TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Taken</option>
            <option value="MISTAKE" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Mistake</option>
            <option value="CANCELLED" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Cancelled</option>
          </select>
        </div>
        </TransitionGroup>
      </template>

      <!-- COA: accepted-uni label (read-only - edit from Invoice) + editable COA + visa selects -->
      <template v-else-if="stageKey === 'coa'">
        <div v-if="acceptedUniversities.length > 0" class="flex items-center gap-1.5">
          <CheckCircle2 class="w-3 h-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span class="text-[9px] font-bold text-zinc-700 dark:text-zinc-300 truncate">
            {{ student.invoice_university || acceptedUniversities[0].name }}
          </span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-[8.5px] font-bold uppercase text-zinc-400 dark:text-zinc-500 shrink-0 w-10">COA</span>
          <select
            :value="student.coa || 'NOT TAKEN'"
            :disabled="!authStore.canEdit"
            :title="getCoaTitle(student.coa)"
            @change="emit('update-coa-status', ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-2 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wider border focus:outline-none shadow-2xs truncate"
            :class="[getCoaBadgeClass(student.coa), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option value="NOT TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Taken</option>
            <option value="TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Taken</option>
            <option value="MISTAKE" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Mistake</option>
            <option value="CANCELLED" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Cancelled</option>
          </select>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-[8.5px] font-bold uppercase text-zinc-400 dark:text-zinc-500 shrink-0 w-10">Visa</span>
          <select
            :value="isVisaActive('APPLIED') ? 'APPLIED' : 'NOT_YET'"
            :disabled="!authStore.canEdit"
            :title="visaCoaSelectTitle"
            @change="emit('update-visa-status', ($event.target as HTMLSelectElement).value === 'APPLIED' ? 'APPLIED' : null)"
            class="flex-1 min-w-0 px-2 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wider border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-300 focus:outline-none shadow-2xs truncate"
            :class="authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90'"
          >
            <option value="NOT_YET" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Yet</option>
            <option value="APPLIED" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Applied</option>
          </select>
        </div>
      </template>

      <!-- VISA: Applied / Approved / Rejected outcome buttons -->
      <template v-else-if="stageKey === 'visa'">
        <div class="grid grid-cols-3 gap-1">
          <button
            type="button"
            :disabled="!authStore.canEdit"
            @click="handleSetVisaStatus('APPLIED')"
            class="py-1 rounded-lg text-[8.5px] font-bold uppercase transition-all border"
            :class="[
              isVisaActive('APPLIED')
                ? 'bg-blue-600 border-transparent text-white shadow-xs'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300',
              authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-80'
            ]"
          >
            Applied
          </button>
          <button
            type="button"
            :disabled="!authStore.canEdit"
            @click="handleSetVisaStatus('APPROVED')"
            class="py-1 rounded-lg text-[8.5px] font-bold uppercase transition-all border"
            :class="[
              isVisaActive('APPROVED')
                ? 'bg-emerald-600 border-transparent text-white shadow-xs'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300',
              authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-80'
            ]"
          >
            Approved
          </button>
          <button
            type="button"
            :disabled="!authStore.canEdit"
            @click="handleSetVisaStatus('REJECTED')"
            class="py-1 rounded-lg text-[8.5px] font-bold uppercase transition-all border"
            :class="[
              isVisaActive('REJECTED')
                ? 'bg-rose-600 border-transparent text-white shadow-xs'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300',
              authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-80'
            ]"
          >
            Rejected
          </button>
        </div>
        <button
          v-if="authStore.canEdit && !isConfirmingRevertToCoa"
          type="button"
          class="flex items-center justify-center gap-1 mt-0.5 px-2 py-0.5 rounded-lg text-[8.5px] font-bold uppercase text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 transition-colors cursor-pointer"
          @click="isConfirmingRevertToCoa = true"
        >
          <ArrowLeft class="w-3 h-3" /> Back to COA
        </button>
        <div v-else-if="authStore.canEdit" class="grid grid-cols-2 gap-1 mt-0.5 animate-confirm-in">
          <button
            type="button"
            class="px-2 py-0.5 rounded-lg text-[8.5px] font-bold uppercase bg-rose-600 hover:bg-rose-700 text-white transition-colors cursor-pointer"
            @click="confirmRevertToCoa"
          >
            Yes, revert
          </button>
          <button
            type="button"
            class="px-2 py-0.5 rounded-lg text-[8.5px] font-bold uppercase text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 transition-colors cursor-pointer"
            @click="isConfirmingRevertToCoa = false"
          >
            No
          </button>
        </div>
      </template>
    </div>
    </div>
  </div>
</template>

<style scoped>
/* Doubled class so this wins over .university-card-row's own `transition` below. */
.university-card-row.university-row-enter-active,
.university-card-row.university-row-leave-active {
  transition:
    opacity 450ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 500ms cubic-bezier(0.22, 1, 0.36, 1),
    max-height 500ms cubic-bezier(0.22, 1, 0.36, 1),
    min-height 500ms cubic-bezier(0.22, 1, 0.36, 1),
    margin-top 500ms cubic-bezier(0.22, 1, 0.36, 1),
    padding 500ms cubic-bezier(0.22, 1, 0.36, 1);
  overflow: hidden;
}

.university-row-enter-from,
.university-row-leave-to {
  opacity: 0;
  transform: translateY(-12px) scaleY(0.86);
  max-height: 0;
  min-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.university-row-enter-to,
.university-row-leave-from {
  opacity: 1;
  transform: translateY(0) scaleY(1);
  max-height: 40px;
}

/* Cancel the flex gap above a row while it is collapsed, so the card
   doesn't jump by the gap size when the row is added/removed. */
.university-row-enter-from:not(:first-child),
.university-row-leave-to:not(:first-child) {
  margin-top: -0.375rem;
}

.university-row-move {
  transition: transform 500ms cubic-bezier(0.22, 1, 0.36, 1);
}

/* Dashed outline sits between Tailwind's 1px and 2px steps - matches the
   Payments module's Kanban card, which uses the same 1.5px rule. */
.kanban-card {
  border-width: 1.5px;
}

.university-card-row {
  min-height: 24px;
  padding: 2px 4px;
  border-radius: 7px;
  background: rgb(255 255 255 / 0.45);
  transition: background-color 180ms ease, transform 180ms ease;
}

.dark .university-card-row {
  background: rgb(255 255 255 / 0.045);
}

.university-card-row:hover {
  background: rgb(255 255 255 / 0.72);
}

.dark .university-card-row:hover {
  background: rgb(255 255 255 / 0.085);
}
</style>
