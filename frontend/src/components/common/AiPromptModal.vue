<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import {
  Sparkles,
  X,
  Check,
  FileText,
  Play,
  Loader2,
  Trash2,
  FileSpreadsheet,
  GraduationCap,
  FolderPlus,
  Folder,
  Palette,
  RotateCcw,
  Filter,
  Award,
  Copy,
  Info,
  AlertCircle
} from 'lucide-vue-next'
import { useUiStore } from '@/stores/ui'
import { useAiBulkOperations } from '@/composables/useAiBulkOperations'

const uiStore = useUiStore()
const {
  isExecuting,
  lastResult,
  officialUniversities,
  clarificationState,
  getOfficialUniversities,
  executeOperation,
  submitClarification
} = useAiBulkOperations()

const STORAGE_KEY = 'salom_bulk_ai_prompt'
const isOpen = ref(false)
const promptText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const isSaved = ref(false)
const isCopied = ref(false)
const universityFilterText = ref('')

const filteredUniversities = computed(() => {
  const q = universityFilterText.value.trim().toUpperCase()
  if (!q) return officialUniversities.value
  return officialUniversities.value.filter(u => u.toUpperCase().includes(q))
})

// Load saved prompt from localStorage
const loadPrompt = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      promptText.value = saved
    }
  } catch {
    // ignore
  }
}

const openModal = () => {
  loadPrompt()
  getOfficialUniversities()
  isOpen.value = true
  isSaved.value = false
  universityFilterText.value = ''
}

const closeModal = () => {
  loadPrompt()
  isOpen.value = false
  lastResult.value = null
  clarificationState.value.isOpen = false
}

const savePrompt = () => {
  const trimmed = promptText.value.trim()
  try {
    localStorage.setItem(STORAGE_KEY, trimmed)
  } catch {
    // ignore
  }

  isSaved.value = true
  uiStore.addToast({
    type: 'success',
    title: 'Prompt Saved',
    message: 'AI prompt for bulk operations has been saved successfully.'
  })

  setTimeout(() => {
    isSaved.value = false
  }, 2000)
}

const handleRun = async () => {
  const text = promptText.value.trim()
  if (!text) return

  const res = await executeOperation(text)
  if (res.type === 'excel') {
    // For Excel, modal closes so the user directly sees the Export Excel & Field Picker modal
    setTimeout(() => {
      isOpen.value = false
    }, 300)
  }
}

const copyResultText = () => {
  if (!lastResult.value) return
  const text = [
    lastResult.value.title,
    lastResult.value.message,
    ...(lastResult.value.details || [])
  ].join('\n')
  navigator.clipboard.writeText(text)
  isCopied.value = true
  setTimeout(() => {
    isCopied.value = false
  }, 1500)
}

const applyExample = (example: string) => {
  promptText.value = example
  nextTick(() => {
    textareaRef.value?.focus()
  })
}

// Focus textarea when opened
watch(isOpen, async (val) => {
  if (val) {
    await nextTick()
    setTimeout(() => {
      textareaRef.value?.focus()
    }, 50)
  }
})

// ─── Keyboard Shortcut Handler: Ctrl+A+I & Esc ──────────────────────────────
let lastCtrlATime = 0
const pressedKeys = new Set<string>()

