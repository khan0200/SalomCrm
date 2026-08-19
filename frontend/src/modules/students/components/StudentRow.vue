<script setup lang="ts">
import { computed } from 'vue'
import type { Student } from '@/types'
import { ROW_COLOR_MAP } from '@/types'
import { MoreVertical, Phone, ExternalLink } from 'lucide-vue-next'

const props = defineProps<{
  student: Student
}>()

const emit = defineEmits<{
  (e: 'open-detail', id: string): void
  (e: 'open-actions', student: Student): void
}>()

const rowBgStyle = computed(() => {
  const colorKey = props.student.row_color?.toUpperCase()
  if (!colorKey || !ROW_COLOR_MAP[colorKey]) return {}
  const mapping = ROW_COLOR_MAP[colorKey]
  return {
    backgroundColor: mapping.bg,
    borderLeft: `4px solid ${mapping.ball}`,
  }
})

const getLevelBadgeClass = (level?: string | null) => {
  switch (level) {
    case 'MASTER NO CERTIFICATE': return 'bg-[#00875a] text-white'
    case 'COLLEGE': return 'bg-[#6554c0] text-white'
    case 'BACHELOR': return 'bg-[#0052cc] text-white'
    case 'MASTERS': return 'bg-[#36b37e] text-white'
    case 'LANGUAGE COURSE': return 'bg-[#ffab00] text-gray-900'
    default: return 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300'
  }
}

const certs = computed(() => {
  const list = [
    { type: props.student.language_certificate, score: props.student.certificate_score, color: 'bg-[#de350b]' },
    { type: props.student.language_certificate_2, score: props.student.certificate_score_2, color: 'bg-[#00b8d9]' },
    { type: props.student.language_certificate_3, score: props.student.certificate_score_3, color: 'bg-[#ff5630]' },
  ]
  return list.filter(c => c.type && c.type !== 'NO CERTIFICATE')
})

const universities = computed(() => {
  return [
    props.student.university_1,
    props.student.university_2,
    props.student.university_3,
    props.student.university_4,
    props.student.university_5,
  ].filter(Boolean)
})
</script>

<template>
  <tr
    @click="emit('open-detail', student.id)"
    class="group cursor-pointer border-b border-zinc-200/80 dark:border-zinc-800/80 text-xs transition-colors hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 select-none"
    :style="rowBgStyle"
  >
    <!-- 1. ID Badge -->
    <td class="px-3 py-3 w-16" @click.stop="emit('open-detail', student.id)">
      <div class="inline-flex items-center justify-center px-2 py-1 text-[11px] font-mono font-bold bg-[#007aff] text-white rounded shadow-2xs select-all">
        {{ student.id }}
      </div>
    </td>

    <!-- 2. Full Name & Certificates -->
    <td class="px-3 py-3 max-w-[280px]">
      <div class="font-bold text-zinc-900 dark:text-zinc-100 truncate text-[13px]" :title="student.full_name">
        {{ student.full_name }}
      </div>
      <div v-if="student.korean_name" class="text-[11px] text-zinc-500 font-medium truncate mt-0.5">
        {{ student.korean_name }}
      </div>

      <!-- Language Certificate Dual Pills -->
      <div v-if="certs.length > 0" class="flex flex-wrap gap-1.5 mt-1.5">
        <div
          v-for="(c, idx) in certs"
          :key="idx"
          class="inline-flex items-center text-[9.5px] font-bold rounded overflow-hidden shadow-2xs"
        >
          <span :class="[c.color, 'text-white px-1.5 py-0.5 uppercase']">{{ c.type }}</span>
          <span class="bg-[#0052cc] text-white px-1.5 py-0.5">{{ c.score || '—' }}</span>
        </div>
      </div>
    </td>

    <!-- 3. Phone -->
    <td class="px-3 py-3 whitespace-nowrap text-zinc-600 dark:text-zinc-400 font-mono">
      {{ student.phone1 || '—' }}
    </td>

    <!-- 4. Level Badge -->
    <td class="px-3 py-3 whitespace-nowrap">
      <span
        v-if="student.level"
        class="inline-flex items-center px-2 py-0.8 rounded text-[10px] font-bold tracking-tight uppercase"
        :class="getLevelBadgeClass(student.level)"
      >
        {{ student.level }}
      </span>
      <span v-else class="text-zinc-400">—</span>
    </td>

    <!-- 5. University Stack -->
    <td class="px-3 py-3 max-w-[240px]">
      <ul v-if="universities.length > 0" class="space-y-0.5 text-[11px] leading-snug">
        <li v-for="(uni, idx) in universities" :key="idx" class="flex items-start gap-1 min-w-0">
          <span class="text-zinc-400 shrink-0">•</span>
          <span class="truncate font-medium text-zinc-700 dark:text-zinc-300" :title="String(uni)">{{ uni }}</span>
        </li>
      </ul>
      <span v-else class="text-zinc-400">—</span>
    </td>

    <!-- 6. Actions -->
    <td class="px-3 py-3 whitespace-nowrap text-right" @click.stop>
      <button
        @click="emit('open-actions', student)"
        class="p-1.5 rounded-lg text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
        title="Student Actions"
      >
        <MoreVertical class="w-4 h-4" />
      </button>
    </td>
  </tr>
</template>
