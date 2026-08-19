<script setup lang="ts">
import { ref } from 'vue'
import { Filter, X, RefreshCw, Check } from 'lucide-vue-next'

const props = defineProps<{
  options: {
    tariffs: { name: string; price: number }[]
    levels: string[]
    groups: string[]
    leads: string[]
  }
  selectedTariffs: string[]
  selectedLevels: string[]
  selectedGroups: string[]
  selectedCerts: string[]
  selectedLeads: string[]
}>()

const emit = defineEmits<{
  (e: 'update:selectedTariffs', val: string[]): void
  (e: 'update:selectedLevels', val: string[]): void
  (e: 'update:selectedGroups', val: string[]): void
  (e: 'update:selectedCerts', val: string[]): void
  (e: 'update:selectedLeads', val: string[]): void
  (e: 'reset'): void
}>()

const CERT_OPTIONS = ['TOPIK', 'IELTS', 'TOEFL', 'CEFR', 'SAT', 'SKA', 'NO CERTIFICATE']

const toggleItem = (list: string[], item: string, emitName: any) => {
  const next = list.includes(item) ? list.filter(i => i !== item) : [...list, item]
  emit(emitName, next)
}
</script>

<template>
  <div class="p-4 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4 text-xs select-none">
    <!-- Header with Reset -->
    <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
      <div class="flex items-center gap-2 font-bold text-zinc-900 dark:text-zinc-100">
        <Filter class="w-4 h-4 text-brand-500" />
        <span>Filter Roster</span>
      </div>
      <button
        @click="emit('reset')"
        class="text-[11px] font-semibold text-zinc-500 hover:text-brand-500 dark:text-zinc-400 flex items-center gap-1 cursor-pointer transition-colors"
      >
        <RefreshCw class="w-3 h-3" />
        Reset Filters
      </button>
    </div>

    <!-- Filter Categories Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      <!-- 1. Tariffs -->
      <div>
        <label class="block font-bold text-[10.5px] uppercase tracking-wider text-zinc-400 mb-2">Tariff</label>
        <div class="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
          <button
            v-for="t in options.tariffs"
            :key="t.name"
            @click="toggleItem(selectedTariffs, t.name, 'update:selectedTariffs')"
            class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all cursor-pointer flex items-center gap-1"
            :class="selectedTariffs.includes(t.name) ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-zinc-50 dark:bg-zinc-800/80 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100'"
          >
            <span>{{ t.name }}</span>
            <Check v-if="selectedTariffs.includes(t.name)" class="w-3 h-3" />
          </button>
        </div>
      </div>

      <!-- 2. Education Level -->
      <div>
        <label class="block font-bold text-[10.5px] uppercase tracking-wider text-zinc-400 mb-2">Education Level</label>
        <div class="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
          <button
            v-for="lvl in options.levels"
            :key="lvl"
            @click="toggleItem(selectedLevels, lvl, 'update:selectedLevels')"
            class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all cursor-pointer flex items-center gap-1"
            :class="selectedLevels.includes(lvl) ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-zinc-50 dark:bg-zinc-800/80 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100'"
          >
            <span>{{ lvl }}</span>
            <Check v-if="selectedLevels.includes(lvl)" class="w-3 h-3" />
          </button>
        </div>
      </div>

      <!-- 3. Language Certificates -->
      <div>
        <label class="block font-bold text-[10.5px] uppercase tracking-wider text-zinc-400 mb-2">Language Certificate</label>
        <div class="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
          <button
            v-for="cert in CERT_OPTIONS"
            :key="cert"
            @click="toggleItem(selectedCerts, cert, 'update:selectedCerts')"
            class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all cursor-pointer flex items-center gap-1"
            :class="selectedCerts.includes(cert) ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-zinc-50 dark:bg-zinc-800/80 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100'"
          >
            <span>{{ cert }}</span>
            <Check v-if="selectedCerts.includes(cert)" class="w-3 h-3" />
          </button>
        </div>
      </div>

      <!-- 4. Group -->
      <div>
        <label class="block font-bold text-[10.5px] uppercase tracking-wider text-zinc-400 mb-2">Student Group</label>
        <div class="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
          <button
            v-for="grp in options.groups"
            :key="grp"
            @click="toggleItem(selectedGroups, grp, 'update:selectedGroups')"
            class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all cursor-pointer flex items-center gap-1"
            :class="selectedGroups.includes(grp) ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-zinc-50 dark:bg-zinc-800/80 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100'"
          >
            <span>{{ grp }}</span>
            <Check v-if="selectedGroups.includes(grp)" class="w-3 h-3" />
          </button>
        </div>
      </div>

      <!-- 5. Lead Source -->
      <div>
        <label class="block font-bold text-[10.5px] uppercase tracking-wider text-zinc-400 mb-2">Lead Source</label>
        <div class="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
          <button
            v-for="lead in options.leads"
            :key="lead"
            @click="toggleItem(selectedLeads, lead, 'update:selectedLeads')"
            class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all cursor-pointer flex items-center gap-1"
            :class="selectedLeads.includes(lead) ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-zinc-50 dark:bg-zinc-800/80 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100'"
          >
            <span>{{ lead }}</span>
            <Check v-if="selectedLeads.includes(lead)" class="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
