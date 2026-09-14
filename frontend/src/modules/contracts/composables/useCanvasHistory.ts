import { ref, computed } from 'vue'
import type { ContractDocumentModel } from '../types/contractCanvas'

export function useCanvasHistory(maxHistory = 50) {
  const history = ref<string[]>([])
  const currentIndex = ref<number>(-1)
  const isUpdatingFromHistory = ref(false)

  const canUndo = computed(() => currentIndex.value > 0)
  const canRedo = computed(() => currentIndex.value < history.value.length - 1)

  function recordSnapshot(doc: ContractDocumentModel) {
    if (isUpdatingFromHistory.value) return
    const serialized = JSON.stringify(doc)

    // Don't record duplicate consecutive states
    if (currentIndex.value >= 0 && history.value[currentIndex.value] === serialized) {
      return
    }

    // Truncate any redo future if we made a new action
    if (currentIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, currentIndex.value + 1)
    }

    history.value.push(serialized)
    if (history.value.length > maxHistory) {
      history.value.shift()
    } else {
      currentIndex.value++
    }
  }

  function undo(): ContractDocumentModel | null {
    if (!canUndo.value) return null
    currentIndex.value--
    isUpdatingFromHistory.value = true
    try {
      const state = JSON.parse(history.value[currentIndex.value])
      return state
    } finally {
      isUpdatingFromHistory.value = false
    }
  }

  function redo(): ContractDocumentModel | null {
    if (!canRedo.value) return null
    currentIndex.value++
    isUpdatingFromHistory.value = true
    try {
      const state = JSON.parse(history.value[currentIndex.value])
      return state
    } finally {
      isUpdatingFromHistory.value = false
    }
  }

  function clearHistory() {
    history.value = []
    currentIndex.value = -1
  }

  return {
    canUndo,
    canRedo,
    recordSnapshot,
    undo,
    redo,
    clearHistory,
    isUpdatingFromHistory,
  }
}
