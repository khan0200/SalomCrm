<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ status: string | undefined | null }>()

function getStatusColor(s: string) {
  const v = (s || '').toLowerCase()
  if (v.includes('approved') || v.includes('visa used') || v.includes('issued')) return 'emerald'
  if (v.includes('reject') || v.includes('cancel') || v.includes('return') || v.includes('expired')) return 'rose'
  if (v.includes('review') || v.includes('processing') || v.includes('simsa')) return 'blue'
  if (v.includes('receiv') || v.includes('jeomsu') || v.includes('submit')) return 'amber'
  if (v.includes('supplem')) return 'orange'
  return 'zinc'
}

function getStatusIcon(s: string) {
  const v = (s || '').toLowerCase()
  if (v.includes('approved') || v.includes('visa used')) return 'check-circle'
  if (v.includes('reject') || v.includes('cancel') || v.includes('return') || v.includes('expired')) return 'x-circle'
  if (v.includes('supplem')) return 'alert-circle'
  if (v.includes('receiv') || v.includes('jeomsu')) return 'archive-restore'
  return 'clock'
}

function getStatusText(s: string) {
  if (!s || s === 'PENDING') return 'Pending'
  return s
}

const color = computed(() => getStatusColor(props.status || ''))
const icon = computed(() => getStatusIcon(props.status || ''))
const text = computed(() => getStatusText(props.status || ''))
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-bold border select-none',
      color === 'emerald' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' :
      color === 'rose'    ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20' :
      color === 'blue'    ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20' :
      color === 'amber'   ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20' :
      color === 'orange'  ? 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20' :
                            'bg-zinc-500/10 text-zinc-500 dark:text-zinc-400 border-zinc-500/20'
    ]"
  >
    <span class="size-1.5 rounded-full bg-current shrink-0" />
    {{ text }}
  </span>
</template>
