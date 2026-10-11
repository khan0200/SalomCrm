<script setup lang="ts">
import { computed } from 'vue'
import type { Student } from '@/types'
import { WORKFLOW_STAGES, calculateStudentWorkflowStage, type WorkflowStage } from '../utils/statusWorkflow'
import KanbanColumn from './KanbanColumn.vue'

const props = defineProps<{
  students: Student[]
  universityOptions: string[]
  universityStatusOptions: string[]
  invoiceSelectResetKey?: number
}>()

const emit = defineEmits<{
  (e: 'click-card', student: Student, event: MouseEvent): void
  (e: 'open-actions', student: Student, event: MouseEvent): void
  (e: 'open-embassy', student: Student): void
  (e: 'open-detail', student: Student): void
  (e: 'update-university', studentId: string, slot: 1 | 2, name: string): void
  (e: 'update-university-status', studentId: string, slot: 1 | 2, status: string): void
  (e: 'update-invoice-status', studentId: string, currentStatus: string | null, newStatus: string): void
  (e: 'update-coa-status', studentId: string, status: string | null): void
  (e: 'update-visa-status', studentId: string, status: string | null): void
  (e: 'revert-to-coa', studentId: string): void
}>()

const studentsByStage = computed(() => {
  const groups: Record<WorkflowStage, Student[]> = {
    student: [], apply: [], invoice: [], coa: [], visa: [],
  }
  for (const student of props.students) {
    groups[calculateStudentWorkflowStage(student)].push(student)
  }
  return groups
})
</script>

<template>
  <div class="overflow-x-auto scrollbar-thin">
    <div class="flex gap-3 pb-2 w-full">
      <KanbanColumn
        v-for="stage in WORKFLOW_STAGES"
        :key="stage.key"
        :stage-key="stage.key"
        :label="stage.label"
        :students="studentsByStage[stage.key]"
        :university-options="universityOptions"
        :university-status-options="universityStatusOptions"
        :invoice-select-reset-key="invoiceSelectResetKey"
        @click-card="(student, event) => emit('click-card', student, event)"
        @open-actions="(student, event) => emit('open-actions', student, event)"
        @open-embassy="(student) => emit('open-embassy', student)"
        @open-detail="(student) => emit('open-detail', student)"
        @update-university="(studentId, slot, name) => emit('update-university', studentId, slot, name)"
        @update-university-status="(studentId, slot, status) => emit('update-university-status', studentId, slot, status)"
        @update-invoice-status="(studentId, currentStatus, newStatus) => emit('update-invoice-status', studentId, currentStatus, newStatus)"
        @update-coa-status="(studentId, status) => emit('update-coa-status', studentId, status)"
        @update-visa-status="(studentId, status) => emit('update-visa-status', studentId, status)"
        @revert-to-coa="(studentId) => emit('revert-to-coa', studentId)"
      />
    </div>
  </div>
</template>
