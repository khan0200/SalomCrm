<script setup lang="ts">
import type { Student } from '@/types'
import StudentRow from './StudentRow.vue'
import { ChevronDown, ChevronUp, Users, Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  students: Student[]
  isLoading: boolean
  sortOrder: 'asc' | 'desc'
}>()

const emit = defineEmits<{
  (e: 'toggle-sort'): void
  (e: 'open-detail', id: string): void
  (e: 'open-actions', student: Student): void
}>()
</script>

<template>
  <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-xs">
    <div class="overflow-x-auto scrollbar-thin">
      <table class="w-full text-left border-collapse min-w-[900px]">
        <!-- Table Header -->
        <thead>
          <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/90 dark:bg-zinc-800/60 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 select-none">
            <!-- ID (Sortable) -->
            <th
              @click="emit('toggle-sort')"
              class="px-4 py-3 cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors w-16"
            >
              <div class="flex items-center gap-1 text-blue-600 dark:text-blue-400">
                <span>ID</span>
                <ChevronDown v-if="sortOrder === 'asc'" class="w-3.5 h-3.5" />
                <ChevronUp v-else class="w-3.5 h-3.5" />
              </div>
            </th>
            <th class="px-4 py-3 w-[36%]">FULL NAME</th>
            <th class="px-4 py-3 w-[15%]">PHONE</th>
            <th class="px-4 py-3 w-[18%]">LEVEL</th>
            <th class="px-4 py-3 w-[25%]">UNIVERSITY</th>
            <th class="px-4 py-3 text-right w-[6%]">ACTIONS</th>
          </tr>
        </thead>

        <!-- Table Body -->
        <tbody class="divide-y divide-zinc-100 dark:divide-zinc-850">
          <tr v-if="isLoading">
            <td colspan="6" class="p-12 text-center text-zinc-400">
              <Loader2 class="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
              <span class="text-xs font-medium">Loading roster data...</span>
            </td>
          </tr>

          <tr v-else-if="students.length === 0">
            <td colspan="6" class="p-12 text-center text-zinc-400">
              <Users class="w-8 h-8 mx-auto text-zinc-300 dark:text-zinc-700 mb-2" />
              <p class="font-bold text-sm text-zinc-700 dark:text-zinc-300">No students found</p>
              <p class="text-xs text-zinc-400 mt-0.5">Try adjusting your filters or search query.</p>
            </td>
          </tr>

          <StudentRow
            v-else
            v-for="student in students"
            :key="student.id"
            :student="student"
            @open-detail="id => emit('open-detail', id)"
            @open-actions="s => emit('open-actions', s)"
          />
        </tbody>
      </table>
    </div>
  </div>
</template>
