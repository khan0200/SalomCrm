<script setup lang="ts">
import type { Student } from '@/types'
import { Calendar, Clock, AlertTriangle, AlertCircle, CheckCircle, FileText, Loader2, Users } from 'lucide-vue-next'

const props = defineProps<{
  students: Student[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'open-kdb-modal', student: Student): void
  (e: 'open-embassy-drawer', student: Student): void
}>()

const getUrgencyBadge = (s: Student) => {
  if (s.days_left === null || s.days_left === undefined) {
    return { text: 'No Take Date', class: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700' }
  }

  if (s.days_left < 0) {
    return {
      text: `OVERDUE (${Math.abs(s.days_left)}d ago)`,
      class: 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border-rose-300 dark:border-rose-800 animate-pulse font-black'
    }
  } else if (s.days_left <= 3) {
    return {
      text: `CRITICAL (${s.days_left}d left)`,
      class: 'bg-orange-100 text-orange-800 dark:bg-orange-950/80 dark:text-orange-300 border-orange-300 dark:border-orange-800 font-bold'
    }
  } else if (s.days_left <= 7) {
    return {
      text: `URGENT (${s.days_left}d left)`,
      class: 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border-amber-300 dark:border-amber-800 font-bold'
    }
  } else {
    return {
      text: `${s.days_left} days left`,
      class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800 font-bold'
    }
  }
}
</script>

<template>
  <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-xs text-xs select-none">
    <table class="w-full text-left border-collapse">
      <thead>
        <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/60 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          <th class="px-4 py-3 w-16">ID</th>
          <th class="px-4 py-3">Full Name</th>
          <th class="px-4 py-3">KDB Put Date</th>
          <th class="px-4 py-3">KDB Take Date</th>
          <th class="px-4 py-3">Urgency / Days Left</th>
          <th class="px-4 py-3 text-right w-36">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-zinc-100 dark:divide-zinc-850">
        <tr v-if="isLoading">
          <td colspan="6" class="p-12 text-center text-zinc-400">
            <Loader2 class="w-6 h-6 animate-spin mx-auto text-brand-500 mb-2" />
            <span>Loading KDB deposit tracking...</span>
          </td>
        </tr>

        <tr v-else-if="students.length === 0">
          <td colspan="6" class="p-12 text-center text-zinc-400">
            <Users class="w-8 h-8 mx-auto text-zinc-300 dark:text-zinc-700 mb-2" />
            <p class="font-bold text-sm text-zinc-700 dark:text-zinc-300">No students found in KDB view</p>
          </td>
        </tr>

        <tr
          v-else
          v-for="s in students"
          :key="s.id"
          class="hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 transition-colors"
        >
          <td class="px-4 py-3 font-mono font-bold text-brand-600 dark:text-brand-400">{{ s.id }}</td>
          <td class="px-4 py-3">
            <div class="font-bold text-zinc-900 dark:text-zinc-100">{{ s.full_name }}</div>
            <div v-if="s.korean_name" class="text-[11px] text-zinc-400 mt-0.5">{{ s.korean_name }}</div>
          </td>

          <!-- Put Date -->
          <td class="px-4 py-3 font-mono font-medium text-zinc-600 dark:text-zinc-400">
            {{ s.kdb_put_date || '—' }}
          </td>

          <!-- Take Date -->
          <td class="px-4 py-3 font-mono font-bold text-zinc-800 dark:text-zinc-200">
            {{ s.kdb_take_date || '—' }}
          </td>

          <!-- Urgency Badge -->
          <td class="px-4 py-3">
            <span class="inline-flex items-center px-2.5 py-1 rounded-lg border text-[11px]" :class="getUrgencyBadge(s).class">
              {{ getUrgencyBadge(s).text }}
            </span>
          </td>

          <!-- Actions -->
          <td class="px-4 py-3 text-right">
            <div class="flex items-center justify-end gap-1.5">
              <button
                @click="emit('open-kdb-modal', s)"
                class="p-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 font-bold transition-colors cursor-pointer"
                title="Edit KDB Dates"
              >
                <Calendar class="w-3.5 h-3.5" />
              </button>
              <button
                @click="emit('open-embassy-drawer', s)"
                class="px-2.5 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-bold text-[11px] flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                title="Manage Embassy & Sponsor Documents"
              >
                <FileText class="w-3.5 h-3.5" />
                <span>Embassy</span>
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
