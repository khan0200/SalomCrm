<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { settingsApi } from '@/api/settings'
import {
  UserPlus, X, AlertCircle, CheckCircle2, Hash, User, Building2,
  Award, GraduationCap, School, Users, UserCheck, ShieldCheck,
  Loader2, Check, Sparkles, Command, ArrowRight
} from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  options?: {
    tariffs?: Array<{ name: string; price?: number } | string>
    levels?: string[]
    groups?: string[]
    leads?: string[]
    coordinators?: string[]
    offices?: string[]
    universities?: string[]
  }
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const studentId = ref('')
const fullName = ref('')
const office = ref('')
const tariff = ref('')
const level = ref('')
const university1 = ref('')
const studentGroup = ref('')
const leadBy = ref('')
const coordinator = ref('')

const submitting = ref(false)
const modalError = ref<string | null>(null)
const modalSuccess = ref(false)

// University suggestions state
const isUniversityDropdownOpen = ref(false)
const highlightedUniversityIndex = ref(0)
const universityInputContainerRef = ref<HTMLElement | null>(null)

// Fetch universities directly from settings to ensure fresh and complete suggestions
const { data: settingsUniversitiesData } = useQuery({
  queryKey: ['settings-universities'],
  queryFn: () => settingsApi.getUniversities(),
  staleTime: 1000 * 60 * 5, // 5 minutes cache
})

const officeOptions = computed(() => props.options?.offices || ['ANDIJON OFFIS', 'TOSHKENT OFFIS'])
const tariffOptions = computed(() => {
  return (props.options?.tariffs || []).map(t => (typeof t === 'string' ? t : t.name))
})
const levelOptions = computed(() => props.options?.levels || ['COLLEGE', 'BACHELOR', 'MASTERS', 'MASTER NO CERTIFICATE', 'LANGUAGE COURSE'])
const groupOptions = computed(() => props.options?.groups || [])
const leadByOptions = computed(() => props.options?.leads || [])
const coordinatorOptions = computed(() => props.options?.coordinators || [])

// Combined unique sorted list of universities from Settings & options
const allUniversities = computed<string[]>(() => {
  const set = new Set<string>()

  // From props.options.universities
  if (Array.isArray(props.options?.universities)) {
    props.options.universities.forEach(u => {
      if (typeof u === 'string' && u.trim()) set.add(u.trim().toUpperCase())
      else if (u && typeof u === 'object' && 'name' in u && (u as any).name) {
        set.add(String((u as any).name).trim().toUpperCase())
      }
    })
  }

  // From settingsApi.getUniversities()
  const rawSettings = settingsUniversitiesData.value as Array<any> | undefined
  if (Array.isArray(rawSettings)) {
    rawSettings.forEach(u => {
      if (u && typeof u === 'object' && 'name' in u && u.name) {
        set.add(String(u.name).trim().toUpperCase())
      } else if (typeof u === 'string' && (u as string).trim()) {
        set.add((u as string).trim().toUpperCase())
      }
    })
  }

  return Array.from(set).sort((a, b) => a.localeCompare(b))
})

// Filtered university suggestions matching current input
const filteredUniversities = computed(() => {
  const query = university1.value.trim().toLowerCase()
  if (!query) {
    return allUniversities.value.slice(0, 15)
  }
  return allUniversities.value.filter(u => u.toLowerCase().includes(query)).slice(0, 20)
})

const selectUniversity = (uniName: string) => {
  university1.value = uniName.toUpperCase()
  isUniversityDropdownOpen.value = false
}

