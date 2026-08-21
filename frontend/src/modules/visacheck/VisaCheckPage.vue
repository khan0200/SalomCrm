<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import {
  ArrowUpDown, Search, Check, RefreshCw, Pin, Trash2, Eye, Download,
  ArchiveRestore, ChevronDown, FileDown, AlertTriangle, X
} from 'lucide-vue-next'
import { visaApi, type VisaType, type VisaStudent, type VisaCheckResult } from '@/api/visa'
import { useUiStore } from '@/stores/ui'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import StudentFormModal from './components/StudentFormModal.vue'
import StudentDetailsModal from './components/StudentDetailsModal.vue'
import StudentUniversityGroup from './components/StudentUniversityGroup.vue'
import StudentContextMenu from './components/StudentContextMenu.vue'
import ChangeReportModal, { type SessionChange, type SessionNoAnswer, type SessionSummary } from './components/ChangeReportModal.vue'
import IosBatchProgressBar from './components/IosBatchProgressBar.vue'
import VisaTypeFilterTabs, { type VisaTypeFilter } from './components/VisaTypeFilterTabs.vue'
import StatusBadge from './components/StatusBadge.vue'
import VisaTypeBadge from './components/VisaTypeBadge.vue'
import CopyField from './components/CopyField.vue'

const uiStore = useUiStore()
const dashboardStore = useStudentDashboardStore()

// ─── State ────────────────────────────────────────────────────────────────────
type StatusFilter = 'pending' | 'application' | 'cancelled' | 'approved'
const currentFilter = ref<StatusFilter>('pending')

const visaTypeFilter = computed({
  get: () => dashboardStore.visaTypeFilter as VisaTypeFilter,
  set: (v) => { dashboardStore.visaTypeFilter = v }
})

const searchQuery = computed({
  get: () => dashboardStore.searchQuery,
  set: (v) => { dashboardStore.searchQuery = v }
})

const isAddModalOpen = computed({
  get: () => dashboardStore.isAddStudentModalOpen,
  set: (v) => { dashboardStore.isAddStudentModalOpen = v }
})

type SortOption = 'university' | 'tariff' | 'date' | 'statusDate' | 'underReview' | 'selected'
const sortBy = ref<SortOption>('university')
const isSortMenuOpen = ref(false)

const students = ref<VisaStudent[]>([])
const isLoading = ref(true)

const checkingPassports = ref<Map<string, 'queued' | 'processing'>>(new Map())
const selectedPassports = ref<Set<string>>(new Set())
const downloadingPassports = ref<Set<string>>(new Set())

// Modal state
const detailsModalOpen = ref(false)
const detailsStudent = ref<VisaStudent | null>(null)
const editingStudent = ref<VisaStudent | null>(null)

// Report & Batch Progress state
const showReportModal = ref(false)
const isRetryingReport = ref(false)
const sessionChanges = ref<SessionChange[]>([])
const sessionNoAnswers = ref<SessionNoAnswer[]>([])
const sessionSummary = ref<SessionSummary>({ total: 0, changed: 0, unchanged: 0, noAnswer: 0 })

const batchProgress = ref<{
  active: boolean
  total: number
  completed: number
  failed: number
  currentName: string
}>({
  active: false,
  total: 0,
  completed: 0,
  failed: 0,
  currentName: ''
})

// Context Menu state
const contextMenuOpen = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuStudent = ref<VisaStudent | null>(null)

function onContextMenu(student: VisaStudent, event: MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  contextMenuStudent.value = student
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  contextMenuOpen.value = true
}

async function handleFlagToggle(student: VisaStudent) {
  student.flag = !student.flag
  try {
    await visaApi.updateVisaStudent(student.passport, { flag: student.flag })
  } catch { /* ignore */ }
}

// Delete confirm
const showDeleteConfirm = ref(false)
const studentToDelete = ref<VisaStudent | null>(null)

// ─── Load from Visa database table (crm_visa_students) ────────────────────────
async function loadStudents() {
  isLoading.value = true
  try {
    const res = await visaApi.getVisaStudents()
    students.value = res.results || []

    // Restore selection state from database
    selectedPassports.value.clear()
    for (const s of students.value) {
      if (s.batch_selected) {
        selectedPassports.value.add(s.passport)
      }
    }
  } catch (err: any) {
    uiStore.addToast({ type: 'error', message: err.message || 'Viza ma\'lumotlarini yuklashda xatolik' })
  } finally {
    isLoading.value = false
  }
}

onMounted(loadStudents)

// ─── Visa Status Helpers (Matching univisacheck /cabinet logic) ───────────────
function bucketForStatus(statusValue: string | undefined | null): StatusFilter {
  const status = (statusValue || '').toLowerCase().replace(/_/g, ' ').replace(/\s+/g, ' ').trim()
  const isApproved = status.includes('approved') || status.includes('visa used') || status.includes('issued') || status.includes('허가') || status.includes('tasdiqlangan')
  const isCancelled = status.includes('cancel') || status.includes('reject') || status.includes('return') || status.includes('expired') || status.includes('불허') || status.includes('rad etil') || status.includes('bekor')
  const isPending = status === 'pending' || status === 'unknown' || status === '' || status.includes('error') || status.includes('not found') || status.includes('no application') || status.includes('topilmadi') || status.includes('mavjud emas')

  if (isApproved) return 'approved'
  if (isCancelled) return 'cancelled'
  if (isPending) return 'pending'
  return 'application'
}

function getStudentVisaStatus(student: VisaStudent): string {
  const raw = (student.status || '').toUpperCase()
  if (raw.includes('APPROV') || raw.includes('PASSED') || raw.includes('ISSUED') || raw.includes('허가')) return 'APPROVED'
  if (raw.includes('REJECT') || raw.includes('CANCEL') || raw.includes('RETURN') || raw.includes('EXPIRED') || raw.includes('불허')) return 'CANCELLED'
  if (raw.includes('REVIEW') || raw.includes('PROCESSING') || raw.includes('SIMSA') || raw.includes('심사중')) return 'UNDER REVIEW'
  if (raw.includes('RECEIV') || raw.includes('SUBMIT') || raw.includes('JEOMSU') || raw.includes('접수') || raw.includes('APP/')) return 'RECEIVED'
  if (raw.includes('SUPPLEM') || raw.includes('보완')) return 'SUPPLEMENT NEEDED'
  return raw || 'PENDING'
}

