<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { Student } from '@/types'
import {
  X, Check, Trash2, StickyNote, Edit3
} from 'lucide-vue-next'
import QuickNoteSuggestionsList from './QuickNoteSuggestionsList.vue'

const props = withDefaults(defineProps<{
  isOpen: boolean
  student: Student | null
  allStudents?: Student[]
}>(), {
  allStudents: () => [],
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', notes: string, student: Student): void
}>()

const isEditing = ref(false)
const noteText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const isSaving = ref(false)

const hasExistingNote = computed(() => {
  return !!(props.student?.quick_notes && props.student.quick_notes.trim())
})

watch(() => props.isOpen, (newVal) => {
  if (newVal && props.student) {
    const existing = props.student.quick_notes || ''
    noteText.value = existing
    // If student already has a note, open in READ-ONLY mode; otherwise start in edit mode
    isEditing.value = !existing.trim()

    if (isEditing.value) {
      nextTick(() => {
        if (textareaRef.value) {
          textareaRef.value.focus()
          textareaRef.value.setSelectionRange(noteText.value.length, noteText.value.length)
        }
      })
    }
  }
})

const startEdit = () => {
  isEditing.value = true
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.focus()
      textareaRef.value.setSelectionRange(noteText.value.length, noteText.value.length)
    }
  })
}

const cancelEdit = () => {
  if (hasExistingNote.value) {
    noteText.value = props.student?.quick_notes || ''
    isEditing.value = false
  } else {
    emit('close')
  }
}

const handleSave = () => {
  if (!props.student) return
  const text = noteText.value.trim()
  props.student.quick_notes = text
  emit('save', text, props.student)
  emit('close')
}

const handleDelete = () => {
  if (!props.student) return
  if (!confirm(`Are you sure you want to delete quick note for "${props.student.full_name}"?`)) return
  noteText.value = ''
  props.student.quick_notes = ''
  emit('save', '', props.student)
  emit('close')
}

const applySuggestion = (suggestion: string) => {
  if (!noteText.value.trim()) {
    noteText.value = suggestion
  } else if (!noteText.value.includes(suggestion)) {
    noteText.value = `${noteText.value.trim()}, ${suggestion}`
  }
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.focus()
    }
  })
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (!props.isOpen) return
  if (e.key === 'Escape') {
    if (isEditing.value && hasExistingNote.value) {
      cancelEdit()
    } else {
      emit('close')
    }
  } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && isEditing.value) {
    e.preventDefault()
    handleSave()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <Teleport to="body">
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen && student"
        class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs overflow-y-auto"
        @click.self="emit('close')"
      >
        <transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="transform scale-95 opacity-0 translate-y-3"
          enter-to-class="transform scale-100 opacity-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="transform scale-100 opacity-100 translate-y-0"
          leave-to-class="transform scale-95 opacity-0 translate-y-3"
        >
          <div
            class="relative w-full max-w-3xl overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl z-10 text-xs text-zinc-900 dark:text-zinc-100 flex flex-col my-auto transition-all"
            @click.stop
          >
            <!-- Header -->
            <div class="flex items-start justify-between gap-3 px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-850/70">
              <div class="min-w-0 flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-xl bg-amber-500/15 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
                  <StickyNote class="w-4 h-4" />
                </div>
                <div class="min-w-0">
                  <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100 truncate" :title="student.full_name">
                    {{ student.full_name }}
                  </h3>
                  <p class="text-[11px] text-zinc-500 dark:text-zinc-400 font-medium">
                    Quick note • Student ID: <span class="font-mono font-bold">{{ student.id }}</span>
                  </p>
                </div>
              </div>
              <button
                type="button"
                @click="emit('close')"
                class="shrink-0 rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-200/60 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
              >
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- Body: READ-ONLY MODE -->
            <div v-if="!isEditing" class="p-6 space-y-4">
              <div class="flex items-center justify-between">
                <span class="font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider text-[10.5px]">
                  SAVED QUICK NOTE (READ ONLY)
                </span>
                <span class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-400">
                  <span>Active Note</span>
                </span>
              </div>

              <!-- Note Display Card -->
              <div class="relative p-4 rounded-xl bg-amber-500/10 dark:bg-amber-500/15 border border-amber-500/30 text-zinc-900 dark:text-zinc-100 leading-relaxed font-medium text-[13px] whitespace-pre-wrap select-text shadow-2xs">
                {{ student.quick_notes }}
              </div>
            </div>

            <!-- Body: EDIT MODE (Left: Textarea, Right: Suggestions Board) -->
            <div v-else class="p-6">
              <div class="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
                <!-- Left: Write Quick Note Input -->
                <div class="md:col-span-7 flex flex-col space-y-2">
                  <div class="flex items-center justify-between">
                    <label class="block font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider text-[11px]">
                      {{ hasExistingNote ? 'EDIT QUICK NOTE' : 'WRITE QUICK NOTE' }}
                    </label>
                    <span class="text-[11px] text-zinc-400 font-mono">{{ noteText.length }} chars</span>
                  </div>

                  <!-- Textarea -->
                  <textarea
                    ref="textareaRef"
                    v-model="noteText"
                    rows="8"
                    placeholder="Type quick note (e.g. O'tgan semestrda atkazi bor, Zagrani hali chiqmadi)..."
                    class="w-full flex-1 px-3.5 py-3 text-xs rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-800/50 text-zinc-800 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all resize-none min-h-[190px]"
                  />
                  <span class="text-[10px] text-zinc-400 italic">Press Ctrl+Enter to save immediately</span>
                </div>

                <!-- Right: Quick Note Suggestion Board -->
                <div class="md:col-span-5 flex flex-col border-t md:border-t-0 md:border-l border-zinc-200 dark:border-zinc-800 pt-4 md:pt-0 md:pl-6">
                  <QuickNoteSuggestionsList
                    :filter-text="noteText"
                    max-height-class="max-h-[220px]"
                    @select="applySuggestion"
                  />
                </div>
              </div>
            </div>

            <!-- Footer: READ-ONLY MODE ACTIONS -->
            <div
              v-if="!isEditing"
              class="px-6 py-4 flex items-center justify-between border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50/40 dark:bg-zinc-850/40"
            >
              <button
                type="button"
                @click="handleDelete"
                class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-rose-200/60 dark:border-rose-900/60 transition-colors cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
                <span>Delete</span>
              </button>

              <div class="flex items-center gap-2">
                <button
                  type="button"
                  @click="emit('close')"
                  class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 font-semibold hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                >
                  Close
                </button>
                <button
                  type="button"
                  @click="startEdit"
                  class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold shadow-md shadow-blue-500/20 transition-all cursor-pointer"
                >
                  <Edit3 class="w-3.5 h-3.5" />
                  <span>Edit Note</span>
                </button>
              </div>
            </div>

            <!-- Footer: EDIT MODE ACTIONS -->
            <div
              v-else
              class="px-6 py-4 flex items-center justify-between border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50/40 dark:bg-zinc-850/40"
            >
              <button
                v-if="hasExistingNote"
                type="button"
                @click="cancelEdit"
                class="px-3.5 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 font-semibold hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <div v-else />

              <div class="flex items-center gap-2">
                <button
                  v-if="!hasExistingNote"
                  type="button"
                  @click="emit('close')"
                  class="px-3.5 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 font-semibold hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  @click="handleSave"
                  class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 transition-all cursor-pointer active:scale-95"
                >
                  <Check class="w-3.5 h-3.5 stroke-[2.5]" />
                  <span>Save Note</span>
                </button>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>
