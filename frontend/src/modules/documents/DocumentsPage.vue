<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { ChevronDown, Check, FileText, ChevronLeft, ChevronRight, RefreshCw, ShieldAlert, X } from 'lucide-vue-next'
import type { Student } from '@/types'
import { studentsApi } from '@/api/students'
import { paymentsApi } from '@/api/payments'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import { useAlphanumericSort } from '@/composables/useAlphanumericSort'
import { useDocumentHelpers, syncMissingDocuments, isFieldFilled } from '@/composables/useDocumentHelpers'
import DocumentsModal from './components/DocumentsModal.vue'
import StudentFilters from '@/modules/students/components/StudentFilters.vue'

const queryClient = useQueryClient()
const dashboardStore = useStudentDashboardStore()
const { compareStudentIds } = useAlphanumericSort()
const {
  getEffectiveMissingDocs, getDocColor, getDocRemainingCount, getShortLabel,
  PICK_NEEDED_LIST, HAND_COUNT_DOCS
} = useDocumentHelpers()

// Search and filters bound to global dashboard store (from Top Navbar)
const searchQuery = computed(() => dashboardStore.searchQuery)
const searchMode = computed(() => dashboardStore.searchMode)

const selectedTariffs = computed({
  get: () => dashboardStore.selectedTariffs,
  set: (v) => { dashboardStore.selectedTariffs = v }
})
const selectedLevels = computed({
  get: () => dashboardStore.selectedLevels,
  set: (v) => { dashboardStore.selectedLevels = v }
})
const selectedGroups = computed({
  get: () => dashboardStore.selectedGroups,
  set: (v) => { dashboardStore.selectedGroups = v }
})
const selectedCerts = computed({
  get: () => dashboardStore.selectedCerts,
  set: (v) => { dashboardStore.selectedCerts = v }
})
const selectedScores = computed({
  get: () => dashboardStore.selectedScores,
  set: (v) => { dashboardStore.selectedScores = v }
})
const selectedTags = computed({
  get: () => dashboardStore.selectedTags,
  set: (v) => { dashboardStore.selectedTags = v }
})
const selectedLeads = computed({
  get: () => dashboardStore.selectedLeads,
  set: (v) => { dashboardStore.selectedLeads = v }
})
const selectedMissingDocs = computed({
  get: () => dashboardStore.selectedMissingDocs,
  set: (v) => { dashboardStore.selectedMissingDocs = v }
})
const isFilterPanelOpen = computed({
  get: () => dashboardStore.isFilterPanelOpen,
  set: (v) => { dashboardStore.isFilterPanelOpen = v }
})

const sortOrder = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)

const isModalOpen = ref(false)
const selectedStudent = ref<Student | null>(null)
const modalUpdating = ref(false)
const studentPaymentsDone = ref<number | null>(null)
const studentPaymentsDoneLoading = ref(false)

// ── Data (shares the same master roster cache as the Students page) ──────────
const { data: optionsData } = useQuery({
  queryKey: ['student-options'],
  queryFn: () => studentsApi.getOptions(),
  staleTime: 1000 * 60 * 10,
})

const { data: allStudentsData, isLoading, isError, refetch } = useQuery({
  queryKey: ['all-students-master'],
  queryFn: () => studentsApi.getStudents({
    page: 1,
    page_size: 5000,
    folder: 'all',
    include_archive: true,
  }),
  staleTime: 1000 * 60 * 5,
})

const students = computed<Student[]>(() => allStudentsData.value?.results || [])

// Reset to page 1 on any filter/search/sort change
watch([
  () => dashboardStore.selectedTariffs,
  () => dashboardStore.selectedLevels,
  () => dashboardStore.selectedGroups,
  () => dashboardStore.selectedCerts,
  () => dashboardStore.selectedScores,
  () => dashboardStore.selectedTags,
  () => dashboardStore.selectedLeads,
  () => dashboardStore.selectedMissingDocs,
  searchQuery,
  searchMode,
  sortOrder
], () => {
  currentPage.value = 1
}, { deep: true })

