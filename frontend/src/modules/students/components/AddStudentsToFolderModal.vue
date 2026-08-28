<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  FolderPlus,
  X,
  Search,
  ChevronDown,
  Folder as FolderIcon,
  Tag,
  GraduationCap,
  Users,
  Award,
  Contact,
  Check,
  RotateCcw
} from 'lucide-vue-next'
import type { Student, Folder } from '@/types'
import { useAlphanumericSort } from '@/composables/useAlphanumericSort'

const props = defineProps<{
  isOpen: boolean
  folderId: string
  folderName: string
  folders: Folder[]
  allStudents: Student[]
  options?: {
    tariffs: { name: string; price: number }[] | string[]
    levels: string[]
    groups: string[]
    leads: string[]
    coordinators?: string[]
    folders?: { id: string; name: string }[]
    offices?: string[]
    tags?: { id: string; name: string; icon?: string }[] | string[]
  }
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', studentIds: string[]): void
}>()

const { compareStudentIds } = useAlphanumericSort()

// ── Search & Filter State ───────────────────────────────────────────
const searchType = ref<'all' | 'id' | 'name' | 'phone' | 'university'>('all')
const searchQuery = ref('')
const selectedFolders = ref<string[]>([])
const selectedTariffs = ref<string[]>([])
const selectedLevels = ref<string[]>([])
const selectedGroups = ref<string[]>([])
const selectedCerts = ref<string[]>([])
const selectedTags = ref<string[]>([])
const selectedLeads = ref<string[]>([])

// Selection
const selectedIds = ref<string[]>([])

// Dropdown open states
const isFolderDropdownOpen = ref(false)
const isTariffDropdownOpen = ref(false)
const isLevelDropdownOpen = ref(false)
const isGroupDropdownOpen = ref(false)
const isCertDropdownOpen = ref(false)
const isTagDropdownOpen = ref(false)
const isLeadDropdownOpen = ref(false)

const closeAllDropdowns = () => {
  isFolderDropdownOpen.value = false
  isTariffDropdownOpen.value = false
  isLevelDropdownOpen.value = false
  isGroupDropdownOpen.value = false
  isCertDropdownOpen.value = false
  isTagDropdownOpen.value = false
  isLeadDropdownOpen.value = false
}

type DropdownKey = 'folder' | 'tariff' | 'level' | 'group' | 'cert' | 'tag' | 'lead'
const dropdownRefs: Record<DropdownKey, typeof isFolderDropdownOpen> = {
  folder: isFolderDropdownOpen,
  tariff: isTariffDropdownOpen,
  level: isLevelDropdownOpen,
  group: isGroupDropdownOpen,
  cert: isCertDropdownOpen,
  tag: isTagDropdownOpen,
  lead: isLeadDropdownOpen,
}

const toggleDropdown = (key: DropdownKey) => {
  const target = dropdownRefs[key]
  const wasOpen = target.value
  closeAllDropdowns()
  target.value = !wasOpen
}

const toggleInList = (list: string[], value: string) => {
  const idx = list.indexOf(value)
  if (idx === -1) list.push(value)
  else list.splice(idx, 1)
}

const CERT_OPTIONS = ['NO CERTIFICATE', 'TOPIK', 'IELTS', 'TOEFL', 'CEFR', 'SAT', 'SKA']
const PREDEFINED_TAGS = ['Call', 'Apply', 'Documents', 'Payment']
const TAG_OPTIONS = [...PREDEFINED_TAGS, 'Custom']

// Dynamic Option Sources
const tariffOptions = computed<string[]>(() => {
  const custom = (props.options?.tariffs || []).map((t: any) => typeof t === 'string' ? t : (t?.name || '')).filter(Boolean)
  const set = new Set<string>(custom)
  props.allStudents.forEach(s => { if (s.tariff) set.add(s.tariff) })
  return Array.from(set).filter(t => t !== 'NO_TARIFF' && t !== 'No Tariff').sort()
})

const levelOptions = computed<string[]>(() => {
  const custom = (props.options?.levels || []).filter(Boolean)
  const set = new Set<string>(custom)
  props.allStudents.forEach(s => { if (s.level) set.add(s.level) })
  return Array.from(set).sort()
})

