<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  X, RefreshCw, FileDown, Pencil, Trash2, Globe, Map, Building2,
  CheckCircle2, XCircle, Clock, AlertCircle, Info, Pin,
  ChevronDown, Check, Search, AlertTriangle
} from 'lucide-vue-next'
import { visaApi, type VisaStudent, type VisaOptions } from '@/api/visa'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import CopyField from './CopyField.vue'
import StatusBadge from './StatusBadge.vue'
import VisaTypeBadge from './VisaTypeBadge.vue'
import { CANCELLATION_REASONS, type CancellationReasonOption } from '../constants/cancellationReasons'

const props = defineProps<{
  isOpen: boolean
  student: VisaStudent | null
  isChecking?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', student: VisaStudent): void
  (e: 'delete', student: VisaStudent): void
  (e: 'refresh', student: VisaStudent): void
  (e: 'downloadPdf', student: VisaStudent): void
  (e: 'updated', student: VisaStudent): void
}>()

const uiStore = useUiStore()
const authStore = useAuthStore()

const isChecking = computed(() => Boolean(props.isChecking))

const isApproved = computed(() => {
  const s = (props.student?.status || '').toUpperCase()
  return s.includes('APPROV') || s.includes('VISA USED') || s.includes('ISSUED')
})

function formatTimestamp(ts: string | undefined | null): string {
  if (!ts) return '--'
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts
    return d.toLocaleString('en-US', {
      month: 'numeric',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    })
  } catch { return ts }
}

import { parseRejectionReasons, type ParsedRejectionReason } from '../utils/rejectionParser'

// ─── Parse rejection reasons ──────────────────────────────────────────────────
const parsedRejectionReasons = computed<ParsedRejectionReason[]>(() => {
  return parseRejectionReasons(props.student?.rejection_reason)
})

// ─── Manual Visa Status Assignment Modal ──────────────────────────────────────
const showAssignStatusModal = ref(false)
const manualStatus = ref<'APPROVED' | 'CANCELLED' | 'PENDING'>('PENDING')
const selectedReasons = ref<string[]>([])
const customReasonText = ref('')
const reasonsDropdownOpen = ref(false)
const reasonSearchQuery = ref('')
const savingStatus = ref(false)

function openAssignStatusModal() {
  if (!props.student) return
  const current = (props.student.status || '').toUpperCase()
  if (current.includes('APPROV') || current.includes('VISA USED') || current.includes('ISSUED') || current.includes('허가') || current.includes('TASDIQLANGAN')) {
    manualStatus.value = 'APPROVED'
  } else if (current.includes('CANCEL') || current.includes('REJECT') || current.includes('RETURN') || current.includes('EXPIRED') || current.includes('불허') || current.includes('RAD ETIL') || current.includes('BEKOR')) {
    manualStatus.value = 'CANCELLED'
  } else {
    manualStatus.value = 'PENDING'
  }

  // Pre-populate reasons if student was cancelled with reasons
  const existingReasons = parsedRejectionReasons.value
  const preSelected: string[] = []
  const customParts: string[] = []
  for (const r of existingReasons) {
    if (r.number && CANCELLATION_REASONS.some(c => c.number === r.number)) {
      if (!preSelected.includes(r.number)) preSelected.push(r.number)
    } else if (r.text) {
      customParts.push(r.text)
    }
  }
  selectedReasons.value = preSelected
  customReasonText.value = customParts.join('; ')
  reasonsDropdownOpen.value = false
  reasonSearchQuery.value = ''
  showAssignStatusModal.value = true
}

function toggleReason(num: string) {
  const idx = selectedReasons.value.indexOf(num)
  if (idx !== -1) {
    selectedReasons.value.splice(idx, 1)
  } else {
    selectedReasons.value.push(num)
    selectedReasons.value.sort((a, b) => Number(a) - Number(b))
  }
}

function removeReason(num: string) {
  const idx = selectedReasons.value.indexOf(num)
  if (idx !== -1) {
    selectedReasons.value.splice(idx, 1)
  }
}

function selectAllReasons() {
  selectedReasons.value = CANCELLATION_REASONS.map(r => r.number)
}

function clearAllReasons() {
  selectedReasons.value = []
}

const filteredReasons = computed(() => {
  const q = reasonSearchQuery.value.trim().toLowerCase()
  if (!q) return CANCELLATION_REASONS
  return CANCELLATION_REASONS.filter(r =>
    r.number.includes(q) ||
    r.korean.toLowerCase().includes(q) ||
    r.uzbek.toLowerCase().includes(q) ||
    r.english.toLowerCase().includes(q)
  )
})