const handleKeyDown = (e: KeyboardEvent) => {
  const isCtrlOrCmd = e.ctrlKey || e.metaKey
  const key = e.key.toLowerCase()
  pressedKeys.add(key)

  const target = e.target as HTMLElement | null
  const isInput = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)

  // 1. Simultaneous Ctrl + A + I (all pressed)
  if (isCtrlOrCmd && pressedKeys.has('a') && pressedKeys.has('i')) {
    e.preventDefault()
    e.stopPropagation()
    pressedKeys.clear()
    lastCtrlATime = 0
    if (isOpen.value) {
      closeModal()
    } else {
      openModal()
    }
    return
  }

  // 2. Sequence: Ctrl+A, then I (within 1500ms)
  if (isCtrlOrCmd && key === 'a') {
    if (!isInput) {
      // Prevent browser default "Select All" blue overlay on the page
      e.preventDefault()
    }
    lastCtrlATime = Date.now()
  } else if (key === 'i' && (Date.now() - lastCtrlATime < 1500)) {
    // If typing 'i' normally inside an input without Ctrl, don't trigger modal
    if (isInput && !isCtrlOrCmd) {
      lastCtrlATime = 0
      return
    }
    e.preventDefault()
    e.stopPropagation()
    lastCtrlATime = 0
    pressedKeys.clear()
    if (isOpen.value) {
      closeModal()
    } else {
      openModal()
    }
    return
  } else if (key !== 'control' && key !== 'meta' && key !== 'shift' && key !== 'alt') {
    lastCtrlATime = 0
  }

  // 3. Escape key closes modal
  if (e.key === 'Escape' && isOpen.value) {
    e.preventDefault()
    closeModal()
    return
  }

  // 4. Ctrl+Enter runs the operation (or Enter when single-line command)
  if (isOpen.value && isCtrlOrCmd && e.key === 'Enter') {
    e.preventDefault()
    handleRun()
  }
}

const handleKeyUp = (e: KeyboardEvent) => {
  pressedKeys.delete(e.key.toLowerCase())
}

const handleTextareaKeyDown = (e: KeyboardEvent) => {
  // If Enter without Shift on a single line command, execute immediately
  if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
    const text = promptText.value.trim()
    if (!text.includes('\n')) {
      e.preventDefault()
      handleRun()
    }
  }
}