const handleUniversityKeyDown = (e: KeyboardEvent) => {
  if (!isUniversityDropdownOpen.value) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      isUniversityDropdownOpen.value = true
      e.preventDefault()
    }
    return
  }

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (filteredUniversities.value.length > 0) {
      highlightedUniversityIndex.value = (highlightedUniversityIndex.value + 1) % filteredUniversities.value.length
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (filteredUniversities.value.length > 0) {
      highlightedUniversityIndex.value = (highlightedUniversityIndex.value - 1 + filteredUniversities.value.length) % filteredUniversities.value.length
    }
  } else if (e.key === 'Enter' || e.key === 'Tab') {
    if (filteredUniversities.value.length > 0 && isUniversityDropdownOpen.value) {
      e.preventDefault()
      const selected = filteredUniversities.value[highlightedUniversityIndex.value]
      if (selected) {
        selectUniversity(selected)
      }
    }
  } else if (e.key === 'Escape') {
    isUniversityDropdownOpen.value = false
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    studentId.value = ''
    fullName.value = ''
    office.value = officeOptions.value[0] || ''
    tariff.value = ''
    level.value = ''
    university1.value = ''
    studentGroup.value = ''
    leadBy.value = ''
    coordinator.value = ''
    modalError.value = null
    modalSuccess.value = false
    submitting.value = false
    isUniversityDropdownOpen.value = false
    highlightedUniversityIndex.value = 0
  }
})

const handleKeyDown = (e: KeyboardEvent) => {
  if (!props.isOpen) return

  // Ctrl+Enter or Cmd+Enter to Submit quickly
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !submitting.value) {
    e.preventDefault()
    handleSubmit()
    return
  }

  if (e.key === 'Escape' && !submitting.value) {
    if (isUniversityDropdownOpen.value) {
      isUniversityDropdownOpen.value = false
    } else {
      emit('close')
    }
  }
}

const handleOutsideClick = (e: MouseEvent) => {
  if (
    universityInputContainerRef.value &&
    !universityInputContainerRef.value.contains(e.target as Node)
  ) {
    isUniversityDropdownOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  document.addEventListener('click', handleOutsideClick, true)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('click', handleOutsideClick, true)
})

