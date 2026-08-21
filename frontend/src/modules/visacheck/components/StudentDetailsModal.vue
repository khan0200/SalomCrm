<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  X, RefreshCw, FileDown, Pencil, Trash2, Globe, Map, Building2,
  CheckCircle2, XCircle, Clock, AlertCircle, Info
} from 'lucide-vue-next'
import { visaApi, type VisaStudent, type VisaOptions } from '@/api/visa'
import { useUiStore } from '@/stores/ui'
import CopyField from './CopyField.vue'
import StatusBadge from './StatusBadge.vue'
import VisaTypeBadge from './VisaTypeBadge.vue'

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

// ─── Parse rejection reasons ──────────────────────────────────────────────────
interface RejectionItem {
  number?: string
  text: string
}

const parsedRejectionReasons = computed<RejectionItem[]>(() => {
  const raw = props.student?.rejection_reason || ''
  if (!raw) return []
  let str = raw.trim().replace(/^Rejected:\s*/i, '').trim()
  const regex = /(\d+)\.\s*([\s\S]+?)(?=(?:\s*\d+\.|$))/g
  const matches = Array.from(str.matchAll(regex))

  if (matches.length > 0) {
    const items: RejectionItem[] = []
    for (const match of matches) {
      const num = match[1]
      const txt = (match[2] ?? '').trim()
      if (txt) items.push({ number: num, text: txt })
    }
    return items
  }
  return [{ text: str }]
})

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
        class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
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
            class="relative w-full max-w-3xl bg-white dark:bg-[#141618] border border-slate-200/90 dark:border-white/10 rounded-2xl shadow-2xl overflow-hidden max-h-[92vh] flex flex-col"
          >
            <!-- Modal Header (matches screenshot: "Student Details" on left, X on right) -->
            <div class="px-6 py-4 border-b border-slate-200 dark:border-zinc-800 flex items-center justify-between">
              <h2 class="text-base font-bold text-slate-900 dark:text-white">
                Student Details
              </h2>
              <button
                type="button"
                @click="emit('close')"
                class="size-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 dark:hover:text-zinc-200 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
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
                    <div class="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white text-base leading-snug">
                      <CopyField :value="student.full_name" label="Copy name">
                        <span class="truncate block max-w-[280px]">{{ student.full_name }}</span>
                      </CopyField>
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
                    <div class="w-full rounded-xl bg-[#E8F5E9] dark:bg-emerald-950/20 border border-[#C8E6C9] dark:border-emerald-900/40 px-4 py-3 text-left hover:bg-[#DCEDC8] dark:hover:bg-emerald-950/40 transition-colors cursor-pointer flex items-center justify-between">
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
                    <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Student ID</p>
                      <CopyField :value="student.student_id || student.id" label="Copy ID" class="text-sm font-semibold text-slate-800 dark:text-zinc-200">
                        {{ student.student_id || student.id || '--' }}
                      </CopyField>
                    </div>

                    <!-- Birthdate -->
                    <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Birthdate</p>
                      <CopyField :value="student.birthday" label="Copy birthday" class="text-sm font-bold font-mono text-slate-900 dark:text-white">
                        {{ student.birthday || '--' }}
                      </CopyField>
                    </div>

                    <!-- Application Date -->
                    <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Application Date</p>
                      <CopyField :value="student.application_date" label="Copy application date" class="text-xs font-semibold text-slate-800 dark:text-zinc-200 font-mono">
                        {{ student.application_date || '--' }}
                      </CopyField>
                    </div>

                    <!-- Application Number -->
                    <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Application Number</p>
                      <CopyField :value="student.application_no" label="Copy app no" class="text-xs font-bold font-mono text-slate-800 dark:text-zinc-200">
                        {{ student.application_no || '--' }}
                      </CopyField>
                    </div>

                    <!-- Status Date (if available) -->
                    <div v-if="student.status_date" class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50">
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Status Date</p>
                      <CopyField :value="student.status_date" label="Copy status date" class="text-xs font-semibold text-slate-800 dark:text-zinc-200 font-mono">
                        {{ student.status_date }}
                      </CopyField>
                    </div>

                    <!-- Last Checked -->
                    <div
                      class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-900/50"
                      :class="{ 'col-span-2': !student.status_date }"
                    >
                      <p class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mb-0.5">Last Checked</p>
                      <p class="text-xs font-semibold text-slate-800 dark:text-zinc-200">
                        {{ formatTimestamp(student.last_checked) }}
                      </p>
                    </div>
                  </div>

                  <!-- Rejection Reason Card (Pink card with red numbered badges matching screenshot) -->
                  <div
                    v-if="parsedRejectionReasons.length > 0"
                    class="rounded-xl p-3 bg-[#FFF1F0] dark:bg-rose-950/30 border border-[#FFA39E] dark:border-rose-900/50 space-y-2 text-xs"
                  >
                    <div
                      v-for="(item, idx) in parsedRejectionReasons"
                      :key="idx"
                      class="flex items-start gap-2 leading-relaxed"
                    >
                      <span
                        v-if="item.number"
                        class="size-4.5 rounded-full bg-rose-600 text-white text-[10.5px] font-bold flex items-center justify-center shrink-0 mt-0.5"
                      >
                        {{ item.number }}
                      </span>
                      <XCircle v-else class="size-4 text-rose-600 shrink-0 mt-0.5" />
                      <span class="text-slate-900 dark:text-rose-100 font-normal">
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
                    <!-- Tariff -->
                    <div>
                      <label class="block text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1">
                        Tariff
                      </label>
                      <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white truncate pr-2">
                          {{ student.tariff || 'None' }}
                        </span>
                        <div class="flex items-center gap-2 shrink-0">
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
                      <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white truncate pr-2">
                          {{ student.university || 'None' }}
                        </span>
                        <div class="flex items-center gap-2 shrink-0">
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
                      <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white truncate pr-2">
                          {{ student.coordinator || 'None' }}
                        </span>
                        <div class="flex items-center gap-2 shrink-0">
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
                      <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white truncate pr-2">
                          {{ student.b2b || 'None' }}
                        </span>
                        <div class="flex items-center gap-2 shrink-0">
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
                      <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                          <span>{{ student.flag ? 'True' : 'False' }}</span>
                          <span v-if="student.flag">🚩</span>
                        </span>
                        <div class="flex items-center gap-2 shrink-0">
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
                      <div class="rounded-xl border border-slate-200 dark:border-zinc-800 p-3 flex items-center justify-between bg-white dark:bg-zinc-900/50">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                          <span>{{ student.refund_application ? 'True' : 'False' }}</span>
                          <span v-if="student.refund_application">💸</span>
                        </span>
                        <div class="flex items-center gap-2 shrink-0">
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
              <!-- Delete -->
              <button
                type="button"
                @click="emit('delete', student)"
                class="flex items-center gap-1.5 text-sm font-semibold text-rose-600 hover:text-rose-700 px-3 py-2 rounded-xl hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
              >
                <Trash2 class="size-4" />
                <span>Delete</span>
              </button>

              <div class="flex items-center gap-3">
                <!-- Edit -->
                <button
                  type="button"
                  @click="emit('edit', student)"
                  class="flex items-center gap-1.5 h-10 px-6 rounded-xl border border-slate-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-slate-700 dark:text-zinc-200 font-semibold text-sm hover:bg-slate-50 dark:hover:bg-zinc-700 transition-colors"
                >
                  <Pencil class="size-4" />
                  <span>Edit</span>
                </button>

                <!-- Check OR PDF button (Dark green #0B4133 matching univisacheck) -->
                <button
                  v-if="isApproved"
                  type="button"
                  @click="emit('downloadPdf', student)"
                  class="flex items-center gap-2 h-10 px-6 rounded-xl bg-[#0B4133] hover:bg-[#082e24] text-white font-bold text-sm shadow-sm transition-all"
                >
                  <Info class="size-4" />
                  <span>PDF</span>
                </button>

                <button
                  v-else
                  type="button"
                  :disabled="isChecking"
                  @click="emit('refresh', student)"
                  class="flex items-center gap-2 h-10 px-6 rounded-xl bg-[#0B4133] hover:bg-[#082e24] text-white font-bold text-sm shadow-sm transition-all disabled:opacity-60"
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
        class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @mousedown.self="showEditFieldModal = false"
      >
        <div class="w-full max-w-sm bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-2xl p-5 space-y-4">
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
                class="w-full h-10 px-3 rounded-xl border border-slate-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-slate-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
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
                class="h-9 px-4 rounded-xl text-xs font-semibold text-slate-600 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="savingField"
                class="h-9 px-5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-colors disabled:opacity-50"
              >
                {{ savingField ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