const handleApplyFilters = (filters: {
  tariffs: string[]
  levels: string[]
  groups: string[]
  certs: string[]
  scores: string[]
  tags: string[]
  leads: string[]
  missingDocs: string[]
}) => {
  dashboardStore.selectedTariffs = filters.tariffs
  dashboardStore.selectedLevels = filters.levels
  dashboardStore.selectedGroups = filters.groups
  dashboardStore.selectedCerts = filters.certs
  dashboardStore.selectedScores = filters.scores
  dashboardStore.selectedTags = filters.tags
  dashboardStore.selectedLeads = filters.leads
  dashboardStore.selectedMissingDocs = filters.missingDocs || []
  currentPage.value = 1
  isFilterPanelOpen.value = false
}

// ── Filtering ───────────────────────────────────────────────────────────────
const filteredStudents = computed(() => students.value.filter(student => {
  // 1. Deleted Students
  const showDeleted = dashboardStore.selectedLevels.includes('DELETED')
  if (showDeleted) {
    if (student.is_deleted !== true) return false
  } else {
    if (student.is_deleted === true) return false
  }

  // 2. Tariff Filter
  if (dashboardStore.selectedTariffs.length > 0) {
    const matchesTariff = dashboardStore.selectedTariffs.includes(student.tariff || 'NO_TARIFF') ||
                          (dashboardStore.selectedTariffs.includes('NO_TARIFF') && !student.tariff)
    if (!matchesTariff) return false
  }

  // 3. Level Filter
  const activeLevels = dashboardStore.selectedLevels.filter(l => l !== 'DELETED')
  if (activeLevels.length > 0) {
    const matchesLevel = activeLevels.includes(student.level || '') ||
                         activeLevels.includes(student.level2 || '') ||
                         (activeLevels.includes('NO_LEVEL') && !student.level && !student.level2)
    if (!matchesLevel) return false
  }

  // 4. Group Filter
  if (dashboardStore.selectedGroups.length > 0) {
    const matchesGroup = dashboardStore.selectedGroups.includes(student.student_group || '') ||
                         (dashboardStore.selectedGroups.includes('NO_GROUP') && !student.student_group)
    if (!matchesGroup) return false
  }

  // 5. Certificate Filter
  if (dashboardStore.selectedCerts.length > 0) {
    let matchesCert = false
    if (dashboardStore.selectedCerts.includes('NO CERTIFICATE') &&
        (!student.language_certificate || student.language_certificate === 'NO CERTIFICATE')) {
      matchesCert = true
    }
    if (dashboardStore.selectedCerts.includes('EXPECTED') &&
        (student.certificate_score?.toUpperCase() === 'EXPECTED' ||
         student.certificate_score_2?.toUpperCase() === 'EXPECTED' ||
         student.certificate_score_3?.toUpperCase() === 'EXPECTED')) {
      matchesCert = true
    }
    const certMatches = [student.language_certificate, student.language_certificate_2, student.language_certificate_3]
      .some(c => c && c !== 'NO CERTIFICATE' && dashboardStore.selectedCerts.includes(c))
    if (certMatches) matchesCert = true

    // If a specific score sub-filter is also active, additionally check score
    if (matchesCert && dashboardStore.selectedScores.length > 0 && dashboardStore.selectedCerts.length === 1) {
      const cert = dashboardStore.selectedCerts[0] || ''
      const scores = [student.certificate_score, student.certificate_score_2, student.certificate_score_3]
      const certs = [student.language_certificate, student.language_certificate_2, student.language_certificate_3]
      matchesCert = certs.some((c, i) => {
        if (!c || c === 'NO CERTIFICATE') return false
        if (c.toUpperCase() !== cert.toUpperCase()) return false
        const score = (scores[i] || '').trim().toUpperCase()
        return dashboardStore.selectedScores.some(f => f.toUpperCase() === score)
      })
    }

    if (!matchesCert) return false
  }

  // 6. Missing Docs Filter (OR matching)
  if (dashboardStore.selectedMissingDocs.length > 0) {
    const missingList = getEffectiveMissingDocs(student)
    const matchesMissing = dashboardStore.selectedMissingDocs.some(d => missingList.includes(d))
    if (!matchesMissing) return false
  }

  // 7. Tags Filter
  if (dashboardStore.selectedTags.length > 0) {
    const matchesTag = dashboardStore.selectedTags.some(tag => {
      if (tag === 'Custom') {
        const predefined = ['Call', 'Apply', 'Documents', 'Payment']
        return student.task_tags && student.task_tags.some(t => !predefined.includes(t))
      }
      return student.task_tags && student.task_tags.includes(tag)
    })
    if (!matchesTag) return false
  }

  // 8. Lead By Filter
  if (dashboardStore.selectedLeads.length > 0) {
    const matchNoLead = dashboardStore.selectedLeads.includes('NO_LEADBY') && !student.lead_by
    const matchLead = student.lead_by && dashboardStore.selectedLeads.includes(student.lead_by)
    if (!matchNoLead && !matchLead) return false
  }

  // 9. Search query matching — identical to students page
  const cleanSearch = searchQuery.value.trim().toLowerCase()
  if (cleanSearch) {
    let matchesSearch: boolean
    if (searchMode.value === 'id') {
      matchesSearch = Boolean(student.id && student.id.toLowerCase().includes(cleanSearch))
    } else {
      matchesSearch = Boolean(
        (student.id && student.id.toLowerCase().includes(cleanSearch)) ||
        (student.full_name && student.full_name.toLowerCase().includes(cleanSearch)) ||
        (student.korean_name && student.korean_name.toLowerCase().includes(cleanSearch)) ||
        (student.passport && student.passport.toLowerCase().includes(cleanSearch)) ||
        (student.phone1 && student.phone1.toLowerCase().includes(cleanSearch)) ||
        (student.phone2 && student.phone2.toLowerCase().includes(cleanSearch)) ||
        (student.father_phone && student.father_phone.toLowerCase().includes(cleanSearch)) ||
        (student.mother_phone && student.mother_phone.toLowerCase().includes(cleanSearch)) ||
        (student.university_1 && student.university_1.toLowerCase().includes(cleanSearch)) ||
        (student.university_2 && student.university_2.toLowerCase().includes(cleanSearch)) ||
        (student.university_3 && student.university_3.toLowerCase().includes(cleanSearch)) ||
        (student.university_4 && student.university_4.toLowerCase().includes(cleanSearch)) ||
        (student.university_5 && student.university_5.toLowerCase().includes(cleanSearch)) ||
        (student.final_school_name && student.final_school_name.toLowerCase().includes(cleanSearch))
      )
    }
    if (!matchesSearch) return false
  }

  return true
}))

