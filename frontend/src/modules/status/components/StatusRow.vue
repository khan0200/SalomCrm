<script setup lang="ts">
import { computed } from 'vue'
import type { Student } from '@/types'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  student: Student
  isKdbMode: boolean
  recentPutDates: string[]
  recentTakeDates: string[]
}>()

const emit = defineEmits<{
  (e: 'click-row', student: Student, event: MouseEvent): void
  (e: 'open-actions', student: Student, event: MouseEvent): void
  (e: 'change-invoice', studentId: string, currentStatus: string | null, newStatus: string): void
  (e: 'change-coa', studentId: string, status: string | null): void
  (e: 'change-put-date', studentId: string, actionOrDate: string): void
  (e: 'change-take-date', studentId: string, actionOrDate: string): void
  (e: 'open-embassy', student: Student): void
}>()

const authStore = useAuthStore()

// Badge classes matching Uniapp2
const getInvoiceBadgeClass = (status: string | null | undefined) => {
  const val = status || 'NOT TAKEN'
  if (val === 'PAID') return 'bg-emerald-600 dark:bg-emerald-500 text-white font-bold border-transparent'
  if (val === 'NOT PAID') return 'bg-amber-500 text-white font-bold border-transparent'
  if (val === 'TAKEN') return 'bg-violet-600 dark:bg-violet-500 text-white font-bold border-transparent'
  if (val === 'CANCELLED') return 'bg-rose-600 dark:bg-rose-500 text-white font-bold border-transparent'
  return 'bg-zinc-400 dark:bg-zinc-500 text-white font-semibold border-transparent'
}

const getCoaBadgeClass = (status: string | null | undefined) => {
  const val = status || 'NOT TAKEN'
  if (val === 'TAKEN') return 'bg-emerald-600 dark:bg-emerald-500 text-white font-bold border-transparent'
  if (val === 'MISTAKE') return 'bg-amber-500 text-white font-bold border-transparent'
  if (val === 'CANCELLED') return 'bg-rose-600 dark:bg-rose-500 text-white font-bold border-transparent'
  return 'bg-zinc-400 dark:bg-zinc-500 text-white font-semibold border-transparent'
}

const getKdbBadgeClass = (val: string | null | undefined) => {
  if (val && val !== 'NO KDB') {
    return 'bg-[#0a5c36] dark:bg-[#084c2c] text-white font-bold border-transparent'
  }
  return 'bg-blue-600 dark:bg-blue-500 text-white font-bold border-transparent'
}

// Remaining Days computation matching Uniapp2
const leftColumnData = computed(() => {
  const takeDateStr = props.student.kdb_take_date
  if (!takeDateStr) {
    return { type: 'not_set', text: 'Take date not set' }
  }

  const takeDate = new Date(takeDateStr)
  if (isNaN(takeDate.getTime())) {
    return { type: 'invalid', text: 'Invalid Date' }
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  takeDate.setHours(0, 0, 0, 0)

  const isBeforeOrOnTakeDate = today.getTime() <= takeDate.getTime()

  if (isBeforeOrOnTakeDate) {
    const diffTime = takeDate.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return { type: 'take_today', text: 'Take Today', isPulse: true, isEmerald: true }
    }
    return { type: 'days_left', text: `${diffDays} ${diffDays === 1 ? 'day' : 'days'} left`, isEmerald: true }
  } else {
    const expirationDate = new Date(takeDate)
    expirationDate.setDate(expirationDate.getDate() + 30)

    const diffTime = expirationDate.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays < 0) {
      return { type: 'expired', text: `Expired (${Math.abs(diffDays)}d ago)`, isRose: true }
    } else if (diffDays === 0) {
      return { type: 'expires_today', text: 'Expires Today', isPulse: true, isRose: true }
    } else {
      return { type: 'expiring_left', text: `${diffDays} ${diffDays === 1 ? 'day' : 'days'} left`, isRose: true }
    }
  }
})

// Row styling based on visa status in Embassy documents panel
const visaRowClass = computed(() => {
  const v = props.student.embassy?.toUpperCase()
  if (v === 'APPROVED') {
    return 'bg-[#a7f3d0]/80 dark:bg-emerald-950/60 hover:bg-[#a7f3d0] dark:hover:bg-emerald-900/70 text-zinc-950 dark:text-zinc-50 font-semibold'
  }
  if (v === 'CANCELLED') {
    return 'bg-[#fecdd3]/80 dark:bg-rose-950/60 hover:bg-[#fecdd3] dark:hover:bg-rose-900/70 text-zinc-950 dark:text-zinc-50 font-semibold'
  }
  return 'bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-850/60'
})

