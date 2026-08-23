<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { Student, Folder } from '@/types'
import { ROW_COLOR_MAP } from '@/types'
import {
  X, Check, CheckCircle2, Trash2, RefreshCw, AlertTriangle
} from 'lucide-vue-next'

export interface CustomTag {
  name: string
  icon: string
}

const props = defineProps<{
  isOpen: boolean
  student: Student | null
  folders: Folder[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'set-color', color: string | null): void
  (e: 'set-folders', folderIds: string[]): void
  (e: 'toggle-tag', tagName: string): void
  (e: 'clear-all'): void
  (e: 'archive'): void
  (e: 'restore'): void
  (e: 'permanent-delete'): void
}>()

import { useCustomTags } from '@/composables/useCustomTags'

const { tagsRegistry: customTagsRegistry, fetchTags } = useCustomTags()
const isPermanentConfirmOpen = ref(false)

// Local optimistic state for instant UI reactivity
const localColor = ref<string | null>(null)
const localFolderIds = ref<string[]>([])
const localTags = ref<string[]>([])

const syncFromStudent = (s: Student | null) => {
  if (s) {
    localColor.value = s.row_color ? String(s.row_color).toUpperCase() : null
    localFolderIds.value = (s.folder_ids || []).map(String)
    localTags.value = [...(s.task_tags || [])]
  } else {
    localColor.value = null
    localFolderIds.value = []
    localTags.value = []
  }
}

watch(() => props.student, (newVal) => {
  syncFromStudent(newVal)
}, { immediate: true, deep: true })

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchTags()
    syncFromStudent(props.student)
    isPermanentConfirmOpen.value = false
  }
})

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) {
    if (isPermanentConfirmOpen.value) {
      isPermanentConfirmOpen.value = false
    } else {
      emit('close')
    }
  }
}

onMounted(() => {
  fetchTags()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

// Action handlers with immediate optimistic updates
const handleColorSelect = (colorKey: string | null) => {
  localColor.value = colorKey ? colorKey.toUpperCase() : null
  emit('set-color', colorKey)
}

const handleClearFolders = () => {
  localFolderIds.value = []
  emit('set-folders', [])
}

const handleToggleFolder = (folderId: string) => {
  const strId = String(folderId)
  const current = [...localFolderIds.value]
  const idx = current.indexOf(strId)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(strId)
  }
  localFolderIds.value = current
  emit('set-folders', current)
}

const handleTagClick = (tagName: string) => {
  const current = [...localTags.value]
  const idx = current.indexOf(tagName)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(tagName)
  }
  localTags.value = current
  emit('toggle-tag', tagName)
}

const handleClearAll = () => {
  localColor.value = null
  localTags.value = []
  emit('clear-all')
}

const handleDeleteStudent = () => {
  const name = props.student?.full_name || 'student'
  if (!confirm(`Are you sure you want to delete student profile "${name}"?`)) return
  emit('archive')
}

