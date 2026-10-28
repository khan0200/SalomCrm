<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import {
  StickyNote, Folder as FolderIcon, Tag, ChevronRight, Check, SlidersHorizontal
} from 'lucide-vue-next'
import type { Student, Folder } from '@/types'
import { useCustomTags } from '@/composables/useCustomTags'

const props = defineProps<{
  isOpen: boolean
  x: number
  y: number
  student: Student | null
  folders: Folder[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'quick-notes', student: Student): void
  (e: 'open-actions', student: Student): void
  (e: 'toggle-folder', folderId: string, student: Student): void
  (e: 'clear-folders', student: Student): void
  (e: 'toggle-tag', tagName: string, student: Student): void
}>()

const { tagsRegistry: customTagsRegistry, fetchTags } = useCustomTags()
fetchTags()

const activeSubmenu = ref<'none' | 'folders' | 'tags'>('none')
const isOpening = ref(false)
let closeSubmenuTimer: any = null

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    isOpening.value = true
    activeSubmenu.value = 'none'
    setTimeout(() => {
      isOpening.value = false
    }, 200)
  }
})

const openSubmenu = (menu: 'folders' | 'tags') => {
  if (closeSubmenuTimer) {
    clearTimeout(closeSubmenuTimer)
    closeSubmenuTimer = null
  }
  activeSubmenu.value = menu
}

const scheduleCloseSubmenu = () => {
  closeSubmenuTimer = setTimeout(() => {
    activeSubmenu.value = 'none'
  }, 300)
}

const cancelCloseSubmenu = () => {
  if (closeSubmenuTimer) {
    clearTimeout(closeSubmenuTimer)
    closeSubmenuTimer = null
  }
}

const menuWidth = 210
const submenuWidth = 200

const adjustedPosition = computed(() => {
  const winW = typeof window !== 'undefined' ? window.innerWidth : 1200
  const winH = typeof window !== 'undefined' ? window.innerHeight : 800

  let left = props.x
  let top = props.y

  if (left + menuWidth > winW - 10) {
    left = winW - menuWidth - 10
  }
  if (top + 160 > winH - 10) {
    top = winH - 160 - 10
  }

  const submenuOnLeft = left + menuWidth + submenuWidth > winW - 10

  return {
    style: {
      left: `${Math.max(10, left)}px`,
      top: `${Math.max(10, top)}px`,
    },
    submenuOnLeft,
  }
})

const isFolderActive = (folderId: string | number) => {
  if (!props.student?.folder_ids) return false
  return props.student.folder_ids.map(String).includes(String(folderId))
}

const isTagActive = (tagName: string) => {
  if (!props.student) return false
  return (
    (props.student.task_tags || []).includes(tagName) ||
    (props.student.my_task_tags || []).includes(tagName)
  )
}

function onDocClick(e: MouseEvent) {
  if (!props.isOpen || isOpening.value) return
  const target = e.target as HTMLElement
  if (!target || !target.closest('[data-student-context-menu]')) {
    emit('close')
  }
}

function onDocContextMenu(e: MouseEvent) {
  if (!props.isOpen || isOpening.value) return
  const target = e.target as HTMLElement
  if (!target || !target.closest('[data-student-context-menu]')) {
    emit('close')
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.isOpen) {
    emit('close')
  }
}

function onScroll(e: Event) {
  if (!props.isOpen || isOpening.value) return
  if (e.target && (e.target as HTMLElement).closest?.('[data-student-context-menu]')) {
    return
  }
  emit('close')
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('contextmenu', onDocContextMenu)
  document.addEventListener('keydown', onKeyDown)
  window.addEventListener('scroll', onScroll, { passive: true, capture: true })
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('contextmenu', onDocContextMenu)
  document.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('scroll', onScroll, { capture: true } as any)
  if (closeSubmenuTimer) clearTimeout(closeSubmenuTimer)
})
</script>

