<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { Sparkles, Plus, Loader2, Pencil, X, Check } from 'lucide-vue-next'
import {
  useQuickNoteSuggestions,
  type QuickNoteSuggestionItem,
} from '@/composables/useQuickNoteSuggestions'

const props = withDefaults(defineProps<{
  filterText?: string
  maxHeightClass?: string
}>(), {
  filterText: '',
  maxHeightClass: 'max-h-[300px]',
})

const emit = defineEmits<{
  (e: 'select', text: string): void
}>()

const {
  suggestions,
  isLoading,
  fetchSuggestions,
  addSuggestion,
  updateSuggestion,
  deleteSuggestion,
  getFilteredSuggestions,
} = useQuickNoteSuggestions()

onMounted(() => {
  fetchSuggestions()
})

const filteredItems = computed(() => {
  return getFilteredSuggestions(props.filterText)
})

// Separate Modal State for Add / Edit
const isModalOpen = ref(false)
const editingItem = ref<QuickNoteSuggestionItem | null>(null)
const modalText = ref('')
const modalInputRef = ref<HTMLTextAreaElement | null>(null)
const isSubmitting = ref(false)

const openAddModal = () => {
  editingItem.value = null
  modalText.value = ''
  isModalOpen.value = true
  nextTick(() => {
    modalInputRef.value?.focus()
  })
}

const openEditModal = (item: QuickNoteSuggestionItem) => {
  editingItem.value = item
  modalText.value = item.text
  isModalOpen.value = true
  nextTick(() => {
    modalInputRef.value?.focus()
    modalInputRef.value?.select()
  })
}

const closeModal = () => {
  isModalOpen.value = false
  editingItem.value = null
  modalText.value = ''
}

const handleModalSave = async () => {
  const text = modalText.value.trim()
  if (!text) return
  isSubmitting.value = true
  try {
    if (editingItem.value) {
      await updateSuggestion(editingItem.value.id, text)
    } else {
      await addSuggestion(text)
    }
    closeModal()
  } finally {
    isSubmitting.value = false
  }
}

const handleDelete = async (item: QuickNoteSuggestionItem) => {
  if (!confirm(`Are you sure you want to delete suggestion "${item.text}"?`)) return
  await deleteSuggestion(item.id)
}
</script>

