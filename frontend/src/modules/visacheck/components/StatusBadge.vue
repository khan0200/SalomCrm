<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ status: string | undefined | null }>()

function getStatusColor(s: string) {
  const v = (s || '').toLowerCase()
  if (v.includes('approved') || v.includes('visa used') || v.includes('issued')) return 'emerald'
  if (v.includes('reject') || v.includes('cancel') || v.includes('return') || v.includes('expired')) return 'rose'
  if (v.includes('review') || v.includes('processing') || v.includes('simsa') || v.includes('심사중')) return 'blue'
  if (v.includes('receiv') || v.includes('jeomsu') || v.includes('submit')) return 'amber'
  if (v.includes('supplem')) return 'orange'
  return 'zinc'
}

function getStatusText(s: string) {
  if (!s || s === 'PENDING') return 'Pending'
  return s
}

const color = computed(() => getStatusColor(props.status || ''))
const text = computed(() => getStatusText(props.status || ''))
</script>

<template>
  <span
    :class="[
      'inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-[11px] font-bold text-white uppercase select-none shadow-xs whitespace-nowrap leading-tight',
      color === 'emerald' ? 'bg-emerald-600 dark:bg-emerald-600' :
      color === 'rose'    ? 'bg-rose-600 dark:bg-rose-600' :
      color === 'blue'    ? 'bg-blue-600 dark:bg-blue-600' :
      color === 'amber'   ? 'bg-amber-500 dark:bg-amber-600' :
      color === 'orange'  ? 'bg-orange-500 dark:bg-orange-600' :
                            'bg-zinc-500 dark:bg-zinc-600'
    ]"
  >
    {{ text }}
  </span>
</template>