function buildCompiledRejectionReason(): string {
  const parts: string[] = []
  const sorted = [...selectedReasons.value].sort((a, b) => Number(a) - Number(b))
  for (const num of sorted) {
    const found = CANCELLATION_REASONS.find(c => c.number === num)
    if (found) {
      parts.push(`${found.number}. ${found.korean}`)
    }
  }
  if (customReasonText.value.trim()) {
    parts.push(customReasonText.value.trim())
  }
  return parts.join(' ')
}

const previewParsedReasons = computed<ParsedRejectionReason[]>(() => {
  const compiled = buildCompiledRejectionReason()
  return parseRejectionReasons(compiled)
})

async function saveManualVisaStatus() {
  if (!props.student) return
  if (manualStatus.value === 'CANCELLED' && selectedReasons.value.length === 0 && !customReasonText.value.trim()) {
    uiStore.addToast({
      type: 'warning',
      message: 'Iltimos, kamida bitta bekor qilish sababini tanlang yoki kiriting.'
    })
    return
  }

  savingStatus.value = true
  try {
    const today = new Date().toISOString().split('T')[0]
    let payload: Partial<VisaStudent> = {}

    if (manualStatus.value === 'APPROVED') {
      payload = {
        status: 'APPROVED',
        rejection_reason: '',
        status_date: props.student.status_date || today,
        batch_selected: false
      }
    } else if (manualStatus.value === 'CANCELLED') {
      const reasonStr = buildCompiledRejectionReason()
      payload = {
        status: 'CANCELLED',
        rejection_reason: reasonStr,
        status_date: props.student.status_date || today,
        batch_selected: false
      }
    } else {
      payload = {
        status: 'PENDING',
        rejection_reason: ''
      }
    }

    const updated = await visaApi.updateVisaStudent(props.student.passport, payload)
    emit('updated', updated)
    showAssignStatusModal.value = false
    uiStore.addToast({
      type: 'success',
      message: `Visa holati ${manualStatus.value} ga o'zgartirildi ✓`
    })
  } catch (err: any) {
    uiStore.addToast({
      type: 'error',
      message: err.message || 'Visa holatini o\'zgartirishda xatolik yuz berdi'
    })
  } finally {
    savingStatus.value = false
  }
}

// ─── Management Dropdown options ──────────────────────────────────────────────
const options = ref<VisaOptions>({
  tariffs: [],
  universities: [],
  coordinators: [],
  b2b: []
})

async function loadOptions() {
  try {
    options.value = await visaApi.getVisaOptions()
  } catch { /* ignore */ }
}

watch(() => props.isOpen, (open) => {
  if (open) loadOptions()
  showEditFieldModal.value = false
  showAssignStatusModal.value = false
})

// ─── Inline Field Editing Modal ───────────────────────────────────────────────
type ManagementField = 'tariff' | 'university' | 'coordinator' | 'b2b' | 'flag' | 'refund_application'

const showEditFieldModal = ref(false)
const editingFieldName = ref<ManagementField | null>(null)
const editingFieldValue = ref('none')
const savingField = ref(false)

function getFieldDisplayTitle(fieldName: ManagementField | null): string {
  if (!fieldName) return ''
  if (fieldName === 'b2b') return 'B2B Partner'
  if (fieldName === 'refund_application') return 'Refund Application'
  return fieldName.charAt(0).toUpperCase() + fieldName.slice(1)
}

function openEditField(fieldName: ManagementField) {
  if (!props.student) return
  editingFieldName.value = fieldName
  if (fieldName === 'flag') {
    editingFieldValue.value = props.student.flag ? 'true' : 'false'
  } else if (fieldName === 'refund_application') {
    editingFieldValue.value = props.student.refund_application ? 'true' : 'false'
  } else {
    editingFieldValue.value = props.student[fieldName] || 'none'
  }
  showEditFieldModal.value = true
}

const currentFieldChoices = computed(() => {
  if (editingFieldName.value === 'flag' || editingFieldName.value === 'refund_application') {
    return [
      { label: 'False', value: 'false' },
      { label: 'True', value: 'true' }
    ]
  }
  let list: { name: string }[] = []
  if (editingFieldName.value === 'tariff') list = options.value.tariffs
  else if (editingFieldName.value === 'university') list = options.value.universities
  else if (editingFieldName.value === 'coordinator') list = options.value.coordinators
  else if (editingFieldName.value === 'b2b') list = options.value.b2b

  const items = list.map(item => ({ label: item.name, value: item.name }))
  return [{ label: 'None', value: 'none' }, ...items]
})

async function saveField(fieldName: ManagementField, val: string) {
  if (!props.student) return
  savingField.value = true
  try {
    const isBool = fieldName === 'flag' || fieldName === 'refund_application'
    const apiVal = isBool ? (val === 'true') : (val === 'none' ? '' : val)
    const updated = await visaApi.updateVisaStudent(props.student.passport, {
      [fieldName]: apiVal
    })
    emit('updated', updated)
    showEditFieldModal.value = false
    uiStore.addToast({
      type: 'success',
      message: `${getFieldDisplayTitle(fieldName)} yangilandi ✓`
    })
  } catch (err: any) {
    uiStore.addToast({
      type: 'error',
      message: err.message || 'Saqlashda xatolik yuz berdi'
    })
  } finally {
    savingField.value = false
  }
}