<template>
  <Teleport to="body">
    <transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen && student"
        data-student-context-menu
        class="fixed z-[100] w-[210px] rounded-xl bg-white/95 dark:bg-[#18181b]/95 backdrop-blur-xl border border-zinc-200/90 dark:border-zinc-750/90 shadow-2xl p-1.5 text-xs text-zinc-800 dark:text-zinc-200 select-none animate-in fade-in zoom-in-95 duration-100"
        :style="adjustedPosition.style"
        @contextmenu.prevent
      >
        <div class="space-y-0.5">
          <!-- 1. Quick notes -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 font-medium transition-colors cursor-pointer group text-left"
            @mouseenter="activeSubmenu = 'none'"
            @click="emit('quick-notes', student); emit('close')"
          >
            <div class="flex items-center gap-2 min-w-0">
              <StickyNote class="w-3.5 h-3.5 text-amber-500 shrink-0" />
              <span class="truncate">Quick notes</span>
            </div>
            <span
              v-if="student.quick_notes && student.quick_notes.trim()"
              class="w-4 h-4 rounded-full bg-amber-500/20 text-amber-600 dark:text-amber-400 font-black text-[10px] flex items-center justify-center shrink-0"
              title="Has quick note"
            >
              !
            </span>
          </button>

          <!-- 2. Assign to Folder > (Hover Submenu) -->
          <div
            class="relative"
            @mouseenter="openSubmenu('folders')"
            @mouseleave="scheduleCloseSubmenu"
          >
            <button
              type="button"
              class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 font-medium transition-colors cursor-pointer group text-left"
              :class="activeSubmenu === 'folders' ? 'bg-zinc-100 dark:bg-zinc-800' : ''"
            >
              <div class="flex items-center gap-2 min-w-0">
                <FolderIcon class="w-3.5 h-3.5 text-blue-500 shrink-0" />
                <span class="truncate">Assign to Folder</span>
              </div>
              <ChevronRight class="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            </button>

            <!-- Folders Submenu Panel -->
            <div
              v-if="activeSubmenu === 'folders'"
              class="absolute top-0 w-[200px] rounded-xl bg-white/95 dark:bg-[#18181b]/95 backdrop-blur-xl border border-zinc-200/90 dark:border-zinc-750/90 shadow-2xl p-1.5 text-xs text-zinc-800 dark:text-zinc-200 z-[105]"
              :class="adjustedPosition.submenuOnLeft ? 'right-full mr-1.5 before:absolute before:-right-3 before:top-0 before:bottom-0 before:w-4' : 'left-full ml-1.5 before:absolute before:-left-3 before:top-0 before:bottom-0 before:w-4'"
              @mouseenter="cancelCloseSubmenu"
              @mouseleave="scheduleCloseSubmenu"
            >
              <!-- All (No Folder) Option -->
              <button
                type="button"
                @click="emit('clear-folders', student); emit('close')"
                class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-left"
                :class="(!student.folder_ids || student.folder_ids.length === 0) ? 'font-bold text-blue-600 dark:text-blue-400 bg-blue-50/60 dark:bg-blue-950/40' : ''"
              >
                <span class="truncate">📁 All (No Folder)</span>
                <Check v-if="!student.folder_ids || student.folder_ids.length === 0" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
              </button>

              <div class="my-1 border-t border-zinc-100 dark:border-zinc-800" />

              <!-- Folder List -->
              <div class="max-h-56 overflow-y-auto space-y-0.5 scrollbar-thin">
                <button
                  v-for="folder in folders"
                  :key="folder.id"
                  type="button"
                  @click="emit('toggle-folder', String(folder.id), student)"
                  class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-left"
                  :class="isFolderActive(folder.id) ? 'font-bold text-blue-600 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-950/30' : ''"
                >
                  <span class="truncate">📁 {{ folder.name }}</span>
                  <Check v-if="isFolderActive(folder.id)" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
                </button>
              </div>
            </div>
          </div>

          <!-- 3. Custom tags > (Hover Submenu) -->
          <div
            class="relative"
            @mouseenter="openSubmenu('tags')"
            @mouseleave="scheduleCloseSubmenu"
          >
            <button
              type="button"
              class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 font-medium transition-colors cursor-pointer group text-left"
              :class="activeSubmenu === 'tags' ? 'bg-zinc-100 dark:bg-zinc-800' : ''"
            >
              <div class="flex items-center gap-2 min-w-0">
                <Tag class="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                <span class="truncate">Custom tags</span>
              </div>
              <ChevronRight class="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            </button>

            <!-- Tags Submenu Panel -->
            <div
              v-if="activeSubmenu === 'tags'"
              class="absolute top-0 w-[200px] rounded-xl bg-white/95 dark:bg-[#18181b]/95 backdrop-blur-xl border border-zinc-200/90 dark:border-zinc-750/90 shadow-2xl p-1.5 text-xs text-zinc-800 dark:text-zinc-200 z-[105]"
              :class="adjustedPosition.submenuOnLeft ? 'right-full mr-1.5 before:absolute before:-right-3 before:top-0 before:bottom-0 before:w-4' : 'left-full ml-1.5 before:absolute before:-left-3 before:top-0 before:bottom-0 before:w-4'"
              @mouseenter="cancelCloseSubmenu"
              @mouseleave="scheduleCloseSubmenu"
            >
              <div v-if="customTagsRegistry.length === 0" class="px-2 py-1.5 text-zinc-400 text-[11px] italic">
                No custom tags
              </div>
              <div v-else class="max-h-56 overflow-y-auto space-y-0.5 scrollbar-thin">
                <button
                  v-for="tag in customTagsRegistry"
                  :key="tag.name"
                  type="button"
                  @click="emit('toggle-tag', tag.name, student)"
                  class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-left"
                  :class="isTagActive(tag.name) ? 'font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/30' : ''"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <span class="shrink-0 text-sm leading-none">{{ tag.icon }}</span>
                    <span class="truncate">{{ tag.name }}</span>
                  </div>
                  <Check v-if="isTagActive(tag.name)" class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 ml-1" />
                </button>
              </div>
            </div>
          </div>

          <div class="my-1 border-t border-zinc-100 dark:border-zinc-800/80" />

          <!-- 4. Quick Actions Modal Trigger -->
          <button
            type="button"
            class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-400 font-medium transition-colors cursor-pointer text-left"
            @mouseenter="activeSubmenu = 'none'"
            @click="emit('open-actions', student); emit('close')"
          >
            <SlidersHorizontal class="w-3.5 h-3.5 shrink-0" />
            <span class="truncate">Full quick actions...</span>
          </button>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

