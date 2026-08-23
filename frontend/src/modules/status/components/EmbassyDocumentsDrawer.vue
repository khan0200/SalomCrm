<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Student } from '@/types'
import {
  X, Plus, CheckCircle2, Check, ChevronDown, ChevronUp
} from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  student: Student | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update-father-docs', docs: string[]): void
  (e: 'update-mother-docs', docs: string[]): void
  (e: 'update-sponsor-notes', notes: string): void
  (e: 'update-visa-status', status: string | null): void
  (e: 'update-status-hidden', isHidden: boolean): void
}>()

const activeAccordion = ref<'father' | 'mother' | 'sponsor' | null>(null)
const newFatherDoc = ref('')
const newMotherDoc = ref('')
const sponsorNotes = ref('')

const QUICK_DOCS = [
  'RASMIY ISH HAQQI',
  'CHET DAVLATI ISH HAQQI',
  'KOREADA RASMIY ISH',
  'KADASTR',
  'KADASTR X2',
  'KADASTR X3',
  'TEX.PASSPORT',
  'TEX.PASSPORT X2',
  'TEX.PASSPORT X3',
  'BANKSHOT',
  'BOBO PENSIYA',
  'BUVI PENSIYA',
  'DO\'KON',
  'YAKKA TADBIRKOR',
  'O\'ZINI BAND QILISH'
]

watch(() => props.student, (s) => {
  if (s) {
    sponsorNotes.value = s.embassy_sponsor_notes || ''
  }
}, { immediate: true })

watch(() => props.isOpen, (open) => {
  if (open) {
    activeAccordion.value = null
  }
})

const handleToggleHidden = () => {
  if (!props.student) return
  emit('update-status-hidden', !props.student.status_hidden)
}

const handleAddFatherDoc = (doc: string) => {
  if (!props.student) return
  const trimmed = doc.trim()
  if (!trimmed) return
  const current = props.student.embassy_father_docs || []
  if (current.includes(trimmed)) return
  emit('update-father-docs', [...current, trimmed])
  newFatherDoc.value = ''
}

const handleRemoveFatherDoc = (doc: string) => {
  if (!props.student) return
  const current = props.student.embassy_father_docs || []
  emit('update-father-docs', current.filter(d => d !== doc))
}

const handleAddMotherDoc = (doc: string) => {
  if (!props.student) return
  const trimmed = doc.trim()
  if (!trimmed) return
  const current = props.student.embassy_mother_docs || []
  if (current.includes(trimmed)) return
  emit('update-mother-docs', [...current, trimmed])
  newMotherDoc.value = ''
}

const handleRemoveMotherDoc = (doc: string) => {
  if (!props.student) return
  const current = props.student.embassy_mother_docs || []
  emit('update-mother-docs', current.filter(d => d !== doc))
}

const handleSaveSponsorNotes = () => {
  emit('update-sponsor-notes', sponsorNotes.value.trim())
}

const handleToggleVisa = (targetStatus: 'APPROVED' | 'CANCELLED') => {
  if (!props.student) return
  const current = props.student.embassy
  emit('update-visa-status', current === targetStatus ? null : targetStatus)
}
</script>

