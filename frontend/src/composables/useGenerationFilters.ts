import { ref } from 'vue'

export const CERT_OPTIONS = ['NO CERTIFICATE', 'EXPECTED', 'TOPIK', 'IELTS', 'TOEFL', 'CEFR', 'SAT', 'SKA']
export const PREDEFINED_TAGS = ['Call', 'Apply', 'Documents', 'Payment']
export const TAG_OPTIONS = [...PREDEFINED_TAGS, 'Custom']

export type GenerationDropdownKey =
  | 'status'
  | 'folder'
  | 'tariff'
  | 'level'
  | 'group'
  | 'cert'
  | 'tag'
  | 'lead'

export const useGenerationFilters = () => {
  const searchType = ref<'all' | 'id' | 'name' | 'phone' | 'university'>('all')
  const searchQuery = ref('')
  const selectedStudentIds = ref<Set<string>>(new Set())

  const selectedStatuses = ref<string[]>(['active'])
  const selectedFolders = ref<string[]>([])
  const selectedTariffs = ref<string[]>([])
  const selectedLevels = ref<string[]>([])
  const selectedGroups = ref<string[]>([])
  const selectedCerts = ref<string[]>([])
  const selectedTags = ref<string[]>([])
  const selectedLeads = ref<string[]>([])

  const isStatusDropdownOpen = ref(false)
  const isFolderDropdownOpen = ref(false)
  const isTariffDropdownOpen = ref(false)
  const isLevelDropdownOpen = ref(false)
  const isGroupDropdownOpen = ref(false)
  const isCertDropdownOpen = ref(false)
  const isTagDropdownOpen = ref(false)
  const isLeadDropdownOpen = ref(false)

  const dropdownRefs = {
    status: isStatusDropdownOpen,
    folder: isFolderDropdownOpen,
    tariff: isTariffDropdownOpen,
    level: isLevelDropdownOpen,
    group: isGroupDropdownOpen,
    cert: isCertDropdownOpen,
    tag: isTagDropdownOpen,
    lead: isLeadDropdownOpen,
  }

  const closeAllDropdowns = () => {
    Object.values(dropdownRefs).forEach(dropdown => {
      dropdown.value = false
    })
  }

  const toggleDropdown = (key: GenerationDropdownKey) => {
    const target = dropdownRefs[key]
    const wasOpen = target.value
    closeAllDropdowns()
    target.value = !wasOpen
  }

  const toggleInList = (list: string[], value: string) => {
    const index = list.indexOf(value)
    if (index === -1) list.push(value)
    else list.splice(index, 1)
  }

  return {
    searchType,
    searchQuery,
    selectedStudentIds,
    selectedStatuses,
    selectedFolders,
    selectedTariffs,
    selectedLevels,
    selectedGroups,
    selectedCerts,
    selectedTags,
    selectedLeads,
    isStatusDropdownOpen,
    isFolderDropdownOpen,
    isTariffDropdownOpen,
    isLevelDropdownOpen,
    isGroupDropdownOpen,
    isCertDropdownOpen,
    isTagDropdownOpen,
    isLeadDropdownOpen,
    closeAllDropdowns,
    toggleDropdown,
    toggleInList,
    CERT_OPTIONS,
    PREDEFINED_TAGS,
    TAG_OPTIONS,
  }
}