const handleRestoreStudent = () => {
  const name = props.student?.full_name || 'student'
  if (!confirm(`Are you sure you want to restore student profile "${name}"?`)) return
  emit('restore')
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop and Main Quick Actions Modal -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen && !isPermanentConfirmOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs overflow-y-auto"
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
            v-if="student"
            class="relative w-full max-w-[640px] overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl z-10 text-xs text-zinc-900 dark:text-zinc-100 flex flex-col my-auto select-none"
            @click.stop
          >
            <!-- 1. Header with Student Name, ID and Close Button -->
            <div class="flex items-start justify-between gap-3 px-6 py-5 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-850/50">
              <div class="min-w-0">
                <h3 class="text-[15px] font-bold text-zinc-900 dark:text-zinc-100 truncate" :title="student.full_name">
                  {{ student.full_name }}
                </h3>
                <p class="text-[11px] text-zinc-500 dark:text-zinc-400 font-medium mt-1">
                  Student ID: <span class="font-mono">{{ student.id }}</span>
                </p>
              </div>
              <button
                type="button"
                @click="emit('close')"
                class="shrink-0 rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-200/60 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
                title="Close Menu"
              >
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- 2. Scrollable Body -->
            <div class="flex flex-col gap-6 px-6 py-6 max-h-[70vh] overflow-y-auto">
              <!-- SELECT COLOR Section -->
              <div>
                <div class="font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider text-[10.5px] mb-3">
                  SELECT COLOR
                </div>
                <div class="flex items-center gap-3 flex-wrap">
                  <button
                    v-for="(data, name) in ROW_COLOR_MAP"
                    :key="name"
                    type="button"
                    @click="handleColorSelect(String(name))"
                    class="relative w-8 h-8 rounded-full cursor-pointer transition-all duration-150 flex items-center justify-center shadow-xs"
                    :class="localColor === name ? 'scale-110 ring-3 ring-offset-2 ring-zinc-700 dark:ring-zinc-200' : 'hover:scale-110 opacity-90 hover:opacity-100'"
                    :style="{ backgroundColor: data.ball }"
                    :title="data.name"
                  >
                    <Check v-if="localColor === name" class="w-4 h-4 text-white stroke-[3.5]" />
                  </button>

                  <!-- Clear Color -->
                  <button
                    type="button"
                    @click="handleColorSelect(null)"
                    class="w-8 h-8 rounded-full border border-dashed border-zinc-300 dark:border-zinc-700 cursor-pointer flex items-center justify-center text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-700 dark:hover:text-zinc-200 transition-all"
                    title="Clear Color"
                  >
                    <X class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div class="border-t border-zinc-100 dark:border-zinc-800" />

              <!-- ASSIGN TO FOLDER Section -->
              <div>
                <div class="font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider text-[10.5px] mb-3">
                  ASSIGN TO FOLDER
                </div>

                <div class="flex flex-wrap gap-2">
                  <!-- All (No Folder) Button -->
                  <button
                    type="button"
                    @click="handleClearFolders"
                    class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-xs"
                    :class="localFolderIds.length === 0
                      ? 'border-blue-600 bg-blue-100/80 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 font-bold shadow-xs ring-1 ring-blue-500/30'
                      : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-800/60 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-100'"
                  >
                    <span>📁 All (No Folder)</span>
                  </button>

                  <!-- Custom Folders -->
                  <button
                    v-for="folder in folders"
                    :key="folder.id"
                    type="button"
                    @click="handleToggleFolder(folder.id)"
                    class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-xs"
                    :class="localFolderIds.includes(String(folder.id))
                      ? 'border-blue-600 bg-blue-100/80 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 font-bold shadow-xs ring-1 ring-blue-500/30'
                      : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-800/60 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-100'"
                  >
                    <span>📁 {{ folder.name }}</span>
                  </button>
                </div>
              </div>

              <div class="border-t border-zinc-100 dark:border-zinc-800" />

              <!-- CUSTOM TAGS Section -->
              <div>
                <div class="font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider text-[10.5px] mb-3">
                  CUSTOM TAGS
                </div>

                <div class="grid grid-cols-2 gap-2 mb-2 max-h-56 overflow-y-auto pr-1">
                  <div v-if="customTagsRegistry.length === 0" class="text-[11px] text-zinc-400 italic py-1 col-span-2">
                    No custom tags yet.
                  </div>
                  <button
                    v-for="tag in customTagsRegistry"
                    :key="tag.name"
                    type="button"
                    @click="handleTagClick(tag.name)"
                    class="flex items-center gap-2 pl-3 pr-3 py-2 rounded-xl border text-[12.5px] font-semibold transition-all text-left w-full cursor-pointer"
                    :class="localTags.includes(tag.name)
                      ? 'border-blue-600 bg-blue-100/90 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 shadow-xs font-bold ring-1 ring-blue-500/30'
                      : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-800/60 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-100'"
                    :title="localTags.includes(tag.name) ? 'Click to remove tag' : 'Click to apply tag'"
                  >
                    <span class="leading-none text-base shrink-0">{{ tag.icon }}</span>
                    <span class="truncate flex-1">{{ tag.name }}</span>
                    <CheckCircle2 v-if="localTags.includes(tag.name)" class="w-4 h-4 shrink-0 text-blue-600 dark:text-blue-400" />
                  </button>
                </div>

                <!-- Settings Shortcut Link -->
                <router-link
                  to="/settings"
                  class="inline-flex items-center gap-1 text-[10.5px] font-semibold text-blue-600 dark:text-blue-400 hover:underline opacity-80 hover:opacity-100 transition-opacity mt-0.5"
                  @click="emit('close')"
                >
                  Manage custom tags in Settings →
                </router-link>
              </div>
            </div>

            <!-- 3. Footer / Action Buttons -->
            <div class="px-6 pb-6 pt-2 flex gap-3 border-t border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/40 dark:bg-zinc-850/40">
              <!-- If student is archived / deleted -->
              <template v-if="student.is_deleted">
                <button
                  type="button"
                  @click="handleRestoreStudent"
                  class="flex-1 py-2.5 rounded-xl border border-emerald-500/25 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/40 font-semibold active:scale-[0.97] transition-all text-[11.5px] cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <RefreshCw class="w-3.5 h-3.5" />
                  <span>Restore Student</span>
                </button>
                <button
                  type="button"
                  @click="isPermanentConfirmOpen = true"
                  class="flex-1 py-2.5 rounded-xl border border-red-500/40 bg-red-500/10 hover:bg-red-500/20 text-red-600 font-bold active:scale-[0.97] transition-all text-[11.5px] cursor-pointer flex items-center justify-center gap-1.5 shadow-2xs"
                >
                  <Trash2 class="w-3.5 h-3.5 text-red-500" />
                  <span>Permanently Delete</span>
                </button>
              </template>

              <!-- If student is active -->
              <template v-else>
                <button
                  type="button"
                  @click="handleClearAll"
                  class="flex-1 py-2.5 rounded-xl border border-red-500/25 bg-red-500/5 text-red-500 hover:bg-red-500/10 hover:border-red-500/40 font-semibold active:scale-[0.97] transition-all text-[11.5px] cursor-pointer"
                >
                  Clear All Color & Tags
                </button>
                <button
                  type="button"
                  @click="handleDeleteStudent"
                  class="flex-1 py-2.5 rounded-xl border border-red-500/40 bg-red-500/10 hover:bg-red-500/20 text-red-600 font-bold active:scale-[0.97] transition-all text-[11.5px] cursor-pointer flex items-center justify-center gap-1.5 shadow-2xs"
                >
                  <Trash2 class="w-3.5 h-3.5 text-red-500" />
                  <span>Delete Student</span>
                </button>
              </template>
            </div>
          </div>
        </transition>
      </div>
    </transition>

    <!-- Permanent Delete Confirmation Dialog -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isPermanentConfirmOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
        @click.self="isPermanentConfirmOpen = false"
      >
        <div class="relative w-full max-w-md overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl p-6 space-y-4 text-xs">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100">Confirm Permanent Deletion</h3>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">This action cannot be undone.</p>
            </div>
            <button
              @click="isPermanentConfirmOpen = false"
              class="rounded-lg p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 flex items-start gap-2.5">
            <AlertTriangle class="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
            <p class="leading-relaxed">
              Are you sure you want to permanently delete <strong>{{ student?.full_name }}</strong> (ID: <strong>{{ student?.id }}</strong>)? All associated records will be permanently removed.
            </p>
          </div>

          <div class="flex items-center justify-end gap-2.5 pt-2">
            <button
              type="button"
              @click="isPermanentConfirmOpen = false"
              class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-bold cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="() => { emit('permanent-delete'); isPermanentConfirmOpen = false; }"
              class="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold cursor-pointer shadow-md shadow-rose-600/20 transition-all"
            >
              Permanently Delete
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>
