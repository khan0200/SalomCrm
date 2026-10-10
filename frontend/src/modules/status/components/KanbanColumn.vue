<script setup lang="ts">
import { ref } from 'vue'
import type { Student } from '@/types'
import type { WorkflowStage } from '../utils/statusWorkflow'
import { Users, ChevronsLeftRight, ChevronsRightLeft } from 'lucide-vue-next'
import KanbanCard from './KanbanCard.vue'

const props = defineProps<{
  stageKey: WorkflowStage
  label: string
  students: Student[]
  universityOptions: string[]
  universityStatusOptions: string[]
  invoiceSelectResetKey?: number
}>()

defineEmits<{
  (e: 'click-card', student: Student, event: MouseEvent): void
  (e: 'open-actions', student: Student, event: MouseEvent): void
  (e: 'open-embassy', student: Student): void
  (e: 'update-university', studentId: string, slot: 1 | 2, name: string): void
  (e: 'update-university-status', studentId: string, slot: 1 | 2, status: string): void
  (e: 'update-invoice-status', studentId: string, currentStatus: string | null, newStatus: string): void
  (e: 'update-coa-status', studentId: string, status: string | null): void
  (e: 'update-visa-status', studentId: string, status: string | null): void
  (e: 'revert-to-coa', studentId: string): void
}>()

const STAGE_ACCENT: Record<WorkflowStage, string> = {
  student: 'text-zinc-500 dark:text-zinc-400',
  apply: 'text-blue-600 dark:text-blue-400',
  invoice: 'text-violet-600 dark:text-violet-400',
  coa: 'text-amber-600 dark:text-amber-400',
  visa: 'text-emerald-600 dark:text-emerald-400',
}

const BASE_WIDTH = 260
const EXPANDED_WIDTH = 340

const expanded = ref(false)
const toggleExpand = () => { expanded.value = !expanded.value }
</script>

<template>
  <div
    class="flex flex-col flex-none max-h-[calc(100vh-220px)] bg-zinc-50/70 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden select-none"
    :style="{ width: (expanded ? EXPANDED_WIDTH : BASE_WIDTH) + 'px', transition: 'width 0.22s cubic-bezier(0.4,0,0.2,1)' }"
  >
    <!-- Column header -->
    <div class="flex items-center justify-between px-3.5 py-3 border-b border-zinc-200 dark:border-zinc-800 shrink-0 bg-white/60 dark:bg-zinc-850/60">
      <h3 class="text-xs font-bold uppercase tracking-wider" :class="STAGE_ACCENT[stageKey]">
        {{ label }}
      </h3>

      <!-- Count badge + expand button -->
      <div class="flex items-center gap-1.5">
        <span class="text-[10.5px] font-bold text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full">
          {{ students.length }}
        </span>
        <button
          type="button"
          @click="toggleExpand"
          :title="expanded ? 'Collapse column' : 'Expand column'"
          class="flex items-center justify-center w-5 h-5 rounded-md text-zinc-400 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
        >
          <ChevronsRightLeft v-if="expanded" class="w-3.5 h-3.5" />
          <ChevronsLeftRight v-else class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Card list -->
    <div class="flex-1 min-h-0 overflow-y-auto scrollbar-thin px-2.5 py-2.5">
      <div
        v-if="students.length === 0"
        class="flex flex-col items-center justify-center gap-1.5 py-10 text-center"
      >
        <Users class="w-5 h-5 text-zinc-300 dark:text-zinc-700" />
        <p class="text-[11px] text-zinc-400 dark:text-zinc-500 font-medium">No students</p>
      </div>

      <TransitionGroup v-else name="kanban-card" tag="div" class="flex flex-col gap-1.5">
        <KanbanCard
          v-for="student in students"
          :key="student.id"
          :student="student"
          :stage-key="stageKey"
          :university-options="universityOptions"
          :university-status-options="universityStatusOptions"
          :invoice-select-reset-key="invoiceSelectResetKey"
          @click="(event) => $emit('click-card', student, event)"
          @open-actions="(event) => $emit('open-actions', student, event)"
          @open-embassy="$emit('open-embassy', student)"
          @update-university="(slot, name) => $emit('update-university', student.id, slot, name)"
          @update-university-status="(slot, status) => $emit('update-university-status', student.id, slot, status)"
          @update-invoice-status="(currentStatus, newStatus) => $emit('update-invoice-status', student.id, currentStatus, newStatus)"
          @update-coa-status="(status) => $emit('update-coa-status', student.id, status)"
          @update-visa-status="(status) => $emit('update-visa-status', student.id, status)"
          @revert-to-coa="() => $emit('revert-to-coa', student.id)"
        />
      </TransitionGroup>
    </div>
  </div>
</template>
