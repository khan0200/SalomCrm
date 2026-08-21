<script setup lang="ts">
import { computed } from 'vue'
import { Globe, Map, Building2 } from 'lucide-vue-next'
const props = defineProps<{ visaType: string | undefined | null }>()
const isEVisa = computed(() => props.visaType === 'E-Visa')
const isRegional = computed(() => props.visaType === 'Regional')
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold border select-none',
      isEVisa    ? 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20' :
      isRegional ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20' :
                   'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border-zinc-300 dark:border-zinc-700'
    ]"
  >
    <Globe v-if="isEVisa" class="size-2.5" />
    <Map v-else-if="isRegional" class="size-2.5" />
    <Building2 v-else class="size-2.5" />
    {{ isEVisa ? 'E-Visa' : isRegional ? 'Regional' : 'Embassy' }}
  </span>
</template>
