<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { settingsApi } from '@/api/settings'
import {
  Sparkles, X, AlertCircle, CheckCircle2, Landmark, User, Building2,
  Award, GraduationCap, School, Users, UserCheck, ShieldCheck, Loader2, Check
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
const levelOptions = computed(() => props.options?.levels || [])
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
  if (e.key === 'Escape' && props.isOpen && !submitting.value) {
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
    modalError.value = 'Student Name is required.'
    return
  }
  if (!office.value) {
    modalError.value = 'Office Branch is required.'
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
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs overflow-y-auto"
        @click.self="() => { if (!submitting) emit('close') }"
      >
        <transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="transform scale-95 opacity-0 translate-y-3"
          enter-to-class="transform scale-100 opacity-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="transform scale-100 opacity-100 translate-y-0"
          leave-to-class="transform scale-95 opacity-0 translate-y-3"
        >
          <div
            class="relative w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl z-10 my-auto"
          >
            <!-- Modal Header -->
            <div class="p-5 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between shrink-0 bg-zinc-50/80 dark:bg-zinc-850/60">
              <div>
                <h2 class="text-lg font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                  <Sparkles class="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  Add New Student
                </h2>
                <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Fill in the required information to register a new student in the CRM.
                </p>
              </div>
              <button
                type="button"
                :disabled="submitting"
                @click="emit('close')"
                class="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-200/60 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer disabled:opacity-50"
              >
                <X class="h-5 w-5" />
              </button>
            </div>

            <!-- Modal Body / Scrollable Form -->
            <div class="p-6 overflow-y-auto flex-1 space-y-4">
              <!-- Error Alert -->
              <div
                v-if="modalError"
                class="flex items-start gap-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/30 p-3.5 text-sm text-rose-800 dark:text-rose-300"
              >
                <AlertCircle class="h-4 w-4 shrink-0 mt-0.5" />
                <p>{{ modalError }}</p>
              </div>

              <!-- Success Alert -->
              <div
                v-if="modalSuccess"
                class="flex items-center gap-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 p-3.5 text-sm text-emerald-800 dark:text-emerald-300"
              >
                <CheckCircle2 class="h-4 w-4 shrink-0" />
                <p>Student successfully registered!</p>
              </div>

              <form id="add-student-form" @submit.prevent="handleSubmit" class="space-y-4">
                <!-- 1. Required Information Section -->
                <div class="bg-zinc-50/90 dark:bg-zinc-800/40 p-4 rounded-xl border border-zinc-200/80 dark:border-zinc-700/60 space-y-3">
                  <span class="text-[11px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 block">
                    1. Required Information *
                  </span>

                  <div class="flex items-center gap-3">
                    <!-- Student ID (Required - Compact width) -->
                    <div class="w-36 shrink-0">
                      <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center justify-between">
                        <span class="flex items-center gap-1">
                          <Landmark class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                          Student ID
                        </span>
                        <span class="text-rose-500 font-bold">*</span>
                      </label>
                      <input
                        v-model="studentId"
                        type="text"
                        required
                        :disabled="submitting || modalSuccess"
                        placeholder="e.g. F101"
                        @input="studentId = studentId.toUpperCase()"
                        class="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all font-mono font-bold text-sm"
                      />
                    </div>

                    <!-- Student Name (Required - Expanded width) -->
                    <div class="flex-1 min-w-0">
                      <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center justify-between">
                        <span class="flex items-center gap-1">
                          <User class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                          Student Name
                        </span>
                        <span class="text-rose-500 font-bold">*</span>
                      </label>
                      <input
                        v-model="fullName"
                        type="text"
                        required
                        :disabled="submitting || modalSuccess"
                        placeholder="BAXTIYOR"
                        @input="fullName = fullName.toUpperCase()"
                        class="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all font-semibold text-sm"
                      />
                    </div>
                  </div>

                  <!-- Office Branch (Required) -->
                  <div>
                    <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center justify-between">
                      <span class="flex items-center gap-1">
                        <Building2 class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                        Office Branch
                      </span>
                      <span class="text-rose-500 font-bold">*</span>
                    </label>
                    <select
                      v-model="office"
                      required
                      :disabled="submitting || modalSuccess"
                      class="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm font-medium cursor-pointer"
                    >
                      <option value="">Select Office Branch</option>
                      <option v-for="opt in officeOptions" :key="opt" :value="opt">{{ opt }}</option>
                    </select>
                  </div>
                </div>

                <!-- 2. Academic & Tariff Details Section -->
                <div class="bg-zinc-50/90 dark:bg-zinc-800/40 p-4 rounded-xl border border-zinc-200/80 dark:border-zinc-700/60 space-y-3">
                  <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block">
                    2. Academic & Tariff Details
                  </span>

                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <!-- Tariff -->
                    <div>
                       <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center gap-1">
                        <Award class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                        Tariff
                      </label>
                      <select
                        v-model="tariff"
                        :disabled="submitting || modalSuccess"
                        class="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm cursor-pointer"
                      >
                        <option value="">Select</option>
                        <option v-for="t in tariffOptions" :key="t" :value="t">{{ t }}</option>
                      </select>
                    </div>

                    <!-- Level to Study -->
                    <div>
                      <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center gap-1">
                        <GraduationCap class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                        Level to Study
                      </label>
                      <select
                        v-model="level"
                        :disabled="submitting || modalSuccess"
                        class="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm cursor-pointer"
                      >
                        <option value="">Select</option>
                        <option v-for="lvl in levelOptions" :key="lvl" :value="lvl">{{ lvl }}</option>
                      </select>
                    </div>
                  </div>

                  <!-- University 1 (Interactive Auto-Suggest from Settings) -->
                  <div ref="universityInputContainerRef" class="relative">
                    <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center justify-between">
                      <span class="flex items-center gap-1">
                        <School class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                        University 1
                      </span>
                      <span v-if="allUniversities.length > 0" class="text-[10.5px] text-zinc-400 dark:text-zinc-500 font-normal">
                        {{ allUniversities.length }} universities from Settings
                      </span>
                    </label>

                    <div class="relative">
                      <input
                        v-model="university1"
                        type="text"
                        :disabled="submitting || modalSuccess"
                        placeholder="Type university name (e.g. SEJONG UNIVERSITY)..."
                        @input="() => { university1 = university1.toUpperCase(); isUniversityDropdownOpen = true; highlightedUniversityIndex = 0; }"
                        @focus="isUniversityDropdownOpen = true"
                        @keydown="handleUniversityKeyDown"
                        class="w-full px-3 py-2 pr-8 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm font-medium uppercase"
                        autocomplete="off"
                      />

                      <!-- Clear / Dropdown Trigger Icon -->
                      <button
                        v-if="university1"
                        type="button"
                        @click="() => { university1 = ''; isUniversityDropdownOpen = true; }"
                        class="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-0.5 rounded cursor-pointer transition-colors"
                        title="Clear university"
                      >
                        <X class="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <!-- Autocomplete Suggestions Dropdown -->
                    <div
                      v-if="isUniversityDropdownOpen && (filteredUniversities.length > 0 || (university1.trim() && allUniversities.length > 0))"
                      class="absolute left-0 right-0 top-full mt-1.5 z-50 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 shadow-xl overflow-hidden backdrop-blur-md"
                    >
                      <div class="px-3 py-1.5 text-[10.5px] font-bold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/75 dark:bg-zinc-900/60 flex items-center justify-between select-none">
                        <span>Universities from Settings</span>
                        <span class="text-[10px] bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded font-mono font-semibold">
                          {{ filteredUniversities.length }} matching
                        </span>
                      </div>

                      <ul class="max-h-48 overflow-y-auto py-1 scrollbar-thin divide-y divide-zinc-50 dark:divide-zinc-800/40">
                        <li
                          v-for="(uni, index) in filteredUniversities"
                          :key="uni"
                          @mousedown.prevent="selectUniversity(uni)"
                          @mouseenter="highlightedUniversityIndex = index"
                          class="px-3 py-2 text-xs flex items-center gap-2 cursor-pointer transition-colors select-none"
                          :class="highlightedUniversityIndex === index || university1 === uni
                            ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold'
                            : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800'"
                        >
                          <School class="w-3.5 h-3.5 shrink-0" :class="highlightedUniversityIndex === index || university1 === uni ? 'text-blue-600 dark:text-blue-400' : 'text-zinc-400'" />
                          <span class="truncate uppercase flex-1">{{ uni }}</span>
                          <Check v-if="university1 === uni" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
                        </li>

                        <li v-if="filteredUniversities.length === 0" class="px-3 py-3 text-xs text-zinc-400 italic text-center select-none">
                          No matching universities in Settings. You can still use "{{ university1 }}".
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <!-- 3. Management & Group Assignment Section -->
                <div class="bg-zinc-50/90 dark:bg-zinc-800/40 p-4 rounded-xl border border-zinc-200/80 dark:border-zinc-700/60 space-y-3">
                  <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 block">
                    3. Group & Staff Assignment
                  </span>

                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <!-- Group -->
                    <div>
                      <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center gap-1">
                        <Users class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                        Group
                      </label>
                      <select
                        v-model="studentGroup"
                        :disabled="submitting || modalSuccess"
                        class="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-xs font-semibold cursor-pointer"
                      >
                        <option value="">Select Group</option>
                        <option v-for="g in groupOptions" :key="g" :value="g">{{ g }}</option>
                      </select>
                    </div>

                    <!-- Lead By -->
                    <div>
                      <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center gap-1">
                        <UserCheck class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                        Lead By
                      </label>
                      <select
                        v-model="leadBy"
                        :disabled="submitting || modalSuccess"
                        class="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-xs font-semibold cursor-pointer"
                      >
                        <option value="">Select Lead By</option>
                        <option v-for="l in leadByOptions" :key="l" :value="l">{{ l }}</option>
                      </select>
                    </div>

                    <!-- Coordinator -->
                    <div>
                      <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1 flex items-center gap-1">
                        <ShieldCheck class="h-3 w-3 text-blue-600 dark:text-blue-400" />
                        Coordinator
                      </label>
                      <select
                        v-model="coordinator"
                        :disabled="submitting || modalSuccess"
                        class="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-xs font-semibold cursor-pointer"
                      >
                        <option value="">Select Coordinator</option>
                        <option v-for="c in coordinatorOptions" :key="c" :value="c">{{ c }}</option>
                      </select>
                    </div>
                  </div>
                </div>
              </form>
            </div>

            <!-- Modal Footer / Action Buttons -->
            <div class="p-4 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between gap-3 shrink-0 bg-zinc-50/80 dark:bg-zinc-850/60">
              <span class="text-xs text-zinc-500 dark:text-zinc-400">
                Fields marked with <span class="text-rose-500 font-bold">*</span> are required.
              </span>

              <div class="flex items-center gap-3">
                <button
                  type="button"
                  :disabled="submitting || modalSuccess"
                  @click="emit('close')"
                  class="px-4 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl bg-transparent text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-semibold transition-all active:scale-[0.96] cursor-pointer disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  form="add-student-form"
                  :disabled="submitting || modalSuccess"
                  class="flex items-center justify-center gap-1.5 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all active:scale-[0.96] cursor-pointer select-none disabled:opacity-50 shadow-md shadow-blue-500/25"
                >
                  <Loader2 v-if="submitting" class="h-3.5 w-3.5 animate-spin" />
                  <span>{{ submitting ? 'Saving Student...' : 'Save Student' }}</span>
                </button>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>
