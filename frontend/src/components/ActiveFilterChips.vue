<script setup lang="ts">
import { X } from 'lucide-vue-next'
import { useStudentDashboardStore } from '@/stores/studentDashboard'

// Single source of truth for the "Active Filters" chip row - previously
// copy-pasted near-identically into DocumentsPage, StudentsPage and
// StatusPage (one chip block per filter dimension in each), so a sizing/
// spacing fix had to be applied three times by hand. All three pages read
// the same dashboardStore filters, so this binds to it directly with no
// props needed.
const dashboardStore = useStudentDashboardStore()
</script>

<template>
  <div v-if="dashboardStore.activeFiltersCount > 0" class="flex flex-wrap items-center gap-1 px-1 select-none text-[10px] -mt-2 -mb-1">
    <span class="font-bold text-zinc-500 mr-1">Active Filters:</span>

    <span
      v-for="t in dashboardStore.selectedTariffs"
      :key="`t-${t}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-full font-medium"
    >
      <span>Tariff: {{ t === 'NO_TARIFF' ? 'No Tariff' : t }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedTariffs = dashboardStore.selectedTariffs.filter(x => x !== t)" />
    </span>

    <span
      v-for="l in dashboardStore.selectedLevels"
      :key="`l-${l}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 rounded-full font-medium"
    >
      <span>Level: {{ l === 'NO_LEVEL' ? 'No Level' : l }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedLevels = dashboardStore.selectedLevels.filter(x => x !== l)" />
    </span>

    <span
      v-for="g in dashboardStore.selectedGroups"
      :key="`g-${g}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 rounded-full font-medium"
    >
      <span>Group: {{ g === 'NO_GROUP' ? 'No Group' : g }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedGroups = dashboardStore.selectedGroups.filter(x => x !== g)" />
    </span>

    <span
      v-for="b in dashboardStore.selectedBranches"
      :key="`b-${b}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 rounded-full font-medium"
    >
      <span>Branch: {{ b === 'NO_BRANCH' ? 'No Branch' : b }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedBranches = dashboardStore.selectedBranches.filter(x => x !== b)" />
    </span>

    <span
      v-for="c in dashboardStore.selectedCerts"
      :key="`c-${c}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 rounded-full font-medium"
    >
      <span>Cert: {{ c }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedCerts = dashboardStore.selectedCerts.filter(x => x !== c)" />
    </span>

    <span
      v-for="s in dashboardStore.selectedScores"
      :key="`s-${s}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 rounded-full font-medium"
    >
      <span>Score: {{ s }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedScores = dashboardStore.selectedScores.filter(x => x !== s)" />
    </span>

    <span
      v-for="m in dashboardStore.selectedMissingDocs"
      :key="`m-${m}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-800 rounded-full font-medium"
    >
      <span>Missing: {{ m }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedMissingDocs = dashboardStore.selectedMissingDocs.filter(x => x !== m)" />
    </span>

    <span
      v-for="tg in dashboardStore.selectedTags"
      :key="`tg-${tg}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-full font-medium"
    >
      <span>Tag: {{ tg }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedTags = dashboardStore.selectedTags.filter(x => x !== tg)" />
    </span>

    <span
      v-for="lb in dashboardStore.selectedLeads"
      :key="`lb-${lb}`"
      class="inline-flex items-center gap-1 px-1.5 py-0 bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 rounded-full font-medium"
    >
      <span>Lead: {{ lb === 'NO_LEADBY' ? 'No Lead by' : lb }}</span>
      <X class="w-2.5 h-2.5 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedLeads = dashboardStore.selectedLeads.filter(x => x !== lb)" />
    </span>

    <button
      type="button"
      @click="dashboardStore.resetAllFilters()"
      class="text-[10px] font-bold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors ml-1 cursor-pointer"
    >
      Clear All
    </button>
  </div>
</template>
