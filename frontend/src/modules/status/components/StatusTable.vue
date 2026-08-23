<script setup lang="ts">
import { computed } from 'vue'
import type { Student } from '@/types'
import StatusRow from './StatusRow.vue'
import { ChevronDown, ChevronUp, Users, Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  students: Student[]
  isLoading: boolean
  isKdbMode: boolean
  sortBy: 'id' | 'left'
  sortOrder: 'asc' | 'desc'
  recentPutDates: string[]
  recentTakeDates: string[]
}>()

const emit = defineEmits<{
  (e: 'toggle-sort', field: 'id' | 'left'): void
  (e: 'click-row', student: Student, event: MouseEvent): void
  (e: 'open-actions', student: Student, event: MouseEvent): void
  (e: 'change-invoice', studentId: string, currentStatus: string | null, newStatus: string): void
  (e: 'change-coa', studentId: string, status: string | null): void
  (e: 'change-put-date', studentId: string, actionOrDate: string): void
  (e: 'change-take-date', studentId: string, actionOrDate: string): void
  (e: 'open-embassy', student: Student): void
}>()
</script>

<template>
  <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-xs">
    <div class="overflow-x-auto scrollbar-thin">
      <table class="w-full table-fixed border-collapse text-left min-w-[700px]">
        <!-- Table Column Widths matching Uniapp2 -->
        <colgroup>
          <col style="width: 4.5rem;" />
          <col :style="{ width: isKdbMode ? '22%' : '22%' }" />
          <col :style="{ width: isKdbMode ? '10%' : '9%' }" />
          <template v-if="isKdbMode">
            <col style="width: 13%;" />
            <col style="width: 15%;" />
            <col style="width: 15%;" />
            <col style="width: 26%;" />
          </template>
          <template v-else>
            <col style="width: 11%;" />
            <col style="width: 9%;" />
            <col style="width: 49%;" />
          </template>
        </colgroup>

        <!-- Table Header -->
        <thead>
          <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/90 dark:bg-zinc-800/60 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 select-none">
            <!-- ID (Sortable) -->
            <th
              @click="emit('toggle-sort', 'id')"
              class="px-2 py-2.5 cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors w-[4.5rem]"
            >
              <div class="flex items-center gap-1">
                <span>ID</span>
                <template v-if="sortBy === 'id'">
                  <ChevronDown v-if="sortOrder === 'asc'" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                  <ChevronUp v-else class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                </template>
                <ChevronDown v-else class="w-3.5 h-3.5 text-zinc-300 dark:text-zinc-600 opacity-40" />
              </div>
            </th>

            <th class="px-2 py-2.5" :class="isKdbMode ? 'w-[22%]' : 'w-[22%]'">Full Name</th>
            <th class="px-3 py-2.5" :class="isKdbMode ? 'w-[10%]' : 'w-[9%]'">Level</th>

            <!-- KDB Mode Headers -->
            <template v-if="isKdbMode">
              <th class="px-3 py-2.5 w-[13%]">CoA</th>
              <th class="px-3 py-2.5 w-[15%]">PUT</th>
              <th class="px-3 py-2.5 w-[15%]">TAKE</th>
              <th
                @click="emit('toggle-sort', 'left')"
                class="px-3 py-2.5 w-[26%] cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <div class="flex items-center gap-1">
                  <span>LEFT</span>
                  <template v-if="sortBy === 'left'">
                    <ChevronDown v-if="sortOrder === 'asc'" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                    <ChevronUp v-else class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                  </template>
                  <ChevronDown v-else class="w-3.5 h-3.5 text-zinc-300 dark:text-zinc-600 opacity-40" />
                </div>
              </th>
            </template>

            <!-- Standard Mode Headers -->
            <template v-else>
              <th class="px-3 py-2.5 w-[11%]">Invoice</th>
              <th class="px-3 py-2.5 w-[9%]">CoA</th>
              <th class="px-3 py-2.5 w-[49%]">Embassy</th>
            </template>
          </tr>
        </thead>

        <!-- Table Body -->
        <tbody class="divide-y divide-zinc-100 dark:divide-zinc-850">
          <tr v-if="isLoading">
            <td :colspan="isKdbMode ? 7 : 6" class="p-12 text-center text-zinc-400">
              <Loader2 class="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
              <span class="text-xs font-medium">Loading status board data...</span>
            </td>
          </tr>

          <tr v-else-if="students.length === 0">
            <td :colspan="isKdbMode ? 7 : 6" class="p-12 text-center text-zinc-400">
              <Users class="w-8 h-8 mx-auto text-zinc-300 dark:text-zinc-700 mb-2" />
              <p class="font-bold text-sm text-zinc-700 dark:text-zinc-300">No students found</p>
              <p class="text-xs text-zinc-400 mt-0.5">Try adjusting your filters or search query.</p>
            </td>
          </tr>

          <StatusRow
            v-else
            v-for="student in students"
            :key="student.id"
            :student="student"
            :is-kdb-mode="isKdbMode"
            :recent-put-dates="recentPutDates"
            :recent-take-dates="recentTakeDates"
            @click-row="(s, e) => emit('click-row', s, e)"
            @open-actions="(s, e) => emit('open-actions', s, e)"
            @change-invoice="(id, cur, next) => emit('change-invoice', id, cur, next)"
            @change-coa="(id, val) => emit('change-coa', id, val)"
            @change-put-date="(id, val) => emit('change-put-date', id, val)"
            @change-take-date="(id, val) => emit('change-take-date', id, val)"
            @open-embassy="s => emit('open-embassy', s)"
          />
        </tbody>
      </table>
    </div>
  </div>
</template>
