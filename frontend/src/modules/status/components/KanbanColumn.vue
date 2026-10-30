<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Student } from '@/types'
import { WORKFLOW_STAGES, type WorkflowStage } from '../utils/statusWorkflow'
import { Users, Filter, X, ChevronsLeftRight, ChevronsRightLeft } from 'lucide-vue-next'
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
  (e: 'open-detail', student: Student): void
  (e: 'update-university', studentId: string, slot: number, name: string): void
  (e: 'update-university-status', studentId: string, slot: number, status: string): void
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

// Each column takes an equal share of the board's width - derived from the
// actual stage count so adding/removing a stage doesn't silently throw the
// widths off (the previous hardcoded `20%` only happened to be correct
// because there were exactly 5 stages). The subtracted gap compensates for
// KanbanBoard's `gap-3` (0.75rem) between columns: with N columns there are
// N-1 gaps to divide out of N columns, i.e. (N-1)/N * 0.75rem per column.
const BOARD_GAP_REM = 0.75
const COLUMN_WIDTH_PERCENT = 100 / WORKFLOW_STAGES.length
const COLUMN_GAP_REM = (BOARD_GAP_REM * (WORKFLOW_STAGES.length - 1)) / WORKFLOW_STAGES.length
const EXPANDED_SCALE = 1.3

const expanded = ref(false)
const isFilterOpen = ref(false)
const selectedUniversityFilters = ref<string[]>([])
const toggleExpand = () => { expanded.value = !expanded.value }

const universityFilters = computed(() => {
  const grouped = new Map<string, Set<string>>()
  for (const student of props.students) {
    for (let slot = 1; slot <= 5; slot++) {
      const name = (student as any)[`university_${slot}`]
      if (typeof name !== 'string' || !name.trim()) continue
      const rawStatus = (student as any)[`university_${slot}_status`]
      const status = typeof rawStatus === 'string' && rawStatus.trim()
        ? rawStatus.trim()
        : 'Not Applied'
      if (!grouped.has(status)) grouped.set(status, new Set())
      grouped.get(status)?.add(name.trim())
    }
  }

  const priority = ['Applied', 'Chosen', 'Accepted', 'Failed', 'Not Applied']
  return [...grouped.entries()]
    .sort(([a], [b]) => {
      const aIndex = priority.findIndex(value => value.toUpperCase() === a.toUpperCase())
      const bIndex = priority.findIndex(value => value.toUpperCase() === b.toUpperCase())
      if (aIndex !== -1 || bIndex !== -1) {
        return (aIndex === -1 ? priority.length : aIndex) - (bIndex === -1 ? priority.length : bIndex)
      }
      return a.localeCompare(b)
    })
    .map(([status, names]) => ({ status, names: [...names].sort((a, b) => a.localeCompare(b)) }))
})

const filteredStudents = computed(() => {
  if (selectedUniversityFilters.value.length === 0) return props.students
  const selected = new Set(selectedUniversityFilters.value)
  return props.students.filter(student =>
    Array.from({ length: 5 }, (_, index) => index + 1)
      .some(slot => {
        const name = (student as any)[`university_${slot}`]
        if (typeof name !== 'string' || !name.trim()) return false
        const rawStatus = (student as any)[`university_${slot}_status`]
        const status = typeof rawStatus === 'string' && rawStatus.trim()
          ? rawStatus.trim()
          : 'Not Applied'
        return selected.has(`${status}::${name.trim()}`)
      })
  )
})

const filterKey = (status: string, name: string) => `${status}::${name}`

const toggleUniversity = (status: string, name: string) => {
  const key = filterKey(status, name)
  selectedUniversityFilters.value = selectedUniversityFilters.value.includes(key)
    ? selectedUniversityFilters.value.filter(value => value !== key)
    : [...selectedUniversityFilters.value, key]
}

const clearFilter = () => {
  selectedUniversityFilters.value = []
}
</script>

