<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Student, Folder } from '@/types'
import { ROW_COLOR_MAP } from '@/types'
import BaseModal from '@/components/common/BaseModal.vue'
import {
  Palette, Folder as FolderIcon, Archive, RefreshCw,
  Trash2, AlertTriangle, Check
} from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  student: Student | null
  folders: Folder[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'set-color', color: string | null): void
  (e: 'set-folders', folderIds: string[]): void
  (e: 'archive'): void
  (e: 'restore'): void
  (e: 'permanent-delete'): void
}>()

const selectedFolderIds = ref<string[]>([])
const isPermanentConfirmOpen = ref(false)

watch(() => props.student, (newVal) => {
  if (newVal) {
    selectedFolderIds.value = [...(newVal.folder_ids || [])]
  }
}, { immediate: true })

const toggleFolder = (folderId: string) => {
  if (selectedFolderIds.value.includes(folderId)) {
    selectedFolderIds.value = selectedFolderIds.value.filter(id => id !== folderId)
  } else {
    selectedFolderIds.value.push(folderId)
  }
  emit('set-folders', selectedFolderIds.value)
}
</script>

<template>
  <div>
    <BaseModal
      :is-open="isOpen"
      :title="`Manage Student: ${student?.full_name || ''}`"
      :subtitle="`ID: ${student?.id || ''} &bull; Options and quick actions`"
      max-width="max-w-lg"
      @close="emit('close')"
    >
      <div v-if="student" class="space-y-6 text-xs select-none">
        <!-- 1. Row Color Selector -->
        <div>
          <div class="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10.5px] text-zinc-400 mb-2.5">
            <Palette class="w-3.5 h-3.5 text-brand-500" />
            <span>Select Row Highlight Color</span>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <button
              @click="emit('set-color', null)"
              class="px-2.5 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition-all"
              :class="!student.row_color ? 'border-zinc-900 bg-zinc-900 text-white dark:border-white dark:bg-white dark:text-zinc-900' : 'border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300'"
            >
              Default (None)
            </button>

            <button
              v-for="(data, name) in ROW_COLOR_MAP"
              :key="name"
              @click="emit('set-color', String(name))"
              class="w-7 h-7 rounded-full border-2 transition-all cursor-pointer flex items-center justify-center shadow-xs"
              :style="{ backgroundColor: data.ball, borderColor: student.row_color?.toUpperCase() === name ? '#000' : 'transparent' }"
              :title="data.name"
            >
              <Check v-if="student.row_color?.toUpperCase() === name" class="w-3.5 h-3.5 text-white" />
            </button>
          </div>
        </div>

        <!-- 2. Folder Assignment -->
        <div>
          <div class="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10.5px] text-zinc-400 mb-2.5">
            <FolderIcon class="w-3.5 h-3.5 text-brand-500" />
            <span>Assign to Folders</span>
          </div>
          <div v-if="folders.length > 0" class="flex flex-wrap gap-2">
            <button
              v-for="f in folders"
              :key="f.id"
              @click="toggleFolder(f.id)"
              class="px-3 py-1.5 rounded-xl border text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5"
              :class="selectedFolderIds.includes(f.id) ? 'bg-brand-500 text-white border-brand-500 shadow-xs' : 'bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100'"
            >
              <FolderIcon class="w-3.5 h-3.5" />
              <span>{{ f.name }}</span>
              <Check v-if="selectedFolderIds.includes(f.id)" class="w-3 h-3" />
            </button>
          </div>
          <div v-else class="text-zinc-400 italic">No folders created yet.</div>
        </div>

        <!-- 3. Status & Archive / Delete Operations -->
        <div class="pt-4 border-t border-zinc-100 dark:border-zinc-800 space-y-2">
          <div class="font-bold uppercase tracking-wider text-[10.5px] text-zinc-400 mb-1">Status & Archive Actions</div>

          <!-- Archive or Restore Button -->
          <button
            v-if="!student.is_deleted"
            @click="emit('archive')"
            class="w-full flex items-center justify-between p-3 rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-950/20 text-amber-800 dark:text-amber-300 hover:bg-amber-100/60 font-bold transition-colors cursor-pointer"
          >
            <div class="flex items-center gap-2">
              <Archive class="w-4 h-4" />
              <span>Archive Student (Move to Deleted Roster)</span>
            </div>
          </button>

          <button
            v-else
            @click="emit('restore')"
            class="w-full flex items-center justify-between p-3 rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/50 dark:bg-emerald-950/20 text-emerald-800 dark:text-emerald-300 hover:bg-emerald-100/60 font-bold transition-colors cursor-pointer"
          >
            <div class="flex items-center gap-2">
              <RefreshCw class="w-4 h-4" />
              <span>Restore to Active Students</span>
            </div>
          </button>

          <!-- Permanent Delete Button -->
          <button
            @click="isPermanentConfirmOpen = true"
            class="w-full flex items-center justify-between p-3 rounded-xl border border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 hover:bg-rose-100/60 font-bold transition-colors cursor-pointer"
          >
            <div class="flex items-center gap-2">
              <Trash2 class="w-4 h-4" />
              <span>Permanently Delete Student</span>
            </div>
          </button>
        </div>
      </div>
    </BaseModal>

    <!-- Permanent Delete Confirmation Dialog -->
    <BaseModal
      :is-open="isPermanentConfirmOpen"
      title="Confirm Permanent Deletion"
      subtitle="This action cannot be undone."
      max-width="max-w-md"
      @close="isPermanentConfirmOpen = false"
    >
      <div class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 flex items-start gap-2.5">
          <AlertTriangle class="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
          <p class="leading-relaxed">
            Are you sure you want to permanently delete <strong>{{ student?.full_name }}</strong> (ID: <strong>{{ student?.id }}</strong>)? All associated records will be permanently removed.
          </p>
        </div>

        <div class="flex items-center justify-end gap-2.5 pt-2">
          <button
            @click="isPermanentConfirmOpen = false"
            class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-bold cursor-pointer hover:bg-zinc-100"
          >
            Cancel
          </button>
          <button
            @click="() => { emit('permanent-delete'); isPermanentConfirmOpen = false; }"
            class="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold cursor-pointer shadow-md shadow-rose-600/20"
          >
            Permanently Delete
          </button>
        </div>
      </div>
    </BaseModal>
  </div>
</template>