const sortedStudents = computed(() =>
  [...filteredStudents.value].sort((a, b) => compareStudentIds(a.id, b.id, sortOrder.value))
)

const PAGE_SIZE = 30
const totalPages = computed(() => Math.max(1, Math.ceil(sortedStudents.value.length / PAGE_SIZE)))
const safePage = computed(() => Math.min(currentPage.value, totalPages.value))
const pagedStudents = computed(() =>
  sortedStudents.value.slice((safePage.value - 1) * PAGE_SIZE, safePage.value * PAGE_SIZE)
)

const pageNumbers = computed(() => {
  const total = totalPages.value
  const cur = safePage.value
  const pages: number[] = []
  const start = Math.max(1, cur - 2)
  const end = Math.min(total, start + 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

// ── Table cell rendering helpers ────────────────────────────────────────────
// Student ghost metadata: "ID | TARIFF | LEVEL | LEVEL2" (empty parts skipped)
const getGhostText = (s: Student) => {
  const parts: string[] = []
  if (s.id) parts.push(s.id)
  if (s.tariff) parts.push(s.tariff)
  if (s.level) parts.push(s.level)
  if (s.level2) parts.push(s.level2)
  return parts.join(' | ')
}

const getMissingPills = (s: Student) => {
  const missingDocs = getEffectiveMissingDocs(s)
  if (missingDocs.includes('FULL OK')) return { fullOk: true, items: [] as string[] }
  const items = missingDocs.filter(d => d !== 'FULL OK' && !(d === 'MARRIAGE CERTIFICATE' && s.has_mc === false))
  return { fullOk: false, items }
}

const getDocCell = (s: Student, docName: string) => {
  if (docName === 'MARRIAGE CERTIFICATE' && s.has_mc === false) {
    return { na: true, count: 0, missing: false }
  }
  const missingList = getEffectiveMissingDocs(s)
  const isMissing = !missingList.includes('FULL OK') && missingList.includes(docName)
  return { na: false, count: getDocRemainingCount(s, docName), missing: isMissing }
}

// ── Modal open (re-syncs pick_needed before showing, as in source) ───────────
const openStudentModal = async (student: Student) => {
  const synced = syncMissingDocuments(student)
  const current = student.pick_needed || []
  const drifted = synced.length !== current.length || synced.some(d => !current.includes(d))

  if (drifted) {
    try {
      await studentsApi.updateStudent(student.id, { pick_needed: synced })
      patchStudentInCache(student.id, { pick_needed: synced })
    } catch (err) {
      console.error('Error syncing missing documents:', err)
    }
  }

  selectedStudent.value = students.value.find(s => s.id === student.id) || student
  isModalOpen.value = true

  // Fetch real payments-done total
  studentPaymentsDone.value = null
  studentPaymentsDoneLoading.value = true
  try {
    const res = await paymentsApi.getPaymentHistory({ student_id: student.id, page_size: 100 })
    const total = (res.results || [])
      .filter((p: any) => !p.is_discount && !p.is_withdrawal)
      .reduce((sum: number, p: any) => sum + (Number(p.amount) || 0), 0)
    studentPaymentsDone.value = total
  } catch (err) {
    console.error('Error loading payments total:', err)
    studentPaymentsDone.value = 0
  } finally {
    studentPaymentsDoneLoading.value = false
  }
}

// Keep the modal's student reference in sync with the master roster
watch(students, (list) => {
  if (selectedStudent.value) {
    const updated = list.find(s => s.id === selectedStudent.value!.id)
    if (updated) selectedStudent.value = updated
  }
})

const patchStudentInCache = (studentId: string, patch: Partial<Student>) => {
  queryClient.setQueryData(['all-students-master'], (old: any) => {
    if (!old?.results) return old
    return {
      ...old,
      results: old.results.map((s: Student) => s.id === studentId ? { ...s, ...patch } : s)
    }
  })
  if (selectedStudent.value?.id === studentId) {
    selectedStudent.value = { ...selectedStudent.value, ...patch } as Student
  }
}

// ── In-Modal Actions ────────────────────────────────────────────────────────
const handleTogglePickNeeded = async (studentId: string, pill: string) => {
  const student = students.value.find(s => s.id === studentId)
  if (!student) return

  let updatedPick: string[] = student.pick_needed ? [...student.pick_needed] : []
  let showMessage: string | null = null

  const isRemoving = updatedPick.includes(pill)

  if (isRemoving) {
    if (pill === '2 ta nomer') {
      const phoneFields = [student.phone1, student.phone2, student.father_phone, student.mother_phone]
      if (phoneFields.filter(isFieldFilled).length < 2) {
        alert('Talabaga kamida 2 ta nomer kirgizing!')
        return
      }
    } else if (pill === 'Email') {
      if (!isFieldFilled(student.email)) { alert('Email manzilini kirgizing!'); return }
    } else if (pill === 'Foreign passport') {
      if (!isFieldFilled(student.passport)) { alert('Pasport raqamini kirgizing!'); return }
    } else if (pill === 'Manzil') {
      if (!isFieldFilled(student.address)) { alert('Talabaning manzilini kirgizing!'); return }
    } else if (pill === 'Edu-Level') {
      if (!isFieldFilled(student.level)) { alert("Ta'lim darajasini kirgizing!"); return }
    }
  }

  if (pill === 'FULL OK') {
    updatedPick = updatedPick.includes('FULL OK') ? [] : ['FULL OK']
  } else {
    updatedPick = updatedPick.filter(p => p !== 'FULL OK')
    if (updatedPick.includes(pill)) {
      updatedPick = updatedPick.filter(p => p !== pill)
      if (pill === 'Foreign passport') {
        showMessage = "Talabani zagranini oldingizmi? uni kirgizing, ismini tekshirib yozib qo'ying!"
      } else if (pill === '2 ta nomer') {
        showMessage = "Talabaning nomerini to'g'ri yozing! Bazaga kiritish esdan chiqmasin!"
      } else if (pill === 'Email') {
        showMessage = 'Email ni tekshirib oling, Bazaga kiritish esdan chiqmasin! Iltimos'
      } else if (pill === 'Manzil') {
        showMessage = 'Manzil ingliz tilida yozing iltimos. Bazaga kiritish esdan chiqmasin'
      } else if (['IELTS', 'TOEFL', 'SKA', 'TOPIK', 'SAT', 'CEFR'].includes(pill)) {
        showMessage = "Til sertifikati va darajasini talabani bazasiga yozib qo'ying!"
      }
    } else {
      updatedPick.push(pill)
    }
  }

  // Run syncMissingDocuments to ensure required fields remain consistent
  updatedPick = syncMissingDocuments({ ...student, pick_needed: updatedPick } as Student)

  modalUpdating.value = true
  try {
    await studentsApi.updateStudent(studentId, { pick_needed: updatedPick })
    patchStudentInCache(studentId, { pick_needed: updatedPick })
    if (showMessage) alert(showMessage)
  } catch (err: any) {
    console.error('Error updating pick needed:', err)
    alert(err.response?.data?.detail || err.message || 'Failed to update missing documents list.')
  } finally {
    modalUpdating.value = false
  }
}

const handleToggleMcEnabled = async (studentId: string) => {
  const student = students.value.find(s => s.id === studentId)
  if (!student) return
  const newMc = !student.has_mc

  modalUpdating.value = true
  try {
    await studentsApi.updateStudent(studentId, { has_mc: newMc })
    patchStudentInCache(studentId, { has_mc: newMc })
  } catch (err: any) {
    console.error('Error toggling has_mc:', err)
    alert(err.response?.data?.detail || err.message || 'Failed to update MC requirement.')
  } finally {
    modalUpdating.value = false
  }
}

const handleUpdateCopyCount = async (studentId: string, field: string, value: number) => {
  if (value < 0) return
  modalUpdating.value = true
  try {
    await studentsApi.updateStudent(studentId, { [field]: value } as Partial<Student>)
    patchStudentInCache(studentId, { [field]: value } as Partial<Student>)
  } catch (err: any) {
    console.error('Error updating hand count:', err)
    alert(err.response?.data?.detail || err.message || 'Failed to update document hand count.')
  } finally {
    modalUpdating.value = false
  }
}

const labelForOption = (opt: string) => {
  if (opt === 'NO_TARIFF') return 'No Tariff'
  if (opt === 'NO_LEVEL') return 'No Level'
  if (opt === 'NO_GROUP') return 'No Group'
  if (opt === 'DELETED') return 'Deleted students'
  return opt
}

const DOC_BADGE_BASE = 'h-6 w-6 shrink-0 rounded-full inline-flex items-center justify-center leading-none font-bold text-[11px] shadow-2xs border'
</script>

<template>
  <div class="flex flex-col gap-3 p-3 sm:p-4">
    <!-- Master-Detail Filter Panel Popover (Triggered from Top Navbar) -->
    <StudentFilters
      :is-open="isFilterPanelOpen"
      :options="optionsData || { tariffs: [], levels: [], groups: [], leads: [], folders: [] }"
      :students="students"
      :selected-tariffs="dashboardStore.selectedTariffs"
      :selected-levels="dashboardStore.selectedLevels"
      :selected-groups="dashboardStore.selectedGroups"
      :selected-certs="dashboardStore.selectedCerts"
      :selected-scores="dashboardStore.selectedScores"
      :selected-tags="dashboardStore.selectedTags"
      :selected-leads="dashboardStore.selectedLeads"
      :selected-missing-docs="dashboardStore.selectedMissingDocs"
      :matching-count="filteredStudents.length"
      @close="isFilterPanelOpen = false"
      @apply="handleApplyFilters"
    />

    <!-- Active Filter Chips (if any selected) -->
    <div v-if="dashboardStore.activeFiltersCount > 0" class="flex flex-wrap items-center gap-1.5 px-1 py-0.5 select-none text-xs">
      <span class="text-[11px] font-bold text-zinc-500 mr-1">Active Filters:</span>

      <span
        v-for="t in dashboardStore.selectedTariffs"
        :key="`t-${t}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-full font-medium"
      >
        <span>Tariff: {{ t === 'NO_TARIFF' ? 'No Tariff' : t }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedTariffs = dashboardStore.selectedTariffs.filter(x => x !== t)" />
      </span>

      <span
        v-for="l in dashboardStore.selectedLevels"
        :key="`l-${l}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 rounded-full font-medium"
      >
        <span>Level: {{ l === 'NO_LEVEL' ? 'No Level' : l }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedLevels = dashboardStore.selectedLevels.filter(x => x !== l)" />
      </span>

      <span
        v-for="g in dashboardStore.selectedGroups"
        :key="`g-${g}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 rounded-full font-medium"
      >
        <span>Group: {{ g === 'NO_GROUP' ? 'No Group' : g }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedGroups = dashboardStore.selectedGroups.filter(x => x !== g)" />
      </span>

      <span
        v-for="c in dashboardStore.selectedCerts"
        :key="`c-${c}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 rounded-full font-medium"
      >
        <span>Cert: {{ c }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedCerts = dashboardStore.selectedCerts.filter(x => x !== c)" />
      </span>

      <span
        v-for="s in dashboardStore.selectedScores"
        :key="`s-${s}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 rounded-full font-medium"
      >
        <span>Score: {{ s }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedScores = dashboardStore.selectedScores.filter(x => x !== s)" />
      </span>

      <span
        v-for="m in dashboardStore.selectedMissingDocs"
        :key="`m-${m}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-800 rounded-full font-medium"
      >
        <span>Missing: {{ m }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedMissingDocs = dashboardStore.selectedMissingDocs.filter(x => x !== m)" />
      </span>

      <span
        v-for="tg in dashboardStore.selectedTags"
        :key="`tg-${tg}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-full font-medium"
      >
        <span>Tag: {{ tg }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedTags = dashboardStore.selectedTags.filter(x => x !== tg)" />
      </span>

      <span
        v-for="lb in dashboardStore.selectedLeads"
        :key="`lb-${lb}`"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 rounded-full font-medium"
      >
        <span>Lead: {{ lb === 'NO_LEADBY' ? 'No Lead by' : lb }}</span>
        <X class="w-3 h-3 cursor-pointer hover:text-red-500" @click="dashboardStore.selectedLeads = dashboardStore.selectedLeads.filter(x => x !== lb)" />
      </span>

      <button
        type="button"
        @click="dashboardStore.resetAllFilters()"
        class="text-xs font-bold text-rose-600 hover:text-rose-700 ml-1 cursor-pointer transition-colors"
      >
        Clear All
      </button>
    </div>

    <!-- Summary line -->
    <div class="flex items-center justify-between px-1">
      <span class="text-xs font-bold text-zinc-500 dark:text-zinc-400">
        Showing {{ pagedStudents.length }} of {{ sortedStudents.length }} students
      </span>
      <a
        href="https://drive.google.com"
        target="_blank"
        rel="noopener noreferrer"
        class="text-xs font-bold text-[#007aff] hover:underline"
      >
        Access to Drive
      </a>
    </div>

    <!-- Table -->
    <div class="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <!-- Loading Skeleton -->
      <div v-if="isLoading" class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60">
              <th class="px-4 py-2.5 text-[10.5px] uppercase font-bold text-zinc-500 dark:text-zinc-400 tracking-wider">ID / Name</th>
              <th class="px-4 py-2.5 text-[10.5px] uppercase font-bold text-zinc-500 dark:text-zinc-400 tracking-wider">Missing</th>
              <th v-for="d in HAND_COUNT_DOCS" :key="d.label" class="px-2 py-2.5 text-center text-[10.5px] uppercase font-bold text-zinc-500 dark:text-zinc-400 tracking-wider w-[56px]">
                {{ d.label }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
            <tr v-for="i in 12" :key="i" class="animate-pulse">
              <td class="px-4 py-2">
                <div class="h-3.5 w-3/5 rounded bg-zinc-200 dark:bg-zinc-800 mb-1" />
                <div class="h-2.5 w-2/5 rounded bg-zinc-100 dark:bg-zinc-800/70" />
              </td>
              <td class="px-4 py-2">
                <div class="flex flex-wrap gap-1.5">
                  <div class="h-4 w-12 rounded-full bg-zinc-100 dark:bg-zinc-800/70" />
                  <div class="h-4 w-14 rounded-full bg-zinc-100 dark:bg-zinc-800/70" />
                  <div class="h-4 w-10 rounded-full bg-zinc-100 dark:bg-zinc-800/70" />
                </div>
              </td>
              <td v-for="d in HAND_COUNT_DOCS" :key="d.label" class="px-2 py-2 text-center">
                <div class="h-6 w-6 rounded-full bg-zinc-100 dark:bg-zinc-800/70 mx-auto" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Error -->
      <div v-else-if="isError" class="p-8 flex flex-col items-center gap-3">
        <span class="text-sm font-bold text-rose-500">Failed to load students.</span>
        <button @click="refetch()" class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#007aff] text-white text-xs font-bold cursor-pointer hover:bg-blue-600 transition-all">
          <RefreshCw class="h-3.5 w-3.5" /> Reload
        </button>
      </div>

      <!-- Empty -->
      <div v-else-if="pagedStudents.length === 0" class="p-8 text-center">
        <FileText class="h-9 w-9 mx-auto text-zinc-400 opacity-40 mb-2.5" />
        <p class="text-sm font-bold text-zinc-800 dark:text-zinc-200">No matching student documents found</p>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">Adjust your filter options.</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60">
              <th class="px-4 py-2.5">
                <button
                  @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
                  class="inline-flex items-center gap-1.5 text-[10.5px] uppercase font-bold text-zinc-500 dark:text-zinc-400 tracking-wider hover:text-zinc-900 dark:hover:text-zinc-100 cursor-pointer transition-all"
                >
                  ID / Name
                  <ChevronDown class="h-3 w-3 transition-transform" :class="sortOrder === 'desc' ? 'rotate-180' : ''" />
                </button>
              </th>
              <th class="px-4 py-2.5 text-[10.5px] uppercase font-bold text-zinc-500 dark:text-zinc-400 tracking-wider">Missing</th>
              <th v-for="d in HAND_COUNT_DOCS" :key="d.label" class="px-2 py-2.5 text-center text-[10.5px] uppercase font-bold text-zinc-500 dark:text-zinc-400 tracking-wider w-[56px]">
                {{ d.label }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800 text-[13px]">
            <tr
              v-for="s in pagedStudents"
              :key="s.id"
              @click="openStudentModal(s)"
              class="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 cursor-pointer transition-colors text-zinc-800 dark:text-zinc-200"
              :class="s.is_deleted ? 'bg-rose-500/5 dark:bg-rose-950/10' : ''"
            >
              <!-- ID / Name -->
              <td class="px-4 py-2 align-middle">
                <div class="flex items-center gap-1.5">
                  <ShieldAlert v-if="s.is_deleted" class="h-3.5 w-3.5 text-rose-500 shrink-0" />
                  <span class="font-bold text-[13px] uppercase tracking-wide leading-tight text-zinc-900 dark:text-zinc-100">{{ s.full_name }}</span>
                </div>
                <span class="text-[11px] text-zinc-500 dark:text-zinc-400 font-medium tracking-wide uppercase mt-0.5 block opacity-75">
                  {{ getGhostText(s) }}
                </span>
              </td>

              <!-- Missing pills -->
              <td class="px-4 py-2 align-middle">
                <span
                  v-if="getMissingPills(s).fullOk"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full h-5 text-[10.5px] font-bold uppercase bg-emerald-500 text-white shadow-2xs leading-none"
                >
                  ✔ FULL OK
                </span>
                <span
                  v-else-if="getMissingPills(s).items.length === 0"
                  class="text-[12px] text-zinc-400 dark:text-zinc-500 italic font-normal opacity-70"
                >
                  No missing documents
                </span>
                <div v-else class="flex flex-wrap gap-1 items-center">
                  <span
                    v-for="d in getMissingPills(s).items"
                    :key="d"
                    class="inline-flex px-2 py-0.5 rounded-full text-[9.5px] font-bold tracking-wide uppercase shadow-2xs text-white border-none"
                    :style="{ backgroundColor: getDocColor(getShortLabel(d)).bg }"
                  >
                    {{ getShortLabel(d) }}
                  </span>
                </div>
              </td>

              <!-- Doc counters -->
              <td v-for="d in HAND_COUNT_DOCS" :key="d.label" class="px-2 py-2 text-center align-middle">
                <span
                  v-if="getDocCell(s, d.name).na"
                  :class="DOC_BADGE_BASE"
                  class="bg-zinc-100 dark:bg-zinc-800 text-zinc-400 dark:text-zinc-500 border-zinc-200 dark:border-zinc-700"
                >
                  N/A
                </span>
                <span
                  v-else-if="getDocCell(s, d.name).missing"
                  :class="DOC_BADGE_BASE"
                  class="bg-rose-500 text-white border-rose-600"
                >
                  0
                </span>
                <span
                  v-else
                  :class="DOC_BADGE_BASE"
                  :style="getDocCell(s, d.name).count > 0
                    ? { backgroundColor: '#007aff', color: '#fff', borderColor: '#007aff' }
                    : {}"
                  class="bg-zinc-100 dark:bg-zinc-800 text-zinc-400 dark:text-zinc-500 border-zinc-200 dark:border-zinc-700"
                >
                  {{ getDocCell(s, d.name).count }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-1.5">
      <button
        :disabled="safePage <= 1"
        @click="currentPage = safePage - 1"
        title="Previous page"
        class="h-8 w-8 rounded-full border border-[var(--border)] bg-[var(--surface-elevated)] flex items-center justify-center text-[var(--foreground-muted)] hover:bg-[var(--border-subtle)] disabled:opacity-40 disabled:pointer-events-none cursor-pointer transition-all"
      >
        <ChevronLeft class="h-4 w-4" />
      </button>

      <button
        v-for="p in pageNumbers"
        :key="p"
        @click="currentPage = p"
        class="h-8 min-w-8 px-2.5 rounded-full text-xs font-bold border transition-all cursor-pointer"
        :class="p === safePage
          ? 'bg-[#007aff] text-white border-[#007aff]'
          : 'bg-[var(--surface-elevated)] text-[var(--foreground)] border-[var(--border)] hover:bg-[var(--border-subtle)]'"
      >
        {{ p }}
      </button>

      <button
        :disabled="safePage >= totalPages"
        @click="currentPage = safePage + 1"
        title="Next page"
        class="h-8 w-8 rounded-full border border-[var(--border)] bg-[var(--surface-elevated)] flex items-center justify-center text-[var(--foreground-muted)] hover:bg-[var(--border-subtle)] disabled:opacity-40 disabled:pointer-events-none cursor-pointer transition-all"
      >
        <ChevronRight class="h-4 w-4" />
      </button>
    </div>

    <!-- Modal -->
    <DocumentsModal
      :is-open="isModalOpen"
      :student="selectedStudent"
      :updating="modalUpdating"
      :payments-done="studentPaymentsDone"
      :payments-done-loading="studentPaymentsDoneLoading"
      @close="isModalOpen = false"
      @toggle-pick="handleTogglePickNeeded"
      @toggle-mc="handleToggleMcEnabled"
      @update-count="handleUpdateCopyCount"
    />
  </div>
</template>
