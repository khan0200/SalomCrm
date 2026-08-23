<script setup lang="ts">
import { computed } from 'vue'
import { BookOpen, X, School, AlertCircle } from 'lucide-vue-next'

export interface UniversityOptionItem {
  slot: number
  name: string
  status?: string | null
  major?: string | null
}

const props = defineProps<{
  isOpen: boolean
  studentId: string | null
  studentName?: string
  pendingStatus: string | null
  assignedUniversities?: UniversityOptionItem[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', university: string): void
}>()

const universitiesList = computed(() => {
  return (props.assignedUniversities || []).filter(u => u && u.name && u.name.trim().length > 0)
})

const handleSelect = (uniName: string) => {
  emit('select', uniName)
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop Overlay -->
    <div
      @click="emit('close')"
      class="fixed inset-0 bg-black/50 transition-opacity duration-200"
    />

    <!-- Modal Panel -->
    <div class="relative w-full max-w-md overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 shadow-2xl z-10 flex flex-col max-h-[85vh] select-none">
      <!-- Header -->
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <School class="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span>Select University for Invoice</span>
        </h3>
        <button
          type="button"
          @click="emit('close')"
          class="rounded-lg p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <p class="text-xs text-zinc-500 dark:text-zinc-400 mb-4">
        Choose which of the student's chosen universities issued this invoice
        <span v-if="studentName" class="font-bold text-zinc-700 dark:text-zinc-300"> ({{ studentName }})</span>:
      </p>

      <!-- Student's Chosen Universities List (1 to 5) -->
      <div v-if="universitiesList.length > 0" class="flex flex-col gap-2.5 my-1">
        <button
          v-for="item in universitiesList"
          :key="item.slot"
          type="button"
          @click="handleSelect(item.name)"
          class="group flex items-center justify-between gap-3 p-3 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-zinc-50/70 dark:bg-zinc-850 hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-950/20 text-xs font-bold text-zinc-900 dark:text-zinc-100 text-left cursor-pointer transition-all duration-150 shadow-2xs hover:scale-[1.01]"
        >
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="flex items-center justify-center w-5 h-5 rounded-md bg-blue-600 text-white text-[10px] font-extrabold shrink-0 shadow-xs">
              {{ item.slot }}
            </span>
            <div class="flex flex-col min-w-0">
              <span class="truncate text-xs font-bold text-zinc-900 dark:text-zinc-100 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                {{ item.name }}
              </span>
              <span v-if="item.major" class="text-[10px] text-zinc-400 font-normal truncate mt-0.5">
                {{ item.major }}
              </span>
            </div>
          </div>

          <span
            v-if="item.status"
            class="px-2 py-0.5 rounded-full text-[9.5px] font-extrabold uppercase shrink-0 border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 shadow-2xs"
          >
            {{ item.status }}
          </span>
        </button>
      </div>

      <!-- Empty State if student has no universities configured -->
      <div v-else class="py-8 px-4 rounded-xl border border-dashed border-zinc-200 dark:border-zinc-800 text-center flex flex-col items-center justify-center gap-2">
        <AlertCircle class="w-7 h-7 text-amber-500 opacity-80" />
        <p class="text-xs font-bold text-zinc-700 dark:text-zinc-300">
          No Universities Configured
        </p>
        <p class="text-[11px] text-zinc-400 max-w-[280px]">
          This student has not selected University 1–5 in Student Details yet. Please add universities in Student Details first.
        </p>
      </div>

      <!-- Footer -->
      <div class="mt-5 pt-3 border-t border-zinc-200 dark:border-zinc-800 flex justify-end">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 text-xs font-semibold border border-zinc-200 dark:border-zinc-700 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all cursor-pointer text-zinc-700 dark:text-zinc-300"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>
