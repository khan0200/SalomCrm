<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Student } from '@/types'
import { ROW_COLOR_MAP } from '@/types'
import { Copy, Check, MoreVertical } from 'lucide-vue-next'

const props = defineProps<{
  student: Student
}>()

const emit = defineEmits<{
  (e: 'open-detail', id: string): void
  (e: 'open-actions', student: Student): void
}>()

const isNameCopied = ref(false)
const isPhoneCopied = ref(false)

const copyName = () => {
  navigator.clipboard.writeText(props.student.full_name)
  isNameCopied.value = true
  setTimeout(() => {
    isNameCopied.value = false
  }, 2000)
}

const copyPhone = () => {
  const lines = [
    `${props.student.id}  ${props.student.full_name}`,
    props.student.phone1,
    props.student.phone2
  ].filter(Boolean)
  navigator.clipboard.writeText(lines.join('\n'))
  isPhoneCopied.value = true
  setTimeout(() => {
    isPhoneCopied.value = false
  }, 2000)
}

const TAG_ICON_MAP: Record<string, string> = {
  'JEONJU REG': '📋',
  'KDB': '💳',
  'Natija kutilmoqda': '⏳',
  'Topik 2': '🏷️',
  'til kursi': '🏷️',
  'BUFS TIL KURSI': '🚩',
  'BUFS APPFEE': '🎫',
  'AeroSpace': '✈️',
  'GIMCHEON OK': '🏷️',
  'WOOSUK APPFEE': '💳',
  'Documents Pending': '📄',
  'Visa Processing': '🎫',
  'Visa Approved': '🛂',
  'Departure': '✈️',
  'Arrived': '📍',
  'Scholarship Awarded': '💎',
}

const getTagIcon = (tag: string) => {
  return TAG_ICON_MAP[tag] || '🏷️'
}

const rowBgClass = computed(() => {
  const colorKey = props.student.row_color?.toUpperCase()
  if (!colorKey) return 'hover:bg-zinc-50/90 dark:hover:bg-zinc-800/40'
  if (colorKey === 'EMERALD') return 'bg-[#8fcc77]/80 hover:bg-[#7ec264] dark:bg-emerald-900/65 dark:hover:bg-emerald-900/80 text-zinc-900 dark:text-zinc-100'
  if (colorKey === 'BLUE') return 'bg-[#82b9e3]/80 hover:bg-[#6aa9da] dark:bg-blue-900/65 dark:hover:bg-blue-900/80 text-zinc-900 dark:text-zinc-100'
  if (colorKey === 'YELLOW') return 'bg-[#ffd24d]/80 hover:bg-[#ffc61a] dark:bg-amber-900/65 dark:hover:bg-amber-900/80 text-zinc-900 dark:text-zinc-100'
  return 'hover:brightness-95 dark:hover:brightness-110'
})

const rowBgStyle = computed(() => {
  const colorKey = props.student.row_color?.toUpperCase()
  if (!colorKey || !ROW_COLOR_MAP[colorKey]) return {}
  const mapping = ROW_COLOR_MAP[colorKey]
  if (['EMERALD', 'BLUE', 'YELLOW'].includes(colorKey)) {
    return { borderLeft: `4px solid ${mapping.ball}` }
  }
  return {
    backgroundColor: mapping.bg,
    borderLeft: `4px solid ${mapping.ball}`,
  }
})

const isDocumentComplete = computed(() => {
  // If passport, photo, and diploma or transcripts uploaded
  const s = props.student
  return !!(s.passport && s.phone1)
})

const getLevelBadgeClass = (level?: string | null) => {
  switch (level?.toUpperCase()) {
    case 'COLLEGE': return 'bg-[#6554c0] text-white'
    case 'LANGUAGE COURSE': return 'bg-[#ffab00] text-zinc-900'
    case 'MASTERS': return 'bg-[#00875a] text-white'
    case 'MASTER NO CERTIFICATE': return 'bg-[#00875a] text-white'
    case 'BACHELOR': return 'bg-[#0052cc] text-white'
    default: return 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300'
  }
}

