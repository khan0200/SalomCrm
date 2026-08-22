<script setup lang="ts">
import { ref } from 'vue'
import { Copy, Check } from 'lucide-vue-next'

const props = defineProps<{
  value: string | undefined | null
  copyId?: string
  label?: string
}>()

const copied = ref(false)
let timer: any = null

async function copy() {
  if (!props.value) return
  try {
    await navigator.clipboard.writeText(props.value)
    copied.value = true
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => { copied.value = false }, 1800)
  } catch { /* ignore */ }
}
</script>

<template>
  <button
    type="button"
    class="group/copy inline-flex items-center gap-1 text-left cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
    :title="label || `Copy ${value}`"
    @click.stop="copy"
  >
    <slot>{{ value }}</slot>
    <Check v-if="copied" class="size-3 text-emerald-500 shrink-0 transition-all" />
    <Copy v-else class="size-3 text-zinc-400 group-hover/copy:text-blue-500 dark:text-zinc-500 dark:group-hover/copy:text-blue-400 shrink-0 transition-colors" />
  </button>
</template>
