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
  const selectedBranches = ref<string[]>([])
  const selectedCerts = ref<string[]>([])
  const selectedScores = ref<string[]>([])
  const selectedCertScores = ref<Record<string, string[]>>({})
  const selectedTags = ref<string[]>([])
  const selectedLeads = ref<string[]>([])
  const selectedCoordinators = ref<string[]>([])
  const selectedMissingDocs = ref<string[]>([])

  const activeFiltersCount = computed(() => {
    let count = 0
    if (selectedTariffs.value.length > 0) count++
    if (selectedLevels.value.length > 0) count++
    if (selectedGroups.value.length > 0) count++
    if (selectedBranches.value.length > 0) count++
    if (selectedCerts.value.length > 0 || Object.keys(selectedCertScores.value).length > 0) count++
    if (selectedScores.value.length > 0) count++
    if (selectedTags.value.length > 0) count++
    if (selectedLeads.value.length > 0) count++
    if (selectedCoordinators.value.length > 0) count++
    if (selectedMissingDocs.value.length > 0) count++
    return count
  })

  const resetAllFilters = () => {
    searchQuery.value = ''
    selectedTariffs.value = []
    selectedLevels.value = []
    selectedGroups.value = []
    selectedBranches.value = []
    selectedCerts.value = []
    selectedScores.value = []
    selectedCertScores.value = {}
    selectedTags.value = []
    selectedLeads.value = []
    selectedCoordinators.value = []
    selectedMissingDocs.value = []
  }

  // Export event trigger callback
  const onExportExcel = ref<(() => void) | null>(null)

  // Bulk Excel export helpers (e.g. via AI prompt /excel f1,f2)
  const excelInitialSelectedIds = ref<string[]>([])
  const excelAutoOpenFieldPicker = ref<boolean>(false)

  const openExportWithSelection = (ids: string[], autoOpenFields = true) => {
    excelInitialSelectedIds.value = [...ids]
    excelAutoOpenFieldPicker.value = autoOpenFields
    isExcelModalOpen.value = true
  }

  const triggerExportExcel = () => {
    if (onExportExcel.value) {
      onExportExcel.value()
    }
  }

  // Visa Check Filters
  const visaTypeFilter = ref<'all' | 'Embassy' | 'E-Visa' | 'Regional'>('all')
  const visaTypeCounts = ref<Record<string, number>>({
    all: 0,
    Embassy: 0,
    'E-Visa': 0,
    Regional: 0,
  })

  return {
    searchQuery,
    searchMode,
    isFilterPanelOpen,
    isAddStudentModalOpen,
    isExcelModalOpen,
    isExcelExporting,
    visaTypeFilter,
    visaTypeCounts,
    selectedTariffs,
    selectedLevels,
    selectedGroups,
    selectedBranches,
    selectedCerts,
    selectedScores,
    selectedCertScores,
    selectedTags,
    selectedLeads,
    selectedCoordinators,
    selectedMissingDocs,
    activeFiltersCount,
    resetAllFilters,
    onExportExcel,
    triggerExportExcel,
    excelInitialSelectedIds,
    excelAutoOpenFieldPicker,
    openExportWithSelection,
  }
})