const visaRowStyle = computed(() => {
  const v = props.student.embassy?.toUpperCase()
  if (v === 'APPROVED') {
    return {
      borderLeft: '5px solid #059669'
    }
  }
  if (v === 'CANCELLED') {
    return {
      borderLeft: '5px solid #e11d48'
    }
  }
  return {}
})

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

const certs = computed(() => {
  const list = [
    { type: props.student.language_certificate, score: props.student.certificate_score, isTopik: props.student.language_certificate?.toUpperCase() === 'TOPIK' },
    { type: props.student.language_certificate_2, score: props.student.certificate_score_2, isTopik: props.student.language_certificate_2?.toUpperCase() === 'TOPIK' },
    { type: props.student.language_certificate_3, score: props.student.certificate_score_3, isTopik: props.student.language_certificate_3?.toUpperCase() === 'TOPIK' },
  ]
  return list.filter(c => c.type && c.type !== 'NO CERTIFICATE')
})

const handleRowClick = (e: MouseEvent) => {
  emit('click-row', props.student, e)
}

const handleContextMenu = (e: MouseEvent) => {
  e.preventDefault()
  emit('open-actions', props.student, e)
}
</script>

<template>
  <tr
    @click="handleRowClick"
    @contextmenu="handleContextMenu"
    class="group cursor-pointer transition-colors text-xs select-none border-b border-zinc-100 dark:border-zinc-800/80"
    :class="visaRowClass"
    :style="visaRowStyle"
  >
    <!-- ID Column (Sortable Badge) -->
    <td class="px-2 py-2.5 w-[4.5rem]">
      <div class="inline-flex items-center justify-center px-2.5 py-1 min-w-[36px] h-7 text-[11px] font-mono font-bold bg-[#007aff] text-white rounded-[4px] shadow-2xs select-all">
        {{ student.id }}
      </div>
    </td>

    <!-- Full Name Column -->
    <td class="px-2 py-2.5" :class="isKdbMode ? 'w-[22%]' : 'w-[21%]'">
      <div class="flex items-center gap-1.5 min-w-0">
        <span class="font-bold uppercase tracking-wide text-xs text-zinc-900 dark:text-zinc-100 truncate">
          {{ student.full_name }}
        </span>
        <span
          v-if="student.is_deleted"
          class="px-1.5 py-0.5 rounded text-[9.5px] font-bold tracking-wider uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shrink-0"
        >
          Archive
        </span>
      </div>
    </td>

    <!-- Level & Certificate Split Badge Column (matching /students) -->
    <td class="px-3.5 py-2.5 whitespace-nowrap" :class="isKdbMode ? 'w-[11%]' : 'w-[13%]'">
      <div class="space-y-1">
        <!-- Level Pills -->
        <div class="flex flex-wrap gap-1">
          <span
            v-if="student.level"
            class="inline-flex items-center px-1.5 py-0.5 rounded-full text-[9.5px] font-bold uppercase tracking-wide shadow-2xs"
            :class="getLevelBadgeClass(student.level)"
          >
            {{ student.level }}
          </span>
          <span
            v-if="student.level2"
            class="inline-flex items-center px-1.5 py-0.5 rounded-full text-[9.5px] font-bold uppercase tracking-wide bg-[#ffab00] text-zinc-900 shadow-2xs"
          >
            {{ student.level2 }}
          </span>
          <span
            v-if="!student.level && !student.level2"
            class="text-xs font-semibold text-zinc-400 dark:text-zinc-500"
          >
            —
          </span>
        </div>

        <!-- Language Certificate Pills -->
        <div v-if="certs.length > 0" class="flex flex-wrap gap-1">
          <span
            v-for="(c, cIdx) in certs"
            :key="cIdx"
            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[9.5px] font-bold shadow-2xs"
            :class="c.isTopik ? 'bg-rose-500 text-white' : 'bg-blue-600 text-white'"
          >
            <span>{{ c.type }}</span>
            <span v-if="c.score" class="opacity-90 font-mono">({{ c.score }})</span>
          </span>
        </div>
      </div>
    </td>

    <!-- ── KDB Folder Mode Columns ────────────────────────────────────── -->
    <template v-if="isKdbMode">
      <!-- CoA Column -->
      <td class="px-3 py-2.5 w-[13%] whitespace-nowrap" @click.stop>
        <select
          :value="student.coa || 'NOT TAKEN'"
          :disabled="!authStore.canEdit"
          @change="emit('change-coa', student.id, ($event.target as HTMLSelectElement).value)"
          class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border focus:outline-none transition-all duration-200 select-none shadow-2xs"
          :class="[getCoaBadgeClass(student.coa), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
        >
          <option value="NOT TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Taken</option>
          <option value="TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Taken</option>
          <option value="MISTAKE" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Mistake</option>
          <option value="CANCELLED" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Cancelled</option>
        </select>
      </td>

      <!-- PUT Date Column -->
      <td class="px-3 py-2.5 w-[15%] whitespace-nowrap" @click.stop>
        <div class="flex flex-col items-start justify-center">
          <select
            :value="student.kdb_put_date || 'NO KDB'"
            :disabled="!authStore.canEdit"
            @change="emit('change-put-date', student.id, ($event.target as HTMLSelectElement).value)"
            class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border focus:outline-none transition-all duration-200 select-none shadow-2xs"
            :class="[getKdbBadgeClass(student.kdb_put_date), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <template v-if="student.kdb_put_date">
              <option :value="student.kdb_put_date" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 font-bold">
                {{ student.kdb_put_date }}
              </option>
              <option value="EDIT" class="bg-white dark:bg-zinc-900 text-blue-600 font-bold">Edit Date</option>
              <option value="NO KDB" class="bg-white dark:bg-zinc-900 text-zinc-500">No KDB</option>
              <template v-if="recentPutDates.length > 0">
                <option disabled class="bg-white dark:bg-zinc-900 text-zinc-400 font-semibold">--- Recent ---</option>
                <option
                  v-for="d in recentPutDates.filter(x => x !== student.kdb_put_date)"
                  :key="d"
                  :value="d"
                  class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200"
                >
                  {{ d }}
                </option>
              </template>
            </template>
            <template v-else>
              <option value="NO KDB" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">No KDB</option>
              <option value="KDB DONE" class="bg-white dark:bg-zinc-900 text-blue-600 font-bold">KDB Done</option>
              <template v-if="recentPutDates.length > 0">
                <option disabled class="bg-white dark:bg-zinc-900 text-zinc-400 font-semibold">--- Recent ---</option>
                <option
                  v-for="d in recentPutDates"
                  :key="d"
                  :value="d"
                  class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200"
                >
                  {{ d }}
                </option>
              </template>
            </template>
          </select>
        </div>
      </td>

      <!-- TAKE Date Column -->
      <td class="px-3 py-2.5 w-[15%] whitespace-nowrap" @click.stop>
        <div class="flex flex-col items-start justify-center">
          <select
            :value="student.kdb_take_date || 'NO KDB'"
            :disabled="!authStore.canEdit"
            @change="emit('change-take-date', student.id, ($event.target as HTMLSelectElement).value)"
            class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border focus:outline-none transition-all duration-200 select-none shadow-2xs"
            :class="[getKdbBadgeClass(student.kdb_take_date), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <template v-if="student.kdb_take_date">
              <option :value="student.kdb_take_date" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 font-bold">
                {{ student.kdb_take_date }}
              </option>
              <option value="EDIT" class="bg-white dark:bg-zinc-900 text-blue-600 font-bold">Edit Date</option>
              <option value="NO KDB" class="bg-white dark:bg-zinc-900 text-zinc-500">No KDB</option>
              <template v-if="recentTakeDates.length > 0">
                <option disabled class="bg-white dark:bg-zinc-900 text-zinc-400 font-semibold">--- Recent ---</option>
                <option
                  v-for="d in recentTakeDates.filter(x => x !== student.kdb_take_date)"
                  :key="d"
                  :value="d"
                  class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200"
                >
                  {{ d }}
                </option>
              </template>
            </template>
            <template v-else>
              <option value="NO KDB" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">No KDB</option>
              <option value="KDB DONE" class="bg-white dark:bg-zinc-900 text-blue-600 font-bold">KDB Done</option>
              <template v-if="recentTakeDates.length > 0">
                <option disabled class="bg-white dark:bg-zinc-900 text-zinc-400 font-semibold">--- Recent ---</option>
                <option
                  v-for="d in recentTakeDates"
                  :key="d"
                  :value="d"
                  class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200"
                >
                  {{ d }}
                </option>
              </template>
            </template>
          </select>
        </div>
      </td>

      <!-- LEFT Remaining Days Column -->
      <td class="px-3 py-2.5 w-[25%] whitespace-nowrap" @click.stop>
        <span
          v-if="leftColumnData.type === 'not_set'"
          class="text-[11px] text-zinc-400 dark:text-zinc-500 italic font-semibold select-none"
        >
          {{ leftColumnData.text }}
        </span>
        <span
          v-else-if="leftColumnData.type === 'invalid'"
          class="text-[11px] text-rose-500 font-semibold select-none"
        >
          {{ leftColumnData.text }}
        </span>
        <span
          v-else
          class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase text-white shadow-xs select-none"
          :class="[
            leftColumnData.isEmerald ? 'bg-emerald-600 dark:bg-emerald-700' : 'bg-rose-600 dark:bg-rose-700',
            leftColumnData.isPulse ? 'animate-pulse' : ''
          ]"
        >
          {{ leftColumnData.text }}
        </span>
      </td>
    </template>

    <!-- ── Standard Status Mode Columns ──────────────────────────────── -->
    <template v-else>
      <!-- Invoice Column -->
      <td class="px-3.5 py-2.5 w-[12%] whitespace-nowrap" @click.stop>
        <div class="flex flex-col items-start justify-center">
          <select
            :value="student.invoice || 'NOT TAKEN'"
            :disabled="!authStore.canEdit"
            @change="emit('change-invoice', student.id, student.invoice || 'NOT TAKEN', ($event.target as HTMLSelectElement).value)"
            class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border focus:outline-none transition-all duration-200 select-none shadow-2xs"
            :class="[getInvoiceBadgeClass(student.invoice), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
          >
            <option value="NOT TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Taken</option>
            <option value="TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Taken</option>
            <option value="NOT PAID" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Paid</option>
            <option value="PAID" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Paid</option>
            <option value="CANCELLED" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Cancelled</option>
          </select>
          <span
            v-if="student.invoice_university"
            class="text-[10px] text-zinc-400 dark:text-zinc-500 font-semibold mt-1 block truncate max-w-[110px]"
            :title="student.invoice_university"
          >
            {{ student.invoice_university }}
          </span>
        </div>
      </td>

      <!-- CoA Column -->
      <td class="px-3 py-2.5 w-[9%] whitespace-nowrap" @click.stop>
        <select
          :value="student.coa || 'NOT TAKEN'"
          :disabled="!authStore.canEdit"
          @change="emit('change-coa', student.id, ($event.target as HTMLSelectElement).value)"
          class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border focus:outline-none transition-all duration-200 select-none shadow-2xs"
          :class="[getCoaBadgeClass(student.coa), authStore.canEdit ? 'cursor-pointer' : 'cursor-default opacity-90']"
        >
          <option value="NOT TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Not Taken</option>
          <option value="TAKEN" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Taken</option>
          <option value="MISTAKE" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Mistake</option>
          <option value="CANCELLED" class="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">Cancelled</option>
        </select>
      </td>

      <!-- Embassy Column -->
      <td
        class="px-3 py-2.5 w-[45%] max-w-0"
        @click.stop="emit('open-embassy', student)"
      >
        <div class="flex flex-col gap-1 cursor-pointer hover:opacity-80 transition-opacity">
          <template v-if="(student.embassy_father_docs && student.embassy_father_docs.length > 0) || (student.embassy_mother_docs && student.embassy_mother_docs.length > 0) || (student.embassy_sponsor_notes && student.embassy_sponsor_notes.trim().length > 0)">
            <!-- Father Docs -->
            <div v-if="student.embassy_father_docs && student.embassy_father_docs.length > 0" class="flex flex-wrap items-center gap-1">
              <span class="text-[9px] font-bold text-blue-500 uppercase tracking-wide mr-1 shrink-0">Ota:</span>
              <span
                v-for="(doc, idx) in student.embassy_father_docs"
                :key="idx"
                class="inline-flex items-center px-1.5 py-0.5 rounded-[4px] text-[9.5px] font-bold bg-blue-600 text-white shadow-xs whitespace-nowrap truncate max-w-[100px]"
                :title="doc"
              >
                {{ doc }}
              </span>
            </div>

            <!-- Mother Docs -->
            <div v-if="student.embassy_mother_docs && student.embassy_mother_docs.length > 0" class="flex flex-wrap items-center gap-1 mt-0.5">
              <span class="text-[9px] font-bold text-rose-500 uppercase tracking-wide mr-1 shrink-0">Ona:</span>
              <span
                v-for="(doc, idx) in student.embassy_mother_docs"
                :key="idx"
                class="inline-flex items-center px-1.5 py-0.5 rounded-[4px] text-[9.5px] font-bold bg-rose-600 text-white shadow-xs whitespace-nowrap truncate max-w-[100px]"
                :title="doc"
              >
                {{ doc }}
              </span>
            </div>

            <!-- Sponsor Notes -->
            <div v-if="student.embassy_sponsor_notes && student.embassy_sponsor_notes.trim().length > 0" class="flex items-center gap-1 mt-0.5 text-[9.5px] text-zinc-500 font-medium truncate max-w-[180px]">
              <span class="font-bold text-amber-500 uppercase tracking-wide shrink-0">Homiy:</span>
              <span class="truncate italic">&quot;{{ student.embassy_sponsor_notes }}&quot;</span>
            </div>
          </template>

          <span
            v-else
            class="text-[11px] text-zinc-400 dark:text-zinc-500 italic hover:text-blue-500 font-semibold select-none transition-colors"
          >
            Add documents...
          </span>
        </div>
      </td>
    </template>
  </tr>
</template>