onMounted(() => {
  loadPrompt()
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none"
        @click.self="closeModal"
      >
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="transform scale-95 opacity-0 translate-y-2"
          enter-to-class="transform scale-100 opacity-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="transform scale-100 opacity-100 translate-y-0"
          leave-to-class="transform scale-95 opacity-0 translate-y-2"
        >
          <div
            class="relative w-full max-w-xl rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden flex flex-col my-8 select-text max-h-[90vh]"
          >
            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-3.5 border-b border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/50 dark:bg-zinc-900/50 select-none">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-violet-500/15 dark:bg-violet-500/25 text-violet-600 dark:text-violet-400 flex items-center justify-center shrink-0">
                  <Sparkles class="w-4 h-4" />
                </div>
                <div>
                  <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    <span>AI Bulk Operations</span>
                  </h3>
                  <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Fast bulk actions, queries, and prompt execution
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] font-mono text-zinc-500 select-none">
                  Ctrl+A+I
                </kbd>
                <button
                  type="button"
                  @click="closeModal"
                  class="p-1 rounded-lg text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                  title="Close (Esc)"
                >
                  <X class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Scrollable Content Area -->
            <div class="p-5 space-y-3 overflow-y-auto max-h-[calc(90vh-140px)]">
              <!-- Prompt Input -->
              <div class="space-y-1.5">
                <div class="flex items-center justify-between">
                  <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300">
                    Command / Prompt
                  </label>
                  <span class="text-[11px] text-zinc-400">
                    Press <kbd class="px-1 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 font-mono text-[10px]">Enter</kbd> to run
                  </span>
                </div>

                <textarea
                  ref="textareaRef"
                  v-model="promptText"
                  rows="3"
                  @keydown="handleTextareaKeyDown"
                  placeholder="e.g. /excel f5,f6,f7 or show university for f5 or set university inha for f6,g6,g15 or /delete f1,f2,f3"
                  class="w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-500 resize-y transition-all leading-relaxed select-text"
                />
              </div>

              <!-- Quick Command Pills -->
              <div class="space-y-1.5 select-none">
                <div class="text-[10.5px] font-semibold uppercase tracking-wider text-zinc-400">
                  Quick Examples
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    @click="applyExample('open folder busan')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 hover:bg-amber-500/20 transition-colors cursor-pointer"
                    title="Create new folder named Busan without navigating"
                  >
                    <FolderPlus class="w-3 h-3 text-amber-600 dark:text-amber-400" />
                    <span>open folder busan</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('folder busan add f1,f5,f6')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border border-cyan-500/20 hover:bg-cyan-500/20 transition-colors cursor-pointer"
                    title="Add students to folder Busan"
                  >
                    <Folder class="w-3 h-3 text-cyan-600 dark:text-cyan-400" />
                    <span>folder busan add f1,f5,f6</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('set row color red f1,f8,f2 only me')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20 hover:bg-rose-500/20 transition-colors cursor-pointer"
                    title="Set personal (Only Me) row color highlight"
                  >
                    <Palette class="w-3 h-3 text-rose-600 dark:text-rose-400" />
                    <span>set row color red f1,f8,f2 only me</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('clear color f1')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-zinc-500/10 text-zinc-700 dark:text-zinc-300 border border-zinc-500/20 hover:bg-zinc-500/20 transition-colors cursor-pointer"
                    title="Clear row color"
                  >
                    <RotateCcw class="w-3 h-3 text-zinc-500 dark:text-zinc-400" />
                    <span>clear color f1</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('filter IELTS 6')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors cursor-pointer"
                    title="Filter students with IELTS 6.0"
                  >
                    <Filter class="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
                    <span>filter IELTS 6</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('filter TOPIK 2')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-purple-500/10 text-purple-700 dark:text-purple-300 border border-purple-500/20 hover:bg-purple-500/20 transition-colors cursor-pointer"
                    title="Filter students with TOPIK 2"
                  >
                    <Filter class="w-3 h-3 text-purple-600 dark:text-purple-400" />
                    <span>filter TOPIK 2</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('who has SAT')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 hover:bg-amber-500/20 transition-colors cursor-pointer"
                    title="Filter students with SAT certificate"
                  >
                    <Award class="w-3 h-3 text-amber-600 dark:text-amber-400" />
                    <span>who has SAT</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('set university inha for f6,g6,g15')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-violet-500/10 text-violet-700 dark:text-violet-300 border border-violet-500/20 hover:bg-violet-500/20 transition-colors cursor-pointer"
                    title="Assign university by name or acronym"
                  >
                    <Sparkles class="w-3 h-3 text-violet-600 dark:text-violet-400" />
                    <span>set university inha for f6,g6,g15</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('show university for f5')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20 hover:bg-blue-500/20 transition-colors cursor-pointer"
                    title="View university choices for student"
                  >
                    <GraduationCap class="w-3 h-3 text-blue-600 dark:text-blue-400" />
                    <span>show university for f5</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('/excel f5,f6,f7')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors cursor-pointer"
                    title="Preselect students and open Excel export"
                  >
                    <FileSpreadsheet class="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                    <span>/excel f5,f6,f7</span>
                  </button>

                  <button
                    type="button"
                    @click="applyExample('/delete f1,f2,f3')"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-mono bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20 hover:bg-rose-500/20 transition-colors cursor-pointer"
                    title="Archive/delete students"
                  >
                    <Trash2 class="w-3 h-3 text-rose-600 dark:text-rose-400" />
                    <span>/delete f1,f2,f3</span>
                  </button>
                </div>
              </div>

              <!-- Interactive Clarification Box (AI Asking Which University) -->
              <div
                v-if="clarificationState.isOpen"
                class="rounded-xl border border-violet-200 bg-violet-50/70 dark:border-violet-900/50 dark:bg-violet-950/20 p-4 space-y-3"
              >
                <div class="flex items-start gap-2.5">
                  <div class="w-6 h-6 rounded-md bg-violet-500 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                    <Sparkles class="w-3.5 h-3.5" />
                  </div>
                  <div class="space-y-0.5 flex-1 min-w-0">
                    <div class="text-xs font-bold text-violet-950 dark:text-violet-200">
                      {{ clarificationState.question }}
                    </div>
                    <p class="text-[11px] text-violet-700/80 dark:text-violet-300/70">
                      Select or search a university from the database to assign to {{ clarificationState.studentIds.join(', ') }}:
                    </p>
                  </div>
                </div>

                <div class="space-y-2">
                  <!-- Search Filter Input -->
                  <input
                    v-model="universityFilterText"
                    type="text"
                    placeholder="Search university (e.g. Inha, BUFS, Joongbu)..."
                    class="w-full px-3 py-1.5 text-xs rounded-lg border border-violet-300 dark:border-violet-700 bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />

                  <!-- Dropdown / List of Universities -->
                  <div class="max-h-44 overflow-y-auto rounded-lg border border-violet-200 dark:border-violet-800/60 bg-white dark:bg-zinc-900 divide-y divide-zinc-100 dark:divide-zinc-800 text-xs">
                    <button
                      type="button"
                      v-for="u in filteredUniversities.slice(0, 60)"
                      :key="u"
                      @click="clarificationState.selectedUniversity = u"
                      class="w-full text-left px-3 py-2 hover:bg-violet-50 dark:hover:bg-violet-950/40 cursor-pointer flex items-center justify-between transition-colors"
                      :class="clarificationState.selectedUniversity === u ? 'bg-violet-100 dark:bg-violet-900/40 font-bold text-violet-900 dark:text-violet-200' : 'text-zinc-700 dark:text-zinc-300'"
                    >
                      <span class="truncate">{{ u }}</span>
                      <Check v-if="clarificationState.selectedUniversity === u" class="w-3.5 h-3.5 text-violet-600 shrink-0 ml-2" />
                    </button>
                    <div v-if="filteredUniversities.length === 0" class="px-3 py-3 text-center text-zinc-400 text-xs">
                      No universities found matching "{{ universityFilterText }}".
                    </div>
                  </div>

                  <!-- Actions -->
                  <div class="flex items-center justify-between pt-1">
                    <span class="text-[10.5px] text-zinc-400 truncate max-w-[240px]">
                      Selected: <strong class="text-zinc-700 dark:text-zinc-200">{{ clarificationState.selectedUniversity || 'None' }}</strong>
                    </span>
                    <div class="flex items-center gap-2">
                      <button
                        type="button"
                        @click="clarificationState.isOpen = false"
                        class="px-2.5 py-1 text-xs text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200 cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        @click="submitClarification"
                        :disabled="!clarificationState.selectedUniversity || isExecuting"
                        class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold text-white bg-violet-600 hover:bg-violet-700 shadow-sm shadow-violet-500/25 transition-all cursor-pointer disabled:opacity-50"
                      >
                        <Check class="w-3.5 h-3.5" />
                        <span>Apply to {{ clarificationState.studentIds.length }} Student{{ clarificationState.studentIds.length === 1 ? '' : 's' }}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Interactive Result / Execution Feedback -->
              <div
                v-if="lastResult"
                class="rounded-xl border p-3.5 space-y-2.5 transition-all text-xs"
                :class="[
                  lastResult.type === 'error'
                    ? 'border-red-200 bg-red-50/50 dark:border-red-900/40 dark:bg-red-950/20 text-red-900 dark:text-red-200'
                    : lastResult.type === 'info'
                    ? 'border-blue-200 bg-blue-50/50 dark:border-blue-900/40 dark:bg-blue-950/20 text-blue-900 dark:text-blue-200'
                    : 'border-zinc-200 bg-zinc-50/70 dark:border-zinc-800 dark:bg-zinc-850/60 text-zinc-900 dark:text-zinc-100'
                ]"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-1.5 font-bold">
                    <AlertCircle v-if="lastResult.type === 'error'" class="w-4 h-4 text-red-500 shrink-0" />
                    <Info v-else-if="lastResult.type === 'info'" class="w-4 h-4 text-blue-500 shrink-0" />
                    <Check v-else class="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>{{ lastResult.title }}</span>
                  </div>

                  <button
                    type="button"
                    @click="copyResultText"
                    class="inline-flex items-center gap-1 text-[11px] text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 cursor-pointer"
                    title="Copy Result"
                  >
                    <Check v-if="isCopied" class="w-3 h-3 text-emerald-500" />
                    <Copy v-else class="w-3 h-3" />
                    <span>{{ isCopied ? 'Copied' : 'Copy' }}</span>
                  </button>
                </div>

                <p class="text-xs text-zinc-600 dark:text-zinc-300">
                  {{ lastResult.message }}
                </p>

                <!-- Detailed University Cards (for show university) -->
                <div
                  v-if="lastResult.universitySummaries && lastResult.universitySummaries.length > 0"
                  class="space-y-2 pt-1"
                >
                  <div
                    v-for="item in lastResult.universitySummaries"
                    :key="item.student.id"
                    class="p-2.5 rounded-lg border border-zinc-200/80 dark:border-zinc-700/80 bg-white dark:bg-zinc-900 space-y-1.5"
                  >
                    <div class="flex items-center justify-between gap-2">
                      <div class="flex items-center gap-2">
                        <span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-600 text-white">
                          {{ item.student.id }}
                        </span>
                        <span class="font-bold uppercase text-zinc-900 dark:text-zinc-100">
                          {{ item.student.full_name }}
                        </span>
                      </div>
                      <span v-if="item.student.korean_name" class="text-[11px] text-zinc-400">
                        {{ item.student.korean_name }}
                      </span>
                    </div>

                    <div v-if="item.universities.length === 0" class="text-zinc-400 italic text-[11px]">
                      No universities selected for this student yet.
                    </div>

                    <div v-else class="grid grid-cols-1 gap-1 pt-1">
                      <div
                        v-for="u in item.universities"
                        :key="u.slot"
                        class="flex items-center justify-between text-[11px] px-2 py-1 rounded bg-zinc-50 dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-750"
                      >
                        <div class="flex items-center gap-1.5 truncate">
                          <span class="text-zinc-400 font-mono text-[10px]">#{{ u.slot }}</span>
                          <span class="font-bold text-zinc-800 dark:text-zinc-200 truncate">{{ u.name }}</span>
                          <span v-if="u.major" class="text-zinc-400 text-[10px] truncate">({{ u.major }})</span>
                        </div>
                        <span
                          v-if="u.status"
                          class="px-1.5 py-0.5 rounded text-[9.5px] font-bold uppercase tracking-wider shrink-0 bg-blue-500/15 text-blue-600 dark:text-blue-400"
                        >
                          {{ u.status }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Detailed Bullet List (for other commands) -->
                <ul
                  v-else-if="lastResult.details && lastResult.details.length > 0"
                  class="space-y-1 pt-1 text-[11.5px] max-h-40 overflow-y-auto"
                >
                  <li
                    v-for="(line, idx) in lastResult.details"
                    :key="idx"
                    class="flex items-start gap-1.5"
                  >
                    <span class="text-zinc-400 select-none">•</span>
                    <span class="text-zinc-700 dark:text-zinc-300">{{ line }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Footer Buttons (Cancel, Save, Run) -->
            <div class="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/50 dark:bg-zinc-900/50 flex items-center justify-between select-none">
              <span class="text-[11px] text-zinc-400">
                Press <kbd class="px-1 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 font-mono text-[10px]">Esc</kbd> to close
              </span>

              <div class="flex items-center gap-2">
                <!-- Cancel Button -->
                <button
                  type="button"
                  @click="closeModal"
                  class="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                >
                  Cancel
                </button>

                <!-- Save Button -->
                <button
                  type="button"
                  @click="savePrompt"
                  class="inline-flex items-center gap-1 px-3.5 py-1.5 rounded-xl text-xs font-semibold border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                  title="Save prompt template to localStorage"
                >
                  <Check v-if="isSaved" class="w-3.5 h-3.5 text-emerald-500" />
                  <span>{{ isSaved ? 'Saved' : 'Save' }}</span>
                </button>

                <!-- Run Operation Button -->
                <button
                  type="button"
                  @click="handleRun"
                  :disabled="isExecuting || !promptText.trim()"
                  class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-sm shadow-blue-500/25 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Loader2 v-if="isExecuting" class="w-3.5 h-3.5 animate-spin" />
                  <Play v-else class="w-3.5 h-3.5 fill-current" />
                  <span>{{ isExecuting ? 'Running...' : 'Run' }}</span>
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