async function clearField(fieldName: ManagementField) {
  if (!props.student) return
  await saveField(fieldName, (fieldName === 'flag' || fieldName === 'refund_application') ? 'false' : 'none')
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen && student"
        class="visacheck-page fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @mousedown.self="emit('close')"
      >
        <Transition
          enter-active-class="transition duration-250 ease-[cubic-bezier(0.22,1,0.36,1)]"
          enter-from-class="scale-95 opacity-0"
          enter-to-class="scale-100 opacity-100"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="scale-100 opacity-100"
          leave-to-class="scale-95 opacity-0"
        >
          <div
            v-if="isOpen && student"
            class="relative w-full max-w-3xl bg-white dark:bg-[#141618] border border-slate-200/90 dark:border-white/10 rounded-lg shadow-2xl overflow-hidden max-h-[92vh] flex flex-col"
          >
            <!-- Modal Header (matches screenshot: "Student Details" on left, X on right) -->
            <div class="px-6 py-4 border-b border-slate-200 dark:border-zinc-800 flex items-center justify-between">
              <h2 class="text-base font-bold text-slate-900 dark:text-white">
                Student Details
              </h2>
              <button
                type="button"
                @click="emit('close')"
                class="size-8 rounded-md flex items-center justify-center text-slate-400 hover:text-slate-700 dark:hover:text-zinc-200 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <X class="size-4.5" />
              </button>
            </div>

            <!-- Modal Body (2-column layout matching screenshots) -->
            <div class="flex-1 overflow-y-auto p-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-8">

                <!-- Left Column: Student Details -->
                <div class="space-y-4">
                  <!-- Name + Badges -->
                  <div>
                    <div class="flex items-center gap-1.5 flex-wrap font-bold text-slate-900 dark:text-white text-base leading-snug">
                      <CopyField :value="student.full_name" label="Copy name">
                        <span class="break-words">{{ student.full_name }}</span>
                      </CopyField>
                      <Pin v-if="student.pinned" class="size-4 text-amber-500 fill-amber-500 shrink-0" title="Pinned" />
                      <span v-if="student.flag" title="Flagged" class="text-sm select-none shrink-0">🚩</span>
                      <span v-if="student.refund_application" title="Refund Application" class="text-sm select-none shrink-0">💸</span>
                    </div>

                    <!-- VisaType and Status Badges -->
                    <div class="flex flex-wrap items-center gap-1.5 mt-2">
                      <VisaTypeBadge :visa-type="student.visa_type" />
                      <StatusBadge :status="student.status" />
                    </div>
                  </div>

                  <!-- Passport Number Box (Mint green matching screenshot) -->
                  <CopyField :value="student.passport" label="Copy passport" class="w-full block">
                    <div class="w-full rounded-md bg-[#E8F5E9] dark:bg-emerald-950/20 border border-[#C8E6C9] dark:border-emerald-900/40 px-4 py-3 text-left hover:bg-[#DCEDC8] dark:hover:bg-emerald-950/40 transition-colors cursor-pointer flex items-center justify-between">
                      <div class="min-w-0">
                        <p class="text-[10.5px] font-bold uppercase tracking-wider text-[#2E7D32] dark:text-emerald-400">
                          PASSPORT NUMBER
                        </p>
                        <p class="text-base font-bold font-mono tracking-wider text-[#1B5E20] dark:text-white truncate">
                          {{ student.passport }}
                        </p>
                      </div>
                    </div>
                  </CopyField>

                  <!-- 2-Column Info Grid -->
                  <div class="grid grid-cols-2 gap-3 text-xs">
                    <!-- Student ID -->
                    <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Student ID</p>
                      <CopyField :value="student.student_id || student.id" label="Copy ID" class="text-sm font-semibold text-slate-800 dark:text-zinc-200">
                        {{ student.student_id || student.id || '--' }}
                      </CopyField>
                    </div>

                    <!-- Birthdate -->
                    <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Birthdate</p>
                      <CopyField :value="student.birthday" label="Copy birthday" class="text-sm font-bold font-mono text-slate-900 dark:text-white">
                        {{ student.birthday || '--' }}
                      </CopyField>
                    </div>

                    <!-- Application Date -->
                    <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Application Date</p>
                      <CopyField :value="student.application_date" label="Copy application date" class="text-xs font-semibold text-slate-800 dark:text-zinc-200 font-mono">
                        {{ student.application_date || '--' }}
                      </CopyField>
                    </div>

                    <!-- Application Number -->
                    <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Application Number</p>
                      <CopyField :value="student.application_no" label="Copy app no" class="text-xs font-bold font-mono text-slate-800 dark:text-zinc-200">
                        {{ student.application_no || '--' }}
                      </CopyField>
                    </div>

                    <!-- Status Date (if available) -->
                    <div v-if="student.status_date" class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Status Date</p>
                      <CopyField :value="student.status_date" label="Copy status date" class="text-xs font-semibold text-slate-800 dark:text-zinc-200 font-mono">
                        {{ student.status_date }}
                      </CopyField>
                    </div>

                    <!-- Last Checked -->
                    <div
                      class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50"
                      :class="{ 'col-span-2': !student.status_date }"
                    >
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Last Checked</p>
                      <p class="text-xs font-semibold text-slate-800 dark:text-zinc-200">
                        {{ formatTimestamp(student.last_checked) }}
                      </p>
                    </div>
                  </div>

                  <!-- Rejection Reason Card (Pink card with red numbered badges matching Screenshot 2) -->
                  <div
                    v-if="parsedRejectionReasons.length > 0"
                    class="rounded-xl p-3.5 bg-[#FFF5F5] dark:bg-rose-950/20 border border-[#FED7D7] dark:border-rose-900/40 space-y-2.5 text-xs"
                  >
                    <div
                      v-for="(item, idx) in parsedRejectionReasons"
                      :key="idx"
                      class="flex items-start gap-2.5 leading-relaxed"
                    >
                      <span
                        v-if="item.number"
                        class="size-5 min-w-[20px] rounded-full bg-[#E02424] text-white text-[11px] font-extrabold flex items-center justify-center shrink-0 mt-0.5"
                      >
                        {{ item.number }}
                      </span>
                      <XCircle v-else class="size-4.5 text-[#E02424] shrink-0 mt-0.5" />
                      <span class="text-[12.5px] text-zinc-900 dark:text-zinc-100 font-normal leading-snug">
                        {{ item.text }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Right Column: Management (Matches screenshot 100%) -->
                <div class="space-y-3.5 border-t md:border-t-0 md:border-l border-slate-200 dark:border-zinc-800 pt-4 md:pt-0 md:pl-6">
                  <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-zinc-400">
                    MANAGEMENT
                  </p>

                  <div class="space-y-3">
                    <!-- Visa Status (Manual Assignment) -->
                    <div class="rounded-lg border border-blue-200/80 dark:border-blue-900/50 bg-blue-50/40 dark:bg-blue-950/20 p-3 space-y-2">
                      <div class="flex items-center justify-between">
                        <label class="block text-xs font-bold text-slate-800 dark:text-zinc-200">
                          Visa Status (Manual Assignment)
                        </label>
                        <span class="text-[10px] font-semibold text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/60 px-2 py-0.5 rounded-full">
                          Manual
                        </span>
                      </div>
                      <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-2.5 flex items-center justify-between bg-white dark:bg-zinc-900/70">
                        <div class="flex items-center gap-2 flex-wrap min-w-0 pr-2">
                          <StatusBadge :status="student.status" />
                          <span
                            v-if="parsedRejectionReasons.length > 0"
                            class="text-[11px] font-semibold text-rose-600 dark:text-rose-400"
                          >
                            ({{ parsedRejectionReasons.length }} ta sabab)
                          </span>
                        </div>
                        <button
                          v-if="authStore.canEdit"
                          type="button"
                          @click="openAssignStatusModal"
                          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-xs transition-colors shrink-0 cursor-pointer"
                          title="Assign Visa Status Manually"
                        >
                          <Pencil class="size-3.5" />
                          <span>Assign Status</span>
                        </button>
                      </div>
                    </div>

                    <!-- Tariff -->
                    <div>
                      <label class="block text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1">
                        Tariff
                      </label>
                      <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white truncate pr-2">
                          {{ student.tariff || 'None' }}
                        </span>
                        <div v-if="authStore.canEdit" class="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            @click="openEditField('tariff')"
                            class="text-slate-700 hover:text-blue-600 dark:text-zinc-300 dark:hover:text-blue-400 transition-colors"
                            title="Edit Tariff"
                          >
                            <Pencil class="size-4" />
                          </button>
                          <button
                            v-if="student.tariff && student.tariff !== 'None'"
                            type="button"
                            @click="clearField('tariff')"
                            class="text-rose-500 hover:text-rose-700 transition-colors"
                            title="Clear Tariff"
                          >
                            <Trash2 class="size-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- University -->
                    <div>
                      <label class="block text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1">
                        University
                      </label>
                      <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white truncate pr-2">
                          {{ student.university || 'None' }}
                        </span>
                        <div v-if="authStore.canEdit" class="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            @click="openEditField('university')"
                            class="text-slate-700 hover:text-blue-600 dark:text-zinc-300 dark:hover:text-blue-400 transition-colors"
                            title="Edit University"
                          >
                            <Pencil class="size-4" />
                          </button>
                          <button
                            v-if="student.university && student.university !== 'None'"
                            type="button"
                            @click="clearField('university')"
                            class="text-rose-500 hover:text-rose-700 transition-colors"
                            title="Clear University"
                          >
                            <Trash2 class="size-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- Coordinator -->
                    <div>
                      <label class="block text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1">
                        Coordinator
                      </label>
                      <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white truncate pr-2">
                          {{ student.coordinator || 'None' }}
                        </span>
                        <div v-if="authStore.canEdit" class="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            @click="openEditField('coordinator')"
                            class="text-slate-700 hover:text-blue-600 dark:text-zinc-300 dark:hover:text-blue-400 transition-colors"
                            title="Edit Coordinator"
                          >
                            <Pencil class="size-4" />
                          </button>
                          <button
                            v-if="student.coordinator && student.coordinator !== 'None'"
                            type="button"
                            @click="clearField('coordinator')"
                            class="text-rose-500 hover:text-rose-700 transition-colors"
                            title="Clear Coordinator"
                          >
                            <Trash2 class="size-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- B2B Partner -->
                    <div>
                      <label class="block text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1">
                        B2B Partner
                      </label>
                      <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white truncate pr-2">
                          {{ student.b2b || 'None' }}
                        </span>
                        <div v-if="authStore.canEdit" class="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            @click="openEditField('b2b')"
                            class="text-slate-700 hover:text-blue-600 dark:text-zinc-300 dark:hover:text-blue-400 transition-colors"
                            title="Edit B2B Partner"
                          >
                            <Pencil class="size-4" />
                          </button>
                          <button
                            v-if="student.b2b && student.b2b !== 'None'"
                            type="button"
                            @click="clearField('b2b')"
                            class="text-rose-500 hover:text-rose-700 transition-colors"
                            title="Clear B2B Partner"
                          >
                            <Trash2 class="size-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- Flag -->
                    <div>
                      <label class="block text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1">
                        Flag
                      </label>
                      <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                          <span>{{ student.flag ? 'True' : 'False' }}</span>
                          <span v-if="student.flag">🚩</span>
                        </span>
                        <div v-if="authStore.canEdit" class="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            @click="openEditField('flag')"
                            class="text-slate-700 hover:text-blue-600 dark:text-zinc-300 dark:hover:text-blue-400 transition-colors"
                            title="Edit Flag"
                          >
                            <Pencil class="size-4" />
                          </button>
                          <button
                            v-if="student.flag"
                            type="button"
                            @click="clearField('flag')"
                            class="text-rose-500 hover:text-rose-700 transition-colors"
                            title="Clear Flag"
                          >
                            <Trash2 class="size-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- Refund Application -->
                    <div>
                      <label class="block text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1">
                        Refund Application
                      </label>
                      <div class="rounded-md border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                          <span>{{ student.refund_application ? 'True' : 'False' }}</span>
                          <span v-if="student.refund_application">💸</span>
                        </span>
                        <div v-if="authStore.canEdit" class="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            @click="openEditField('refund_application')"
                            class="text-slate-700 hover:text-blue-600 dark:text-zinc-300 dark:hover:text-blue-400 transition-colors"
                            title="Edit Refund Application"
                          >
                            <Pencil class="size-4" />
                          </button>
                          <button
                            v-if="student.refund_application"
                            type="button"
                            @click="clearField('refund_application')"
                            class="text-rose-500 hover:text-rose-700 transition-colors"
                            title="Clear Refund Application"
                          >
                            <Trash2 class="size-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>

            <!-- Footer Action Buttons (Matches screenshot 100%) -->
            <div class="px-6 py-4 border-t border-slate-200 dark:border-zinc-800 flex items-center justify-between gap-4">
              <!-- Delete (Managers only) -->
              <div>
                <button
                  v-if="authStore.canDelete"
                  type="button"
                  @click="emit('delete', student)"
                  class="flex items-center gap-1.5 text-sm font-semibold text-rose-600 hover:text-rose-700 px-3 py-2 rounded-md hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
                >
                  <Trash2 class="size-4" />
                  <span>Delete</span>
                </button>
              </div>

              <div class="flex items-center gap-3">
                <!-- Edit (Managers only) -->
                <button
                  v-if="authStore.canEdit"
                  type="button"
                  @click="emit('edit', student); emit('close')"
                  class="flex items-center gap-1.5 h-10 px-6 rounded-md border border-slate-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-slate-700 dark:text-zinc-200 font-semibold text-sm hover:bg-slate-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
                >
                  <Pencil class="size-4" />
                  <span>Edit</span>
                </button>

                <!-- Check OR PDF button (Dark green #0B4133 matching univisacheck) -->
                <button
                  v-if="isApproved"
                  type="button"
                  @click="emit('downloadPdf', student)"
                  class="flex items-center gap-2 h-10 px-6 rounded-md bg-[#0B4133] hover:bg-[#082e24] text-white font-bold text-sm shadow-sm transition-all"
                >
                  <Info class="size-4" />
                  <span>PDF</span>
                </button>

                <button
                  v-else
                  type="button"
                  :disabled="isChecking"
                  @click="emit('refresh', student)"
                  class="flex items-center gap-2 h-10 px-6 rounded-md bg-[#0B4133] hover:bg-[#082e24] text-white font-bold text-sm shadow-sm transition-all disabled:opacity-60"
                >
                  <RefreshCw class="size-4" :class="{ 'animate-spin': isChecking }" />
                  <span>{{ isChecking ? 'Checking...' : 'Check' }}</span>
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- Sub-modal for Editing a Management Field -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="showEditFieldModal && editingFieldName"
        class="visacheck-page fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @mousedown.self="showEditFieldModal = false"
      >
        <div class="w-full max-w-sm bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-lg shadow-2xl p-5 space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-sm text-slate-900 dark:text-white">
              Edit {{ getFieldDisplayTitle(editingFieldName) }}
            </h3>
            <button type="button" @click="showEditFieldModal = false" class="text-slate-400 hover:text-slate-700">
              <X class="size-4" />
            </button>
          </div>

          <form @submit.prevent="saveField(editingFieldName!, editingFieldValue)" class="space-y-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 dark:text-zinc-400 mb-1.5">
                {{ getFieldDisplayTitle(editingFieldName) }}
              </label>
              <select
                v-model="editingFieldValue"
                class="w-full h-10 px-3 rounded-md border border-slate-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-slate-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
              >
                <option
                  v-for="opt in currentFieldChoices"
                  :key="opt.value"
                  :value="opt.value"
                >
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <div class="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                @click="showEditFieldModal = false"
                class="h-9 px-4 rounded-md text-xs font-semibold text-slate-600 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="savingField"
                class="h-9 px-5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-colors disabled:opacity-50"
              >
                {{ savingField ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- Sub-modal for Manual Assignment of Visa Status -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="showAssignStatusModal && student"
        class="visacheck-page fixed inset-0 z-[75] flex items-center justify-center p-4 bg-black/65 backdrop-blur-xs"
        @mousedown.self="showAssignStatusModal = false"
      >
        <div class="w-full max-w-lg bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-xl shadow-2xl p-6 space-y-5 max-h-[90vh] flex flex-col">
          <!-- Modal Header -->
          <div class="flex items-center justify-between border-b border-slate-100 dark:border-zinc-800 pb-3.5 shrink-0">
            <div>
              <h3 class="font-bold text-base text-slate-900 dark:text-white">
                Manual Assignment of Visa Status
              </h3>
              <p class="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">
                {{ student.full_name }} • <span class="font-mono font-semibold">{{ student.passport }}</span>
              </p>
            </div>
            <button
              type="button"
              @click="showAssignStatusModal = false"
              class="size-8 rounded-md flex items-center justify-center text-slate-400 hover:text-slate-700 dark:hover:text-zinc-200 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <X class="size-4.5" />
            </button>
          </div>

          <!-- Modal Scrollable Content -->
          <div class="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-thin">
            <!-- 1. Choose Status (Approved, Cancelled, Pending) -->
            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-zinc-300 mb-2 uppercase tracking-wider">
                Select Visa Status
              </label>
              <div class="grid grid-cols-3 gap-2.5">
                <!-- Approved -->
                <button
                  type="button"
                  @click="manualStatus = 'APPROVED'"
                  class="p-3 rounded-lg border-2 text-left transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5"
                  :class="manualStatus === 'APPROVED'
                    ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 shadow-sm'
                    : 'border-slate-200 dark:border-zinc-800 hover:border-emerald-300 dark:hover:border-emerald-900/60 bg-white dark:bg-zinc-950 text-slate-700 dark:text-zinc-300'"
                >
                  <CheckCircle2 class="size-6 text-emerald-600 dark:text-emerald-400" />
                  <span class="text-xs font-bold leading-tight">Approved</span>
                  <span class="text-[10px] text-emerald-600/80 dark:text-emerald-400/80 font-medium">To Approved tab</span>
                </button>

                <!-- Cancelled -->
                <button
                  type="button"
                  @click="manualStatus = 'CANCELLED'"
                  class="p-3 rounded-lg border-2 text-left transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5"
                  :class="manualStatus === 'CANCELLED'
                    ? 'border-rose-600 bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 shadow-sm'
                    : 'border-slate-200 dark:border-zinc-800 hover:border-rose-300 dark:hover:border-rose-900/60 bg-white dark:bg-zinc-950 text-slate-700 dark:text-zinc-300'"
                >
                  <XCircle class="size-6 text-rose-600 dark:text-rose-400" />
                  <span class="text-xs font-bold leading-tight">Cancelled</span>
                  <span class="text-[10px] text-rose-600/80 dark:text-rose-400/80 font-medium">With reasons</span>
                </button>

                <!-- Pending -->
                <button
                  type="button"
                  @click="manualStatus = 'PENDING'"
                  class="p-3 rounded-lg border-2 text-left transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5"
                  :class="manualStatus === 'PENDING'
                    ? 'border-slate-600 bg-slate-100 dark:bg-zinc-800 text-slate-900 dark:text-zinc-100 shadow-sm'
                    : 'border-slate-200 dark:border-zinc-800 hover:border-slate-300 dark:hover:border-zinc-700 bg-white dark:bg-zinc-950 text-slate-700 dark:text-zinc-300'"
                >
                  <Clock class="size-6 text-slate-500 dark:text-zinc-400" />
                  <span class="text-xs font-bold leading-tight">Pending</span>
                  <span class="text-[10px] text-slate-500 dark:text-zinc-400 font-medium">To Pending tab</span>
                </button>
              </div>
            </div>

            <!-- 2. Contextual details for Approved / Pending -->
            <div
              v-if="manualStatus === 'APPROVED'"
              class="p-3.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/50 flex items-start gap-2.5 text-xs text-emerald-900 dark:text-emerald-200 leading-relaxed"
            >
              <CheckCircle2 class="size-4.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p class="font-bold">Student will be marked as APPROVED</p>
                <p class="text-[11.5px] text-emerald-700 dark:text-emerald-300 mt-0.5">
                  The student will immediately move to the <strong>Approved</strong> tab. Any existing rejection reasons will be cleared.
                </p>
              </div>
            </div>

            <div
              v-if="manualStatus === 'PENDING'"
              class="p-3.5 rounded-lg bg-slate-50 dark:bg-zinc-800/60 border border-slate-200 dark:border-zinc-700 flex items-start gap-2.5 text-xs text-slate-700 dark:text-zinc-300 leading-relaxed"
            >
              <Clock class="size-4.5 text-slate-500 dark:text-zinc-400 shrink-0 mt-0.5" />
              <div>
                <p class="font-bold">Student will be reset to PENDING</p>
                <p class="text-[11.5px] text-slate-600 dark:text-zinc-400 mt-0.5">
                  The student will move to the <strong>Pending</strong> tab. Any previous rejection reasons will be cleared.
                </p>
              </div>
            </div>

            <!-- 3. Cancellation Reasons (When Cancelled is selected) -->
            <div v-if="manualStatus === 'CANCELLED'" class="space-y-3.5 pt-1">
              <div>
                <div class="flex items-center justify-between mb-1.5">
                  <label class="block text-xs font-bold text-slate-800 dark:text-zinc-200">
                    Cancellation / Refusal Reasons (Multiple Select)
                  </label>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      @click="selectAllReasons"
                      class="text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline cursor-pointer"
                    >
                      Select all
                    </button>
                    <span class="text-slate-300 dark:text-zinc-700">|</span>
                    <button
                      type="button"
                      @click="clearAllReasons"
                      class="text-[11px] font-semibold text-rose-600 dark:text-rose-400 hover:underline cursor-pointer"
                    >
                      Clear
                    </button>
                  </div>
                </div>

                <!-- Multi-select Dropdown Container -->
                <div class="relative">
                  <!-- Trigger Button -->
                  <button
                    type="button"
                    @click="reasonsDropdownOpen = !reasonsDropdownOpen"
                    class="w-full min-h-[44px] px-3 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-left text-sm flex items-center justify-between gap-2 focus:outline-none focus:border-blue-500 cursor-pointer shadow-2xs"
                  >
                    <div class="flex items-center gap-1.5 flex-wrap min-w-0">
                      <span v-if="selectedReasons.length === 0" class="text-xs text-slate-400 dark:text-zinc-500">
                        Select cancellation reasons from dropdown...
                      </span>
                      <span
                        v-for="num in selectedReasons"
                        :key="num"
                        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 text-xs font-semibold"
                      >
                        <span class="size-4 rounded-full bg-[#E02424] text-white text-[9px] font-extrabold flex items-center justify-center">
                          {{ num }}
                        </span>
                        <span class="text-[11px]">Reason #{{ num }}</span>
                        <button
                          type="button"
                          @click.stop="removeReason(num)"
                          class="hover:text-rose-900 dark:hover:text-white"
                        >
                          <X class="size-3" />
                        </button>
                      </span>
                    </div>
                    <div class="flex items-center gap-1.5 text-slate-400 shrink-0">
                      <span v-if="selectedReasons.length > 0" class="text-[11px] font-bold text-rose-600 bg-rose-50 dark:bg-rose-950/50 px-2 py-0.5 rounded-full">
                        {{ selectedReasons.length }} selected
                      </span>
                      <ChevronDown class="size-4.5 transition-transform" :class="{ 'rotate-180': reasonsDropdownOpen }" />
                    </div>
                  </button>

                  <!-- Reasons List (Dropdown / collapsible) -->
                  <div
                    v-if="reasonsDropdownOpen"
                    class="mt-1.5 max-h-56 overflow-y-auto rounded-lg border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-xl p-2 space-y-1 scrollbar-thin"
                  >
                    <!-- Search inside reasons -->
                    <div class="sticky top-0 bg-white dark:bg-zinc-900 pb-2 pt-0.5 border-b border-slate-100 dark:border-zinc-800 z-10">
                      <div class="relative">
                        <Search class="size-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input
                          v-model="reasonSearchQuery"
                          type="text"
                          placeholder="Search reasons by number, Korean or Uzbek..."
                          class="w-full h-8 pl-8 pr-3 text-xs rounded-md border border-slate-200 dark:border-zinc-700 bg-slate-50 dark:bg-zinc-950 text-slate-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </div>

                    <!-- Items -->
                    <div
                      v-for="opt in filteredReasons"
                      :key="opt.number"
                      @click="toggleReason(opt.number)"
                      class="flex items-start gap-2.5 p-2 rounded-md hover:bg-slate-100 dark:hover:bg-zinc-800 cursor-pointer transition-colors"
                      :class="selectedReasons.includes(opt.number) ? 'bg-rose-50/70 dark:bg-rose-950/30' : ''"
                    >
                      <input
                        type="checkbox"
                        :checked="selectedReasons.includes(opt.number)"
                        @click.stop="toggleReason(opt.number)"
                        class="mt-1 size-4 rounded text-rose-600 focus:ring-rose-500 cursor-pointer"
                      />
                      <span class="size-5 min-w-[20px] rounded-full bg-[#E02424] text-white text-[10px] font-extrabold flex items-center justify-center shrink-0 mt-0.5">
                        {{ opt.number }}
                      </span>
                      <div class="min-w-0 flex-1">
                        <p class="text-xs font-bold text-slate-900 dark:text-zinc-100 leading-snug">
                          {{ opt.korean }}
                        </p>
                        <p class="text-[11px] text-slate-500 dark:text-zinc-400 mt-0.5 leading-tight">
                          {{ opt.uzbek }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Custom / Extra Reason Text Field -->
              <div>
                <label class="block text-xs font-semibold text-slate-600 dark:text-zinc-400 mb-1">
                  Custom Notes / Extra Reason (Optional)
                </label>
                <input
                  v-model="customReasonText"
                  type="text"
                  placeholder="e.g. Qo'shimcha tushuntirish yoki konsullik izohi..."
                  class="w-full h-9 px-3 rounded-md border border-slate-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-slate-900 dark:text-white text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <!-- Live Preview Card -->
              <div
                v-if="selectedReasons.length > 0 || customReasonText.trim()"
                class="rounded-xl p-3 bg-[#FFF5F5] dark:bg-rose-950/20 border border-[#FED7D7] dark:border-rose-900/40 space-y-2 text-xs"
              >
                <p class="text-[10px] font-bold uppercase tracking-wider text-rose-700 dark:text-rose-400">
                  Preview in Student Details
                </p>
                <div
                  v-for="(item, idx) in previewParsedReasons"
                  :key="idx"
                  class="flex items-start gap-2.5 leading-relaxed"
                >
                  <span
                    v-if="item.number"
                    class="size-4.5 min-w-[18px] rounded-full bg-[#E02424] text-white text-[10px] font-extrabold flex items-center justify-center shrink-0 mt-0.5"
                  >
                    {{ item.number }}
                  </span>
                  <XCircle v-else class="size-4 text-[#E02424] shrink-0 mt-0.5" />
                  <span class="text-[12px] text-zinc-900 dark:text-zinc-100 font-normal leading-snug">
                    {{ item.text }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100 dark:border-zinc-800 shrink-0">
            <button
              type="button"
              @click="showAssignStatusModal = false"
              class="h-9 px-4 rounded-md text-xs font-semibold text-slate-600 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              :disabled="savingStatus"
              @click="saveManualVisaStatus"
              class="h-9 px-5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-2 cursor-pointer shadow-sm"
            >
              <RefreshCw v-if="savingStatus" class="size-3.5 animate-spin" />
              <span>{{ savingStatus ? 'Saving...' : 'Save & Apply Status' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
