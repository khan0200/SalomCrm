<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { Sparkles, Plus, Loader2 } from 'lucide-vue-next'
import {
  useQuickNoteSuggestions,
  type QuickNoteSuggestionItem,
} from '@/composables/useQuickNoteSuggestions'

const props = withDefaults(defineProps<{
  filterText?: string
  maxHeightClass?: string
}>(), {
  filterText: '',
  maxHeightClass: 'max-h-[320px]',
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
        <span>Suggestions (Click to insert):</span>
      </div>

      <button
        v-if="!isAdding"
        type="button"
        @click="openAdd"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-bold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/50 transition-colors cursor-pointer select-none"
        title="Add new suggestion template"
      >
        <Plus class="w-3.5 h-3.5 stroke-[2.5]" />
        <span>Add</span>
      </button>
    </div>

    <!-- Inline Add New Template Form -->
    <div v-if="isAdding" class="flex items-center gap-1.5 p-1.5 rounded-xl border border-blue-300 dark:border-blue-700 bg-blue-50/40 dark:bg-blue-950/20">
      <input
        ref="addInputRef"
        v-model="newText"
        type="text"
        placeholder="Type new template..."
        class="flex-1 px-2.5 py-1 text-xs rounded-lg border border-blue-400 dark:border-blue-600 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
        @keydown.enter.prevent="handleSaveNew"
        @keydown.esc.prevent="cancelAdd"
      />
      <button
        type="button"
        @click="handleSaveNew"
        :disabled="isSubmittingAdd || !newText.trim()"
        class="px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-[11px] transition-all cursor-pointer shadow-2xs"
      >
        <Loader2 v-if="isSubmittingAdd" class="w-3 h-3 animate-spin" />
        <span v-else>Save</span>
      </button>
      <button
        type="button"
        @click="cancelAdd"
        class="p-1 rounded text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 text-xs transition-colors cursor-pointer"
        title="Cancel"
      >
        ✕
      </button>
    </div>

    <!-- Vertical List of Suggestions: Suggestion A (Edit, Delete) -->
    <div
      class="flex flex-col gap-1.5 overflow-y-auto scrollbar-thin pr-0.5"
      :class="maxHeightClass"
    >
      <div v-if="isLoading && suggestions.length === 0" class="flex items-center gap-1.5 py-3 text-xs text-zinc-400">
        <Loader2 class="w-3.5 h-3.5 animate-spin text-amber-500" />
        <span>Loading suggestions...</span>
      </div>

      <div
        v-for="item in filteredItems"
        :key="item.id"
        class="group/sug relative flex items-center justify-between gap-2 p-2 rounded-xl border border-zinc-200/90 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-850/60 hover:bg-amber-50/50 dark:hover:bg-amber-950/20 hover:border-amber-300/80 dark:hover:border-amber-700/60 transition-all text-xs"
      >
        <!-- 1. Inline Edit Mode for this row -->
        <div v-if="editingId === item.id" class="flex items-center gap-1.5 w-full">
          <input
            ref="editInputRef"
            v-model="editingText"
            type="text"
            class="flex-1 px-2.5 py-1 text-xs rounded-lg border border-blue-500 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:outline-none ring-1 ring-blue-500/20"
            @keydown.enter.prevent="handleSaveEdit(item)"
            @keydown.esc.prevent="cancelEdit"
          />
          <button
            type="button"
            @click="handleSaveEdit(item)"
            :disabled="isSubmittingEdit"
            class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px] cursor-pointer transition-colors shadow-2xs"
            title="Save edit"
          >
            Save
          </button>
          <button
            type="button"
            @click="cancelEdit"
            class="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 text-xs rounded cursor-pointer transition-colors"
            title="Cancel"
          >
            ✕
          </button>
        </div>

        <!-- 2. Normal View: Text on Left, Edit & Delete on Right -->
        <template v-else>
          <button
            type="button"
            @click="emit('select', item.text)"
            class="flex-1 text-left font-medium text-zinc-800 dark:text-zinc-200 hover:text-amber-800 dark:hover:text-amber-300 transition-colors cursor-pointer text-xs leading-snug line-clamp-2"
            :title="`Click to insert: ${item.text}`"
          >
            <span class="text-amber-500 font-bold mr-1 select-none">+</span>
            <span>{{ item.text }}</span>
          </button>

          <!-- (Edit, Delete) Buttons -->
          <div class="flex items-center gap-1 shrink-0 text-[11px] select-none">
            <button
              type="button"
              @click.stop="startEdit(item)"
              class="px-2 py-0.5 rounded text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/50 font-semibold transition-colors cursor-pointer"
              title="Edit suggestion"
            >
              Edit
            </button>
            <span class="text-zinc-300 dark:text-zinc-700">|</span>
            <button
              type="button"
              @click.stop="handleDelete(item)"
              class="px-2 py-0.5 rounded text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50 font-semibold transition-colors cursor-pointer"
              title="Delete suggestion"
            >
              Delete
            </button>
          </div>
        </template>
      </div>

      <div
        v-if="!isLoading && filteredItems.length === 0"
        class="py-3 text-center text-xs text-zinc-400 italic"
      >
        No matching suggestions. Click "+ Add" to create one.
      </div>
    </div>
  </div>
</template>