<template>
  <!-- min-w-0 is the actual fix for long card text pushing the column wider
       than its calc() width: flex items default to `min-width: auto`, which
       sizes them to fit their content's intrinsic width regardless of the
       explicit `width` style below. Without it, a long unbreakable string
       in a card (e.g. a long university name) would still force this
       column past its budget even though the <select>/<span> elements
       inside KanbanCard.vue have their own `truncate` class - `truncate`
       only clips an element's own rendered box, it doesn't change how the
       browser computes that box's preferred size in a flex container. -->
  <div
    class="flex flex-col min-w-0 max-h-[calc(100vh-220px)] bg-zinc-50/70 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden select-none shrink-0"
    :style="{ width: expanded ? `calc((${COLUMN_WIDTH_PERCENT}% - ${COLUMN_GAP_REM}rem) * ${EXPANDED_SCALE})` : `calc(${COLUMN_WIDTH_PERCENT}% - ${COLUMN_GAP_REM}rem)`, transition: 'width 0.22s cubic-bezier(0.4,0,0.2,1)' }"
  >
    <!-- Column header -->
    <div class="flex items-center justify-between px-3.5 py-3 border-b border-zinc-200 dark:border-zinc-800 shrink-0 bg-white/60 dark:bg-zinc-850/60">
      <h3 class="text-xs font-bold uppercase tracking-wider" :class="STAGE_ACCENT[stageKey]">
        {{ label }} ({{ filteredStudents.length }})
      </h3>

      <!-- Filter and expand controls -->
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          @click="isFilterOpen = true"
          title="Filter by university"
          class="flex items-center justify-center w-5 h-5 rounded-md transition-colors cursor-pointer"
          :class="selectedUniversityFilters.length > 0
            ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40'
            : 'text-zinc-400 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-700'"
        >
          <Filter class="w-3.5 h-3.5" />
        </button>
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

    <!-- University status filter modal -->
    <Teleport to="body">
      <div
        v-if="isFilterOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 dark:bg-black/50 px-4"
        @click.self="isFilterOpen = false"
      >
        <div
          class="w-full max-w-[32rem] max-h-[min(34rem,calc(100vh-2rem))] flex flex-col rounded-2xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-2xl"
          role="dialog"
          aria-modal="true"
          :aria-label="`${label} university filter`"
        >
          <div class="flex items-center justify-between px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
            <h4 class="text-[13px] font-bold text-zinc-800 dark:text-zinc-100">Filter</h4>
            <button
              type="button"
              title="Close filter"
              class="flex items-center justify-center w-7 h-7 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 dark:hover:text-zinc-200 dark:hover:bg-zinc-800 cursor-pointer"
              @click="isFilterOpen = false"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="overflow-y-auto px-4 py-3 space-y-4">
            <section v-for="group in universityFilters" :key="group.status">
              <h5 class="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                {{ group.status }}:
              </h5>
              <label
                v-for="university in group.names"
                :key="`${group.status}-${university}`"
                class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-[11px] text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="selectedUniversityFilters.includes(filterKey(group.status, university))"
                  class="accent-blue-600"
                  @change="toggleUniversity(group.status, university)"
                />
                <span class="truncate">{{ university }}</span>
              </label>
            </section>
            <p v-if="universityFilters.length === 0" class="py-6 text-center text-[11px] text-zinc-400">
              No universities in this column.
            </p>
          </div>

          <div class="flex items-center justify-between gap-2 px-4 py-3 border-t border-zinc-200 dark:border-zinc-800">
            <button
              type="button"
              class="px-3 py-1.5 rounded-lg text-[11px] font-semibold text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer"
              :disabled="selectedUniversityFilters.length === 0"
              @click="clearFilter"
            >
              Clear
            </button>
            <button
              type="button"
              class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-[11px] font-bold text-white cursor-pointer"
              @click="isFilterOpen = false"
            >
              Show ({{ filteredStudents.length }})
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Card list -->
    <div class="flex-1 min-h-0 overflow-y-auto scrollbar-thin px-2.5 py-2.5">
      <div
        v-if="students.length === 0"
        class="flex flex-col items-center justify-center gap-1.5 py-10 text-center"
      >
        <Users class="w-5 h-5 text-zinc-300 dark:text-zinc-700" />
        <p class="text-[11px] text-zinc-400 dark:text-zinc-500 font-medium">No students</p>
      </div>

      <TransitionGroup v-else name="kanban-card" tag="div" class="relative flex flex-col gap-1.5">
        <KanbanCard
          v-for="student in filteredStudents"
          :key="student.id"
          :student="student"
          :stage-key="stageKey"
          :university-options="universityOptions"
          :university-status-options="universityStatusOptions"
          :invoice-select-reset-key="invoiceSelectResetKey"
          @click="(event) => $emit('click-card', student, event)"
          @open-actions="(event) => $emit('open-actions', student, event)"
          @open-embassy="$emit('open-embassy', student)"
          @open-detail="$emit('open-detail', student)"
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
