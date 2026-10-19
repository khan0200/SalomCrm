<script setup lang="ts">
import { computed } from 'vue'

// Ghost "last edited" date shown in a field card's bottom-right corner, in the
// spirit of the timestamp inside a Telegram message bubble: present enough to
// answer "is this fresh or stale?", quiet enough to ignore while reading.
//
// Renders nothing when the field has no recorded edit. A missing date means
// "never edited since tracking began" - deliberately blank rather than falling
// back to the student's created_at, which would assert a date we do not know.
const props = defineProps<{
  date?: string | null
  // 'light' inverts the colour for the white-on-gradient finance widgets,
  // where the default zinc ghost text would be all but invisible.
  tone?: 'default' | 'light'
}>()

const hasDate = computed(() => !!props.date && String(props.date).trim().length > 0)

// Stored as a plain YYYY-MM-DD string, which is already the display format.
const label = computed(() => String(props.date || '').trim())

const title = computed(() => `Last updated: ${label.value}`)

const toneClass = computed(() =>
  props.tone === 'light' ? 'text-white/55' : 'text-zinc-400/70 dark:text-zinc-500/70'
)
</script>

<template>
  <span
    v-if="hasDate"
    class="pointer-events-none select-none absolute bottom-1 right-2 text-[8.5px] font-medium tabular-nums leading-none"
    :class="toneClass"
    :title="title"
  >
    {{ label }}
  </span>
</template>
