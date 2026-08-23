<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search, X, Check, GraduationCap, Users } from 'lucide-vue-next'
import type { Student, Folder } from '@/types'

const props = defineProps<{
  isOpen: boolean
  folderId: string
  folderName: string
  folders: Folder[]
  allStudents: Student[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', studentIds: string[]): void
}>()

const searchQuery = ref('')
const selectedIds = ref<string[]>([])
const selectedLevel = ref<string>('all')

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
      selectedLevel.value = 'all'
      selectedIds.value = []
    }
  },
  { immediate: true }
)

// Distinct Study Levels present in pickable active student roster
const availableLevels = computed(() => {
  const levelsSet = new Set<string>()
  for (const s of pickableStudents.value) {
    if (s.level && String(s.level).trim()) {
      levelsSet.add(String(s.level).trim())
    }
  }
  return Array.from(levelsSet).sort()
})

// Filtered list applying Search and Study Level filter
const filteredStudents = computed(() => {
  let list = pickableStudents.value

  // 1. Level Filter
  if (selectedLevel.value !== 'all') {
    list = list.filter(s => (s.level || '').trim().toUpperCase() === selectedLevel.value.trim().toUpperCase())
  }

  // 2. Search Query
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(s =>
      (s.full_name || '').toLowerCase().includes(q) ||
      (s.id || '').toLowerCase().includes(q)
    )
  }

  return list
})

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

// Level Badge Color Resolver
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
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4">
    <!-- Backdrop Overlay -->
    <div
      @click="emit('close')"
      class="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-200"
    />

    <!-- Modal Panel -->
    <div
      class="relative w-full max-w-xl overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] shadow-2xl z-10 flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150"
      @click.stop
    >
      <!-- ── Header ─────────────────────────────────────────────── -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-100 dark:border-zinc-800 shrink-0">
        <div>
          <h3 class="text-base font-extrabold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
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
        <button
          type="button"
          @click="emit('close')"
          class="p-1.5 rounded-xl text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- ── Search & Filter Toolbar ────────────────────────────── -->
      <div class="px-6 pt-3.5 pb-2.5 space-y-3 bg-zinc-50/70 dark:bg-zinc-850/40 border-b border-zinc-100 dark:border-zinc-800/80 shrink-0">
        <!-- 1. Search Bar & Level Selector Row -->
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          <!-- Search Bar -->
          <div class="relative flex-1">
            <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search active students by name or ID..."
              class="w-full pl-10 pr-9 py-2 text-xs font-medium border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 shadow-2xs transition-all"
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

          <!-- Level to Study Filter -->
          <div class="flex items-center gap-1.5 shrink-0">
            <GraduationCap class="w-4 h-4 text-zinc-400 shrink-0 hidden sm:block" />
            <select
              v-model="selectedLevel"
              class="w-full sm:w-44 px-2.5 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-xs font-bold text-zinc-700 dark:text-zinc-300 focus:outline-none focus:border-blue-500 shadow-2xs cursor-pointer truncate"
            >
              <option value="all">All Levels ({{ pickableStudents.length }})</option>
              <option
                v-for="lvl in availableLevels"
                :key="lvl"
                :value="lvl"
              >
                {{ lvl }}
              </option>
            </select>
          </div>
        </div>

        <!-- 2. Quick Action & Summary Header -->
        <div class="flex items-center justify-between pt-0.5">
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
            Showing <strong class="text-zinc-700 dark:text-zinc-300">{{ filteredStudents.length }}</strong> active students
          </span>
        </div>
      </div>

      <!-- ── Scrollable Student List ────────────────────────────── -->
      <div class="flex-1 overflow-y-auto px-6 py-3.5 flex flex-col gap-2 scrollbar-thin">
        <div
          v-if="filteredStudents.length === 0"
          class="py-14 text-center text-xs text-zinc-400 italic"
        >
          <Users class="w-8 h-8 text-zinc-300 dark:text-zinc-700 mx-auto mb-2" />
          <p class="font-bold text-zinc-600 dark:text-zinc-400">No active students match your filter.</p>
          <p class="mt-0.5 text-zinc-400">Try adjusting the study level or search keyword.</p>
        </div>

        <!-- Student Item Card -->
        <div
          v-for="s in filteredStudents"
          :key="s.id"
          @click="toggleStudent(s.id)"
          class="group flex items-center gap-3.5 px-3.5 py-2.5 rounded-xl border text-left cursor-pointer transition-all w-full select-none"
          :class="[
            selectedIds.includes(s.id)
              ? 'border-blue-500 bg-blue-50/70 dark:bg-blue-950/40 shadow-xs'
              : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] hover:border-zinc-300 dark:hover:border-zinc-700 hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60'
          ]"
        >
          <!-- Prominent Checkbox (Square & High Visibility) -->
          <div
            class="w-5 h-5 min-w-[20px] rounded-lg border-2 flex items-center justify-center shrink-0 transition-all"
            :class="[
              selectedIds.includes(s.id)
                ? 'border-blue-600 bg-blue-600 shadow-xs text-white'
                : 'border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 group-hover:border-blue-400'
            ]"
          >
            <Check v-if="selectedIds.includes(s.id)" class="w-3.5 h-3.5 stroke-[3]" />
          </div>

          <!-- Student Info (Name, ID, Level, Folder Pills) -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide truncate">
                {{ s.full_name }}
              </span>
            </div>

            <div class="flex items-center gap-2 mt-1 flex-wrap">
              <!-- ID Pill -->
              <span class="text-[10.5px] text-zinc-500 dark:text-zinc-400 font-mono font-bold bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded border border-zinc-200 dark:border-zinc-700">
                {{ s.id }}
              </span>

              <!-- Level to study Badge -->
              <span
                v-if="s.level"
                class="text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase"
                :class="getLevelBadgeClass(s.level)"
              >
                {{ s.level }}
              </span>
            </div>
          </div>

          <!-- Right Other Folder Badges -->
          <div class="flex items-center flex-wrap gap-1 shrink-0">
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

      <!-- ── Footer ─────────────────────────────────────────────── -->
      <div class="px-6 py-3.5 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between gap-3 bg-zinc-50/80 dark:bg-[#0e1012] shrink-0">
        <div class="text-xs font-semibold text-zinc-600 dark:text-zinc-400 flex items-center gap-1.5">
          <span>Selected:</span>
          <span class="px-2 py-0.5 rounded-md bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold border border-blue-200 dark:border-blue-800/50">
            {{ selectedIds.length }} student{{ selectedIds.length !== 1 ? 's' : '' }}
          </span>
        </div>

        <div class="flex items-center gap-2">
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
            class="px-5 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl shadow-xs transition-all cursor-pointer"
          >
            Save ({{ selectedIds.length }})
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