function isPdfEligible(student: VisaStudent): boolean {
  const s = getStudentVisaStatus(student)
  return s.includes('APPROV') || s.includes('VISA USED')
}

// ─── Filtered by Search & Visa Type ───────────────────────────────────────────
const matchingSearchAndType = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  const vType = visaTypeFilter.value
  return students.value.filter(s => {
    const sType = s.visa_type || 'Embassy'
    if (vType !== 'all' && sType !== vType) return false
    if (!q) return true
    const name = (s.full_name || '').toLowerCase()
    const pass = (s.passport || '').toLowerCase()
    const id   = (s.student_id || s.id || '').toLowerCase()
    const univ = (s.university || '').toLowerCase()
    const tariff = (s.tariff || '').toLowerCase()
    return name.includes(q) || pass.includes(q) || id.includes(q) || univ.includes(q) || tariff.includes(q)
  })
})

// ─── Sync visaTypeCounts to dashboardStore for Top Navbar ─────────────────────
watch([students, searchQuery], () => {
  const q = searchQuery.value.toLowerCase().trim()
  const res: Record<string, number> = { all: 0, Embassy: 0, 'E-Visa': 0, Regional: 0 }
  for (const s of students.value) {
    if (q) {
      const name = (s.full_name || '').toLowerCase()
      const pass = (s.passport || '').toLowerCase()
      const id   = (s.student_id || s.id || '').toLowerCase()
      const univ = (s.university || '').toLowerCase()
      const tariff = (s.tariff || '').toLowerCase()
      if (!name.includes(q) && !pass.includes(q) && !id.includes(q) && !univ.includes(q) && !tariff.includes(q)) continue
    }
    res.all++
    const type = s.visa_type || 'Embassy'
    if (type === 'E-Visa') res['E-Visa']++
    else if (type === 'Regional') res.Regional++
    else res.Embassy++
  }
  dashboardStore.visaTypeCounts = res
}, { immediate: true, deep: true })

// ─── Counts (Tabs matching univisacheck /cabinet) ─────────────────────────────
const counts = computed(() => {
  const result: Record<StatusFilter, number> = { pending: 0, application: 0, cancelled: 0, approved: 0 }
  for (const s of matchingSearchAndType.value) {
    const bucket = bucketForStatus(s.status)
    result[bucket]++
  }
  return result
})

// ─── Filtered Students for Current Status Tab ─────────────────────────────────
const filteredStudents = computed(() => {
  const list = matchingSearchAndType.value.filter(s => bucketForStatus(s.status) === currentFilter.value)

  return [...list].sort((a, b) => {
    if (sortBy.value === 'selected') {
      const aS = selectedPassports.value.has(a.passport) ? 1 : 0
      const bS = selectedPassports.value.has(b.passport) ? 1 : 0
      if (aS !== bS) return bS - aS
    }

    if (currentFilter.value === 'application') {
      const isUnderReviewA = (a.status || '').toUpperCase().includes('REVIEW') || (a.status || '').toUpperCase().includes('SUPPLEM') ? 1 : 0
      const isUnderReviewB = (b.status || '').toUpperCase().includes('REVIEW') || (b.status || '').toUpperCase().includes('SUPPLEM') ? 1 : 0
      if (isUnderReviewA !== isUnderReviewB) return isUnderReviewB - isUnderReviewA
    }

    if (a.pinned && !b.pinned) return -1
    if (!a.pinned && b.pinned) return 1

    if (sortBy.value === 'statusDate') {
      const dateA = a.status_date || '9999-99-99'
      const dateB = b.status_date || '9999-99-99'
      if (dateA !== dateB) return dateB.localeCompare(dateA)
    }

    if (sortBy.value === 'university') return (a.university || '').localeCompare(b.university || '')
    if (sortBy.value === 'tariff') return (a.tariff || '').localeCompare(b.tariff || '')

    const dateA = a.application_date || a.created_at || '9999-99-99'
    const dateB = b.application_date || b.created_at || '9999-99-99'
    return dateB.localeCompare(dateA)
  })
})

// ─── Grouping Logic (Accordion matching /cabinet) ─────────────────────────────
const hasAnyGroup = computed(() => {
  const sort = sortBy.value
  if (sort === 'university') return filteredStudents.value.some(s => !!s.university)
  if (sort === 'tariff') return filteredStudents.value.some(s => !!s.tariff)
  if (sort === 'date') return filteredStudents.value.some(s => !!s.application_date)
  if (sort === 'statusDate') return filteredStudents.value.some(s => !!s.status_date)
  if (sort === 'underReview') return filteredStudents.value.some(s => (s.status || '').toUpperCase().includes('REVIEW') || (s.status || '').toUpperCase().includes('SUPPLEM'))
  return false
})

const groupedStudents = computed((): { groupName: string; students: VisaStudent[] }[] => {
  const map = new Map<string, VisaStudent[]>()
  const sort = sortBy.value

  for (const s of filteredStudents.value) {
    let key = ''
    if (sort === 'university') key = s.university?.trim() || ''
    else if (sort === 'tariff') key = s.tariff?.trim() || ''
    else if (sort === 'date') key = s.application_date?.trim() || ''
    else if (sort === 'statusDate') key = s.status_date?.trim() || ''
    else if (sort === 'underReview') {
      const st = (s.status || '').toUpperCase()
      if (st.includes('SUPPLEM') && st.includes('SUBMIT')) key = 'Supplement Submitted'
      else if (st.includes('SUPPLEM')) key = 'Supplement Needed'
      else if (st.includes('REVIEW')) key = 'Under Review'
    }

    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(s)
  }

  return [...map.entries()]
    .sort(([a], [b]) => {
      if (sort === 'underReview') {
        if (a === 'Supplement Needed') return -1
        if (b === 'Supplement Needed') return 1
        if (a === 'Supplement Submitted') return -1
        if (b === 'Supplement Submitted') return 1
        if (a === 'Under Review') return -1
        if (b === 'Under Review') return 1
      }
      if (a === '') return 1
      if (b === '') return -1
      return a.localeCompare(b)
    })
    .map(([groupName, groupStudents]) => ({ groupName, students: groupStudents }))
})