const groupOptions = computed<string[]>(() => {
  const custom = (props.options?.groups || []).filter(Boolean)
  const set = new Set<string>(custom)
  props.allStudents.forEach(s => { if (s.student_group) set.add(s.student_group) })
  return Array.from(set).sort()
})

const leadOptions = computed<string[]>(() => {
  const custom = (props.options?.leads || []).filter(Boolean)
  const set = new Set<string>(custom)
  props.allStudents.forEach(s => { if (s.lead_by) set.add(s.lead_by) })
  return Array.from(set).sort()
})

// Only Active students (!s.is_deleted) who do not already belong to this target folder
const pickableStudents = computed(() => {
  const targetFolderId = String(props.folderId)
  return props.allStudents.filter(s => {
    if (s.is_deleted) return false
    const currentFolderIds = (s.folder_ids || []).map(String)
    return !currentFolderIds.includes(targetFolderId)
  })
})

// Reset state when modal opens
watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      searchQuery.value = ''
      searchType.value = 'all'
      selectedFolders.value = []
      selectedTariffs.value = []
      selectedLevels.value = []
      selectedGroups.value = []
      selectedCerts.value = []
      selectedTags.value = []
      selectedLeads.value = []
      selectedIds.value = []
      closeAllDropdowns()
    }
  },
  { immediate: true }
)

// Filtered student list
const filteredStudents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const filtered = pickableStudents.value.filter(s => {
    // 1. Search Query
    if (q) {
      if (searchType.value === 'id' && !s.id.toLowerCase().includes(q)) return false
      if (searchType.value === 'name' && !s.full_name.toLowerCase().includes(q) && !(s.korean_name || '').toLowerCase().includes(q)) return false
      if (searchType.value === 'phone' && !(s.phone1 || '').includes(q) && !(s.phone2 || '').includes(q)) return false
      if (searchType.value === 'university') {
        const unis = [s.university_1, s.university_2, s.university_3, s.university_4, s.university_5].filter(Boolean).join(' ').toLowerCase()
        if (!unis.includes(q)) return false
      }
      if (searchType.value === 'all') {
        const match = s.id.toLowerCase().includes(q) ||
          s.full_name.toLowerCase().includes(q) ||
          (s.korean_name || '').toLowerCase().includes(q) ||
          (s.passport || '').toLowerCase().includes(q) ||
          (s.phone1 || '').includes(q) ||
          (s.phone2 || '').includes(q) ||
          (s.university_1 || '').toLowerCase().includes(q)
        if (!match) return false
      }
    }

    // 2. Folders
    if (selectedFolders.value.length > 0) {
      const studentFolderIds = (s.folder_ids || []).map(String)
      const hasFolder = selectedFolders.value.some(fid => {
        if (fid === 'NO_FOLDER') return studentFolderIds.length === 0
        return studentFolderIds.includes(fid)
      })
      if (!hasFolder) return false
    }

    // 3. Tariffs
    if (selectedTariffs.value.length > 0) {
      const t = s.tariff || 'NO_TARIFF'
      if (!selectedTariffs.value.includes(t)) return false
    }

    // 4. Levels
    if (selectedLevels.value.length > 0) {
      const match = selectedLevels.value.includes(s.level || '') || selectedLevels.value.includes(s.level2 || '')
      if (!match) return false
    }

    // 5. Groups
    if (selectedGroups.value.length > 0 && !selectedGroups.value.includes(s.student_group || '')) return false

    // 6. Certificates
    if (selectedCerts.value.length > 0) {
      let matchesCert = false
      if (selectedCerts.value.includes('NO CERTIFICATE')) {
        if (!s.language_certificate || s.language_certificate === 'NO CERTIFICATE') matchesCert = true
      }
      const certs = [s.language_certificate, s.language_certificate_2, s.language_certificate_3]
      if (certs.some(c => c && c !== 'NO CERTIFICATE' && selectedCerts.value.includes(c))) matchesCert = true
      if (!matchesCert) return false
    }

    // 7. Tags
    if (selectedTags.value.length > 0) {
      const tags = s.task_tags || []
      const match = selectedTags.value.some(tag => {
        if (tag === 'Custom') return tags.some(t => !PREDEFINED_TAGS.includes(t))
        return tags.includes(tag)
      })
      if (!match) return false
    }

    // 8. Leads
    if (selectedLeads.value.length > 0 && !selectedLeads.value.includes(s.lead_by || '')) return false

    return true
  })

  return [...filtered].sort((a, b) => compareStudentIds(a.id, b.id, 'asc'))
})

