<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Student } from '@/types'
import { ROW_COLOR_MAP } from '@/types'
import { Copy, Check, MoreVertical, Folder, ExternalLink } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  student: Student
}>()

const emit = defineEmits<{
  (e: 'open-detail', id: string): void
  (e: 'open-actions', student: Student): void
}>()

const authStore = useAuthStore()

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

const openGoogleDrive = (url: string) => {
  if (url) window.open(url, '_blank')
}

import { useCustomTags } from '@/composables/useCustomTags'

const { getTagIcon } = useCustomTags()

const rowBgClass = computed(() => {
  const colorKey = props.student.row_color?.toUpperCase()
  if (!colorKey) return 'hover:bg-zinc-50/90 dark:hover:bg-zinc-800/40'
  return 'hover:brightness-90 dark:hover:brightness-110 text-zinc-950 dark:text-white font-medium'
})

const rowBgStyle = computed(() => {
  const colorKey = props.student.row_color?.toUpperCase()
  if (!colorKey || !ROW_COLOR_MAP[colorKey]) return {}
  const mapping = ROW_COLOR_MAP[colorKey]
  return {
    backgroundColor: mapping.bg,
    borderLeft: `5px solid ${mapping.ball}`,
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

        <!-- Archive Badge -->
        <span
          v-if="student.is_deleted"
          class="px-1.5 py-0.5 rounded text-[9.5px] font-bold tracking-wider uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shrink-0"
        >
          Archive
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

        <!-- Google Drive Folder Link (opens in new tab) -->
        <button
          v-if="student.google_drive_url"
          type="button"
          @click.stop="openGoogleDrive(student.google_drive_url)"
          class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25 hover:bg-emerald-500/25 transition-colors cursor-pointer shrink-0"
          title="Open student's Google Drive documents folder"
        >
          <Folder class="w-3 h-3" />
          <ExternalLink class="w-2.5 h-2.5 opacity-80" />
        </button>

        <!-- Copy Full Name Button -->
        <button
          @click.stop="copyName"
          class="p-1 rounded transition-colors cursor-pointer"
          :class="student.row_color ? 'text-zinc-700 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-white' : 'text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'"
          title="Copy full name"
        >
          <Check v-if="isNameCopied" class="w-3.5 h-3.5 text-emerald-600" />
          <Copy v-else class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Tariff subtext -->
      <div
        class="text-[10.5px] uppercase tracking-wider mt-0.5"
        :class="student.row_color ? 'text-zinc-800/90 dark:text-zinc-200 font-bold' : 'text-zinc-400 dark:text-zinc-500 font-semibold'"
      >
        {{ student.tariff || 'NO TARIFF' }}
      </div>
    </td>

    <!-- 3. Phone Numbers Column -->
    <td
      class="px-4 py-3 whitespace-nowrap font-mono text-xs"
      :class="student.row_color ? 'text-zinc-950 dark:text-white font-semibold' : 'text-zinc-700 dark:text-zinc-300'"
    >
      <div class="flex items-center justify-start gap-2">
        <div class="leading-tight space-y-0.5">
          <div>{{ student.phone1 || '—' }}</div>
          <div v-if="student.phone2" :class="student.row_color ? 'text-zinc-800 dark:text-zinc-200 font-medium' : 'text-zinc-500 dark:text-zinc-400'">{{ student.phone2 }}</div>
        </div>

        <button
          @click.stop="copyPhone"
          class="p-1 rounded transition-colors cursor-pointer shrink-0"
          :class="student.row_color ? 'text-zinc-700 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-white' : 'text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'"
          title="Copy ID, name, and phones"
        >
          <Check v-if="isPhoneCopied" class="w-3.5 h-3.5 text-emerald-600" />
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

        <!-- Language Certificate Pills -->
        <div v-if="certs.length > 0" class="flex flex-wrap gap-1">
          <span
            v-for="(c, cIdx) in certs"
            :key="cIdx"
            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-bold shadow-2xs"
            :class="c.isTopik ? 'bg-rose-500 text-white' : 'bg-blue-600 text-white'"
          >
            <span>{{ c.type }}</span>
            <span v-if="c.score" class="opacity-90 font-mono">({{ c.score }})</span>
          </span>
        </div>
      </div>
    </td>

    <!-- 5. University Priority List Column -->
    <td class="px-4 py-3 text-xs max-w-[240px]">
      <ul v-if="universities.length > 0" class="space-y-1">
        <li
          v-for="(uni, uniIdx) in universities"
          :key="uniIdx"
          class="flex items-center gap-1.5 text-[11.5px]"
        >
          <span :class="student.row_color ? 'text-zinc-700 dark:text-zinc-300 font-bold' : 'text-zinc-400'" class="shrink-0">•</span>
          <span
            class="truncate uppercase"
            :class="student.row_color ? 'font-bold text-zinc-950 dark:text-white' : 'font-medium text-zinc-700 dark:text-zinc-300'"
            :title="String(uni)"
          >
            {{ uni }}
          </span>
        </li>
      </ul>
      <span v-else class="text-zinc-400">—</span>
    </td>

    <!-- 6. Actions Column (Tags & Actions Menu Trigger) -->
    <td class="px-4 py-3 text-right whitespace-nowrap" @click.stop>
      <div class="flex items-center justify-end gap-2">
        <!-- Task Tags Container (Icon only with iOS-styled Solid Black Tooltip) -->
        <div v-if="student.task_tags && student.task_tags.length > 0" class="flex items-center gap-1 flex-wrap justify-end shrink-0">
          <div
            v-for="(tag, tagIdx) in student.task_tags"
            :key="tagIdx"
            class="group/tag relative inline-flex items-center justify-center"
          >
            <!-- Tag Icon Badge -->
            <div
              class="inline-flex items-center justify-center w-6 h-6 text-sm bg-zinc-900/10 dark:bg-white/15 border border-zinc-900/20 dark:border-white/25 text-zinc-950 dark:text-zinc-50 rounded-lg shadow-2xs cursor-pointer select-none backdrop-blur-xs hover:scale-110 active:scale-95 transition-all"
            >
              <span class="leading-none select-none">{{ getTagIcon(tag) }}</span>
            </div>

            <!-- iOS Styled Solid Black Tooltip -->
            <div
              class="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 opacity-0 scale-90 translate-y-1 group-hover/tag:opacity-100 group-hover/tag:scale-100 group-hover/tag:translate-y-0 transition-all duration-150 ease-out z-50 flex flex-col items-center select-none"
            >
              <div class="px-2.5 py-1 bg-black text-white text-[11px] font-semibold rounded-md shadow-xl shadow-black/50 whitespace-nowrap tracking-wide flex items-center gap-1">
                <span>{{ tag }}</span>
              </div>
              <!-- Tooltip Arrow Tail -->
              <div class="w-0 h-0 border-x-4 border-x-transparent border-t-4 border-t-black -mt-[0.5px]"></div>
            </div>
          </div>
        </div>

        <!-- Actions Menu Trigger (Hidden for Tenant Staff) -->
        <button
          v-if="authStore.canEdit"
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