const certs = computed(() => {
  const list = [
    { type: props.student.language_certificate, score: props.student.certificate_score, isTopik: props.student.language_certificate?.toUpperCase() === 'TOPIK' },
    { type: props.student.language_certificate_2, score: props.student.certificate_score_2, isTopik: props.student.language_certificate_2?.toUpperCase() === 'TOPIK' },
    { type: props.student.language_certificate_3, score: props.student.certificate_score_3, isTopik: props.student.language_certificate_3?.toUpperCase() === 'TOPIK' },
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
    class="group cursor-pointer border-b border-zinc-200/70 dark:border-zinc-800/70 text-xs transition-colors select-none"
    :class="rowBgClass"
    :style="rowBgStyle"
  >
    <!-- 1. ID Badge -->
    <td class="px-4 py-3 w-16" @click.stop="emit('open-detail', student.id)">
      <div class="inline-flex items-center justify-center px-2 py-1 text-[11px] font-mono font-bold bg-[#007aff] text-white rounded-[4px] shadow-2xs select-all min-w-[34px]">
        {{ student.id }}
      </div>
    </td>

    <!-- 2. Full Name & Status Badge & Tariff -->
    <td class="px-4 py-3">
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="font-bold text-zinc-900 dark:text-zinc-100 text-[13px] tracking-wide uppercase">
          {{ student.full_name }}
        </span>

        <!-- Document Status Indicator -->
        <span
          v-if="isDocumentComplete"
          title="All required details / documents completed"
          class="inline-flex items-center justify-center w-4 h-4 rounded-full bg-emerald-500 text-white text-[9px] font-bold shadow-xs shrink-0"
        >
          ✓
        </span>
        <span
          v-else
          title="Missing documents or information"
          class="inline-flex items-center justify-center w-4 h-4 rounded-full bg-amber-500 text-white text-[9px] font-black shadow-xs shrink-0"
        >
          !
        </span>

        <!-- Copy Full Name Button -->
        <button
          @click.stop="copyName"
          class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
          title="Copy full name"
        >
          <Check v-if="isNameCopied" class="w-3.5 h-3.5 text-emerald-500" />
          <Copy v-else class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Tariff subtext -->
      <div class="text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mt-0.5">
        {{ student.tariff || 'NO TARIFF' }}
      </div>
    </td>

    <!-- 3. Phone Numbers Column -->
    <td class="px-4 py-3 whitespace-nowrap font-mono text-xs text-zinc-700 dark:text-zinc-300">
      <div class="flex items-center justify-start gap-2">
        <div class="leading-tight space-y-0.5">
          <div>{{ student.phone1 || '—' }}</div>
          <div v-if="student.phone2" class="text-zinc-500 dark:text-zinc-400">{{ student.phone2 }}</div>
        </div>

        <button
          @click.stop="copyPhone"
          class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer shrink-0"
          title="Copy ID, name, and phones"
        >
          <Check v-if="isPhoneCopied" class="w-3.5 h-3.5 text-emerald-500" />
          <Copy v-else class="w-3.5 h-3.5" />
        </button>
      </div>
    </td>

    <!-- 4. Level & Certificate Split Badge Column -->
    <td class="px-4 py-3 whitespace-nowrap">
      <div class="space-y-1.5">
        <!-- Level Pills -->
        <div class="flex flex-wrap gap-1.5">
          <span
            v-if="student.level"
            class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide shadow-2xs"
            :class="getLevelBadgeClass(student.level)"
          >
            {{ student.level }}
          </span>
          <span
            v-if="student.level2"
            class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-[#ffab00] text-zinc-900 shadow-2xs"
          >
            {{ student.level2 }}
          </span>
        </div>

        <!-- Split Certificate Badges: [TOPIK | 2] -->
        <div v-if="certs.length > 0" class="flex flex-wrap gap-1.5">
          <div
            v-for="(c, idx) in certs"
            :key="idx"
            class="inline-flex items-center text-[9.5px] font-bold rounded overflow-hidden shadow-2xs select-none"
          >
            <span
              class="px-1.5 py-0.5 text-white uppercase tracking-wider"
              :class="c.isTopik ? 'bg-[#de350b]' : 'bg-[#00b8d9]'"
            >
              {{ c.type }}
            </span>
            <span class="bg-[#0052cc] text-white px-1.5 py-0.5">
              {{ c.score || '—' }}
            </span>
          </div>
        </div>
      </div>
    </td>

    <!-- 5. University Choices Column -->
    <td class="px-4 py-3 max-w-[280px]">
      <ul v-if="universities.length > 0" class="space-y-0.5 text-[11px] leading-snug">
        <li v-for="(uni, idx) in universities" :key="idx" class="flex items-start gap-1 min-w-0">
          <span class="text-zinc-400 shrink-0">•</span>
          <span class="truncate font-medium text-zinc-700 dark:text-zinc-300 uppercase" :title="String(uni)">{{ uni }}</span>
        </li>
      </ul>
      <span v-else class="text-zinc-400">—</span>
    </td>

    <!-- 6. Actions Column (Tags & Actions Menu Trigger) -->
    <td class="px-4 py-3 text-right whitespace-nowrap" @click.stop>
      <div class="flex items-center justify-end gap-2">
        <!-- Task Tags Container -->
        <div v-if="student.task_tags && student.task_tags.length > 0" class="flex items-center gap-1.5 flex-nowrap shrink-0">
          <span
            v-for="(tag, tagIdx) in student.task_tags"
            :key="tagIdx"
            class="inline-flex items-center justify-center px-1.5 py-0.5 text-xs bg-white/80 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded shadow-2xs cursor-pointer select-none"
            :title="tag"
          >
            {{ getTagIcon(tag) }}
          </span>
        </div>

        <!-- Actions Menu Trigger -->
        <button
          @click="emit('open-actions', student)"
          class="p-1.5 rounded-lg text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
          title="Student Actions"
        >
          <MoreVertical class="w-4 h-4" />
        </button>
      </div>
    </td>
  </tr>
</template>
