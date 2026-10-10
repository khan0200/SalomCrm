<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import { useStudentDashboardStore } from '@/stores/studentDashboard'

const dashboardStore = useStudentDashboardStore()

const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
  staleTime: 1000 * 60 * 10,
})

const groups = computed<string[]>(() => optionsData.value?.groups || [])
const levels = computed<string[]>(() => optionsData.value?.levels || [])

const toggleGroup = (group: string) => {
  const current = [...dashboardStore.selectedGroups]
  const idx = current.indexOf(group)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(group)
  }
  dashboardStore.selectedGroups = current
}

const toggleLevel = (level: string) => {
  const current = [...dashboardStore.selectedLevels]
  const idx = current.indexOf(level)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(level)
  }
  dashboardStore.selectedLevels = current
}
</script>

<template>
  <div class="flex-1 flex items-center justify-center min-w-0 px-2 overflow-hidden">
    <div class="flex overflow-x-auto scrollbar-none gap-2 py-1 items-center w-full justify-start md:justify-center">
      <!-- Groups -->
      <button
        v-for="g in groups"
        :key="'g-'+g"
        @click="toggleGroup(g)"
        :title="g"
        class="shrink-0 px-2 max-w-[110px] truncate rounded-full text-[9px] font-bold uppercase transition-colors border select-none cursor-pointer tracking-wide"
        :class="dashboardStore.selectedGroups.includes(g) 
          ? 'bg-blue-100 dark:bg-blue-900/40 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300 shadow-xs' 
          : 'bg-white dark:bg-[#111315] border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-900'"
      >
        {{ g }}
      </button>

      <!-- Divider -->
      <div v-if="groups.length > 0 && levels.length > 0" class="w-px h-3.5 bg-zinc-300 dark:bg-zinc-700 shrink-0 mx-0.5"></div>

      <!-- Levels -->
      <button
        v-for="l in levels"
        :key="'l-'+l"
        @click="toggleLevel(l)"
        :title="l"
        class="shrink-0 px-2 max-w-[110px] truncate rounded-full text-[9px] font-bold uppercase transition-colors border select-none cursor-pointer tracking-wide"
        :class="dashboardStore.selectedLevels.includes(l) 
          ? 'bg-purple-100 dark:bg-purple-900/40 border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300 shadow-xs' 
          : 'bg-white dark:bg-[#111315] border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-900'"
      >
        {{ l }}
      </button>
    </div>
  </div>
</template>