const handleSubmit = async () => {
  if (!studentId.value.trim()) {
    modalError.value = 'Student ID is required (e.g. F101).'
    return
  }
  if (!fullName.value.trim()) {
    modalError.value = 'Student Full Name is required.'
    return
  }
  if (!office.value) {
    modalError.value = 'Office Branch selection is required.'
    return
  }

  submitting.value = true
  modalError.value = null

  try {
    emit('submit', {
      id: studentId.value.trim().toUpperCase(),
      full_name: fullName.value.trim().toUpperCase(),
      office: office.value || null,
      tariff: tariff.value || null,
      level: level.value || null,
      university_1: university1.value ? university1.value.trim().toUpperCase() : null,
      student_group: studentGroup.value || null,
      lead_by: leadBy.value || null,
      coordinator: coordinator.value || null,
    })
  } catch (err: any) {
    modalError.value = err.message || 'Failed to register student.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
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
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
        @click.self="() => { if (!submitting) emit('close') }"
      >
        <transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="transform scale-95 opacity-0"
          enter-to-class="transform scale-100 opacity-100"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="transform scale-100 opacity-100"
          leave-to-class="transform scale-95 opacity-0"
        >
          <div
            class="relative w-full max-w-[700px] flex flex-col rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xl overflow-hidden"
          >
            <!-- Modal Header -->
            <div class="px-5 py-3.5 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/75 dark:bg-zinc-850/50 shrink-0">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950/50 border border-blue-200/60 dark:border-blue-800/60 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                  <UserPlus class="w-4 h-4" />
                </div>
                <div>
                  <h2 class="text-sm font-bold text-zinc-900 dark:text-zinc-100 leading-tight">
                    Add New Student
                  </h2>
                  <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Register a new student in the CRM
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <span class="text-[10px] font-mono text-zinc-400 dark:text-zinc-500 px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                  ESC
                </span>
                <button
                  type="button"
                  :disabled="submitting"
                  @click="emit('close')"
                  class="rounded-md p-1 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                  title="Close"
                >
                  <X class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Modal Body (Compact Form) -->
            <form id="add-student-form" @submit.prevent="handleSubmit" class="p-5 space-y-3.5">
              <!-- Error Alert -->
              <div
                v-if="modalError"
                class="flex items-center gap-2 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 px-3 py-2 text-xs text-rose-700 dark:text-rose-300"
              >
                <AlertCircle class="h-4 w-4 shrink-0 text-rose-500" />
                <span>{{ modalError }}</span>
              </div>

              <!-- Success Alert -->
              <div
                v-if="modalSuccess"
                class="flex items-center gap-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/40 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300"
              >
                <CheckCircle2 class="h-4 w-4 shrink-0 text-emerald-500" />
                <span>Student successfully registered!</span>
              </div>

              <!-- Row 1: Student ID (compact ~105px), Student Name (expanded flex-1), Office Branch -->
              <div class="flex items-center gap-3">
                <div class="w-24 sm:w-28 shrink-0">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 mb-1 flex items-center justify-between">
                    <span>Student ID</span>
                    <span class="text-rose-500">*</span>
                  </label>
                  <input
                    v-model="studentId"
                    type="text"
                    required
                    :disabled="submitting || modalSuccess"
                    placeholder="e.g. F101"
                    @input="studentId = studentId.toUpperCase()"
                    class="w-full h-9 px-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all font-mono font-bold text-xs uppercase"
                  />
                </div>

                <div class="flex-1 min-w-0">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 mb-1 flex items-center justify-between">
                    <span>Student Name</span>
                    <span class="text-rose-500">*</span>
                  </label>
                  <input
                    v-model="fullName"
                    type="text"
                    required
                    :disabled="submitting || modalSuccess"
                    placeholder="BAXTIYOR ALIMOV"
                    @input="fullName = fullName.toUpperCase()"
                    class="w-full h-9 px-3 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all font-semibold text-xs uppercase"
                  />
                </div>

                <div class="w-44 sm:w-48 shrink-0">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 mb-1 flex items-center justify-between">
                    <span>Office Branch</span>
                    <span class="text-rose-500">*</span>
                  </label>
                  <select
                    v-model="office"
                    required
                    :disabled="submitting || modalSuccess"
                    class="w-full h-9 px-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all text-xs font-medium cursor-pointer"
                  >
                    <option value="">Select</option>
                    <option v-for="opt in officeOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                </div>
              </div>

              <!-- Row 2: Tariff & Level to Study (2 columns with generous width) -->
              <div class="grid grid-cols-12 gap-3">
                <div class="col-span-6">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 mb-1">
                    Tariff
                  </label>
                  <select
                    v-model="tariff"
                    :disabled="submitting || modalSuccess"
                    class="w-full h-9 px-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all text-xs font-medium cursor-pointer"
                  >
                    <option value="">Select</option>
                    <option v-for="t in tariffOptions" :key="t" :value="t">{{ t }}</option>
                  </select>
                </div>

                <div class="col-span-6">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 mb-1">
                    Level to Study
                  </label>
                  <select
                    v-model="level"
                    :disabled="submitting || modalSuccess"
                    class="w-full h-9 px-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all text-xs font-medium cursor-pointer"
                  >
                    <option value="">Select</option>
                    <option v-for="lvl in levelOptions" :key="lvl" :value="lvl">{{ lvl }}</option>
                  </select>
                </div>
              </div>

              <!-- Row 3: University 1 (Interactive Auto-Suggest) -->
              <div ref="universityInputContainerRef" class="relative">
                <div class="flex items-center justify-between mb-1">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400">
                    University 1
                  </label>
                  <span v-if="allUniversities.length > 0" class="text-[10px] text-zinc-400 dark:text-zinc-500">
                    {{ allUniversities.length }} universities
                  </span>
                </div>

                <div class="relative">
                  <input
                    v-model="university1"
                    type="text"
                    :disabled="submitting || modalSuccess"
                    placeholder="Type university name (e.g. SEJONG)..."
                    @input="() => { university1 = university1.toUpperCase(); isUniversityDropdownOpen = true; highlightedUniversityIndex = 0; }"
                    @focus="isUniversityDropdownOpen = true"
                    @keydown="handleUniversityKeyDown"
                    class="w-full h-9 px-3 pr-8 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all text-xs font-medium uppercase"
                    autocomplete="off"
                  />

                  <!-- Clear Button -->
                  <button
                    v-if="university1"
                    type="button"
                    @click="() => { university1 = ''; isUniversityDropdownOpen = true; }"
                    class="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-0.5 rounded cursor-pointer"
                    title="Clear"
                  >
                    <X class="w-3.5 h-3.5" />
                  </button>
                </div>

                <!-- Autocomplete Dropdown -->
                <div
                  v-if="isUniversityDropdownOpen && (filteredUniversities.length > 0 || (university1.trim() && allUniversities.length > 0))"
                  class="absolute left-0 right-0 top-full mt-1 z-50 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 shadow-xl overflow-hidden"
                >
                  <ul class="max-h-44 overflow-y-auto py-1 divide-y divide-zinc-100 dark:divide-zinc-800">
                    <li
                      v-for="(uni, index) in filteredUniversities"
                      :key="uni"
                      @mousedown.prevent="selectUniversity(uni)"
                      @mouseenter="highlightedUniversityIndex = index"
                      class="px-3 py-1.5 text-xs flex items-center justify-between cursor-pointer transition-colors"
                      :class="highlightedUniversityIndex === index || university1 === uni
                        ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-semibold'
                        : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800'"
                    >
                      <span class="truncate uppercase">{{ uni }}</span>
                      <Check v-if="university1 === uni" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0 ml-2" />
                    </li>

                    <li v-if="filteredUniversities.length === 0" class="px-3 py-2 text-xs text-zinc-400 italic text-center">
                      No matching universities. Custom entry "{{ university1 }}" will be used.
                    </li>
                  </ul>
                </div>
              </div>

              <!-- Row 4: Group, Lead By, Coordinator -->
              <div class="grid grid-cols-12 gap-3">
                <div class="col-span-4">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 mb-1">
                    Group
                  </label>
                  <select
                    v-model="studentGroup"
                    :disabled="submitting || modalSuccess"
                    class="w-full h-9 px-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all text-xs font-medium cursor-pointer"
                  >
                    <option value="">Select Group</option>
                    <option v-for="g in groupOptions" :key="g" :value="g">{{ g }}</option>
                  </select>
                </div>

                <div class="col-span-4">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 mb-1">
                    Lead By
                  </label>
                  <select
                    v-model="leadBy"
                    :disabled="submitting || modalSuccess"
                    class="w-full h-9 px-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all text-xs font-medium cursor-pointer"
                  >
                    <option value="">Select Lead By</option>
                    <option v-for="l in leadByOptions" :key="l" :value="l">{{ l }}</option>
                  </select>
                </div>

                <div class="col-span-4">
                  <label class="block text-[11px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 mb-1">
                    Coordinator
                  </label>
                  <select
                    v-model="coordinator"
                    :disabled="submitting || modalSuccess"
                    class="w-full h-9 px-2.5 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1.5 focus:ring-blue-500 focus:border-blue-500 transition-all text-xs font-medium cursor-pointer"
                  >
                    <option value="">Select Coordinator</option>
                    <option v-for="c in coordinatorOptions" :key="c" :value="c">{{ c }}</option>
                  </select>
                </div>
              </div>
            </form>

            <!-- Modal Footer -->
            <div class="px-5 py-3.5 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/75 dark:bg-zinc-850/50 shrink-0">
              <span class="text-xs text-zinc-500 dark:text-zinc-400">
                Fields with <span class="text-rose-500 font-bold">*</span> are required
              </span>

              <div class="flex items-center gap-2">
                <button
                  type="button"
                  :disabled="submitting || modalSuccess"
                  @click="emit('close')"
                  class="px-4 py-2 rounded-lg text-[13px] font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  form="add-student-form"
                  :disabled="submitting || modalSuccess"
                  class="px-4 py-2 rounded-lg text-[13px] font-semibold bg-blue-600 hover:bg-blue-700 text-white transition-colors cursor-pointer select-none disabled:opacity-50 flex items-center gap-2 shadow-xs"
                >
                  <Loader2 v-if="submitting" class="w-4 h-4 animate-spin" />
                  <span>{{ submitting ? 'Saving...' : 'Save Student' }}</span>
                </button>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