<template>
  <div v-if="isOpen && student" class="fixed inset-y-0 right-0 z-50 pointer-events-none flex justify-end p-2 md:p-2.5">
    <!-- Backdrop Overlay -->
    <div
      class="fixed inset-0 bg-black/30 transition-opacity ease-out pointer-events-auto z-0"
      @click="emit('close')"
    />

    <!-- Drawer Panel -->
    <div
      class="relative w-full max-w-3xl h-full bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl z-10 flex flex-col overflow-hidden pointer-events-auto transition-transform"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-5 border-b border-zinc-200 dark:border-zinc-800 shrink-0 bg-zinc-50/50 dark:bg-zinc-850/50 select-none">
        <div>
          <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100">Embassy Documents</h3>
          <div class="flex items-center gap-2 mt-1">
            <span class="text-[11px] font-bold bg-[#007aff] text-white px-1.5 py-0.5 rounded-[4px] shadow-xs">
              {{ student.id }}
            </span>
            <span class="text-xs font-semibold text-zinc-600 dark:text-zinc-400 uppercase tracking-wide truncate max-w-[250px]">
              {{ student.full_name }}
            </span>
          </div>
        </div>
        <button
          @click="emit('close')"
          class="rounded-lg p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <X class="h-5 w-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-6 flex flex-col gap-6 select-none scrollbar-thin">
        <!-- Hide Student Toggle -->
        <div class="flex items-center justify-between p-3.5 bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-700/80 rounded-2xl shadow-2xs">
          <div class="flex flex-col pr-4">
            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100">Hide Student</span>
            <span class="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5">
              Hide this student from the active Status table view
            </span>
          </div>
          <button
            type="button"
            @click="handleToggleHidden"
            class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
            :class="student.status_hidden ? 'bg-amber-500' : 'bg-zinc-200 dark:bg-zinc-700'"
          >
            <span
              class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out"
              :class="student.status_hidden ? 'translate-x-5' : 'translate-x-0'"
            />
          </button>
        </div>

        <!-- SECTION 1: FATHER (OTA) -->
        <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 bg-zinc-50/40 dark:bg-zinc-850/40 flex flex-col shadow-2xs transition-all duration-200">
          <div
            @click="activeAccordion = activeAccordion === 'father' ? null : 'father'"
            class="flex items-center justify-between cursor-pointer"
          >
            <h4 class="text-sm font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
              <div class="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
              <span>Ota (Father)</span>
            </h4>
            <div class="flex items-center gap-2">
              <span class="text-[10.5px] font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40 px-2 py-0.5 rounded-full border border-blue-200 dark:border-blue-800/40">
                {{ (student.embassy_father_docs || []).length }} docs
              </span>
              <ChevronUp v-if="activeAccordion === 'father'" class="h-4 w-4 text-blue-500" />
              <ChevronDown v-else class="h-4 w-4 text-blue-500" />
            </div>
          </div>

          <div
            v-if="activeAccordion !== 'father' && (student.embassy_father_docs || []).length > 0"
            class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-2 font-medium truncate"
          >
            {{ (student.embassy_father_docs || []).join(', ') }}
          </div>

          <div v-if="activeAccordion === 'father'" class="flex flex-col gap-4 mt-4">
            <!-- Add Father Custom Doc -->
            <form @submit.prevent="handleAddFatherDoc(newFatherDoc)" class="flex gap-2">
              <input
                v-model="newFatherDoc"
                type="text"
                placeholder="Custom ota hujjati..."
                class="flex-1 px-3.5 py-1.5 text-xs border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-xl focus:outline-none focus:border-blue-500 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 font-semibold shadow-2xs"
              />
              <button
                type="submit"
                class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all cursor-pointer inline-flex items-center gap-1 shrink-0"
              >
                <Plus class="h-3.5 w-3.5" />
                Add
              </button>
            </form>

            <!-- Quick Add Grid -->
            <div class="flex flex-col gap-1.5">
              <label class="text-[9.5px] font-bold uppercase tracking-wider text-zinc-400">
                Quick Add
              </label>
              <div class="grid grid-cols-3 gap-1.5">
                <button
                  v-for="doc in QUICK_DOCS"
                  :key="doc"
                  type="button"
                  :disabled="(student.embassy_father_docs || []).includes(doc)"
                  @click="handleAddFatherDoc(doc)"
                  class="px-2.5 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer text-center truncate"
                  :class="[
                    (student.embassy_father_docs || []).includes(doc)
                      ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400 border-transparent opacity-60 cursor-not-allowed'
                      : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 dark:hover:bg-blue-950/20 dark:hover:text-blue-400'
                  ]"
                  :title="doc"
                >
                  {{ doc }}
                </button>
              </div>
            </div>

            <!-- Father Docs List -->
            <div
              v-if="(student.embassy_father_docs || []).length > 0"
              class="flex flex-wrap gap-1.5 bg-white dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 p-3 rounded-2xl shadow-2xs"
            >
              <span
                v-for="doc in student.embassy_father_docs"
                :key="doc"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10.5px] font-bold bg-blue-600 text-white shadow-xs"
              >
                <span>{{ doc }}</span>
                <button
                  type="button"
                  @click="handleRemoveFatherDoc(doc)"
                  class="text-white/80 hover:text-white cursor-pointer transition-colors"
                >
                  <X class="h-3.5 w-3.5" />
                </button>
              </span>
            </div>
          </div>
        </div>

        <!-- SECTION 2: MOTHER (ONA) -->
        <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 bg-zinc-50/40 dark:bg-zinc-850/40 flex flex-col shadow-2xs transition-all duration-200">
          <div
            @click="activeAccordion = activeAccordion === 'mother' ? null : 'mother'"
            class="flex items-center justify-between cursor-pointer"
          >
            <h4 class="text-sm font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
              <div class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
              <span>Ona (Mother)</span>
            </h4>
            <div class="flex items-center gap-2">
              <span class="text-[10.5px] font-bold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded-full border border-rose-200 dark:border-rose-800/40">
                {{ (student.embassy_mother_docs || []).length }} docs
              </span>
              <ChevronUp v-if="activeAccordion === 'mother'" class="h-4 w-4 text-rose-500" />
              <ChevronDown v-else class="h-4 w-4 text-rose-500" />
            </div>
          </div>

          <div
            v-if="activeAccordion !== 'mother' && (student.embassy_mother_docs || []).length > 0"
            class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-2 font-medium truncate"
          >
            {{ (student.embassy_mother_docs || []).join(', ') }}
          </div>

          <div v-if="activeAccordion === 'mother'" class="flex flex-col gap-4 mt-4">
            <!-- Add Mother Custom Doc -->
            <form @submit.prevent="handleAddMotherDoc(newMotherDoc)" class="flex gap-2">
              <input
                v-model="newMotherDoc"
                type="text"
                placeholder="Custom ona hujjati..."
                class="flex-1 px-3.5 py-1.5 text-xs border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-xl focus:outline-none focus:border-blue-500 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 font-semibold shadow-2xs"
              />
              <button
                type="submit"
                class="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-xl transition-all cursor-pointer inline-flex items-center gap-1 shrink-0"
              >
                <Plus class="h-3.5 w-3.5" />
                Add
              </button>
            </form>

            <!-- Quick Add Grid -->
            <div class="flex flex-col gap-1.5">
              <label class="text-[9.5px] font-bold uppercase tracking-wider text-zinc-400">
                Quick Add
              </label>
              <div class="grid grid-cols-3 gap-1.5">
                <button
                  v-for="doc in QUICK_DOCS"
                  :key="doc"
                  type="button"
                  :disabled="(student.embassy_mother_docs || []).includes(doc)"
                  @click="handleAddMotherDoc(doc)"
                  class="px-2.5 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer text-center truncate"
                  :class="[
                    (student.embassy_mother_docs || []).includes(doc)
                      ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400 border-transparent opacity-60 cursor-not-allowed'
                      : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-200 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 dark:hover:bg-rose-950/20 dark:hover:text-rose-400'
                  ]"
                  :title="doc"
                >
                  {{ doc }}
                </button>
              </div>
            </div>

            <!-- Mother Docs List -->
            <div
              v-if="(student.embassy_mother_docs || []).length > 0"
              class="flex flex-wrap gap-1.5 bg-white dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 p-3 rounded-2xl shadow-2xs"
            >
              <span
                v-for="doc in student.embassy_mother_docs"
                :key="doc"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10.5px] font-bold bg-rose-600 text-white shadow-xs"
              >
                <span>{{ doc }}</span>
                <button
                  type="button"
                  @click="handleRemoveMotherDoc(doc)"
                  class="text-white/80 hover:text-white cursor-pointer transition-colors"
                >
                  <X class="h-3.5 w-3.5" />
                </button>
              </span>
            </div>
          </div>
        </div>

        <!-- SECTION 3: SPONSOR (HOMIY) -->
        <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 bg-zinc-50/40 dark:bg-zinc-850/40 flex flex-col shadow-2xs transition-all duration-200">
          <div
            @click="activeAccordion = activeAccordion === 'sponsor' ? null : 'sponsor'"
            class="flex items-center justify-between cursor-pointer"
          >
            <h4 class="text-sm font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
              <div class="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
              <span>Homiy (Sponsor Notes)</span>
            </h4>
            <div class="flex items-center gap-2">
              <ChevronUp v-if="activeAccordion === 'sponsor'" class="h-4 w-4 text-amber-500" />
              <ChevronDown v-else class="h-4 w-4 text-amber-500" />
            </div>
          </div>

          <div
            v-if="activeAccordion !== 'sponsor' && student.embassy_sponsor_notes && student.embassy_sponsor_notes.trim().length > 0"
            class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-2 font-medium truncate italic"
          >
            &quot;{{ student.embassy_sponsor_notes }}&quot;
          </div>

          <div v-if="activeAccordion === 'sponsor'" class="flex flex-col gap-3 mt-4">
            <textarea
              v-model="sponsorNotes"
              @blur="handleSaveSponsorNotes"
              rows="4"
              placeholder="Homiy haqida ma'lumot kiriting (Sponsor notes)..."
              class="w-full px-3.5 py-2.5 text-xs border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-xl focus:outline-none focus:border-amber-500 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 font-medium shadow-2xs resize-none"
            />
            <div class="flex justify-end">
              <button
                type="button"
                @click="handleSaveSponsorNotes"
                class="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-xl transition-all cursor-pointer flex items-center gap-1.5 shadow-xs"
              >
                <Check class="h-4 w-4" />
                <span>Save Sponsor Notes</span>
              </button>
            </div>
          </div>
        </div>

        <!-- SECTION 4: VISA STATUS -->
        <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 bg-zinc-50/40 dark:bg-zinc-850/40 flex flex-col shadow-2xs transition-all duration-200">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-bold text-violet-600 dark:text-violet-400 uppercase tracking-wider flex items-center gap-1.5">
              <div class="w-2.5 h-2.5 rounded-full bg-violet-500 animate-pulse" />
              <span>Visa</span>
            </h4>
          </div>

          <div class="flex gap-3 mt-4">
            <button
              type="button"
              @click="handleToggleVisa('APPROVED')"
              class="flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all cursor-pointer border flex items-center justify-center gap-2"
              :class="[
                student.embassy === 'APPROVED'
                  ? 'bg-emerald-600 border-transparent text-white shadow-md hover:bg-emerald-700'
                  : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-200 hover:bg-emerald-50 hover:text-emerald-600 dark:hover:bg-emerald-950/20 dark:hover:text-emerald-400'
              ]"
            >
              <CheckCircle2 class="h-4.5 w-4.5" />
              <span>APPROVED</span>
            </button>
            <button
              type="button"
              @click="handleToggleVisa('CANCELLED')"
              class="flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all cursor-pointer border flex items-center justify-center gap-2"
              :class="[
                student.embassy === 'CANCELLED'
                  ? 'bg-rose-600 border-transparent text-white shadow-md hover:bg-rose-700'
                  : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-200 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400'
              ]"
            >
              <X class="h-4.5 w-4.5" />
              <span>CANCELLED</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
