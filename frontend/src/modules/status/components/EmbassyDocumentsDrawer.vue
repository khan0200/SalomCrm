<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Student } from '@/types'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import {
  FileText, ShieldCheck, Check, Save, User, Building, AlertCircle
} from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  student: Student | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: any): void
}>()

const FATHER_DOCS_OPTIONS = [
  'RASMIY ISH HAQQI', 'KADASTR', 'KADASTR X2', 'DO\'KON', 'TEX.PASSPORT', 'BANKSHOT'
]

const MOTHER_DOCS_OPTIONS = [
  'RASMIY ISH HAQQI', 'KADASTR', 'TEX.PASSPORT', 'BANKSHOT'
]

const VISA_STATUS_OPTIONS = ['PENDING', 'SUBMITTED', 'APPROVED', 'REJECTED', 'NOT APPLIED']

const fatherDocs = ref<string[]>([])
const motherDocs = ref<string[]>([])
const sponsorNotes = ref('')
const embassyStatus = ref('PENDING')
const isStatusHidden = ref(false)
const isSaving = ref(false)

watch(() => props.student, (newVal) => {
  if (newVal) {
    fatherDocs.value = [...(newVal.embassy_father_docs || [])]
    motherDocs.value = [...(newVal.embassy_mother_docs || [])]
    sponsorNotes.value = newVal.embassy_sponsor_notes || ''
    embassyStatus.value = newVal.embassy || 'PENDING'
    isStatusHidden.value = !!newVal.status_hidden
  }
}, { immediate: true })

const toggleDoc = (list: string[], doc: string, targetRef: any) => {
  if (list.includes(doc)) {
    targetRef.value = list.filter(d => d !== doc)
  } else {
    targetRef.value = [...list, doc]
  }
}

const handleSave = () => {
  isSaving.value = true
  emit('save', {
    embassy_father_docs: fatherDocs.value,
    embassy_mother_docs: motherDocs.value,
    embassy_sponsor_notes: sponsorNotes.value.trim() || null,
    embassy: embassyStatus.value,
    status_hidden: isStatusHidden.value,
  })
  isSaving.value = false
}
</script>

<template>
  <BaseDrawer
    :is-open="isOpen"
    :title="`Embassy Documents & Visa: ${student?.full_name || ''}`"
    :subtitle="`ID: ${student?.id || ''} &bull; Manage financial sponsorship documents for embassy submission`"
    width="max-w-2xl"
    @close="emit('close')"
  >
    <div v-if="student" class="space-y-6 text-xs select-none">
      <!-- Top Visa Status & Hide Switch -->
      <div class="p-4 rounded-2xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <label class="block text-[10.5px] font-bold uppercase tracking-wider text-zinc-400 mb-1">Embassy Visa Status</label>
          <select
            v-model="embassyStatus"
            class="px-3 py-1.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-bold text-zinc-800 dark:text-zinc-200 outline-none cursor-pointer"
          >
            <option v-for="s in VISA_STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <input
            id="statusHiddenCheck"
            v-model="isStatusHidden"
            type="checkbox"
            class="w-4 h-4 rounded text-brand-500 focus:ring-brand-500 cursor-pointer"
          />
          <label for="statusHiddenCheck" class="font-bold text-zinc-700 dark:text-zinc-300 cursor-pointer">
            Hide from Active Status Board
          </label>
        </div>
      </div>

      <!-- 1. Father Sponsor Documents -->
      <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-3">
        <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <User class="w-4 h-4 text-blue-500" />
          <span>Father's Sponsorship Documents (Ota Hujjatlari)</span>
        </h3>

        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
          <button
            v-for="doc in FATHER_DOCS_OPTIONS"
            :key="doc"
            type="button"
            @click="toggleDoc(fatherDocs, doc, fatherDocs)"
            class="p-2.5 rounded-xl border text-xs font-bold transition-all text-left flex items-center justify-between cursor-pointer"
            :class="fatherDocs.includes(doc) ? 'bg-blue-500 text-white border-blue-500 shadow-xs' : 'bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100'"
          >
            <span>{{ doc }}</span>
            <Check v-if="fatherDocs.includes(doc)" class="w-3.5 h-3.5 shrink-0" />
          </button>
        </div>
      </div>

      <!-- 2. Mother Sponsor Documents -->
      <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-3">
        <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <User class="w-4 h-4 text-rose-500" />
          <span>Mother's Sponsorship Documents (Ona Hujjatlari)</span>
        </h3>

        <div class="grid grid-cols-2 sm:grid-cols-2 gap-2.5">
          <button
            v-for="doc in MOTHER_DOCS_OPTIONS"
            :key="doc"
            type="button"
            @click="toggleDoc(motherDocs, doc, motherDocs)"
            class="p-2.5 rounded-xl border text-xs font-bold transition-all text-left flex items-center justify-between cursor-pointer"
            :class="motherDocs.includes(doc) ? 'bg-rose-500 text-white border-rose-500 shadow-xs' : 'bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100'"
          >
            <span>{{ doc }}</span>
            <Check v-if="motherDocs.includes(doc)" class="w-3.5 h-3.5 shrink-0" />
          </button>
        </div>
      </div>

      <!-- 3. Sponsor Notes -->
      <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-2">
        <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <FileText class="w-4 h-4 text-amber-500" />
          <span>Sponsorship & Embassy Special Notes</span>
        </h3>
        <textarea
          v-model="sponsorNotes"
          rows="3"
          placeholder="e.g. Ota rasmiy firma egasi, oylik daromadi 15mln, bankda 10,000$ depozit bor..."
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none resize-none"
        />
      </div>
    </div>

    <!-- Drawer Footer -->
    <template #footer>
      <button
        @click="emit('close')"
        class="px-4 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
      >
        Cancel
      </button>
      <button
        @click="handleSave"
        :disabled="isSaving"
        class="px-5 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold transition-all shadow-md shadow-brand-500/25 cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
      >
        <Save class="w-4 h-4" />
        <span>Save Embassy Record</span>
      </button>
    </template>
  </BaseDrawer>
</template>
