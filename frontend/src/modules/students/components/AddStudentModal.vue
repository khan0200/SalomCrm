<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { settingsApi } from '@/api/settings'
import {
  UserPlus, X, AlertCircle, CheckCircle2, Hash, User, Building2,
  Award, GraduationCap, School, Users, UserCheck, ShieldCheck,
  Check, ChevronDown, Sparkles
} from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  isSubmitting?: boolean
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

const modalError = ref<string | null>(null)
const modalSuccess = ref(false)

// University suggestions state
const isUniversityDropdownOpen = ref(false)
const highlightedUniversityIndex = ref(0)
const universityInputContainerRef = ref<HTMLElement | null>(null)

// Detect Mac OS for keyboard shortcuts
const isMac = computed(() => {
  if (typeof navigator === 'undefined') return false
  return /(Mac|iPhone|iPod|iPad)/i.test(navigator.platform || navigator.userAgent)
})

// Fetch universities directly from settings to ensure fresh and complete suggestions
const { data: settingsUniversitiesData } = useQuery({
  queryKey: ['settings-universities'],
  queryFn: () => settingsApi.getUniversities(),
  staleTime: 1000 * 60 * 5, // 5 minutes cache
})

import { getTariffPrice } from '@/utils/tariff'
import { useCurrency } from '@/composables/useCurrency'

const { formatCurrency } = useCurrency()

const officeOptions = computed(() => {
  return props.options?.offices || []
})

const tariffOptions = computed(() => {
  return (props.options?.tariffs || []).map(t => (typeof t === 'string' ? t : t.name))
})

const getTariffOptionLabel = (t: string) => {
  if (!t) return ''
  const price = getTariffPrice(t, null, props.options?.tariffs || [])
  if (price > 0) {
    return `${t} — ${formatCurrency(price)}`
  }
  return t
}

const levelOptions = computed(() => {
  return props.options?.levels || ['COLLEGE', 'BACHELOR', 'MASTERS', 'MASTER NO CERTIFICATE', 'LANGUAGE COURSE']
})

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
  return allUniversities.value.filter(u => u.toLowerCase().includes(query)).slice(0, 25)
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
    isUniversityDropdownOpen.value = false
    highlightedUniversityIndex.value = 0
  }
})