// ─── Show/Hide Columns ────────────────────────────────────────────────────────
const showSelectColumn = computed(() => currentFilter.value === 'application' || currentFilter.value === 'pending')
const showAppliedColumn = computed(() => currentFilter.value !== 'pending')
const showPdfColumn = computed(() =>
  currentFilter.value === 'approved' || filteredStudents.value.some(s => isPdfEligible(s))
)
const showStatusDateColumn = computed(() => currentFilter.value === 'approved')

// ─── Selection ────────────────────────────────────────────────────────────────
const hasAnySelected = computed(() => filteredStudents.value.some(s => selectedPassports.value.has(s.passport)))
const selectedInCurrentTab = computed(() => filteredStudents.value.filter(s => selectedPassports.value.has(s.passport)))

async function toggleSelect(student: VisaStudent, checked: boolean) {
  student.batch_selected = checked
  if (checked) selectedPassports.value.add(student.passport)
  else selectedPassports.value.delete(student.passport)

  try {
    await visaApi.updateVisaStudent(student.passport, { batch_selected: checked })
  } catch (err) {
    console.error('Failed to persist selection:', err)
  }
}

async function handleDeselectAll() {
  const toDeselect = filteredStudents.value.filter(s => selectedPassports.value.has(s.passport))
  for (const s of toDeselect) {
    s.batch_selected = false
    selectedPassports.value.delete(s.passport)
    visaApi.updateVisaStudent(s.passport, { batch_selected: false }).catch(() => {})
  }
}

async function handleDeselectGroup(groupStudents: VisaStudent[]) {
  const toDeselect = groupStudents.filter(s => selectedPassports.value.has(s.passport))
  for (const s of toDeselect) {
    s.batch_selected = false
    selectedPassports.value.delete(s.passport)
    visaApi.updateVisaStudent(s.passport, { batch_selected: false }).catch(() => {})
  }
}

// ─── Pin ─────────────────────────────────────────────────────────────────────
async function handlePinToggle(student: VisaStudent) {
  student.pinned = !student.pinned
  try {
    await visaApi.updateVisaStudent(student.passport, { pinned: student.pinned })
  } catch { /* ignore */ }
}

// ─── Row click → Details ──────────────────────────────────────────────────────
function onRowClick(student: VisaStudent, event: MouseEvent) {
  const target = event.target as HTMLElement
  if (target.closest('button, input, a, select')) return
  openDetails(student)
}

function openDetails(student: VisaStudent) {
  detailsStudent.value = student
  detailsModalOpen.value = true
}

function openEditModal(student: VisaStudent) {
  editingStudent.value = student
  isAddModalOpen.value = true
}

function handleModalClose() {
  isAddModalOpen.value = false
  editingStudent.value = null
}

function handleStudentUpdated(updated: VisaStudent) {
  const idx = students.value.findIndex(s => s.passport === updated.passport)
  if (idx !== -1) {
    students.value[idx] = updated
  }
  if (detailsStudent.value?.passport === updated.passport) {
    detailsStudent.value = updated
  }
}

// ─── Single Visa Check ────────────────────────────────────────────────────────
async function checkStudentVisa(
  student: VisaStudent,
  silent: boolean = false
): Promise<{ success: boolean; error?: string; changed: boolean }> {
  const pass = (student.passport || '').trim().toUpperCase()
  const name = (student.full_name || '').trim().toUpperCase()
  const dob  = (student.birthday || '').trim()
  if (!pass || !name || !dob) {
    if (!silent) {
      uiStore.addToast({ type: 'warning', message: `${student.full_name}: Pasport, ism yoki tug'ilgan sana to'liq emas` })
    }
    return { success: false, error: "Pasport yoki tug'ilgan sana to'liq emas", changed: false }
  }

  checkingPassports.value.set(pass, 'processing')
  const oldStatus = student.status || 'PENDING'

  try {
    const res = await visaApi.checkVisa({
      passport: pass,
      full_name: name,
      birth_date: dob,
      visa_type: student.visa_type || 'Embassy',
      application_no: student.application_no
    })

    const newStatus = (res.latest_status || (res.found ? 'APP/RECEIVED' : 'PENDING')).toUpperCase()
    const changed = res.found && oldStatus.toUpperCase() !== newStatus.toUpperCase()

    if (res.found && res.latest_status) {
      student.status = res.latest_status.toUpperCase()
    }
    if (res.latest_date) student.application_date = res.latest_date
    if (res.entry_date) student.status_date = res.entry_date
    if (res.rejection_reason) student.rejection_reason = res.rejection_reason
    if (res.pdf_url) student.pdf_url = res.pdf_url
    student.last_checked = new Date().toISOString()

    if (changed) {
      const exists = sessionChanges.value.some(c => c.passport === student.passport)
      if (!exists) {
        sessionChanges.value.push({
          fullName: student.full_name,
          passport: student.passport,
          oldStatus: oldStatus,
          newStatus: newStatus
        })
      }
      if (!silent) {
        uiStore.addToast({
          type: 'success',
          message: `🎉 ${student.full_name}: Viza statusi o'zgardi! (${oldStatus} ➔ ${newStatus})`
        })
      }
    } else if (!silent) {
      uiStore.addToast({
        type: res.found ? 'info' : 'warning',
        message: res.found ? `${student.full_name}: ${student.status}` : `${student.full_name}: Ariza topilmadi`
      })
    }

    return { success: true, changed }
  } catch (err: any) {
    const msg = err.message || 'Serverdan javob olinmadi'
    if (!silent) {
      uiStore.addToast({ type: 'error', message: `${student.full_name}: Tekshirishda xatolik (${msg})` })
    }
    return { success: false, error: msg, changed: false }
  } finally {
    checkingPassports.value.delete(pass)
  }
}

