<script setup lang="ts">
import { ref } from 'vue'
import type { Folder } from '@/types'
import { Folder as FolderIcon, Plus, EyeOff, Trash2, Layers } from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'

const props = defineProps<{
  folders: Folder[]
  activeFolder: string
  totalCount?: number
  isDeletedActive?: boolean
  isHiddenActive?: boolean
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
</script>

<template>
  <div class="flex items-center gap-1.5 overflow-x-auto py-1 select-none text-xs">
    <!-- All Students Tab -->
    <button
      @click="emit('select', 'all')"
      class="px-3.5 py-1.5 rounded-xl font-bold border transition-all cursor-pointer flex items-center gap-1.5 shrink-0"
      :class="activeFolder === 'all' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 border-transparent shadow-xs' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
    >
      <Layers class="w-3.5 h-3.5" />
      <span>All Students</span>
    </button>

    <!-- Except Folders Tab -->
    <button
      @click="emit('select', 'except')"
      class="px-3.5 py-1.5 rounded-xl font-bold border transition-all cursor-pointer flex items-center gap-1.5 shrink-0"
      :class="activeFolder === 'except' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 border-transparent shadow-xs' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
    >
      <span>Except Folders</span>
    </button>

    <!-- Custom Folder Tabs -->
    <button
      v-for="f in folders"
      :key="f.id"
      @click="emit('select', f.id)"
      class="px-3.5 py-1.5 rounded-xl font-bold border transition-all cursor-pointer flex items-center gap-1.5 shrink-0"
      :class="activeFolder === f.id ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
    >
      <FolderIcon class="w-3.5 h-3.5" />
      <span>{{ f.name }}</span>
      <span
        v-if="f.student_count !== undefined"
        class="px-1.5 py-0.2 rounded-full text-[10px]"
        :class="activeFolder === f.id ? 'bg-white/20 text-white' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500'"
      >
        {{ f.student_count }}
      </span>
    </button>

    <!-- + Add Folder Button -->
    <button
      @click="isCreateModalOpen = true"
      class="px-2.5 py-1.5 rounded-xl font-bold border border-dashed border-zinc-300 dark:border-zinc-700 text-zinc-500 hover:text-brand-500 hover:border-brand-500 transition-colors cursor-pointer flex items-center gap-1 shrink-0"
      title="Create New Folder"
    >
      <Plus class="w-3.5 h-3.5" />
      <span>Folder</span>
    </button>

    <!-- Hidden & Archive Tabs on right -->
    <div class="ml-auto flex items-center gap-1.5 pl-2 shrink-0">
      <button
        @click="emit('select', 'hidden')"
        class="px-3 py-1.5 rounded-xl font-bold border transition-all cursor-pointer flex items-center gap-1.5"
        :class="activeFolder === 'hidden' ? 'bg-amber-500 text-white border-amber-500 shadow-xs' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/20'"
      >
        <EyeOff class="w-3.5 h-3.5" />
        <span>Hidden</span>
      </button>

      <button
        @click="emit('select', 'deleted')"
        class="px-3 py-1.5 rounded-xl font-bold border transition-all cursor-pointer flex items-center gap-1.5"
        :class="activeFolder === 'deleted' ? 'bg-rose-600 text-white border-rose-600 shadow-xs' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20'"
      >
        <Trash2 class="w-3.5 h-3.5" />
        <span>Archive</span>
      </button>
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
            placeholder="e.g. VIP 2026, Fall Intake"
            required
            class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-medium focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
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
            class="px-4 py-1.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold shadow-xs cursor-pointer"
          >
            Create Folder
          </button>
        </div>
      </form>
    </BaseModal>
  </div>
</template>