// Active filter summary chips
const hasActiveFilters = computed(() =>
  selectedFolders.value.length > 0 ||
  selectedTariffs.value.length > 0 ||
  selectedLevels.value.length > 0 ||
  selectedGroups.value.length > 0 ||
  selectedCerts.value.length > 0 ||
  selectedTags.value.length > 0 ||
  selectedLeads.value.length > 0
)

const activeFilterChips = computed(() => {
  const chips: { key: string; label: string; clear: () => void }[] = []
  if (selectedFolders.value.length > 0) {
    chips.push({ key: 'folder', label: `Folder: ${selectedFolders.value.length}`, clear: () => { selectedFolders.value = [] } })
  }
  if (selectedTariffs.value.length > 0) {
    chips.push({ key: 'tariff', label: `Tariff: ${selectedTariffs.value.length}`, clear: () => { selectedTariffs.value = [] } })
  }
  if (selectedLevels.value.length > 0) {
    chips.push({ key: 'level', label: `Level: ${selectedLevels.value.length}`, clear: () => { selectedLevels.value = [] } })
  }
  if (selectedGroups.value.length > 0) {
    chips.push({ key: 'group', label: `Group: ${selectedGroups.value.length}`, clear: () => { selectedGroups.value = [] } })
  }
  if (selectedCerts.value.length > 0) {
    chips.push({ key: 'cert', label: `Cert: ${selectedCerts.value.length}`, clear: () => { selectedCerts.value = [] } })
  }
  if (selectedTags.value.length > 0) {
    chips.push({ key: 'tag', label: `Tag: ${selectedTags.value.length}`, clear: () => { selectedTags.value = [] } })
  }
  if (selectedLeads.value.length > 0) {
    chips.push({ key: 'lead', label: `Lead: ${selectedLeads.value.length}`, clear: () => { selectedLeads.value = [] } })
  }
  return chips
})

const clearAllFilters = () => {
  selectedFolders.value = []
  selectedTariffs.value = []
  selectedLevels.value = []
  selectedGroups.value = []
  selectedCerts.value = []
  selectedTags.value = []
  selectedLeads.value = []
}

const isAllFilteredSelected = computed(() => {
  if (filteredStudents.value.length === 0) return false
  return filteredStudents.value.every(s => selectedIds.value.includes(s.id))
})

const toggleSelectAll = () => {
  const currentFilteredIds = filteredStudents.value.map(s => s.id)
  if (isAllFilteredSelected.value) {
    selectedIds.value = selectedIds.value.filter(id => !currentFilteredIds.includes(id))
  } else {
    selectedIds.value = Array.from(new Set([...selectedIds.value, ...currentFilteredIds]))
  }
}

const toggleStudent = (id: string) => {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter(x => x !== id)
  } else {
    selectedIds.value.push(id)
  }
}

const handleSave = () => {
  emit('save', selectedIds.value)
}

const getOtherFolderNames = (s: Student) => {
  if (!s.folder_ids || s.folder_ids.length === 0) return []
  return s.folder_ids
    .map(fId => {
      const found = props.folders.find(f => String(f.id) === String(fId))
      return found?.name || ''
    })
    .filter(name => Boolean(name) && name.toUpperCase() !== 'KDB' && name !== props.folderName)
}

