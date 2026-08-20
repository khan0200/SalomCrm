import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useStudentDashboardStore = defineStore('studentDashboard', () => {
  const searchQuery = ref('')
  const searchMode = ref<'all' | 'id'>('all')
  const isFilterPanelOpen = ref(false)
  const isAddStudentModalOpen = ref(false)
  const isExcelModalOpen = ref(false)
  const isExcelExporting = ref(false)

  // Filters
  const selectedTariffs = ref<string[]>([])
  const selectedLevels = ref<string[]>([])
  const selectedGroups = ref<string[]>([])
  const selectedCerts = ref<string[]>([])
  const selectedScores = ref<string[]>([])
  const selectedTags = ref<string[]>([])
  const selectedLeads = ref<string[]>([])

  const activeFiltersCount = computed(() => {
    return (
      selectedTariffs.value.length +
      selectedLevels.value.length +
      selectedGroups.value.length +
      selectedCerts.value.length +
      selectedScores.value.length +
      selectedTags.value.length +
      selectedLeads.value.length
    )
  })

  const resetAllFilters = () => {
    searchQuery.value = ''
    selectedTariffs.value = []
    selectedLevels.value = []
    selectedGroups.value = []
    selectedCerts.value = []
    selectedScores.value = []
    selectedTags.value = []
    selectedLeads.value = []
  }

  // Export event trigger callback
  const onExportExcel = ref<(() => void) | null>(null)

  const triggerExportExcel = () => {
    if (onExportExcel.value) {
      onExportExcel.value()
    }
  }

  return {
    searchQuery,
    searchMode,
    isFilterPanelOpen,
    isAddStudentModalOpen,
    isExcelModalOpen,
    isExcelExporting,
    selectedTariffs,
    selectedLevels,
    selectedGroups,
    selectedCerts,
    selectedScores,
    selectedTags,
    selectedLeads,
    activeFiltersCount,
    resetAllFilters,
    onExportExcel,
    triggerExportExcel,
  }
})