// ─── High-Performance Concurrent Batch Check with 1x Auto-Retry ──────────────
async function runBatchCheck(list: VisaStudent[]) {
  const toCheck = list.filter(s => s.passport && !checkingPassports.value.has(s.passport))
  if (toCheck.length === 0) return

  sessionChanges.value = []
  sessionNoAnswers.value = []
  batchProgress.value = {
    active: true,
    total: toCheck.length,
    completed: 0,
    failed: 0,
    currentName: toCheck[0]?.full_name || ''
  }

  // Mark all as processing
  for (const s of toCheck) {
    checkingPassports.value.set(s.passport, 'processing')
  }

  const CHUNK_SIZE = 5
  const STAGGER_DELAY = 150
  const firstPassFailed: { student: VisaStudent; reason?: string }[] = []
  let completedCount = 0

  // Pass 1: Chunked batches
  for (let i = 0; i < toCheck.length; i += CHUNK_SIZE) {
    const chunk = toCheck.slice(i, i + CHUNK_SIZE)
    const inFlightPromises: Promise<void>[] = []

    for (let j = 0; j < chunk.length; j++) {
      const student = chunk[j]!
      inFlightPromises.push(
        (async () => {
          batchProgress.value.currentName = student.full_name
          const res = await checkStudentVisa(student, true)
          if (res.success) {
            completedCount++
          } else {
            firstPassFailed.push({ student, reason: res.error })
          }
          batchProgress.value.completed = completedCount
          batchProgress.value.failed = firstPassFailed.length
        })()
      )
      if (j < chunk.length - 1) {
        await new Promise(r => setTimeout(r, STAGGER_DELAY))
      }
    }
    await Promise.allSettled(inFlightPromises)
  }

  // Pass 2: 1x Automatic Retry for Failed ones
  const stillFailed: { student: VisaStudent; reason?: string }[] = []
  if (firstPassFailed.length > 0) {
    await new Promise(r => setTimeout(r, 400))
    for (let i = 0; i < firstPassFailed.length; i += CHUNK_SIZE) {
      const retryChunk = firstPassFailed.slice(i, i + CHUNK_SIZE)
      const retryPromises: Promise<void>[] = []
      for (let j = 0; j < retryChunk.length; j++) {
        const { student } = retryChunk[j]!
        retryPromises.push(
          (async () => {
            batchProgress.value.currentName = student.full_name
            const res = await checkStudentVisa(student, true)
            if (res.success) {
              completedCount++
              batchProgress.value.completed = completedCount
              batchProgress.value.failed = Math.max(0, batchProgress.value.failed - 1)
            } else {
              stillFailed.push({ student, reason: res.error })
            }
          })()
        )
        if (j < retryChunk.length - 1) {
          await new Promise(r => setTimeout(r, STAGGER_DELAY))
        }
      }
      await Promise.allSettled(retryPromises)
    }
  }

  // Clear checking status
  for (const s of toCheck) {
    checkingPassports.value.delete(s.passport)
  }

  // Compile Session Report
  sessionNoAnswers.value = stillFailed.map(f => ({
    fullName: f.student.full_name || f.student.passport,
    passport: f.student.passport,
    reason: f.reason || 'Serverdan javob olinmadi (Timeout)'
  }))

  const changedCount = sessionChanges.value.length
  const noAnswerCount = stillFailed.length
  const unchangedCount = Math.max(0, completedCount - changedCount)

  sessionSummary.value = {
    total: toCheck.length,
    changed: changedCount,
    unchanged: unchangedCount,
    noAnswer: noAnswerCount
  }

  // Finish batch & open report modal
  setTimeout(() => {
    batchProgress.value.active = false
    showReportModal.value = true
    uiStore.addToast({
      type: changedCount > 0 ? 'success' : 'info',
      message: `Viza tekshiruvi yakunlandi: ${completedCount}/${toCheck.length} ta tekshirildi (${changedCount} ta o'zgarish).`
    })
  }, 600)
}

// Batch check selected in table
async function handleBatchCheck() {
  if (!selectedInCurrentTab.value.length) return
  await runBatchCheck(selectedInCurrentTab.value)
}

// Group check
async function handleGroupRefresh(groupList: VisaStudent[]) {
  if (!groupList.length) return
  await runBatchCheck(groupList)
}

// Retry failed from summary modal
async function handleRetryNoAnswers() {
  if (sessionNoAnswers.value.length === 0) return
  const failedPassports = new Set(sessionNoAnswers.value.map(s => s.passport.toUpperCase().trim()))
  const retryList = students.value.filter(s => failedPassports.has(s.passport.toUpperCase().trim()))
  if (retryList.length === 0) return
  isRetryingReport.value = true
  showReportModal.value = false
  try {
    await runBatchCheck(retryList)
  } finally {
    isRetryingReport.value = false
  }
}

// ─── PDF Download ─────────────────────────────────────────────────────────────
async function handleDownloadPdf(student: VisaStudent) {
  const pass = (student.passport || '').trim().toUpperCase()
  const name = (student.full_name || '').trim().toUpperCase()
  const dob  = (student.birthday || '').trim()
  downloadingPassports.value.add(pass)
  try {
    const blob = await visaApi.downloadPdf({
      passport: pass,
      full_name: name,
      birth_date: dob,
      visa_type: student.visa_type || 'Embassy',
      pdf_url: student.pdf_url
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `visa_${pass}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    uiStore.addToast({ type: 'success', message: 'Viza sertifikati yuklab olindi!' })
  } catch {
    uiStore.addToast({ type: 'error', message: 'PDF yuklab olishda xatolik yuz berdi' })
  } finally {
    downloadingPassports.value.delete(pass)
  }
}

// ─── Delete ───────────────────────────────────────────────────────────────────
function promptDelete(student: VisaStudent) {
  studentToDelete.value = student
  showDeleteConfirm.value = true
  if (detailsModalOpen.value) detailsModalOpen.value = false
}

async function confirmDelete() {
  if (!studentToDelete.value) return
  try {
    await visaApi.deleteVisaStudent(studentToDelete.value.passport)
    students.value = students.value.filter(s => s.passport !== studentToDelete.value!.passport)
    uiStore.addToast({ type: 'success', message: 'Talaba viza bazasidan o\'chirildi ✓' })
    showDeleteConfirm.value = false
    studentToDelete.value = null
  } catch (err: any) {
    uiStore.addToast({ type: 'error', message: err.message || 'O\'chirishda xatolik' })
  }
}

// ─── formatTimestampCompact ────────────────────────────────────────────────────
function formatTimestampCompact(ts: string | undefined | null): string {
  if (!ts) return '—'
  try {
    const d = new Date(ts)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Hozirgina'
    if (mins < 60) return `${mins} daqiqa oldin`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours} soat oldin`
    const days = Math.floor(hours / 24)
    if (days < 7) return `${days} kun oldin`
    return d.toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit', year: '2-digit' })
  } catch { return ts }
}

// ─── Virtual Scroll ───────────────────────────────────────────────────────────
const containerRef = ref<HTMLElement | null>(null)
const containerTop = ref(300)
const scrollY = ref(0)
const windowHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 800)

function updateContainerTop() {
  if (containerRef.value) {
    containerTop.value = containerRef.value.getBoundingClientRect().top + window.scrollY
  }
}

function onScroll() { scrollY.value = window.scrollY }
function onResize() { windowHeight.value = window.innerHeight; updateContainerTop() }

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onResize)
  updateContainerTop()
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onResize)
})

