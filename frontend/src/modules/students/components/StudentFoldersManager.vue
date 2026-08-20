<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Folder } from '@/types'
import { Plus, X } from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'

const props = defineProps<{
  folders: Folder[]
  activeFolder: string
  totalCount: number
  folderCounts?: Record<string, number>
}>()

const emit = defineEmits<{
  (e: 'select', folderId: string): void
  (e: 'create-folder', name: string): void
  (e: 'delete-folder', id: string): void
}>()

const isCreateModalOpen = ref(false)
const newFolderName = ref('')

const handleCreate = () => {
  if (!newFolderName.value.trim()) return
  emit('create-folder', newFolderName.value.trim())
  newFolderName.value = ''
  isCreateModalOpen.value = false
}

const activeFolderName = computed(() => {
  if (props.activeFolder === 'all') return 'All'
  if (props.activeFolder === 'except') return 'Except'
  if (props.activeFolder === 'deleted' || props.activeFolder === 'archive') return 'Archive'
  if (props.activeFolder === 'hidden') return 'Hidden'
  const f = props.folders.find(x => String(x.id) === String(props.activeFolder))
  return f ? f.name : props.activeFolder
})
</script>

<template>
  <div class="space-y-2 select-none">
    <!-- Folder Tabs Row -->
    <div class="flex items-center justify-between border-b border-zinc-200 dark:border-zinc-800 pb-2.5 px-1 overflow-x-auto scrollbar-none gap-4">
      <!-- Left Folder Tabs -->
      <div class="flex items-center gap-3 sm:gap-5 min-w-0 flex-nowrap">
        <!-- All Tab -->
        <button
          @click="emit('select', 'all')"
          class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2.5 -mb-3 border-b-2 shrink-0"
          :class="[
            activeFolder === 'all'
              ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 font-bold'
              : 'text-zinc-600 dark:text-zinc-400 border-transparent hover:text-zinc-900 dark:hover:text-zinc-100'
          ]"
        >
          <span>All</span>
          <span
            class="ml-1 text-xs font-normal"
            :class="activeFolder === 'all' ? 'text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-400 dark:text-zinc-500'"
          >
            ({{ folderCounts?.all ?? totalCount }})
          </span>
        </button>

        <!-- Custom Folder Tabs -->
        <button
          v-for="folder in folders.filter(f => f.name?.toUpperCase() !== 'KDB')"
          :key="folder.id"
          @click="emit('select', folder.id)"
          class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2.5 -mb-3 border-b-2 shrink-0"
          :class="[
            String(activeFolder) === String(folder.id)
              ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 font-bold'
              : 'text-zinc-600 dark:text-zinc-400 border-transparent hover:text-zinc-900 dark:hover:text-zinc-100'
          ]"
        >
          <span>{{ folder.name }}</span>
          <span
            class="ml-1 text-xs font-normal"
            :class="String(activeFolder) === String(folder.id) ? 'text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-400 dark:text-zinc-500'"
          >
            ({{ folderCounts?.[folder.id] ?? folder.student_count ?? 0 }})
          </span>
        </button>

        <!-- Add Folder Button -->
        <button
          @click="isCreateModalOpen = true"
          class="inline-flex items-center justify-center p-1 text-zinc-400 hover:text-blue-600 dark:hover:text-blue-400 rounded-md hover:bg-blue-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer shrink-0"
          title="Create New Folder"
        >
          <Plus class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Right Folder Tabs (Except & Archive) -->
      <div class="flex items-center gap-3 sm:gap-4 shrink-0 pl-2">
        <!-- Except Tab -->
        <button
          @click="emit('select', 'except')"
          class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2.5 -mb-3 border-b-2"
          :class="[
            activeFolder === 'except'
              ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 font-bold'
              : 'text-zinc-600 dark:text-zinc-400 border-transparent hover:text-zinc-900 dark:hover:text-zinc-100'
          ]"
        >
          <span>Except</span>
          <span
            class="ml-1 text-xs font-normal"
            :class="activeFolder === 'except' ? 'text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-400 dark:text-zinc-500'"
          >
            ({{ folderCounts?.except ?? 0 }})
          </span>
        </button>

        <!-- Archive Tab -->
        <button
          @click="emit('select', 'deleted')"
          class="relative text-sm font-semibold transition-all cursor-pointer whitespace-nowrap pb-2.5 -mb-3 border-b-2"
          :class="[
            activeFolder === 'deleted' || activeFolder === 'archive'
              ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 font-bold'
              : 'text-zinc-600 dark:text-zinc-400 border-transparent hover:text-zinc-900 dark:hover:text-zinc-100'
          ]"
        >
          <span>Archive</span>
          <span
            class="ml-1 text-xs font-normal"
            :class="activeFolder === 'deleted' || activeFolder === 'archive' ? 'text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-400 dark:text-zinc-500'"
          >
            ({{ folderCounts?.deleted ?? 0 }})
          </span>
        </button>
      </div>
    </div>

    <!-- Subtitle Bar matching the screenshot -->
    <div class="flex items-center justify-between text-[11px] text-zinc-400 dark:text-zinc-500 px-1 pt-0.5 select-none">
      <div class="italic">
        Showing all students in <span class="font-medium text-zinc-600 dark:text-zinc-300">{{ activeFolderName }}</span>
      </div>
      <div class="italic">
        Total {{ totalCount }} students
      </div>
    </div>

    <!-- Create Folder Modal -->
    <BaseModal
      :is-open="isCreateModalOpen"
      title="Create Student Folder"
      subtitle="Organize students into a custom folder."
      max-width="max-w-sm"
      @close="isCreateModalOpen = false"
    >
      <form @submit.prevent="handleCreate" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 mb-1">Folder Name</label>
          <input
            v-model="newFolderName"
            type="text"
            placeholder="e.g. Jeonju, WOOSUK, NEXT SEMESTER"
            required
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-medium focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
          />
        </div>
        <div class="flex items-center justify-end gap-2">
          <button
            type="button"
            @click="isCreateModalOpen = false"
            class="px-3.5 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-bold text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-xs cursor-pointer"
          >
            Create Folder
          </button>
        </div>
      </form>
    </BaseModal>
  </div>
</template>
