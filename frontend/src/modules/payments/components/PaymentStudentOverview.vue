<script setup lang="ts">
import type { Student } from '@/types'
import {
  UserX, Plus, ChevronDown, ChevronUp
} from 'lucide-vue-next'
import PaymentStudentKanban from './PaymentStudentKanban.vue'

defineProps<{
  students: Student[]
  totalFilteredCount: number
  isLoading: boolean
  viewMode: 'kanban' | 'table'
  sortOrder: 'asc' | 'desc'
}>()

const emit = defineEmits<{
  (e: 'toggle-sort'): void
  (e: 'open-add-payment', studentId?: string): void
  (e: 'open-detail', studentId: string): void
}>()

function formatAmount(val: number | string | null | undefined) {
  if (val === null || val === undefined) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('uz-UZ').format(Math.round(num || 0))
}
</script>

<template>
  <div class="flex flex-col gap-4 select-none text-xs">
    <!-- Student Count -->
    <div class="text-xs text-zinc-500 dark:text-zinc-400 italic px-1">
      <span v-if="isLoading" class="inline-block h-3 w-24 rounded bg-zinc-200 dark:bg-zinc-800 animate-pulse align-middle" />
      <template v-else>{{ totalFilteredCount }} students</template>
    </div>

    <!-- ── Loading Skeleton: Kanban View ───────────────────────────────────── -->
    <div v-if="isLoading && viewMode === 'kanban'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <div
        v-for="i in 9"
        :key="i"
        class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] p-4 shadow-sm animate-pulse"
      >
        <div class="flex items-start justify-between gap-2 mb-3">
          <div class="h-3.5 w-1/2 rounded bg-zinc-200 dark:bg-zinc-800" />
          <div class="h-3 w-12 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
        <div class="h-3 w-1/3 rounded bg-zinc-100 dark:bg-zinc-800/70 mb-4" />
        <div class="flex items-center gap-2 mb-3">
          <div class="h-5 w-20 rounded bg-zinc-100 dark:bg-zinc-800/70" />
          <div class="h-5 w-16 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
        <div class="pt-3 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between">
          <div class="h-3 w-24 rounded bg-zinc-100 dark:bg-zinc-800/70" />
          <div class="h-3 w-14 rounded bg-zinc-100 dark:bg-zinc-800/70" />
        </div>
      </div>
    </div>

    <!-- ── Loading Skeleton: Table View ────────────────────────────────────── -->
    <div v-else-if="isLoading" class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60 text-[12px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300 select-none">
              <th class="px-5 py-3.5 w-[30%]">Student / Full Name</th>
              <th class="px-5 py-3.5 w-[14%]">Group</th>
              <th class="px-5 py-3.5 w-[22%]">Tariff</th>
              <th class="px-5 py-3.5 w-[18%]">Balance</th>
              <th class="px-5 py-3.5 w-[12%]">Discount</th>
              <th class="px-5 py-3.5 text-center w-24">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
            <tr v-for="i in 12" :key="i" class="animate-pulse">
              <td class="px-5 py-3.5">
                <div class="h-3.5 w-3/5 rounded bg-zinc-200 dark:bg-zinc-800 mb-1.5" />
                <div class="h-2.5 w-1/3 rounded bg-zinc-100 dark:bg-zinc-800/70" />
              </td>
              <td class="px-5 py-3.5"><div class="h-3 w-16 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-5 py-3.5"><div class="h-3 w-24 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-5 py-3.5"><div class="h-3 w-20 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-5 py-3.5"><div class="h-3 w-14 rounded bg-zinc-100 dark:bg-zinc-800/70" /></td>
              <td class="px-5 py-3.5">
                <div class="flex items-center justify-center gap-1.5">
                  <div class="h-6 w-6 rounded-md bg-zinc-100 dark:bg-zinc-800/70" />
                  <div class="h-6 w-6 rounded-md bg-zinc-100 dark:bg-zinc-800/70" />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── 1. Kanban View (Payment Status Board: NEW / Qarzdor / FULL / B2B) ── -->
    <PaymentStudentKanban
      v-else-if="viewMode === 'kanban'"
      :students="students"
      @open-add-payment="(id) => emit('open-add-payment', id)"
      @open-detail="(id) => emit('open-detail', id)"
    />

    <!-- ── 2. Table View (UniApp2 Table 1-to-1) ────────────────────────────── -->
    <div v-else class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60 text-[12px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300 select-none">
              <!-- Student / Full Name (Sortable) -->
              <th
                @click="emit('toggle-sort')"
                class="px-5 py-3.5 cursor-pointer select-none hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors w-[30%]"
              >
                <span class="flex items-center gap-1.5 font-bold text-[12.5px] uppercase tracking-wider text-zinc-700 dark:text-zinc-200">
                  Student / Full Name
                  <ChevronDown v-if="sortOrder === 'asc'" class="h-3.5 w-3.5 text-blue-600" />
                  <ChevronUp v-else class="h-3.5 w-3.5 text-blue-600" />
                </span>
              </th>
              <th class="px-5 py-3.5 w-[14%]">Group</th>
              <th class="px-5 py-3.5 w-[22%]">Tariff</th>
              <th class="px-5 py-3.5 w-[18%]">Balance</th>
              <th class="px-5 py-3.5 w-[12%]">Discount</th>
              <th class="px-5 py-3.5 text-center w-24">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800 text-[13.5px]">
            <tr
              v-for="student in students"
              :key="student.id"
              class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors text-zinc-800 dark:text-zinc-200"
            >
              <!-- Student: Full Name on top, ID below -->
              <td class="px-5 py-3">
                <div class="flex flex-col gap-0.5">
                  <div class="flex items-center gap-2">
                    <span class="font-bold uppercase tracking-wide text-zinc-900 dark:text-zinc-100 truncate">
                      {{ student.full_name }}
                    </span>
                    <span
                      v-if="student.is_permanently_deleted"
                      class="px-1.5 py-0.5 rounded text-[9.5px] font-bold tracking-wider uppercase bg-rose-600/15 text-rose-700 dark:text-rose-400 border border-rose-600/25 shrink-0"
                    >
                      Permanently Deleted
                    </span>
                    <span
                      v-else-if="student.is_deleted"
                      class="px-1.5 py-0.5 rounded text-[9.5px] font-bold tracking-wider uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 shrink-0"
                    >
                      Archive
                    </span>
                  </div>
                  <div class="flex items-center gap-1">
                    <span class="font-mono text-[11px] font-bold text-[#0066cc] dark:text-blue-400 tracking-wider">
                      {{ student.id }}
                    </span>
                  </div>
                </div>
              </td>

              <!-- Group -->
              <td class="px-5 py-3.5 text-[13.5px] font-medium text-zinc-500 dark:text-zinc-400 uppercase">
                {{ student.student_group || '—' }}
              </td>

              <!-- Tariff -->
              <td class="px-5 py-3.5">
                <span
                  v-if="student.tariff"
                  class="inline-flex px-2 py-0.5 rounded-[4px] text-[12px] font-bold bg-[#10b981] text-white uppercase shadow-2xs"
                >
                  {{ student.tariff }}
                </span>
                <span v-else class="text-zinc-400">—</span>
              </td>

              <!-- Balance -->
              <td class="px-5 py-3.5 font-mono font-bold">
                <span
                  class="inline-flex px-2 py-0.5 rounded-[4px] text-[12.5px] font-bold text-white shadow-2xs"
                  :class="(Number(student.balance) || 0) < 0 ? 'bg-[#ef4444]' : 'bg-[#10b981]'"
                >
                  {{ (Number(student.balance) || 0) > 0 ? '+' : '' }}{{ formatAmount(student.balance) }} UZS
                </span>
              </td>

              <!-- Discount -->
              <td class="px-5 py-3.5">
                <span
                  v-if="student.discount !== null && student.discount !== undefined && Number(student.discount) > 0"
                  class="inline-flex px-2 py-0.5 rounded-[4px] text-[12px] font-bold font-mono bg-[#be185d] text-white shadow-2xs"
                >
                  {{ formatAmount(student.discount) }} UZS
                </span>
                <span v-else class="text-zinc-400">—</span>
              </td>

              <!-- Actions -->
              <td class="px-5 py-3.5 text-center">
                <button
                  type="button"
                  @click="emit('open-add-payment', student.id)"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-all cursor-pointer shadow-2xs"
                >
                  <Plus class="h-3.5 w-3.5 stroke-[2.5]" />
                  <span>Pay</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="students.length === 0 && !isLoading"
      class="rounded-xl border border-zinc-200 dark:border-zinc-800 border-dashed bg-white dark:bg-[#111315] py-16 px-6 text-center space-y-3"
    >
      <div class="w-14 h-14 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center mx-auto text-zinc-400">
        <UserX class="h-7 w-7" />
      </div>
      <p class="font-bold text-sm text-zinc-800 dark:text-zinc-200">No students found</p>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        No students match your search or filters. Try adjusting them.
      </p>
    </div>
  </div>
</template>