watch(filteredStudents, () => nextTick(updateContainerTop))

const DESKTOP_ROW_H = 73
const MOBILE_ROW_H = 175
const BUFFER = 15

const startIndex = computed(() => {
  const rel = Math.max(0, scrollY.value - containerTop.value)
  return Math.max(0, Math.floor(rel / DESKTOP_ROW_H) - BUFFER)
})
const endIndex = computed(() => {
  const rel = Math.max(0, scrollY.value - containerTop.value)
  const vis = Math.ceil(windowHeight.value / DESKTOP_ROW_H)
  return Math.min(filteredStudents.value.length, Math.floor(rel / DESKTOP_ROW_H) + vis + BUFFER)
})
const visibleStudents = computed(() => filteredStudents.value.slice(startIndex.value, endIndex.value))
const topSpacerH = computed(() => startIndex.value * DESKTOP_ROW_H)
const bottomSpacerH = computed(() => Math.max(0, (filteredStudents.value.length - endIndex.value) * DESKTOP_ROW_H))

const mStartIndex = computed(() => Math.max(0, Math.floor(Math.max(0, scrollY.value - containerTop.value) / MOBILE_ROW_H) - BUFFER))
const mEndIndex = computed(() => Math.min(filteredStudents.value.length, mStartIndex.value + Math.ceil(windowHeight.value / MOBILE_ROW_H) + BUFFER * 2))
const visibleMobileStudents = computed(() => filteredStudents.value.slice(mStartIndex.value, mEndIndex.value))
const mTopSpacerH = computed(() => mStartIndex.value * MOBILE_ROW_H)
const mBottomSpacerH = computed(() => Math.max(0, (filteredStudents.value.length - mEndIndex.value) * MOBILE_ROW_H))

const columnCount = computed(() => {
  let c = 5
  if (showSelectColumn.value) c++
  if (showPdfColumn.value) c++
  if (showAppliedColumn.value) c++
  return c
})

