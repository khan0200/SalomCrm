<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Building2, Tag, Calendar, Eye, AlertCircle, RefreshCw, ChevronDown, FileCheck,
  Pin, Check, X, FileDown
} from 'lucide-vue-next'
import type { VisaStudent } from '@/api/visa'
import StatusBadge from './StatusBadge.vue'
import VisaTypeBadge from './VisaTypeBadge.vue'
import CopyField from './CopyField.vue'
import { formatTimestampCompact } from '../useTimeAgo'

const props = defineProps<{
  groupName: string
  students: VisaStudent[]
  currentFilter: string
  checkingPassports: Map<string, 'queued' | 'processing'>
  selectedPassports: Set<string>
  downloadingPassports: Set<string>
}>()

const emit = defineEmits<{
  (e: 'edit', student: VisaStudent): void
  (e: 'details', student: VisaStudent): void
  (e: 'delete', student: VisaStudent): void
  (e: 'refresh', student: VisaStudent): void
  (e: 'refresh-group', students: VisaStudent[]): void
  (e: 'download-pdf', student: VisaStudent): void
  (e: 'toggle-select', student: VisaStudent, checked: boolean): void
  (e: 'toggle-pin', student: VisaStudent): void
  (e: 'toggle-flag', student: VisaStudent): void
  (e: 'deselect-group', students: VisaStudent[]): void
  (e: 'contextmenu', student: VisaStudent, event: MouseEvent): void
}>()

const isOpen = ref(true)
const displayName = computed(() => props.groupName || 'No Group / Boshqa')
const groupIsChecking = computed(() =>
  props.students.some(s => props.checkingPassports.has(s.passport))
)

const groupIcon = computed(() => {
  const name = props.groupName.toLowerCase()
  if (name.includes('under review')) return Eye
  if (name.includes('supplement submitted') || name.includes('supplement completed')) return FileCheck
  if (name.includes('supplement')) return AlertCircle
  if (/^\d{4}[-./]\d{1,2}/.test(props.groupName)) return Calendar
  if (name.includes('standard') || name.includes('vip') || name.includes('premium') || name.includes('tariff')) return Tag
  return Building2
})

function getStudentVisaStatus(student: VisaStudent): string {
  const raw = (student.status || '').toUpperCase()
  if (raw.includes('APPROV') || raw.includes('PASSED') || raw.includes('ISSUED') || raw.includes('허가')) return 'APPROVED'
  if (raw.includes('REJECT') || raw.includes('CANCEL') || raw.includes('RETURN') || raw.includes('EXPIRED') || raw.includes('불허')) return 'CANCELLED'
  if (raw.includes('REVIEW') || raw.includes('PROCESSING') || raw.includes('SIMSA') || raw.includes('심사중')) return 'UNDER REVIEW'
  if (raw.includes('RECEIV') || raw.includes('SUBMIT') || raw.includes('JEOMSU') || raw.includes('접수') || raw.includes('APP/')) return 'RECEIVED'
  if (raw.includes('SUPPLEM') || raw.includes('보완')) return 'SUPPLEMENT NEEDED'
  return raw || 'PENDING'
}

function isPdfEligible(student: VisaStudent): boolean {
  const s = getStudentVisaStatus(student)
  return s.includes('APPROV') || s.includes('VISA USED')
}

const showSelectColumn = computed(() => props.currentFilter === 'application' || props.currentFilter === 'pending')
const showAppliedColumn = computed(() => props.currentFilter !== 'pending')
const showPdfColumn = computed(() =>
  props.currentFilter === 'approved' || props.students.some(s => isPdfEligible(s))
)
const showStatusDateColumn = computed(() => props.currentFilter === 'approved')

const groupHasSelected = computed(() =>
  props.students.some(s => props.selectedPassports.has(s.passport))
)
</script>