const handleKeyDown = (e: KeyboardEvent) => {
  if (!props.isOpen) return

  // Ctrl+Enter or Cmd+Enter to Submit quickly
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !props.isSubmitting) {
    e.preventDefault()
    handleSubmit()
    return
  }

  if (e.key === 'Escape' && !props.isSubmitting) {
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

const handleSubmit = () => {
  if (props.isSubmitting) return

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

  modalError.value = null

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
    // Every new student starts with Apostille on the checklist. 2 ta nomer
    // and Manzil need no seeding here — syncMissingDocuments derives both
    // automatically from the (still empty) phone/address fields.
    pick_needed: ['APOSTILLE'],
  })
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop with iOS Blur Transition -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[60] flex items-center justify-center p-3 sm:p-4 bg-black/45 dark:bg-black/70 backdrop-blur-md"
        @mousedown.self="() => { if (!isSubmitting) emit('close') }"
      >
        <!-- Modal Card with Apple Continuous Squircles & Spring Animation -->
        <Transition
          enter-active-class="transition duration-250 ease-[cubic-bezier(0.16,1,0.3,1)]"
          enter-from-class="transform scale-95 opacity-0 -translate-y-2"
          enter-to-class="transform scale-100 opacity-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="transform scale-100 opacity-100 translate-y-0"
          leave-to-class="transform scale-95 opacity-0 -translate-y-2"
        >
          <div
            v-if="isOpen"
            class="relative w-full max-w-[660px] flex flex-col rounded-[22px] border border-zinc-200/90 dark:border-white/10 bg-white dark:bg-[#15171a] shadow-[0_25px_60px_-15px_rgba(0,0,0,0.25)] dark:shadow-[0_30px_70px_-15px_rgba(0,0,0,0.7)] overflow-hidden max-h-[92vh]"
          >
            <!-- iOS Glass Header -->
            <div class="px-5 py-3.5 border-b border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between bg-zinc-50/70 dark:bg-zinc-900/50 backdrop-blur-md shrink-0">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-[12px] bg-gradient-to-br from-blue-500/10 to-indigo-500/10 dark:from-blue-500/20 dark:to-indigo-500/20 border border-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 shadow-xs">
                  <UserPlus class="w-4.5 h-4.5" />
                </div>
                <div>
                  <h2 class="text-sm sm:text-base font-bold text-zinc-900 dark:text-white tracking-tight leading-tight flex items-center gap-2">
                    <span>Add New Student</span>
                  </h2>
                  <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Register a new student into the master roster
                  </p>
                </div>
              </div>

              <!-- Header Controls -->
              <div class="flex items-center gap-2">
                <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-mono font-medium text-zinc-400 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                  ESC
                </kbd>
                <button
                  type="button"
                  :disabled="isSubmitting"
                  @click="emit('close')"
                  class="w-7 h-7 rounded-full bg-zinc-100 hover:bg-zinc-200/80 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200 flex items-center justify-center transition-all cursor-pointer active:scale-90"
                  title="Close (Esc)"
                >
                  <X class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <!-- Modal Body (iOS Inset-Grouped Cards) -->
            <form id="add-student-form" @submit.prevent="handleSubmit" class="overflow-y-auto px-5 py-4 space-y-3.5 flex-1 scrollbar-thin">
              <!-- Error Banner -->
              <Transition
                enter-active-class="transition duration-150 ease-out"
                enter-from-class="opacity-0 -translate-y-1"
                enter-to-class="opacity-100 translate-y-0"
              >
                <div
                  v-if="modalError"
                  class="flex items-center gap-2.5 rounded-[12px] bg-rose-50 dark:bg-rose-950/40 border border-rose-200/80 dark:border-rose-900/50 px-3.5 py-2.5 text-xs text-rose-700 dark:text-rose-300 shadow-xs"
                >
                  <AlertCircle class="h-4 w-4 shrink-0 text-rose-500" />
                  <span class="font-medium">{{ modalError }}</span>
                </div>
              </Transition>

              <!-- Success Banner -->
              <Transition
                enter-active-class="transition duration-150 ease-out"
                enter-from-class="opacity-0 -translate-y-1"
                enter-to-class="opacity-100 translate-y-0"
              >
                <div
                  v-if="modalSuccess"
                  class="flex items-center gap-2.5 rounded-[12px] bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-900/50 px-3.5 py-2.5 text-xs text-emerald-700 dark:text-emerald-300 shadow-xs"
                >
                  <CheckCircle2 class="h-4 w-4 shrink-0 text-emerald-500" />
                  <span class="font-medium">Student registered successfully!</span>
                </div>
              </Transition>

              <!-- Section 1: Identification Card -->
              <div class="space-y-1.5">
                <div class="flex items-center justify-between px-1">
                  <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 flex items-center gap-1.5">
                    <User class="w-3 h-3 text-blue-500" /> Identification
                  </span>
                  <span class="text-[10px] text-zinc-400 font-medium">* Required</span>
                </div>

                <div class="rounded-[16px] bg-zinc-50/80 dark:bg-zinc-900/70 border border-zinc-200/80 dark:border-zinc-800 p-3 sm:p-3.5 space-y-3">
                  <!-- Row 1: Student ID & Full Name -->
                  <div class="flex items-start gap-3">
                    <!-- Student ID Input -->
                    <div class="w-32 sm:w-36 shrink-0 space-y-1">
                      <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center justify-between">
                        <span>ID</span>
                        <span class="text-rose-500">*</span>
                      </label>
                      <div class="relative flex items-center rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 shadow-2xs focus-within:border-blue-500 focus-within:ring-3 focus-within:ring-blue-500/15 transition-all">
                        <Hash class="w-3.5 h-3.5 text-zinc-400 ml-2.5 shrink-0" />
                        <input
                          v-model="studentId"
                          type="text"
                          required
                          autofocus
                          :disabled="isSubmitting || modalSuccess"
                          placeholder="F101"
                          @input="studentId = studentId.toUpperCase()"
                          class="w-full h-9 pl-2 pr-2.5 bg-transparent text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none font-mono font-bold text-xs uppercase"
                        />
                      </div>
                    </div>

                    <!-- Full Name Input -->
                    <div class="flex-1 min-w-0 space-y-1">
                      <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center justify-between">
                        <span>Student Full Name</span>
                        <span class="text-rose-500">*</span>
                      </label>
                      <div class="relative flex items-center rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 shadow-2xs focus-within:border-blue-500 focus-within:ring-3 focus-within:ring-blue-500/15 transition-all">
                        <User class="w-3.5 h-3.5 text-zinc-400 ml-2.5 shrink-0" />
                        <input
                          v-model="fullName"
                          type="text"
                          required
                          :disabled="isSubmitting || modalSuccess"
                          placeholder="BAXTIYOR ALIMOV"
                          @input="fullName = fullName.toUpperCase()"
                          class="w-full h-9 pl-2 pr-7 bg-transparent text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none font-semibold text-xs uppercase"
                        />
                        <button
                          v-if="fullName"
                          type="button"
                          @click="fullName = ''"
                          class="absolute right-2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-0.5 rounded cursor-pointer"
                        >
                          <X class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Section 2: Branch & Academic Plan Card -->
              <div class="space-y-1.5">
                <div class="flex items-center justify-between px-1">
                  <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 flex items-center gap-1.5">
                    <GraduationCap class="w-3 h-3 text-indigo-500" /> Academic & Branch
                  </span>
                </div>

                <div class="rounded-[16px] bg-zinc-50/80 dark:bg-zinc-900/70 border border-zinc-200/80 dark:border-zinc-800 p-3 sm:p-3.5 space-y-3">
                  <!-- Office Branch Segmented Switcher / Selector -->
                  <div class="space-y-1">
                    <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center justify-between">
                      <span>Office Branch</span>
                      <span class="text-rose-500">*</span>
                    </label>

                    <!-- Segmented Control for 2-3 branches (iOS Native Style) -->
                    <div
                      v-if="officeOptions.length <= 3"
                      class="flex p-1 bg-zinc-200/70 dark:bg-zinc-800 rounded-[12px] gap-1 shadow-2xs"
                    >
                      <button
                        v-for="opt in officeOptions"
                        :key="opt"
                        type="button"
                        @click="office = opt"
                        :disabled="isSubmitting || modalSuccess"
                        class="flex-1 py-1.5 px-3 rounded-[9px] text-xs font-semibold transition-all duration-200 flex items-center justify-center gap-1.5 select-none cursor-pointer active:scale-[0.98]"
                        :class="office === opt
                          ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-white shadow-xs font-bold'
                          : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'"
                      >
                        <Building2 class="w-3.5 h-3.5" :class="office === opt ? 'text-blue-600 dark:text-blue-400' : 'text-zinc-400'" />
                        <span>{{ opt }}</span>
                      </button>
                    </div>

                    <!-- Dropdown for 4+ branches -->
                    <div v-else class="relative">
                      <select
                        v-model="office"
                        required
                        :disabled="isSubmitting || modalSuccess"
                        class="w-full h-9 pl-3 pr-8 rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 text-xs font-medium focus:outline-none focus:border-blue-500 focus:ring-3 focus:ring-blue-500/15 cursor-pointer appearance-none shadow-2xs"
                      >
                        <option value="">Select Office</option>
                        <option v-for="opt in officeOptions" :key="opt" :value="opt">{{ opt }}</option>
                      </select>
                      <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>

                  <!-- Tariff & Level to Study (2 Columns) -->
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <!-- Tariff -->
                    <div class="space-y-1">
                      <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center gap-1">
                        <Award class="w-3 h-3 text-amber-500" />
                        <span>Tariff</span>
                      </label>
                      <div class="relative">
                        <select
                          v-model="tariff"
                          :disabled="isSubmitting || modalSuccess"
                          class="w-full h-9 pl-3 pr-8 rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 text-xs font-medium focus:outline-none focus:border-blue-500 focus:ring-3 focus:ring-blue-500/15 cursor-pointer appearance-none shadow-2xs transition-all"
                        >
                          <option value="">Select Tariff</option>
                          <option v-for="t in tariffOptions" :key="t" :value="t">{{ getTariffOptionLabel(t) }}</option>
                        </select>
                        <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      </div>
                    </div>

                    <!-- Level to Study -->
                    <div class="space-y-1">
                      <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center gap-1">
                        <GraduationCap class="w-3 h-3 text-indigo-500" />
                        <span>Level to Study</span>
                      </label>
                      <div class="relative">
                        <select
                          v-model="level"
                          :disabled="isSubmitting || modalSuccess"
                          class="w-full h-9 pl-3 pr-8 rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 text-xs font-medium focus:outline-none focus:border-blue-500 focus:ring-3 focus:ring-blue-500/15 cursor-pointer appearance-none shadow-2xs transition-all"
                        >
                          <option value="">Select Level</option>
                          <option v-for="lvl in levelOptions" :key="lvl" :value="lvl">{{ lvl }}</option>
                        </select>
                        <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      </div>
                    </div>
                  </div>

                  <!-- University 1 (Spotlight-Style Autocomplete Search) -->
                  <div ref="universityInputContainerRef" class="relative space-y-1">
                    <div class="flex items-center justify-between">
                      <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center gap-1">
                        <School class="w-3 h-3 text-blue-500" />
                        <span>University 1</span>
                      </label>
                      <span v-if="allUniversities.length > 0" class="text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.2 rounded-md border border-zinc-200/60 dark:border-zinc-700">
                        {{ allUniversities.length }} universities
                      </span>
                    </div>

                    <div class="relative flex items-center rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 shadow-2xs focus-within:border-blue-500 focus-within:ring-3 focus-within:ring-blue-500/15 transition-all">
                      <School class="w-3.5 h-3.5 text-zinc-400 ml-2.5 shrink-0" />
                      <input
                        v-model="university1"
                        type="text"
                        :disabled="isSubmitting || modalSuccess"
                        placeholder="Type university name (e.g. SEJONG)..."
                        @input="() => { university1 = university1.toUpperCase(); isUniversityDropdownOpen = true; highlightedUniversityIndex = 0; }"
                        @focus="isUniversityDropdownOpen = true"
                        @keydown="handleUniversityKeyDown"
                        class="w-full h-9 pl-2 pr-7 bg-transparent text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none text-xs font-medium uppercase"
                        autocomplete="off"
                      />

                      <!-- Clear Button -->
                      <button
                        v-if="university1"
                        type="button"
                        @click="() => { university1 = ''; isUniversityDropdownOpen = true; }"
                        class="absolute right-2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-0.5 rounded cursor-pointer"
                        title="Clear"
                      >
                        <X class="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <!-- Spotlight Floating Dropdown Popover -->
                    <Transition
                      enter-active-class="transition duration-150 ease-out"
                      enter-from-class="opacity-0 scale-98 -translate-y-1"
                      enter-to-class="opacity-100 scale-100 translate-y-0"
                      leave-active-class="transition duration-100 ease-in"
                      leave-from-class="opacity-100 scale-100 translate-y-0"
                      leave-to-class="opacity-0 scale-98 -translate-y-1"
                    >
                      <div
                        v-if="isUniversityDropdownOpen && (filteredUniversities.length > 0 || (university1.trim() && allUniversities.length > 0))"
                        class="absolute left-0 right-0 top-full mt-1.5 z-50 rounded-[14px] border border-zinc-200 dark:border-zinc-700 bg-white/95 dark:bg-zinc-850/95 backdrop-blur-xl shadow-2xl overflow-hidden"
                      >
                        <ul class="max-h-48 overflow-y-auto py-1 divide-y divide-zinc-100/80 dark:divide-zinc-800 scrollbar-thin">
                          <li
                            v-for="(uni, index) in filteredUniversities"
                            :key="uni"
                            @mousedown.prevent="selectUniversity(uni)"
                            @mouseenter="highlightedUniversityIndex = index"
                            class="px-3 py-2 text-xs flex items-center justify-between cursor-pointer transition-colors"
                            :class="highlightedUniversityIndex === index || university1 === uni
                              ? 'bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 font-semibold'
                              : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800/60'"
                          >
                            <div class="flex items-center gap-2 truncate">
                              <School class="w-3 h-3 shrink-0 text-zinc-400" />
                              <span class="truncate uppercase">{{ uni }}</span>
                            </div>
                            <Check v-if="university1 === uni" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0 ml-2" />
                          </li>

                          <li v-if="filteredUniversities.length === 0" class="px-3 py-2.5 text-xs text-zinc-400 italic text-center">
                            Custom entry "{{ university1 }}" will be used.
                          </li>
                        </ul>
                      </div>
                    </Transition>
                  </div>
                </div>
              </div>

              <!-- Section 3: Assignment & Management Card -->
              <div class="space-y-1.5">
                <div class="flex items-center justify-between px-1">
                  <span class="text-[10.5px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 flex items-center gap-1.5">
                    <Users class="w-3 h-3 text-purple-500" /> Assignment & Coordination
                  </span>
                </div>

                <div class="rounded-[16px] bg-zinc-50/80 dark:bg-zinc-900/70 border border-zinc-200/80 dark:border-zinc-800 p-3 sm:p-3.5">
                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <!-- Group -->
                    <div class="space-y-1">
                      <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center gap-1">
                        <Users class="w-3 h-3 text-purple-500" />
                        <span>Group</span>
                      </label>
                      <div class="relative">
                        <select
                          v-model="studentGroup"
                          :disabled="isSubmitting || modalSuccess"
                          class="w-full h-9 pl-3 pr-8 rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 text-xs font-medium focus:outline-none focus:border-blue-500 focus:ring-3 focus:ring-blue-500/15 cursor-pointer appearance-none shadow-2xs transition-all"
                        >
                          <option value="">Select Group</option>
                          <option v-for="g in groupOptions" :key="g" :value="g">{{ g }}</option>
                        </select>
                        <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      </div>
                    </div>

                    <!-- Lead By -->
                    <div class="space-y-1">
                      <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center gap-1">
                        <UserCheck class="w-3 h-3 text-emerald-500" />
                        <span>Lead By</span>
                      </label>
                      <div class="relative">
                        <select
                          v-model="leadBy"
                          :disabled="isSubmitting || modalSuccess"
                          class="w-full h-9 pl-3 pr-8 rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 text-xs font-medium focus:outline-none focus:border-blue-500 focus:ring-3 focus:ring-blue-500/15 cursor-pointer appearance-none shadow-2xs transition-all"
                        >
                          <option value="">Select Lead By</option>
                          <option v-for="l in leadByOptions" :key="l" :value="l">{{ l }}</option>
                        </select>
                        <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      </div>
                    </div>

                    <!-- Coordinator -->
                    <div class="space-y-1">
                      <label class="block text-[10.5px] font-bold uppercase tracking-wide text-zinc-600 dark:text-zinc-300 flex items-center gap-1">
                        <ShieldCheck class="w-3 h-3 text-blue-500" />
                        <span>Coordinator</span>
                      </label>
                      <div class="relative">
                        <select
                          v-model="coordinator"
                          :disabled="isSubmitting || modalSuccess"
                          class="w-full h-9 pl-3 pr-8 rounded-[11px] border border-zinc-300/90 dark:border-zinc-700/80 bg-white dark:bg-zinc-850 text-zinc-900 dark:text-zinc-100 text-xs font-medium focus:outline-none focus:border-blue-500 focus:ring-3 focus:ring-blue-500/15 cursor-pointer appearance-none shadow-2xs transition-all"
                        >
                          <option value="">Select Coordinator</option>
                          <option v-for="c in coordinatorOptions" :key="c" :value="c">{{ c }}</option>
                        </select>
                        <ChevronDown class="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </form>

            <!-- iOS Glass Footer -->
            <div class="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between bg-zinc-50/70 dark:bg-zinc-900/50 backdrop-blur-md shrink-0">
              <div class="flex items-center gap-2 text-[11px] text-zinc-500 dark:text-zinc-400">
                <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-zinc-400 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                  {{ isMac ? '⌘ + ↵' : 'Ctrl + Enter' }}
                </kbd>
                <span class="hidden sm:inline text-zinc-400">to save</span>
              </div>

              <div class="flex items-center gap-2">
                <button
                  type="button"
                  :disabled="isSubmitting || modalSuccess"
                  @click="emit('close')"
                  class="px-4 py-2 rounded-[12px] text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all cursor-pointer disabled:opacity-50 active:scale-95 select-none"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  form="add-student-form"
                  :disabled="isSubmitting || modalSuccess"
                  class="px-5 py-2 rounded-[12px] text-xs font-bold bg-gradient-to-b from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white transition-all cursor-pointer select-none disabled:opacity-50 flex items-center gap-2 shadow-sm shadow-blue-500/30 active:scale-95"
                >
                  <Sparkles class="w-3.5 h-3.5" :class="{ 'animate-sparkle': isSubmitting }" />
                  <span>{{ isSubmitting ? 'Saving...' : 'Save Student' }}</span>
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