function onDocClick(e: MouseEvent) {
  if (isSortMenuOpen.value) {
    const t = e.target as HTMLElement
    if (!t.closest('[data-sort-menu]')) isSortMenuOpen.value = false
  }
}
onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div class="space-y-4 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto min-w-0">

    <!-- ── Top Filter & Action Bar (Matching /cabinet layout) ── -->
    <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 min-w-0">

      <!-- Left Action Buttons + Visa Type Tabs -->
      <div class="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">

        <!-- Sort Dropdown -->
        <div class="relative" data-sort-menu>
          <button
            type="button"
            @click.stop="isSortMenuOpen = !isSortMenuOpen"
            class="h-11 px-4 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 font-bold text-sm flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors shadow-xs cursor-pointer"
          >
            <ArrowUpDown class="size-4 text-zinc-400" />
            <span>Sort: <span class="text-blue-600 dark:text-blue-400 capitalize">{{ sortBy }}</span></span>
            <ChevronDown class="size-3.5 text-zinc-400" />
          </button>
          <Transition
            enter-active-class="transition duration-100 ease-out"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
            leave-active-class="transition duration-75 ease-in"
            leave-from-class="opacity-100 scale-100"
            leave-to-class="opacity-0 scale-95"
          >
            <div
              v-if="isSortMenuOpen"
              class="absolute left-0 mt-1 w-52 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xl py-2 z-40 text-xs"
            >
              <button
                v-for="opt in [
                  { id: 'university',  label: 'University (Guruhlash)' },
                  { id: 'tariff',      label: 'Tariff (Guruhlash)' },
                  { id: 'date',        label: 'Date (Guruhlash)' },
                  { id: 'statusDate',  label: 'Status Date (Guruhlash)' },
                  { id: 'underReview', label: 'Under Review (Guruhlash)' },
                  { id: 'selected',    label: 'Selected (Tanlanganlar)' }
                ]"
                :key="opt.id"
                type="button"
                @click="sortBy = opt.id as any; isSortMenuOpen = false"
                class="w-full text-left px-4 py-2.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 flex items-center justify-between text-zinc-700 dark:text-zinc-200 font-semibold cursor-pointer transition-colors"
              >
                <span>{{ opt.label }}</span>
                <Check v-if="sortBy === opt.id" class="size-4 text-emerald-500" />
              </button>
            </div>
          </Transition>
        </div>

        <!-- Undo (deselect) -->
        <button
          v-if="selectedInCurrentTab.length > 0"
          type="button"
          @click="handleDeselectAll"
          class="h-11 px-4 rounded-xl bg-[#FBBF24] hover:bg-[#F59E0B] text-[#0B4133] font-bold text-sm shadow-xs transition-all flex items-center gap-1.5 cursor-pointer"
        >
          Undo ({{ selectedInCurrentTab.length }})
        </button>

        <!-- Batch Check -->
        <button
          v-if="selectedInCurrentTab.length > 0"
          type="button"
          :disabled="batchProgress.active"
          @click="handleBatchCheck"
          class="h-11 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-xs transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw v-if="batchProgress.active" class="size-4 animate-spin" />
          Check ({{ selectedInCurrentTab.length }})
        </button>
      </div>

      <!-- Status Tabs (4 mutually exclusive tabs in dark green pill) -->
      <div class="w-full lg:w-auto shrink-0">
        <div class="grid grid-cols-4 sm:inline-flex sm:items-center gap-1 p-1 rounded-xl bg-[#0B4133] w-full sm:w-auto shadow-sm">
          <button
            v-for="tab in [
              { value: 'pending',     label: 'Pending',     count: counts.pending },
              { value: 'application', label: 'Application', count: counts.application },
              { value: 'cancelled',   label: 'Cancelled',   count: counts.cancelled },
              { value: 'approved',    label: 'Approved',    count: counts.approved }
            ]"
            :key="tab.value"
            type="button"
            @click="currentFilter = tab.value as StatusFilter"
            class="relative flex flex-col sm:flex-row items-center justify-center gap-1 rounded-lg px-2.5 sm:px-3.5 py-1.5 text-xs sm:text-sm font-semibold transition-all cursor-pointer"
            :class="currentFilter === tab.value ? 'bg-white text-[#0B4133] shadow-sm font-bold' : 'text-white/85 hover:text-white hover:bg-white/10'"
          >
            <span>{{ tab.label }}</span>
            <span
              class="text-[10px] sm:text-[11px] font-bold rounded-md px-1.5 py-0.5 min-w-[1.25rem] text-center"
              :class="currentFilter === tab.value ? 'bg-[#FBBF24] text-[#0B4133]' : 'bg-white/15 text-white'"
            >
              {{ tab.count }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Search Alert Bar -->
    <div
      v-if="searchQuery"
      class="flex items-center justify-between px-4 py-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 text-xs text-blue-700 dark:text-blue-300"
    >
      <div class="flex items-center gap-2">
        <Search class="size-4 text-blue-500" />
        <span>Qidiruv: "<strong>{{ searchQuery }}</strong>" — {{ filteredStudents.length }} ta talaba</span>
      </div>
      <button type="button" @click="searchQuery = ''" class="text-blue-500 hover:text-blue-700 font-bold underline cursor-pointer">Tozalash</button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="p-8 space-y-4 animate-pulse">
      <div v-for="i in 6" :key="i" class="h-16 bg-zinc-100 dark:bg-zinc-800/60 rounded-2xl" />
    </div>

    <!-- Empty State -->
    <div
      v-else-if="filteredStudents.length === 0"
      class="rounded-2xl border border-neutral-300 dark:border-white/20 bg-white dark:bg-zinc-900 py-16 px-6 text-center space-y-3 shadow-sm"
    >
      <div class="w-14 h-14 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center mx-auto text-zinc-400">
        <ArchiveRestore class="size-7" />
      </div>
      <p class="font-bold text-zinc-800 dark:text-zinc-200">Talabalar topilmadi</p>
      <p class="text-xs text-zinc-500 dark:text-zinc-400 max-w-sm mx-auto">
        Ushbu statusda talabalar mavjud emas yoki tanlangan filtrlar bo'yicha natija chiqmadi.
      </p>
    </div>

    <!-- ── Grouped Accordion List (when hasAnyGroup is true) ── -->
    <div
      v-else-if="hasAnyGroup"
      class="space-y-3.5"
    >
      <StudentUniversityGroup
        v-for="group in groupedStudents"
        :key="`${currentFilter}-${sortBy}-${group.groupName}`"
        :group-name="group.groupName"
        :students="group.students"
        :current-filter="currentFilter"
        :checking-passports="checkingPassports"
        :selected-passports="selectedPassports"
        :downloading-passports="downloadingPassports"
        @edit="openEditModal"
        @details="openDetails"
        @delete="promptDelete"
        @refresh="checkStudentVisa"
        @refresh-group="handleGroupRefresh"
        @download-pdf="handleDownloadPdf"
        @toggle-select="toggleSelect"
        @toggle-pin="handlePinToggle"
        @toggle-flag="handleFlagToggle"
        @deselect-group="handleDeselectGroup"
        @contextmenu="onContextMenu"
      />
    </div>

    <!-- ── Flat Table Card (when hasAnyGroup is false / selected mode) ── -->
    <div
      v-else
      class="rounded-2xl border border-neutral-300 dark:border-white/20 bg-white dark:bg-zinc-900 shadow-[0_8px_30px_rgba(15,23,42,0.1),0_2px_8px_rgba(15,23,42,0.06)] dark:shadow-[0_12px_40px_rgba(0,0,0,0.7)] overflow-hidden"
    >
      <!-- Mobile Cards -->
      <div
        ref="containerRef"
        :key="`m-${currentFilter}`"
        class="md:hidden space-y-3 p-3"
      >
        <div v-if="mTopSpacerH > 0" :style="{ height: `${mTopSpacerH}px` }" />
        <div
          v-for="st in visibleMobileStudents"
          :key="st.passport"
          class="p-4 space-y-2.5 rounded-xl border border-neutral-300/90 dark:border-white/20 bg-white dark:bg-zinc-900 shadow-sm cursor-pointer active:bg-blue-50/60 dark:active:bg-white/[0.03]"
          @click="onRowClick(st, $event)"
          @contextmenu.prevent="onContextMenu(st, $event)"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="font-bold text-zinc-900 dark:text-white flex items-center gap-1.5 flex-wrap">
                <CopyField :value="st.full_name" label="Copy name" class="text-sm">{{ st.full_name }}</CopyField>
                <Pin v-if="st.pinned" class="size-3.5 text-amber-500 fill-amber-500 shrink-0" />
              </div>
              <div class="flex flex-wrap items-center gap-1.5 mt-1">
                <VisaTypeBadge :visa-type="st.visa_type" />
                <span v-if="st.student_id || st.id" class="text-xs text-zinc-400 font-mono">#{{ st.student_id || st.id }}</span>
              </div>
            </div>
            <div v-if="showSelectColumn" class="flex items-center justify-center shrink-0 pt-0.5">
              <input
                type="checkbox"
                class="size-6 rounded-md border-2 border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-2 focus:ring-blue-500 cursor-pointer transition-all"
                :checked="selectedPassports.has(st.passport)"
                @click.stop
                @change="toggleSelect(st, ($event.target as HTMLInputElement).checked)"
              />
            </div>
          </div>

          <div class="flex items-center justify-between text-sm">
            <div>
              <CopyField :value="st.passport" label="Copy passport" class="font-bold font-mono text-zinc-700 dark:text-zinc-300">{{ st.passport }}</CopyField>
              <CopyField :value="st.birthday" label="Copy birthday" class="text-xs font-bold font-mono text-zinc-400 mt-0.5">{{ st.birthday }}</CopyField>
            </div>
            <StatusBadge :status="getStudentVisaStatus(st)" />
          </div>

          <div v-if="st.rejection_reason" class="text-[11px] text-rose-500 font-medium truncate">
            Sabab: {{ st.rejection_reason }}
          </div>

          <div class="flex items-center justify-between text-xs text-zinc-400">
            <span v-if="showAppliedColumn">Applied: {{ st.application_date || st.created_at?.slice(0, 10) || '--' }}</span>
            <span v-if="checkingPassports.has(st.passport)" class="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400 font-medium">
              <RefreshCw class="size-3 animate-spin" />Checking...
            </span>
            <span v-else>Checked: {{ formatTimestampCompact(st.last_checked) }}</span>
          </div>

          <div class="grid grid-cols-2 gap-1.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800">
            <button
              type="button"
              :disabled="checkingPassports.has(st.passport)"
              @click.stop="checkStudentVisa(st)"
              class="h-9 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
            >
              <RefreshCw class="size-3.5" :class="{ 'animate-spin': checkingPassports.has(st.passport) }" />
              Check
            </button>
            <button
              type="button"
              @click.stop="openDetails(st)"
              class="h-9 rounded-lg bg-amber-400 hover:bg-amber-500 text-amber-950 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
            >
              <Eye class="size-3.5" />
              View
            </button>
          </div>
        </div>
        <div v-if="mBottomSpacerH > 0" :style="{ height: `${mBottomSpacerH}px` }" />
      </div>

      <!-- Desktop Table -->
      <div
        ref="containerRef"
        class="hidden md:block overflow-x-auto"
      >
        <table
          :key="`t-${currentFilter}`"
          class="w-full min-w-[900px] text-sm border-collapse table-fixed"
        >
          <thead class="sticky top-0 z-10 bg-neutral-100/90 dark:bg-[#111928] backdrop-blur">
            <tr class="border-b border-neutral-300 dark:border-white/20 text-left text-[10px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-300">
              <th class="px-4 py-2 min-w-[220px]">Name</th>
              <th class="px-4 py-2 w-36">Passport</th>
              <th class="px-4 py-2 w-44">Status</th>
              <th v-if="showAppliedColumn" class="px-4 py-2 w-28">Applied</th>
              <th v-if="showStatusDateColumn" class="px-4 py-2 w-32">Status Date</th>
              <th v-else class="px-4 py-2 w-44">Checked</th>
              <th v-if="showSelectColumn" class="px-4 py-2 w-24 text-center align-middle">
                <div class="flex items-center justify-center gap-1.5">
                  <span>Select</span>
                  <button
                    v-if="hasAnySelected"
                    type="button"
                    class="p-0.5 rounded text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-zinc-200 dark:hover:bg-white/10 transition-colors"
                    title="Deselect all"
                    @click.stop="handleDeselectAll"
                  >
                    <X class="size-3.5" />
                  </button>
                </div>
              </th>
              <th v-if="showPdfColumn" class="px-4 py-2 w-14 text-center">PDF</th>
              <th class="px-4 py-2 w-32 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-neutral-200 dark:divide-white/10">
            <tr v-if="topSpacerH > 0" key="__top" :style="{ height: `${topSpacerH}px` }">
              <td :colspan="columnCount" style="padding:0;border:0" />
            </tr>

            <tr
              v-for="st in visibleStudents"
              :key="st.passport"
              class="cursor-pointer transition-colors hover:bg-blue-50/60 dark:hover:bg-white/[0.03]"
              :class="{ 'bg-blue-50/30 dark:bg-white/[0.02]': selectedPassports.has(st.passport) }"
              @click="onRowClick(st, $event)"
              @contextmenu.prevent="onContextMenu(st, $event)"
            >
              <!-- Name Column -->
              <td class="px-4 py-3 align-top">
                <div class="font-bold text-zinc-900 dark:text-white flex items-center gap-1.5 flex-wrap">
                  <CopyField :value="st.full_name" label="Copy name">{{ st.full_name }}</CopyField>
                  <Pin v-if="st.pinned" class="size-3.5 text-amber-500 fill-amber-500 shrink-0" />
                </div>
                <div class="flex flex-wrap items-center gap-1.5 mt-1">
                  <VisaTypeBadge :visa-type="st.visa_type" />
                  <span v-if="st.student_id || st.id" class="text-xs text-zinc-400 font-mono">
                    <CopyField :value="st.student_id || st.id" label="Copy ID">#{{ st.student_id || st.id }}</CopyField>
                  </span>
                  <span v-if="st.application_no" class="text-xs text-zinc-400 font-mono">
                    <CopyField :value="st.application_no" label="Copy app no">{{ st.application_no }}</CopyField>
                  </span>
                </div>
                <p v-if="st.rejection_reason" class="text-[11px] text-rose-500 font-medium mt-0.5 line-clamp-1 max-w-xs">
                  {{ st.rejection_reason }}
                </p>
              </td>

              <!-- Passport Column -->
              <td class="px-4 py-3 align-middle whitespace-nowrap">
                <div class="font-bold text-zinc-900 dark:text-white font-mono text-[13px]">
                  <CopyField :value="st.passport" label="Copy passport">{{ st.passport || '—' }}</CopyField>
                </div>
                <div class="text-xs font-mono text-zinc-400 mt-0.5">
                  <CopyField :value="st.birthday" label="Copy birthday">{{ st.birthday || '—' }}</CopyField>
                </div>
              </td>

              <!-- Status Column -->
              <td class="px-4 py-3 align-middle">
                <StatusBadge :status="getStudentVisaStatus(st)" />
              </td>

              <!-- Applied Column -->
              <td v-if="showAppliedColumn" class="px-4 py-3 align-middle whitespace-nowrap text-zinc-500 dark:text-zinc-400 text-xs">
                {{ st.application_date || st.created_at?.slice(0, 10) || '--' }}
              </td>

              <!-- Status Date / Checked Column -->
              <td v-if="showStatusDateColumn" class="px-4 py-3 align-middle whitespace-nowrap text-zinc-500 dark:text-zinc-400 text-xs">
                {{ st.status_date || '--' }}
              </td>
              <td v-else class="px-4 py-3 align-middle whitespace-nowrap text-xs">
                <span
                  v-if="checkingPassports.has(st.passport)"
                  class="inline-flex items-center gap-1.5"
                >
                  <RefreshCw class="size-3.5 animate-spin text-blue-500" />
                  <span class="text-blue-600 dark:text-blue-400 font-medium">Checking...</span>
                </span>
                <span v-else class="text-zinc-400">
                  {{ formatTimestampCompact(st.last_checked) }}
                </span>
              </td>

              <!-- Select Column -->
              <td v-if="showSelectColumn" class="px-4 py-3 align-middle text-center">
                <div class="flex items-center justify-center h-full">
                  <input
                    type="checkbox"
                    class="size-6 rounded-md border-2 border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer transition-all hover:border-blue-500"
                    :checked="selectedPassports.has(st.passport)"
                    @click.stop
                    @change="toggleSelect(st, ($event.target as HTMLInputElement).checked)"
                  />
                </div>
              </td>

              <!-- PDF Column -->
              <td v-if="showPdfColumn" class="px-4 py-3 align-middle text-center">
                <button
                  v-if="isPdfEligible(st)"
                  type="button"
                  :disabled="downloadingPassports.has(st.passport)"
                  class="text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-200 transition-colors disabled:opacity-40 cursor-pointer"
                  title="Viza PDF yuklab olish"
                  @click.stop="handleDownloadPdf(st)"
                >
                  <FileDown class="size-5" />
                </button>
              </td>

              <!-- Actions Column -->
              <td class="p-0 align-top w-px h-px" style="border-top-width:0">
                <div class="flex items-stretch justify-end h-full">
                  <button
                    type="button"
                    :disabled="checkingPassports.has(st.passport)"
                    class="px-5 py-2 h-full font-bold text-white text-xs bg-blue-600 hover:bg-blue-500 transition-colors rounded-none disabled:opacity-50 flex items-center gap-1.5 whitespace-nowrap cursor-pointer"
                    @click.stop="checkStudentVisa(st)"
                  >
                    <RefreshCw class="size-3.5" :class="{ 'animate-spin': checkingPassports.has(st.passport) }" />
                    Check
                  </button>
                  <button
                    type="button"
                    class="px-4 py-2 h-full bg-amber-400 hover:bg-amber-500 dark:bg-amber-500 dark:hover:bg-amber-400 text-amber-950 dark:text-slate-950 rounded-none transition-colors cursor-pointer"
                    aria-label="View details"
                    @click.stop="openDetails(st)"
                  >
                    <Eye class="size-5" />
                  </button>
                </div>
              </td>
            </tr>

            <tr v-if="bottomSpacerH > 0" key="__bottom" :style="{ height: `${bottomSpacerH}px` }">
              <td :colspan="columnCount" style="padding:0;border:0" />
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Modals ── -->

    <!-- Add / Edit Student Modal -->
    <StudentFormModal
      :is-open="isAddModalOpen"
      :editing-student="editingStudent"
      @close="handleModalClose"
      @saved="loadStudents"
    />

    <!-- Student Details Modal -->
    <StudentDetailsModal
      :is-open="detailsModalOpen"
      :student="detailsStudent"
      :is-checking="detailsStudent ? checkingPassports.has(detailsStudent.passport) : false"
      @close="detailsModalOpen = false"
      @edit="openEditModal"
      @delete="promptDelete"
      @refresh="checkStudentVisa"
      @download-pdf="handleDownloadPdf"
      @updated="handleStudentUpdated"
    />

    <!-- Delete Confirm Modal -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showDeleteConfirm"
          class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          @mousedown.self="showDeleteConfirm = false"
        >
          <div class="w-full max-w-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl p-6 space-y-4">
            <div class="flex items-start gap-3">
              <div class="size-10 rounded-full bg-rose-100 dark:bg-rose-950/40 flex items-center justify-center shrink-0">
                <AlertTriangle class="size-5 text-rose-600 dark:text-rose-400" />
              </div>
              <div>
                <h3 class="font-bold text-zinc-900 dark:text-white">Talabani o'chirish?</h3>
                <p class="text-sm text-zinc-500 dark:text-zinc-400 mt-1 leading-relaxed">
                  <strong class="text-zinc-900 dark:text-white">{{ studentToDelete?.full_name }}</strong> ni faqat Viza tekshirish bazasidan o'chirasizmi? (Asosiy talabalar bazasi o'zgarmaydi).
                </p>
              </div>
            </div>
            <div class="flex items-center justify-end gap-2">
              <button
                type="button"
                @click="showDeleteConfirm = false"
                class="px-4 py-2 rounded-xl text-sm font-semibold text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                Bekor
              </button>
              <button
                type="button"
                @click="confirmDelete"
                class="px-4 py-2 rounded-xl text-sm font-bold text-white bg-rose-600 hover:bg-rose-500 transition-colors shadow-sm shadow-rose-500/30"
              >
                O'chirish
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Floating Dynamic Island Batch Progress Bar ── -->
    <IosBatchProgressBar
      :active="batchProgress.active"
      :total="batchProgress.total"
      :completed="batchProgress.completed"
      :failed="batchProgress.failed"
      :current-student-name="batchProgress.currentName"
    />

    <!-- ── Viza Hisoboti (Change Report Summary Modal) ── -->
    <ChangeReportModal
      :is-open="showReportModal"
      :changes="sessionChanges"
      :no-answers="sessionNoAnswers"
      :summary="sessionSummary"
      :is-retrying="isRetryingReport"
      @close="showReportModal = false"
      @retry-no-answers="handleRetryNoAnswers"
    />

    <!-- ── Context Menu (Right Click Menu) ── -->
    <StudentContextMenu
      :is-open="contextMenuOpen"
      :x="contextMenuX"
      :y="contextMenuY"
      :student="contextMenuStudent"
      :is-checking="contextMenuStudent ? checkingPassports.has(contextMenuStudent.passport) : false"
      @close="contextMenuOpen = false"
      @check="checkStudentVisa"
      @details="openDetails"
      @edit="openEditModal"
      @toggle-pin="handlePinToggle"
      @toggle-flag="handleFlagToggle"
      @download-pdf="handleDownloadPdf"
      @delete="promptDelete"
    />

  </div>
</template>