<template>
  <div class="rounded-lg border border-neutral-300 dark:border-white/20 shadow-[0_8px_30px_rgba(15,23,42,0.1),0_2px_8px_rgba(15,23,42,0.06)] dark:shadow-[0_12px_40px_rgba(0,0,0,0.7)] overflow-hidden bg-white dark:bg-zinc-900 transition-all">
    <!-- Accordion header with #0B4133 dark green -->
    <div class="w-full flex items-center justify-between bg-[#0B4133] hover:bg-[#0d4e3d] transition-colors select-none">
      <!-- Clickable area to toggle accordion -->
      <button
        type="button"
        class="flex-1 flex items-center gap-2.5 px-4 py-2.5 min-w-0 text-left cursor-pointer focus:outline-none"
        :aria-expanded="isOpen"
        @click="isOpen = !isOpen"
      >
        <component
          :is="groupIcon"
          class="flex-shrink-0 size-4 text-white/90"
        />
        <span class="font-bold text-white text-xs sm:text-sm truncate tracking-wide">
          {{ displayName }}
        </span>
        <span class="flex-shrink-0 inline-flex items-center justify-center min-w-[1.25rem] h-5 px-2 rounded-md text-[10px] font-bold bg-[#FBBF24] text-[#0B4133]">
          {{ students.length }}
        </span>
      </button>

      <!-- Actions area -->
      <div class="flex items-center gap-1.5 pr-3 shrink-0">
        <!-- Refresh all in group -->
        <button
          type="button"
          class="flex items-center justify-center text-white hover:text-white bg-white/10 hover:bg-white/20 transition-colors px-2.5 py-1 rounded-md text-xs font-bold gap-1.5 focus:outline-none cursor-pointer disabled:opacity-50 shadow-2xs"
          title="Check all in group"
          :disabled="groupIsChecking"
          @click.stop="emit('refresh-group', students)"
        >
          <RefreshCw
            class="size-3.5"
            :class="{ 'animate-spin': groupIsChecking }"
          />
          <span class="hidden sm:inline">Check Group</span>
        </button>

        <!-- Toggle Chevron -->
        <button
          type="button"
          class="flex items-center justify-center text-white/90 hover:text-white p-1 rounded-md hover:bg-white/10 transition-transform cursor-pointer"
          @click.stop="isOpen = !isOpen"
        >
          <ChevronDown
            class="size-4 transition-transform duration-200"
            :class="{ 'rotate-180': isOpen }"
          />
        </button>
      </div>
    </div>

    <!-- Collapsible body -->
    <div
      v-show="isOpen"
      class="border-t border-neutral-200 dark:border-white/10"
    >
      <!-- Mobile Cards -->
      <div class="md:hidden space-y-3 p-3">
        <div
          v-for="st in students"
          :key="st.passport"
          class="p-4 space-y-2.5 rounded-md border border-neutral-300/90 dark:border-white/20 bg-white dark:bg-zinc-900 shadow-sm cursor-pointer active:bg-blue-50/60 dark:active:bg-white/[0.03]"
          @click="emit('details', st)"
          @contextmenu.prevent="emit('contextmenu', st, $event)"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="font-bold text-zinc-900 dark:text-white flex items-center gap-1.5 flex-wrap">
                <CopyField :value="st.full_name" label="Copy name" class="text-sm">{{ st.full_name }}</CopyField>
                <button
                  v-if="st.pinned"
                  type="button"
                  class="focus:outline-none cursor-pointer inline-flex items-center"
                  title="Pinned (Click to unpin)"
                  @click.stop="emit('toggle-pin', st)"
                >
                  <Pin class="size-3.5 text-amber-500 fill-amber-500 shrink-0" />
                </button>
              </div>
              <div class="flex flex-wrap items-center gap-1.5 mt-1">
                <VisaTypeBadge :visa-type="st.visa_type" />
                <span v-if="st.student_id || st.id" class="text-xs text-zinc-400 font-mono">#{{ st.student_id || st.id }}</span>
              </div>
            </div>
            <div v-if="showSelectColumn" class="flex items-center justify-center shrink-0 pt-0.5">
              <input
                type="checkbox"
                class="size-6 rounded border-2 border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-2 focus:ring-blue-500 cursor-pointer transition-all"
                :checked="selectedPassports.has(st.passport)"
                @click.stop
                @change="emit('toggle-select', st, ($event.target as HTMLInputElement).checked)"
              />
            </div>
          </div>

          <div class="flex items-center justify-between text-sm">
            <div>
              <CopyField :value="st.passport" label="Copy passport" class="font-bold font-mono text-zinc-700 dark:text-zinc-300">{{ st.passport }}</CopyField>
              <CopyField :value="st.birthday" label="Copy birthday" class="text-xs font-bold font-mono text-zinc-400 mt-0.5">{{ st.birthday }}</CopyField>
            </div>
            <StatusBadge :status="getStudentVisaStatus(st)" />
          </div>

          <div v-if="st.rejection_reason" class="text-[11px] text-rose-500 font-medium truncate">
            Sabab: {{ st.rejection_reason }}
          </div>

          <div class="flex items-center justify-between text-xs text-zinc-400">
            <span v-if="showAppliedColumn">Applied: {{ st.application_date || st.created_at?.slice(0, 10) || '--' }}</span>
            <span v-if="checkingPassports.has(st.passport)" class="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400 font-medium">
              <RefreshCw class="size-3 animate-spin" />Checking...
            </span>
            <span v-else>Checked: {{ formatTimestampCompact(st.last_checked) }}</span>
          </div>

          <div class="grid grid-cols-2 gap-1.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800">
            <button
              type="button"
              :disabled="checkingPassports.has(st.passport)"
              @click.stop="emit('refresh', st)"
              class="h-9 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
            >
              <RefreshCw class="size-3.5" :class="{ 'animate-spin': checkingPassports.has(st.passport) }" />
              Check
            </button>
            <button
              type="button"
              @click.stop="emit('details', st)"
              class="h-9 rounded-md bg-amber-400 hover:bg-amber-500 text-amber-950 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
            >
              <Eye class="size-3.5" />
              View
            </button>
          </div>
        </div>
      </div>

      <!-- Desktop Table -->
      <div class="hidden md:block overflow-x-auto">
        <table class="w-full min-w-[900px] text-sm border-collapse table-fixed">
          <thead class="sticky top-0 z-10 bg-neutral-100/90 dark:bg-[#111928] backdrop-blur">
            <tr class="border-b border-neutral-300 dark:border-white/20 text-left text-[10px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-300">
              <th class="px-4 py-2 min-w-[220px]">Name</th>
              <th class="px-4 py-2 w-36">Passport</th>
              <th class="px-4 py-2 w-44">Status</th>
              <th v-if="showAppliedColumn" class="px-4 py-2 w-28">Applied</th>
              <th v-if="showStatusDateColumn" class="px-4 py-2 w-32">Status Date</th>
              <th v-else class="px-4 py-2 w-44">Checked</th>
              <th v-if="showSelectColumn" class="px-4 py-2 w-24 text-center align-middle">
                <div class="flex items-center justify-center gap-1.5">
                  <span>Select</span>
                  <button
                    v-if="groupHasSelected"
                    type="button"
                    class="p-0.5 rounded-sm text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-zinc-200 dark:hover:bg-white/10 transition-colors"
                    title="Deselect group"
                    @click.stop="emit('deselect-group', students)"
                  >
                    <X class="size-3.5" />
                  </button>
                </div>
              </th>
              <th v-if="showPdfColumn" class="px-4 py-2 w-14 text-center">PDF</th>
              <th class="px-4 py-2 w-32 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-neutral-200 dark:divide-white/10">
            <tr
              v-for="st in students"
              :key="st.passport"
              class="cursor-pointer transition-colors hover:bg-blue-50/60 dark:hover:bg-white/[0.03]"
              :class="{ 'bg-blue-50/30 dark:bg-white/[0.02]': selectedPassports.has(st.passport) }"
              @click="emit('details', st)"
              @contextmenu.prevent="emit('contextmenu', st, $event)"
            >
              <!-- Name Column -->
              <td class="px-4 py-3 align-top">
                <div class="font-bold text-zinc-900 dark:text-white flex items-center gap-1.5 flex-wrap">
                  <CopyField :value="st.full_name" label="Copy name">{{ st.full_name }}</CopyField>
                  <button
                    v-if="st.pinned"
                    type="button"
                    class="focus:outline-none cursor-pointer inline-flex items-center"
                    title="Pinned (Click to unpin)"
                    @click.stop="emit('toggle-pin', st)"
                  >
                    <Pin class="size-3.5 text-amber-500 fill-amber-500 shrink-0" />
                  </button>
                </div>
                <div class="flex flex-wrap items-center gap-1.5 mt-1">
                  <VisaTypeBadge :visa-type="st.visa_type" />
                  <span v-if="st.student_id || st.id" class="text-xs text-zinc-400 font-mono">
                    <CopyField :value="st.student_id || st.id" label="Copy ID">#{{ st.student_id || st.id }}</CopyField>
                  </span>
                  <span v-if="st.application_no" class="text-xs text-zinc-400 font-mono">
                    <CopyField :value="st.application_no" label="Copy app no">{{ st.application_no }}</CopyField>
                  </span>
                </div>
                <p v-if="st.rejection_reason" class="text-[11px] text-rose-500 font-medium mt-0.5 line-clamp-1 max-w-xs">
                  {{ st.rejection_reason }}
                </p>
              </td>

              <!-- Passport Column -->
              <td class="px-4 py-3 align-middle whitespace-nowrap">
                <div class="font-bold text-zinc-900 dark:text-white font-mono text-[13px]">
                  <CopyField :value="st.passport" label="Copy passport">{{ st.passport || '—' }}</CopyField>
                </div>
                <div class="text-xs font-mono text-zinc-400 mt-0.5">
                  <CopyField :value="st.birthday" label="Copy birthday">{{ st.birthday || '—' }}</CopyField>
                </div>
              </td>

              <!-- Status Column -->
              <td class="px-4 py-3 align-middle">
                <StatusBadge :status="getStudentVisaStatus(st)" />
              </td>

              <!-- Applied Column -->
              <td v-if="showAppliedColumn" class="px-4 py-3 align-middle whitespace-nowrap text-zinc-500 dark:text-zinc-400 text-xs">
                {{ st.application_date || st.created_at?.slice(0, 10) || '--' }}
              </td>

              <!-- Status Date / Checked Column -->
              <td v-if="showStatusDateColumn" class="px-4 py-3 align-middle whitespace-nowrap text-zinc-500 dark:text-zinc-400 text-xs">
                {{ st.status_date || '--' }}
              </td>
              <td v-else class="px-4 py-3 align-middle whitespace-nowrap text-xs">
                <span
                  v-if="checkingPassports.has(st.passport)"
                  class="inline-flex items-center gap-1.5"
                >
                  <RefreshCw class="size-3.5 animate-spin text-blue-500" />
                  <span class="text-blue-600 dark:text-blue-400 font-medium">Checking...</span>
                </span>
                <span v-else class="text-zinc-400">
                  {{ formatTimestampCompact(st.last_checked) }}
                </span>
              </td>

              <!-- Select Column -->
              <td v-if="showSelectColumn" class="px-4 py-3 align-middle text-center">
                <div class="flex items-center justify-center h-full">
                  <input
                    type="checkbox"
                    class="size-6 rounded border-2 border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer transition-all hover:border-blue-500"
                    :checked="selectedPassports.has(st.passport)"
                    @click.stop
                    @change="emit('toggle-select', st, ($event.target as HTMLInputElement).checked)"
                  />
                </div>
              </td>

              <!-- PDF Column -->
              <td v-if="showPdfColumn" class="px-4 py-3 align-middle text-center">
                <button
                  v-if="isPdfEligible(st)"
                  type="button"
                  :disabled="downloadingPassports.has(st.passport)"
                  class="text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-200 transition-colors disabled:opacity-40"
                  title="Viza PDF yuklab olish"
                  @click.stop="emit('download-pdf', st)"
                >
                  <FileDown class="size-5" />
                </button>
              </td>

              <!-- Actions Column -->
              <td class="p-0 align-top w-px h-px" style="border-top-width:0">
                <div class="flex items-stretch justify-end h-full">
                  <button
                    type="button"
                    :disabled="checkingPassports.has(st.passport)"
                    class="px-5 py-2 h-full font-bold text-white text-xs bg-blue-600 hover:bg-blue-500 transition-colors rounded-none disabled:opacity-50 flex items-center gap-1.5 whitespace-nowrap"
                    @click.stop="emit('refresh', st)"
                  >
                    <RefreshCw class="size-3.5" :class="{ 'animate-spin': checkingPassports.has(st.passport) }" />
                    Check
                  </button>
                  <button
                    type="button"
                    class="px-4 py-2 h-full bg-amber-400 hover:bg-amber-500 dark:bg-amber-500 dark:hover:bg-amber-400 text-amber-950 dark:text-slate-950 rounded-none transition-colors"
                    aria-label="View details"
                    @click.stop="emit('details', st)"
                  >
                    <Eye class="size-5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
