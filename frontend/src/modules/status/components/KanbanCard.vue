<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Student } from '@/types'
import type { WorkflowStage } from '../utils/statusWorkflow'
import { useAuthStore } from '@/stores/auth'
import { useUniversityStatuses } from '@/composables/useUniversityStatuses'
import { CheckCircle2, ArrowLeft } from 'lucide-vue-next'

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
  (e: 'update-university', slot: 1 | 2, name: string): void
  (e: 'update-university-status', slot: 1 | 2, status: string): void
  (e: 'update-invoice-status', currentStatus: string | null, newStatus: string): void
  (e: 'update-coa-status', status: string | null): void
  (e: 'update-visa-status', status: string | null): void
  (e: 'revert-to-coa'): void
}>()

const authStore = useAuthStore()
const { getStatusBadgeClass } = useUniversityStatuses()

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

const primaryCert = computed(() => {
  const type = props.student.language_certificate
  if (!type || type === 'NO CERTIFICATE') return null
  return { type, score: props.student.certificate_score }
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

const uniName = (slot: 1 | 2) => (slot === 1 ? props.student.university_1 : props.student.university_2) || ''
const uniStatus = (slot: 1 | 2) => {
  const val = slot === 1 ? props.student.university_1_status : props.student.university_2_status
  return val && val.trim() ? val : 'Not Applied'
}

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

// ── VISA column: 3-state outcome selector, legacy CANCELLED = Rejected ──
const isVisaActive = (status: 'APPLIED' | 'APPROVED' | 'REJECTED') => {
  const current = props.student.embassy
  if (status === 'REJECTED') return current === 'REJECTED' || current === 'CANCELLED'
  return current === status
}

const visaCardClass = computed(() => {
  if (isVisaActive('APPROVED')) {
    return 'border-emerald-300 dark:border-emerald-800 bg-emerald-50/60 dark:bg-emerald-950/30'
  }
  if (isVisaActive('REJECTED')) {
    return 'border-rose-300 dark:border-rose-800 bg-rose-50/60 dark:bg-rose-950/30'
  }
  if (isVisaActive('APPLIED')) {
    return 'border-blue-300 dark:border-blue-800 bg-blue-50/60 dark:bg-blue-950/30'
  }
  return 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900'
})

const handleSetVisaStatus = (status: 'APPLIED' | 'APPROVED' | 'REJECTED') => {
  emit('update-visa-status', isVisaActive(status) ? null : status)
}

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
    class="group rounded-xl border p-2.5 shadow-md hover:shadow-lg transition-all cursor-pointer"
    :class="stageKey === 'visa' ? visaCardClass : 'border-zinc-200/80 dark:border-zinc-700/80 bg-white dark:bg-zinc-900'"
    @click="handleCardClick"
    @contextmenu="handleContextMenu"
  >
    <!-- Shared header: ID, name, level, cert -->
    <div class="flex items-center gap-1.5 mb-1.5 min-w-0">
      <span class="text-[9px] font-bold bg-[#007aff] text-white px-1.5 py-0.5 rounded-[4px] shrink-0 shadow-xs">
        {{ student.id }}
      </span>
      <span class="text-[11px] font-bold uppercase tracking-wide text-zinc-900 dark:text-zinc-100 truncate">
        {{ student.full_name }}
      </span>
    </div>

    <div class="flex flex-wrap gap-1 mb-2">
      <span
        v-if="student.level"
        class="inline-flex items-center px-1.5 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wide shadow-2xs"
        :class="getLevelBadgeClass(student.level)"
      >
        {{ student.level }}
      </span>
      <span
        v-if="primaryCert"
        class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[8.5px] font-bold shadow-2xs"
        :class="primaryCert.type === 'TOPIK' ? 'bg-rose-500 text-white' : 'bg-blue-600 text-white'"
      >
        <span>{{ primaryCert.type }}</span>
        <span v-if="primaryCert.score" class="opacity-90 font-mono">({{ primaryCert.score }})</span>
      </span>
      <span v-if="!student.level && !primaryCert" class="text-[9px] text-zinc-400 dark:text-zinc-500">—</span>
    </div>

    <!-- Stage-specific body -->
    <div class="flex flex-col gap-1.5" @click.stop>
      <!-- STUDENT: university selector + Not Applied/Applied -->
      <template v-if="stageKey === 'student'">
        <div v-for="slot in [1, 2] as const" :key="slot" class="flex items-center gap-1.5">
          <select
            :value="uniName(slot)"
            :disabled="!authStore.canEdit"
            :title="uniName(slot)"
            @change="emit('update-university', slot, ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-1.5 py-0.5 text-[9px] font-semibold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 focus:outline-none truncate"
            :class="authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90'"
          >
            <option value="" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">University {{ slot }}...</option>
            <option v-for="uni in universityOptions" :key="uni" :value="uni" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ uni }}</option>
          </select>
          <select
            :value="uniStatus(slot)"
            :disabled="!authStore.canEdit || !uniName(slot)"
            @change="emit('update-university-status', slot, ($event.target as HTMLSelectElement).value)"
            class="px-1.5 py-0.5 text-[8.5px] font-bold uppercase rounded-full border focus:outline-none shrink-0 w-[88px] truncate"
            :class="[getStatusBadgeClass(uniStatus(slot)), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option v-for="opt in statusOptions" :key="opt" :value="opt" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ opt }}</option>
          </select>
        </div>
      </template>

      <!-- APPLY: both slots, full status range. Empty slot gets a university
           name picker (same as Student column) instead of just a label,
           so a second university can still be added from here. -->
      <template v-else-if="stageKey === 'apply'">
        <div v-for="slot in [1, 2] as const" :key="slot" class="flex items-center gap-1.5">
          <select
            v-if="!uniName(slot)"
            :value="uniName(slot)"
            :disabled="!authStore.canEdit"
            @change="emit('update-university', slot, ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-1.5 py-0.5 text-[9px] font-semibold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 focus:outline-none truncate"
            :class="authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90'"
          >
            <option value="" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">University {{ slot }}...</option>
            <option v-for="uni in universityOptions" :key="uni" :value="uni" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ uni }}</option>
          </select>
          <span v-else class="flex-1 min-w-0 text-[9px] font-semibold text-zinc-700 dark:text-zinc-300 truncate" :title="uniName(slot)">
            {{ uniName(slot) }}
          </span>
          <select
            :value="uniStatus(slot)"
            :disabled="!authStore.canEdit || !uniName(slot)"
            @change="emit('update-university-status', slot, ($event.target as HTMLSelectElement).value)"
            class="px-1.5 py-0.5 text-[8.5px] font-bold uppercase rounded-full border focus:outline-none shrink-0 w-[88px] truncate"
            :class="[getStatusBadgeClass(uniStatus(slot)), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option v-for="opt in statusOptions" :key="opt" :value="opt" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ opt }}</option>
          </select>
        </div>
      </template>

      <!-- INVOICE: both slots shown, status editable. Empty slot gets a
           university name picker (same as Apply/Student columns) instead
           of being hidden, so a second university can be added here too. -->
      <template v-else-if="stageKey === 'invoice'">
        <div v-for="slot in [1, 2] as const" :key="slot" class="flex items-center gap-1.5">
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
            <option value="" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">University {{ slot }}...</option>
            <option v-for="uni in universityOptions" :key="uni" :value="uni" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">{{ uni }}</option>
          </select>
          <span v-else class="flex-1 min-w-0 text-[9px] font-semibold text-zinc-700 dark:text-zinc-300 truncate" :title="uniName(slot)">
            {{ uniName(slot) }}
          </span>
          <select
            :value="uniStatus(slot)"
            :disabled="!authStore.canEdit || !uniName(slot)"
            @change="emit('update-university-status', slot, ($event.target as HTMLSelectElement).value)"
            class="px-1.5 py-0.5 text-[8.5px] font-bold uppercase rounded-full border focus:outline-none shrink-0 w-[88px] truncate"
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
            @change="emit('update-invoice-status', student.invoice || 'NOT TAKEN', ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-2 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wider border focus:outline-none shadow-2xs"
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
            @change="emit('update-coa-status', ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-2 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wider border focus:outline-none shadow-2xs"
            :class="[getCoaBadgeClass(student.coa), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option value="NOT TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Taken</option>
            <option value="TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Taken</option>
            <option value="MISTAKE" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Mistake</option>
            <option value="CANCELLED" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Cancelled</option>
          </select>
        </div>
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
            @change="emit('update-coa-status', ($event.target as HTMLSelectElement).value)"
            class="flex-1 min-w-0 px-2 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wider border focus:outline-none shadow-2xs"
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
            @change="emit('update-visa-status', ($event.target as HTMLSelectElement).value === 'APPLIED' ? 'APPLIED' : null)"
            class="flex-1 min-w-0 px-2 py-0.5 rounded-full text-[8.5px] font-bold uppercase tracking-wider border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-300 focus:outline-none shadow-2xs"
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
</template>