<template>
  <div class="flex flex-col h-full space-y-2">
    <!-- Header: Title + Add Trigger -->
    <div class="flex items-center justify-between pb-0.5">
      <div class="flex items-center gap-1.5 text-[11px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider select-none">
        <Sparkles class="w-3.5 h-3.5 text-amber-500 shrink-0" />
        <span>SUGGESTIONS:</span>
      </div>

      <button
        type="button"
        @click="openAddModal"
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/50 transition-colors cursor-pointer select-none"
        title="Add new suggestion template"
      >
        <Plus class="w-3.5 h-3.5 stroke-[2.5]" />
        <span>Add</span>
      </button>
    </div>

    <!-- Vertical List of Suggestions: Suggestion A (Edit, Delete) -->
    <div
      class="flex flex-col gap-1.5 overflow-y-auto scrollbar-thin pr-1"
      :class="maxHeightClass"
    >
      <div v-if="isLoading && suggestions.length === 0" class="flex items-center gap-1.5 py-3 text-xs text-zinc-400">
        <Loader2 class="w-3.5 h-3.5 animate-spin text-amber-500" />
        <span>Loading suggestions...</span>
      </div>

      <div
        v-for="item in filteredItems"
        :key="item.id"
        class="group/sug relative flex items-center justify-between gap-3 px-3 py-2 rounded-xl border border-zinc-200/90 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-850/70 hover:bg-amber-50/50 dark:hover:bg-amber-950/20 hover:border-amber-300/80 dark:hover:border-amber-700/60 transition-all text-xs"
      >
        <!-- Suggestion Text (Click to insert) -->
        <button
          type="button"
          @click="emit('select', item.text)"
          class="flex-1 text-left font-medium text-zinc-800 dark:text-zinc-200 hover:text-amber-800 dark:hover:text-amber-300 transition-colors cursor-pointer text-xs leading-snug break-words"
          :title="`Click to insert: ${item.text}`"
        >
          <span class="text-amber-500 font-bold mr-1.5 select-none">+</span>
          <span>{{ item.text }}</span>
        </button>

        <!-- (Edit, Delete) Buttons -->
        <div class="flex items-center gap-1.5 shrink-0 text-[11px] select-none">
          <button
            type="button"
            @click.stop="openEditModal(item)"
            class="px-2 py-0.5 rounded-md text-blue-600 dark:text-blue-400 hover:bg-blue-100/60 dark:hover:bg-blue-950/60 font-semibold transition-colors cursor-pointer"
            title="Edit suggestion"
          >
            Edit
          </button>
          <span class="text-zinc-300 dark:text-zinc-700">|</span>
          <button
            type="button"
            @click.stop="handleDelete(item)"
            class="px-2 py-0.5 rounded-md text-rose-600 dark:text-rose-400 hover:bg-rose-100/60 dark:hover:bg-rose-950/60 font-semibold transition-colors cursor-pointer"
            title="Delete suggestion"
          >
            Delete
          </button>
        </div>
      </div>

      <div
        v-if="!isLoading && filteredItems.length === 0"
        class="py-4 text-center text-xs text-zinc-400 italic"
      >
        No matching suggestions. Click "+ Add" to create one.
      </div>
    </div>

    <!-- SEPARATE MODAL: Edit / Add Suggestion Modal Dialog -->
    <Teleport to="body">
      <transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="isModalOpen"
          class="fixed inset-0 z-[140] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none"
          @click.self="closeModal"
        >
          <div
            class="relative w-full max-w-md rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl p-5 space-y-4 text-zinc-900 dark:text-zinc-100"
            @click.stop
          >
            <!-- Modal Header -->
            <div class="flex items-center justify-between pb-1 border-b border-zinc-100 dark:border-zinc-800">
              <h4 class="text-sm font-bold flex items-center gap-2 text-zinc-900 dark:text-zinc-100">
                <Pencil v-if="editingItem" class="w-4 h-4 text-amber-500" />
                <Plus v-else class="w-4 h-4 text-blue-500" />
                <span>{{ editingItem ? 'Edit Suggestion Template' : 'New Suggestion Template' }}</span>
              </h4>
              <button
                type="button"
                @click="closeModal"
                class="p-1 rounded-lg text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors cursor-pointer"
              >
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- Modal Body: Textarea -->
            <div class="space-y-1.5">
              <label class="block text-[11px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
                Template Text
              </label>
              <textarea
                ref="modalInputRef"
                v-model="modalText"
                rows="3"
                placeholder="Enter suggestion template..."
                class="w-full px-3 py-2 text-xs rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all resize-y select-text"
                @keydown.ctrl.enter.prevent="handleModalSave"
                @keydown.enter.exact.prevent="handleModalSave"
                @keydown.esc.prevent="closeModal"
              />
              <p class="text-[10px] text-zinc-400">Press Enter or Ctrl+Enter to save</p>
            </div>

            <!-- Modal Footer -->
            <div class="flex items-center justify-end gap-2 pt-1 border-t border-zinc-100 dark:border-zinc-800">
              <button
                type="button"
                @click="closeModal"
                class="px-4 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 font-semibold text-xs hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                @click="handleModalSave"
                :disabled="isSubmitting || !modalText.trim()"
                class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-xs shadow-xs transition-all cursor-pointer active:scale-95"
              >
                <Loader2 v-if="isSubmitting" class="w-3.5 h-3.5 animate-spin" />
                <Check v-else class="w-3.5 h-3.5 stroke-[2.5]" />
                <span>{{ editingItem ? 'Save Changes' : 'Add Template' }}</span>
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>