const getLevelBadgeClass = (lvl?: string | null) => {
  if (!lvl) return 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 border-zinc-200 dark:border-zinc-700'
  const u = lvl.toUpperCase()
  if (u.includes('BACHELOR') || u.includes('BAKALAVR')) {
    return 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800/60'
  }
  if (u.includes('COLLEGE') || u.includes('KASBIY')) {
    return 'bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 border-purple-200 dark:border-purple-800/60'
  }
  if (u.includes('MASTER') || u.includes('MAGISTR')) {
    return 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/60'
  }
  if (u.includes('LANG') || u.includes('TIL') || u.includes('COURSE')) {
    return 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800/60'
  }
  return 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700'
}

// Global click outside for filter popovers
const handleGlobalKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    if (isFolderDropdownOpen.value || isTariffDropdownOpen.value || isLevelDropdownOpen.value || isGroupDropdownOpen.value || isCertDropdownOpen.value || isTagDropdownOpen.value || isLeadDropdownOpen.value) {
      closeAllDropdowns()
    } else if (props.isOpen) {
      emit('close')
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 md:p-6 select-none">
    <!-- Backdrop Overlay -->
    <div
      @click="emit('close')"
      class="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-200"
    />

    <!-- Modal Panel (Large, Wide and Tall) -->
    <div
      class="relative w-full max-w-5xl md:max-w-6xl overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] shadow-2xl z-10 flex flex-col h-[90vh] max-h-[92vh] animate-in fade-in zoom-in-95 duration-150"
      @click="closeAllDropdowns"
    >
      <!-- ── Header ─────────────────────────────────────────────── -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-100 dark:border-zinc-800 shrink-0 bg-white dark:bg-[#111315]">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800/60 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0 shadow-2xs">
            <FolderPlus class="w-5 h-5" />
          </div>
          <div>
            <h3 class="text-lg font-extrabold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <span>Add Students to Folder</span>
            </h3>
            <p class="text-xs text-zinc-500 font-medium mt-0.5 flex items-center gap-1.5">
              <span>Target Folder:</span>
              <span class="font-bold text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-md bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/50">
                {{ folderName }}
              </span>
              <span v-if="selectedIds.length > 0" class="text-blue-600 dark:text-blue-400 font-bold ml-1">
                · {{ selectedIds.length }} selected
              </span>
            </p>
          </div>
        </div>

        <button
          type="button"
          @click="emit('close')"
          class="p-2 rounded-xl text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- ── Search & Filter Controls Box (1-to-1 with Download Excel Modal) ── -->
      <div
        class="px-6 py-3.5 space-y-3 bg-zinc-50/80 dark:bg-zinc-850/50 border-b border-zinc-200/80 dark:border-zinc-800 shrink-0"
        @click.stop
      >
        <!-- 1. Search Row with Field Selector -->
        <div class="flex items-stretch gap-0 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 overflow-hidden focus-within:border-blue-500 shadow-2xs transition-colors">
          <div class="relative shrink-0 border-r border-zinc-200 dark:border-zinc-700">
            <select
              v-model="searchType"
              class="h-10 pl-3 pr-7 bg-transparent text-xs font-bold text-zinc-600 dark:text-zinc-300 focus:outline-none cursor-pointer appearance-none"
            >
              <option value="all">All Fields</option>
              <option value="id">ID</option>
              <option value="name">Name</option>
              <option value="phone">Phone</option>
              <option value="university">University</option>
            </select>
            <ChevronDown class="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-zinc-400 pointer-events-none" />
          </div>
          <div class="relative flex-1">
            <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search students by name, ID, phone, university..."
              class="w-full h-10 pl-10 pr-9 bg-transparent text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none placeholder:text-zinc-400"
              autofocus
            />
            <button
              v-if="searchQuery"
              type="button"
              @click="searchQuery = ''"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-0.5"
            >
              <X class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- 2. Filter Grid (7 Dropdowns matching Download Excel Modal) -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-2">
          <!-- Folder Filter -->
          <div class="relative">
            <button
              type="button"
              @click="toggleDropdown('folder')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors select-none"
              :class="selectedFolders.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <FolderIcon class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedFolders.length === 0 ? 'Folder' : `Folder · ${selectedFolders.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isFolderDropdownOpen"
              class="absolute left-0 mt-1 w-52 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedFolders.length === 0" @change="selectedFolders = []" class="rounded text-blue-600" />
                <span>All Folders</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="selectedFolders.includes('NO_FOLDER')"
                  @change="selectedFolders.includes('NO_FOLDER') ? selectedFolders = selectedFolders.filter(x => x !== 'NO_FOLDER') : selectedFolders.push('NO_FOLDER')"
                  class="rounded text-blue-600"
                />
                <span>No Folder</span>
              </label>
              <label
                v-for="f in folders"
                :key="f.id"
                class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="selectedFolders.includes(String(f.id))"
                  @change="selectedFolders.includes(String(f.id)) ? selectedFolders = selectedFolders.filter(x => x !== String(f.id)) : selectedFolders.push(String(f.id))"
                  class="rounded text-blue-600"
                />
                <span class="truncate">{{ f.name }}</span>
              </label>
            </div>
          </div>

          <!-- Tariff Filter -->
          <div class="relative">
            <button
              type="button"
              @click="toggleDropdown('tariff')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors select-none"
              :class="selectedTariffs.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Award class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedTariffs.length === 0 ? 'Tariff' : `Tariff · ${selectedTariffs.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isTariffDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedTariffs.length === 0" @change="selectedTariffs = []" class="rounded text-blue-600" />
                <span>All Tariffs</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedTariffs.includes('NO_TARIFF')" @change="toggleInList(selectedTariffs, 'NO_TARIFF')" class="rounded text-blue-600" />
                <span>No Tariff</span>
              </label>
              <label v-for="t in tariffOptions" :key="t" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedTariffs.includes(t)" @change="toggleInList(selectedTariffs, t)" class="rounded text-blue-600" />
                <span class="truncate">{{ t }}</span>
              </label>
            </div>
          </div>

          <!-- Level Filter -->
          <div class="relative">
            <button
              type="button"
              @click="toggleDropdown('level')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors select-none"
              :class="selectedLevels.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <GraduationCap class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedLevels.length === 0 ? 'Level' : `Level · ${selectedLevels.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isLevelDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedLevels.length === 0" @change="selectedLevels = []" class="rounded text-blue-600" />
                <span>All Levels</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label v-for="l in levelOptions" :key="l" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedLevels.includes(l)" @change="toggleInList(selectedLevels, l)" class="rounded text-blue-600" />
                <span class="truncate">{{ l }}</span>
              </label>
            </div>
          </div>

          <!-- Group Filter -->
          <div class="relative">
            <button
              type="button"
              @click="toggleDropdown('group')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors select-none"
              :class="selectedGroups.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Users class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedGroups.length === 0 ? 'Group' : `Group · ${selectedGroups.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isGroupDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedGroups.length === 0" @change="selectedGroups = []" class="rounded text-blue-600" />
                <span>All Groups</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label v-for="g in groupOptions" :key="g" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedGroups.includes(g)" @change="toggleInList(selectedGroups, g)" class="rounded text-blue-600" />
                <span class="truncate">{{ g }}</span>
              </label>
            </div>
          </div>

          <!-- Certificate Filter -->
          <div class="relative">
            <button
              type="button"
              @click="toggleDropdown('cert')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors select-none"
              :class="selectedCerts.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Award class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedCerts.length === 0 ? 'Certificate' : `Cert · ${selectedCerts.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isCertDropdownOpen"
              class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedCerts.length === 0" @change="selectedCerts = []" class="rounded text-blue-600" />
                <span>All Certificates</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label v-for="c in CERT_OPTIONS" :key="c" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedCerts.includes(c)" @change="toggleInList(selectedCerts, c)" class="rounded text-blue-600" />
                <span class="truncate">{{ c }}</span>
              </label>
            </div>
          </div>

          <!-- Tag Filter -->
          <div class="relative">
            <button
              type="button"
              @click="toggleDropdown('tag')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors select-none"
              :class="selectedTags.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Tag class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedTags.length === 0 ? 'Tag' : `Tag · ${selectedTags.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isTagDropdownOpen"
              class="absolute left-0 mt-1 w-44 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedTags.length === 0" @change="selectedTags = []" class="rounded text-blue-600" />
                <span>All Tags</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label v-for="t in TAG_OPTIONS" :key="t" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedTags.includes(t)" @change="toggleInList(selectedTags, t)" class="rounded text-blue-600" />
                <span class="truncate">{{ t }}</span>
              </label>
            </div>
          </div>

          <!-- Lead Filter -->
          <div class="relative">
            <button
              type="button"
              @click="toggleDropdown('lead')"
              class="w-full h-9 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between cursor-pointer border transition-colors select-none"
              :class="selectedLeads.length > 0
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'"
            >
              <div class="flex items-center gap-1.5 truncate">
                <Contact class="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ selectedLeads.length === 0 ? 'Lead' : `Lead · ${selectedLeads.length}` }}</span>
              </div>
              <ChevronDown class="w-3.5 h-3.5 shrink-0 ml-1 opacity-60" />
            </button>
            <div
              v-if="isLeadDropdownOpen"
              class="absolute right-0 sm:left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
              @click.stop
            >
              <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                <input type="checkbox" :checked="selectedLeads.length === 0" @change="selectedLeads = []" class="rounded text-blue-600" />
                <span>All Leads</span>
              </label>
              <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
              <label v-for="l in leadOptions" :key="l" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                <input type="checkbox" :checked="selectedLeads.includes(l)" @change="toggleInList(selectedLeads, l)" class="rounded text-blue-600" />
                <span class="truncate">{{ l }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 3. Active Filters Chips & Reset Row -->
        <div v-if="hasActiveFilters" class="flex items-center flex-wrap gap-1.5 pt-1">
          <span class="text-[11px] font-bold text-zinc-400 mr-1">Active:</span>
          <span
            v-for="chip in activeFilterChips"
            :key="chip.key"
            class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/60"
          >
            <span>{{ chip.label }}</span>
            <button type="button" @click="chip.clear" class="hover:text-blue-900 dark:hover:text-blue-100 cursor-pointer">
              <X class="w-3 h-3" />
            </button>
          </span>
          <button
            type="button"
            @click="clearAllFilters"
            class="inline-flex items-center gap-1 text-[11px] font-bold text-rose-600 dark:text-rose-400 hover:underline ml-1 cursor-pointer"
          >
            <RotateCcw class="w-3 h-3" />
            <span>Reset All</span>
          </button>
        </div>

        <!-- 4. Selection Toolbar -->
        <div class="flex items-center justify-between pt-1 border-t border-zinc-200/60 dark:border-zinc-800/80">
          <button
            v-if="filteredStudents.length > 0"
            type="button"
            @click="toggleSelectAll"
            class="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline cursor-pointer select-none"
          >
            {{ isAllFilteredSelected ? 'Deselect all' : `Select all ${filteredStudents.length}` }}
          </button>
          <span v-else class="text-xs text-zinc-400 italic">No matching students</span>

          <span class="text-[11px] font-medium text-zinc-400">
            Showing <strong class="text-zinc-700 dark:text-zinc-300">{{ filteredStudents.length }}</strong> active students ({{ pickableStudents.length }} total available)
          </span>
        </div>
      </div>

      <!-- ── Scrollable Student List ────────────────────────────── -->
      <div class="flex-1 overflow-y-auto p-6 scrollbar-thin">
        <div
          v-if="filteredStudents.length === 0"
          class="py-16 text-center text-xs text-zinc-400 italic flex flex-col items-center justify-center"
        >
          <Users class="w-10 h-10 text-zinc-300 dark:text-zinc-700 mb-3" />
          <p class="font-bold text-sm text-zinc-600 dark:text-zinc-400">No active students match your criteria.</p>
          <p class="mt-1 text-xs text-zinc-400">Try clearing active filters or adjusting your search keyword.</p>
        </div>

        <!-- Student Items Grid (Clean Responsive 2-column or 1-column layout) -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          <div
            v-for="s in filteredStudents"
            :key="s.id"
            @click="toggleStudent(s.id)"
            class="group flex items-start gap-3.5 p-3.5 rounded-xl border text-left cursor-pointer transition-all select-none"
            :class="[
              selectedIds.includes(s.id)
                ? 'border-blue-500 bg-blue-50/60 dark:bg-blue-950/40 shadow-xs ring-1 ring-blue-500/50'
                : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] hover:border-zinc-300 dark:hover:border-zinc-700 hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60'
            ]"
          >
            <!-- Checkbox -->
            <div
              class="w-5 h-5 min-w-[20px] rounded-lg border-2 flex items-center justify-center shrink-0 mt-0.5 transition-all"
              :class="[
                selectedIds.includes(s.id)
                  ? 'border-blue-600 bg-blue-600 shadow-xs text-white'
                  : 'border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 group-hover:border-blue-400'
              ]"
            >
              <Check v-if="selectedIds.includes(s.id)" class="w-3.5 h-3.5 stroke-[3]" />
            </div>

            <!-- Student Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide truncate">
                    {{ s.full_name }}
                  </span>
                  <span v-if="s.korean_name" class="text-[11px] font-medium text-zinc-400 truncate">
                    ({{ s.korean_name }})
                  </span>
                </div>

                <!-- ID Pill -->
                <span class="text-[10.5px] text-zinc-500 dark:text-zinc-400 font-mono font-bold bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded border border-zinc-200 dark:border-zinc-700 shrink-0">
                  {{ s.id }}
                </span>
              </div>

              <!-- Metadata Row: Level, Tariff, Group, Phone -->
              <div class="flex items-center gap-1.5 mt-2 flex-wrap text-[10.5px]">
                <!-- Level Badge -->
                <span
                  v-if="s.level"
                  class="font-bold px-1.5 py-0.5 rounded border uppercase"
                  :class="getLevelBadgeClass(s.level)"
                >
                  {{ s.level }}
                </span>

                <!-- Tariff Badge -->
                <span
                  v-if="s.tariff"
                  class="font-bold px-1.5 py-0.5 rounded border bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/60 uppercase"
                >
                  {{ s.tariff }}
                </span>

                <!-- Group Badge -->
                <span
                  v-if="s.student_group"
                  class="font-semibold text-zinc-600 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 px-1.5 py-0.5 rounded"
                >
                  {{ s.student_group }}
                </span>

                <!-- Phone -->
                <span v-if="s.phone1" class="text-zinc-400 font-mono">
                  {{ s.phone1 }}
                </span>
              </div>

              <!-- Other Existing Folders Badges -->
              <div v-if="getOtherFolderNames(s).length > 0" class="flex items-center gap-1 mt-2 flex-wrap">
                <span class="text-[10px] text-zinc-400 font-medium">Folders:</span>
                <span
                  v-for="name in getOtherFolderNames(s)"
                  :key="name"
                  class="text-[10px] font-semibold text-zinc-600 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md px-1.5 py-0.5 uppercase"
                >
                  {{ name }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Footer ─────────────────────────────────────────────── -->
      <div class="px-6 py-4 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between gap-3 bg-zinc-50/80 dark:bg-[#0e1012] shrink-0">
        <div class="text-xs font-semibold text-zinc-600 dark:text-zinc-400 flex items-center gap-2">
          <span>Selected for <strong>{{ folderName }}</strong>:</span>
          <span class="px-2.5 py-1 rounded-lg bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-extrabold border border-blue-200 dark:border-blue-800/50">
            {{ selectedIds.length }} student{{ selectedIds.length !== 1 ? 's' : '' }}
          </span>
        </div>

        <div class="flex items-center gap-2.5">
          <button
            type="button"
            @click="emit('close')"
            class="px-4 py-2 text-xs font-bold border border-zinc-200 dark:border-zinc-700 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            @click="handleSave"
            :disabled="selectedIds.length === 0"
            class="px-6 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl shadow-sm transition-all cursor-pointer flex items-center gap-1.5"
          >
            <FolderPlus class="w-4 h-4" />
            <span>Add {{ selectedIds.length > 0 ? `(${selectedIds.length})` : '' }} to Folder</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
