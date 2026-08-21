<script setup lang="ts">
import { computed } from 'vue'
import { Layers, Building2, Globe, Map } from 'lucide-vue-next'
import type { VisaType } from '@/api/visa'

export type VisaTypeFilter = 'all' | VisaType

const props = defineProps<{
  modelValue: VisaTypeFilter
  counts: Record<VisaTypeFilter, number>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: VisaTypeFilter): void
}>()

const options: { value: VisaTypeFilter; label: string; icon: any }[] = [
  { value: 'all', label: 'All', icon: Layers },
  { value: 'Embassy', label: 'Embassy', icon: Building2 },
  { value: 'E-Visa', label: 'E-Visa', icon: Globe },
  { value: 'Regional', label: 'Regional', icon: Map }
]
</script>

<template>
  <div class="grid grid-cols-4 sm:inline-flex sm:items-center gap-1 p-1 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs w-full sm:w-auto">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="relative flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-1.5 rounded-lg px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-semibold transition-all duration-150 whitespace-nowrap cursor-pointer"
      :class="props.modelValue === opt.value
        ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-white shadow-xs font-bold border border-zinc-300 dark:border-zinc-700'
        : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-850 hover:text-zinc-900 dark:hover:text-zinc-200 border border-transparent'"
      @click="emit('update:modelValue', opt.value)"
    >
      <component
        :is="opt.icon"
        class="hidden sm:block size-3.5 shrink-0 opacity-70"
      />
      <span>{{ opt.label }}</span>
      <span
        class="text-[10px] sm:text-[11px] font-bold rounded-md px-1.5 py-0.5 min-w-[1.2rem] text-center transition-colors"
        :class="props.modelValue === opt.value
          ? 'bg-[#0B4133] text-white'
          : 'bg-zinc-200/80 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-400'"
      >
        {{ props.counts[opt.value] || 0 }}
      </span>
    </button>
  </div>
</template>
