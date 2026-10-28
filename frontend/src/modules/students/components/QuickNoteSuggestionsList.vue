<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { Sparkles, Plus, Pencil, Trash2, X, Check, Loader2 } from 'lucide-vue-next'
import {
  useQuickNoteSuggestions,
  type QuickNoteSuggestionItem,
} from '@/composables/useQuickNoteSuggestions'

const props = withDefaults(defineProps<{
  filterText?: string
  maxHeightClass?: string
}>(), {
  filterText: '',
  maxHeightClass: 'max-h-36',
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

// Add New Suggestion State
const isAdding = ref(false)
const newText = ref('')
const addInputRef = ref<HTMLInputElement | null>(null)
const isSubmittingAdd = ref(false)

const openAdd = () => {
  isAdding.value = true
  newText.value = ''
  nextTick(() => {
    addInputRef.value?.focus()
  })
}

const handleSaveNew = async () => {
  const text = newText.value.trim()
  if (!text) {
    isAdding.value = false
    return
  }
  isSubmittingAdd.value = true
  try {
    await addSuggestion(text)
    newText.value = ''
    isAdding.value = false
  } finally {
    isSubmittingAdd.value = false
  }
}

const cancelAdd = () => {
  isAdding.value = false
  newText.value = ''
}

// Edit Existing Suggestion State
const editingId = ref<string | number | null>(null)
const editingText = ref('')
const editInputRef = ref<HTMLInputElement | null>(null)
const isSubmittingEdit = ref(false)

const startEdit = (item: QuickNoteSuggestionItem) => {
  editingId.value = item.id
  editingText.value = item.text
  nextTick(() => {
    editInputRef.value?.focus()
    editInputRef.value?.select()
  })
}

const handleSaveEdit = async (item: QuickNoteSuggestionItem) => {
  const text = editingText.value.trim()
  if (!text) {
    cancelEdit()
    return
  }
  isSubmittingEdit.value = true
  try {
    await updateSuggestion(item.id, text)
    editingId.value = null
    editingText.value = ''
  } finally {
    isSubmittingEdit.value = false
  }
}

const cancelEdit = () => {
  editingId.value = null
  editingText.value = ''
}

const handleDelete = async (item: QuickNoteSuggestionItem) => {
  if (!confirm(`Delete suggestion "${item.text}"?`)) return
  await deleteSuggestion(item.id)
}
</script>

<template>
  <div class="space-y-1.5 pt-1">
    <!-- Header: Title + Add Trigger -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-1 text-[10.5px] font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider select-none">
        <Sparkles class="w-3 h-3 text-amber-500" />
        <span>Suggestions (Click to insert):</span>
      </div>

      <button
        v-if="!isAdding"
        type="button"
        @click="openAdd"
        class="inline-flex items-center gap-0.5 text-[10.5px] font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors cursor-pointer select-none"
        title="Add new template"
      >
        <Plus class="w-3 h-3 stroke-[2.5]" />
        <span>Add</span>
      </button>
    </div>

    <!-- Inline Add New Template Form -->
    <div v-if="isAdding" class="flex items-center gap-1.5 py-1">
      <input
        ref="addInputRef"
        v-model="newText"
        type="text"
        placeholder="Type new suggestion template..."
        class="flex-1 px-2.5 py-1 text-xs rounded-lg border border-blue-400 dark:border-blue-600 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        @keydown.enter.prevent="handleSaveNew"
        @keydown.esc.prevent="cancelAdd"
      />
      <button
        type="button"
        @click="handleSaveNew"
        :disabled="isSubmittingAdd || !newText.trim()"
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-[11px] transition-all cursor-pointer shadow-2xs"
      >
        <Loader2 v-if="isSubmittingAdd" class="w-3 h-3 animate-spin" />
        <span>Save</span>
      </button>
      <button
        type="button"
        @click="cancelAdd"
        class="p-1 rounded text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 text-xs transition-colors cursor-pointer"
        title="Cancel"
      >
        <X class="w-3.5 h-3.5" />
      </button>
    </div>

    <!-- Chips Container -->
    <div
      class="flex flex-wrap gap-1.5 overflow-y-auto scrollbar-thin py-0.5"
      :class="maxHeightClass"
    >
      <div v-if="isLoading && suggestions.length === 0" class="flex items-center gap-1.5 py-2 text-xs text-zinc-400">
        <Loader2 class="w-3.5 h-3.5 animate-spin text-amber-500" />
        <span>Loading suggestions...</span>
      </div>

      <div
        v-for="item in filteredItems"
        :key="item.id"
        class="inline-flex items-center"
      >
        <!-- 1. Inline Edit Mode for this Chip -->
        <div
          v-if="editingId === item.id"
          class="inline-flex items-center gap-1 px-1 py-0.5 rounded-lg border-2 border-blue-500 bg-white dark:bg-zinc-800 shadow-xs"
        >
          <input
            ref="editInputRef"
            v-model="editingText"
            type="text"
            class="px-1.5 py-0.5 text-[11px] bg-transparent text-zinc-900 dark:text-zinc-100 focus:outline-none min-w-[140px] max-w-[240px]"
            @keydown.enter.prevent="handleSaveEdit(item)"
            @keydown.esc.prevent="cancelEdit"
          />
          <button
            type="button"
            @click="handleSaveEdit(item)"
            :disabled="isSubmittingEdit"
            class="p-1 text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 rounded hover:bg-emerald-50 dark:hover:bg-emerald-950/50 cursor-pointer transition-colors"
            title="Save edit"
          >
            <Check class="w-3 h-3 stroke-[2.5]" />
          </button>
          <button
            type="button"
            @click="cancelEdit"
            class="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 rounded cursor-pointer transition-colors"
            title="Cancel"
          >
            <X class="w-3 h-3" />
          </button>
        </div>

        <!-- 2. Normal Chip View with Edit & Delete Actions -->
        <div
          v-else
          class="group/sug relative inline-flex items-center rounded-lg border border-zinc-200 dark:border-zinc-700/80 bg-zinc-50 dark:bg-zinc-800/60 hover:border-amber-300 dark:hover:border-amber-700 text-zinc-700 dark:text-zinc-300 hover:text-amber-900 dark:hover:text-amber-100 transition-all text-[11px]"
        >
          <!-- Main Clickable Text to Insert -->
          <button
            type="button"
            @click="emit('select', item.text)"
            class="inline-flex items-center gap-1 pl-2.5 pr-1.5 py-1 font-medium hover:bg-amber-50 dark:hover:bg-amber-950/40 rounded-l-lg transition-colors cursor-pointer text-left"
            :title="`Click to insert: ${item.text}`"
          >
            <span class="text-amber-500 font-bold select-none">+</span>
            <span class="select-none">{{ item.text }}</span>
          </button>

          <!-- Edit & Delete Action Buttons (revealed subtly on hover) -->
          <div class="flex items-center gap-0.5 pr-1 pl-0.5 border-l border-zinc-200/60 dark:border-zinc-700/60 opacity-40 group-hover/sug:opacity-100 transition-opacity">
            <button
              type="button"
              @click.stop="startEdit(item)"
              class="p-1 text-zinc-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/50 rounded transition-colors cursor-pointer"
              title="Edit suggestion"
            >
              <Pencil class="w-2.5 h-2.5" />
            </button>
            <button
              type="button"
              @click.stop="handleDelete(item)"
              class="p-1 text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50 rounded transition-colors cursor-pointer"
              title="Delete suggestion"
            >
              <X class="w-2.5 h-2.5 stroke-[2.5]" />
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="!isLoading && filteredItems.length === 0"
        class="py-1 text-[11px] text-zinc-400 italic"
      >
        No matching suggestions. Click "+ Add" to create one.
      </div>
    </div>
  </div>
</template>
