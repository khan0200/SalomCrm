<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { Payment, Student } from '@/types'
import {
  DollarSign, TrendingUp, TrendingDown, Users, AlertCircle,
  FileSpreadsheet, Filter, Calendar, Search, ArrowUpRight,
  ArrowDownRight, Percent, Wallet, CreditCard, Lock,
  ChevronDown, ChevronUp, Printer, Copy, Check, X,
  Clock, Tag, RefreshCw, UserCheck, GraduationCap, Hash, RotateCcw,
  ExternalLink, Download, Phone, ArrowRight, ChevronLeft, ChevronRight,
  ChevronsLeft, ChevronsRight, Award, Contact, Folder, Bookmark
} from 'lucide-vue-next'

const props = defineProps<{
  payments: Payment[]
  students: Student[]
  paymentMethods: string[]
  paymentReceivers: string[]
  options?: any
  isLoading?: boolean
}>()

const emit = defineEmits<{
  (e: 'lock-finance'): void
  (e: 'open-edit-payment', payment: Payment): void
  (e: 'delete-payment', payment: Payment): void
  (e: 'open-add-payment', studentId?: string): void
}>()

const ITEMS_PER_PAGE = 30

// ── Date Filters ──────────────────────────────────────────────────────
type DatePreset = 'all' | 'today' | 'yesterday' | 'this_week' | 'this_month' | 'last_month' | 'this_year' | 'custom'

const selectedDatePreset = ref<DatePreset>('all')
const customStartDate = ref('')
const customEndDate = ref('')

// Other Filters
const searchFinance = ref('')
const selectedMethod = ref('all')
const selectedReceiver = ref('all')
const selectedType = ref<'all' | 'payments' | 'withdrawals' | 'discounts'>('all')
const currentPage = ref(1)

// Receipt Modal State
const viewingPayment = ref<Payment | null>(null)
const copiedField = ref<string | null>(null)

const handleCopy = (field: string, text?: string | number | null) => {
  if (!text) return
  navigator.clipboard.writeText(String(text))
  copiedField.value = field
  setTimeout(() => {
    if (copiedField.value === field) copiedField.value = null
  }, 1600)
}

// ── Student Lookup Map ────────────────────────────────────────────────
const studentMap = computed(() => {
  const map = new Map<string, Student>()
  props.students.forEach(s => {
    if (s.id) {
      map.set(s.id, s)
      map.set(s.id.toLowerCase(), s)
    }
  })
  return map
})

const getStudent = (studentId?: string | null): Student | undefined => {
  if (!studentId) return undefined
  return studentMap.value.get(studentId) || studentMap.value.get(studentId.toLowerCase())
}

// ── 5 Multi-Select Filter Options (Tariff, Group, Coordinator, Level, ID) ──
const availableTariffs = computed<string[]>(() => {
  const set = new Set<string>()
  if (props.options?.tariffs) {
    props.options.tariffs.forEach((t: any) => {
      const name = typeof t === 'string' ? t : t?.name
      if (name && name !== 'No Tariff' && name !== 'NO_TARIFF') set.add(name)
    })
  }
  props.students.forEach(s => {
    if (s.tariff && s.tariff !== 'No Tariff' && s.tariff !== 'NO_TARIFF') {
      set.add(s.tariff)
    }
  })
  const sorted = Array.from(set).sort((a, b) => a.localeCompare(b))
  return [...sorted, 'No Tariff']
})

const availableGroups = computed<string[]>(() => {
  const set = new Set<string>()
  if (props.options?.groups) {
    props.options.groups.forEach((g: any) => {
      const name = typeof g === 'string' ? g : g?.name
      if (name && name !== 'No Group' && name !== 'NO_GROUP') set.add(name)
    })
  }
  props.students.forEach(s => {
    if (s.student_group && s.student_group !== 'No Group' && s.student_group !== 'NO_GROUP') {
      set.add(s.student_group)
    }
  })
  const sorted = Array.from(set).sort((a, b) => a.localeCompare(b))
  return [...sorted, 'No Group']
})

const availableCoordinators = computed<string[]>(() => {
  const set = new Set<string>()
  if (props.options?.coordinators) {
    props.options.coordinators.forEach((c: any) => {
      const name = typeof c === 'string' ? c : c?.name
      if (name && name !== 'No Coordinator' && name !== 'NO_COORDINATOR') set.add(name)
    })
  }
  props.students.forEach(s => {
    if (s.coordinator && s.coordinator !== 'No Coordinator' && s.coordinator !== 'NO_COORDINATOR') {
      set.add(s.coordinator)
    }
  })
  const sorted = Array.from(set).sort((a, b) => a.localeCompare(b))
  return [...sorted, 'No Coordinator']
})

const availableLevels = computed<string[]>(() => {
  const set = new Set<string>()
  const defaultLevels = ['COLLEGE', 'BACHELOR', 'MASTERS', 'MASTER NO CERTIFICATE', 'LANGUAGE COURSE']
  defaultLevels.forEach(l => set.add(l))
  if (props.options?.levels) {
    props.options.levels.forEach((l: any) => {
      const name = typeof l === 'string' ? l : l?.name
      if (name && name !== 'No Level' && name !== 'NO_LEVEL') set.add(name)
    })
  }
  props.students.forEach(s => {
    if (s.level) set.add(s.level)
    if (s.level2) set.add(s.level2)
  })
  const sorted = Array.from(set).sort((a, b) => a.localeCompare(b))
  return [...sorted, 'No Level']
})

const extractIdPrefix = (idStr?: string | null): string => {
  if (!idStr) return 'No ID'
  const str = idStr.trim()
  if (!str || str === '—' || str === '-') return 'No ID'
  const match = str.match(/^([A-Za-z]+)/)
  if (match && match[1]) {
    return match[1].toUpperCase()
  }
  return 'No ID'
}

const availableIds = computed<string[]>(() => {
  const set = new Set<string>()
  props.students.forEach(s => {
    if (s.id) {
      const prefix = extractIdPrefix(s.id)
      if (prefix && prefix !== 'No ID') set.add(prefix)
    }
  })
  props.payments.forEach(pay => {
    if (pay.student_id) {
      const prefix = extractIdPrefix(pay.student_id)
      if (prefix && prefix !== 'No ID') set.add(prefix)
    }
  })
  const sorted = Array.from(set).sort((a, b) => a.localeCompare(b))
  return [...sorted, 'No ID']
})

const idPrefixStudentCounts = computed(() => {
  const map = new Map<string, Set<string>>()

  // 1. Unique students from props.students
  props.students.forEach(s => {
    const sid = s.id || (s as any).student_id
    if (sid) {
      const prefix = extractIdPrefix(sid)
      if (!map.has(prefix)) map.set(prefix, new Set())
      map.get(prefix)!.add(String(sid).trim().toUpperCase())
    }
  })

  // 2. Unique students from props.payments
  props.payments.forEach(pay => {
    if (pay.student_id) {
      const prefix = extractIdPrefix(pay.student_id)
      if (!map.has(prefix)) map.set(prefix, new Set())
      map.get(prefix)!.add(String(pay.student_id).trim().toUpperCase())
    }
  })

  const counts = new Map<string, number>()
  map.forEach((uniqueIds, prefix) => {
    counts.set(prefix, uniqueIds.size)
  })

  // Count No ID
  let noIdStudents = 0
  props.students.forEach(s => {
    const sid = s.id || (s as any).student_id
    if (!sid || extractIdPrefix(sid) === 'No ID') noIdStudents++
  })
  if (noIdStudents === 0) {
    const noIdTx = new Set<string>()
    props.payments.forEach(pay => {
      if (!pay.student_id || extractIdPrefix(pay.student_id) === 'No ID') {
        noIdTx.add(pay.id || `${pay.amount}_${pay.created_at}`)
      }
    })
    noIdStudents = noIdTx.size
  }
  counts.set('No ID', noIdStudents)

  return counts
})

// ── Multi-Select States (null = all checked by default) ───────────────
const selectedTariffs = ref<string[] | null>(null)
const selectedGroups = ref<string[] | null>(null)
const selectedCoordinators = ref<string[] | null>(null)
const selectedLevels = ref<string[] | null>(null)
const selectedIds = ref<string[] | null>(null)

// Effective selected arrays
const effectiveSelectedTariffs = computed<string[]>(() => selectedTariffs.value ?? availableTariffs.value)
const effectiveSelectedGroups = computed<string[]>(() => selectedGroups.value ?? availableGroups.value)
const effectiveSelectedCoordinators = computed<string[]>(() => selectedCoordinators.value ?? availableCoordinators.value)
const effectiveSelectedLevels = computed<string[]>(() => selectedLevels.value ?? availableLevels.value)
const effectiveSelectedIds = computed<string[]>(() => selectedIds.value ?? availableIds.value)

// Checkers & Toggles for Tariff
const isTariffSelected = (val: string) => effectiveSelectedTariffs.value.includes(val)
const isAllTariffsSelected = computed(() => {
  return availableTariffs.value.length > 0 &&
    effectiveSelectedTariffs.value.length === availableTariffs.value.length
})
const toggleTariff = (val: string) => {
  const current = [...effectiveSelectedTariffs.value]
  const idx = current.indexOf(val)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(val)
  }
  selectedTariffs.value = current
}
const toggleAllTariffs = () => {
  if (isAllTariffsSelected.value) {
    selectedTariffs.value = []
  } else {
    selectedTariffs.value = [...availableTariffs.value]
  }
}

// Checkers & Toggles for Group
const isGroupSelected = (val: string) => effectiveSelectedGroups.value.includes(val)
const isAllGroupsSelected = computed(() => {
  return availableGroups.value.length > 0 &&
    effectiveSelectedGroups.value.length === availableGroups.value.length
})
const toggleGroup = (val: string) => {
  const current = [...effectiveSelectedGroups.value]
  const idx = current.indexOf(val)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(val)
  }
  selectedGroups.value = current
}
const toggleAllGroups = () => {
  if (isAllGroupsSelected.value) {
    selectedGroups.value = []
  } else {
    selectedGroups.value = [...availableGroups.value]
  }
}

// Checkers & Toggles for Coordinator
const isCoordinatorSelected = (val: string) => effectiveSelectedCoordinators.value.includes(val)
const isAllCoordinatorsSelected = computed(() => {
  return availableCoordinators.value.length > 0 &&
    effectiveSelectedCoordinators.value.length === availableCoordinators.value.length
})
const toggleCoordinator = (val: string) => {
  const current = [...effectiveSelectedCoordinators.value]
  const idx = current.indexOf(val)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(val)
  }
  selectedCoordinators.value = current
}
const toggleAllCoordinators = () => {
  if (isAllCoordinatorsSelected.value) {
    selectedCoordinators.value = []
  } else {
    selectedCoordinators.value = [...availableCoordinators.value]
  }
}

// Checkers & Toggles for Level
const isLevelSelected = (val: string) => effectiveSelectedLevels.value.includes(val)
const isAllLevelsSelected = computed(() => {
  return availableLevels.value.length > 0 &&
    effectiveSelectedLevels.value.length === availableLevels.value.length
})
const toggleLevel = (val: string) => {
  const current = [...effectiveSelectedLevels.value]
  const idx = current.indexOf(val)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(val)
  }
  selectedLevels.value = current
}
const toggleAllLevels = () => {
  if (isAllLevelsSelected.value) {
    selectedLevels.value = []
  } else {
    selectedLevels.value = [...availableLevels.value]
  }
}

// Checkers & Toggles for ID
const isIdSelected = (val: string) => effectiveSelectedIds.value.includes(val)
const isAllIdsSelected = computed(() => {
  return availableIds.value.length > 0 &&
    effectiveSelectedIds.value.length === availableIds.value.length
})
const toggleId = (val: string) => {
  const current = [...effectiveSelectedIds.value]
  const idx = current.indexOf(val)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(val)
  }
  selectedIds.value = current
}
const toggleAllIds = () => {
  if (isAllIdsSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = [...availableIds.value]
  }
}

// ── Dropdown Open & Search States ────────────────────────────────────
const isTariffOpen = ref(false)
const isGroupOpen = ref(false)
const isCoordinatorOpen = ref(false)
const isLevelOpen = ref(false)
const isIdOpen = ref(false)

const tariffRef = ref<HTMLElement | null>(null)
const groupRef = ref<HTMLElement | null>(null)
const coordinatorRef = ref<HTMLElement | null>(null)
const levelRef = ref<HTMLElement | null>(null)
const idRef = ref<HTMLElement | null>(null)

const tariffSearch = ref('')
const groupSearch = ref('')
const coordinatorSearch = ref('')
const levelSearch = ref('')
const idSearch = ref('')

const filteredAvailableTariffs = computed(() => {
  const q = tariffSearch.value.trim().toLowerCase()
  if (!q) return availableTariffs.value
  return availableTariffs.value.filter(t => t.toLowerCase().includes(q))
})

const filteredAvailableGroups = computed(() => {
  const q = groupSearch.value.trim().toLowerCase()
  if (!q) return availableGroups.value
  return availableGroups.value.filter(g => g.toLowerCase().includes(q))
})

const filteredAvailableCoordinators = computed(() => {
  const q = coordinatorSearch.value.trim().toLowerCase()
  if (!q) return availableCoordinators.value
  return availableCoordinators.value.filter(c => c.toLowerCase().includes(q))
})

const filteredAvailableLevels = computed(() => {
  const q = levelSearch.value.trim().toLowerCase()
  if (!q) return availableLevels.value
  return availableLevels.value.filter(l => l.toLowerCase().includes(q))
})

const filteredAvailableIds = computed(() => {
  const q = idSearch.value.trim().toLowerCase()
  if (!q) return availableIds.value
  return availableIds.value.filter(prefix => prefix.toLowerCase().includes(q))
})

const toggleDropdown = (name: 'tariff' | 'group' | 'coordinator' | 'level' | 'id') => {
  isTariffOpen.value = name === 'tariff' ? !isTariffOpen.value : false
  isGroupOpen.value = name === 'group' ? !isGroupOpen.value : false
  isCoordinatorOpen.value = name === 'coordinator' ? !isCoordinatorOpen.value : false
  isLevelOpen.value = name === 'level' ? !isLevelOpen.value : false
  isIdOpen.value = name === 'id' ? !isIdOpen.value : false
}

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as Node
  if (tariffRef.value && !tariffRef.value.contains(target)) isTariffOpen.value = false
  if (groupRef.value && !groupRef.value.contains(target)) isGroupOpen.value = false
  if (coordinatorRef.value && !coordinatorRef.value.contains(target)) isCoordinatorOpen.value = false
  if (levelRef.value && !levelRef.value.contains(target)) isLevelOpen.value = false
  if (idRef.value && !idRef.value.contains(target)) isIdOpen.value = false
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})

const hasActiveStudentFilters = computed(() => {
  return !isAllTariffsSelected.value ||
    !isAllGroupsSelected.value ||
    !isAllCoordinatorsSelected.value ||
    !isAllLevelsSelected.value ||
    !isAllIdsSelected.value
})

const resetStudentFilters = () => {
  selectedTariffs.value = null
  selectedGroups.value = null
  selectedCoordinators.value = null
  selectedLevels.value = null
  selectedIds.value = null
  tariffSearch.value = ''
  groupSearch.value = ''
  coordinatorSearch.value = ''
  levelSearch.value = ''
  idSearch.value = ''
}

// ── Matching Helper for Student Criteria ─────────────────────────────
const matchesStudentCriteria = (studentId?: string | null) => {
  const s = getStudent(studentId)

  // 1. Tariff Filter
  const tariffVal = s?.tariff || 'No Tariff'
  if (!effectiveSelectedTariffs.value.includes(tariffVal)) return false

  // 2. Group Filter
  const groupVal = s?.student_group || 'No Group'
  if (!effectiveSelectedGroups.value.includes(groupVal)) return false

  // 3. Coordinator Filter
  const coordVal = s?.coordinator || 'No Coordinator'
  if (!effectiveSelectedCoordinators.value.includes(coordVal)) return false

  // 4. Level Filter
  if (s) {
    const hasLevel1 = !!s.level
    const hasLevel2 = !!s.level2
    if (!hasLevel1 && !hasLevel2) {
      if (!effectiveSelectedLevels.value.includes('No Level')) return false
    } else {
      const match1 = hasLevel1 && effectiveSelectedLevels.value.includes(s.level!)
      const match2 = hasLevel2 && effectiveSelectedLevels.value.includes(s.level2!)
      if (!match1 && !match2) return false
    }
  } else {
    if (!effectiveSelectedLevels.value.includes('No Level')) return false
  }

  // 5. ID Prefix Filter (e.g. CF, D, F, AB, T, YU, etc.)
  const idPrefix = extractIdPrefix(studentId)
  if (!effectiveSelectedIds.value.includes(idPrefix)) return false

  return true
}

// ── Date Range Computation Helpers ─────────────────────────────────────
const getDateRange = (preset: DatePreset): { start: Date | null; end: Date | null } => {
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0)
  const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999)

  switch (preset) {
    case 'today':
      return { start: todayStart, end: todayEnd }

    case 'yesterday': {
      const yStart = new Date(todayStart)
      yStart.setDate(yStart.getDate() - 1)
      const yEnd = new Date(todayEnd)
      yEnd.setDate(yEnd.getDate() - 1)
      return { start: yStart, end: yEnd }
    }

    case 'this_week': {
      // Start of current week (Monday)
      const day = todayStart.getDay()
      const diff = todayStart.getDate() - day + (day === 0 ? -6 : 1)
      const weekStart = new Date(todayStart.setDate(diff))
      return { start: weekStart, end: todayEnd }
    }

    case 'this_month': {
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0, 0)
      return { start: monthStart, end: todayEnd }
    }

    case 'last_month': {
      const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1, 0, 0, 0, 0)
      const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59, 999)
      return { start: lastMonthStart, end: lastMonthEnd }
    }

    case 'this_year': {
      const yearStart = new Date(now.getFullYear(), 0, 1, 0, 0, 0, 0)
      return { start: yearStart, end: todayEnd }
    }

    case 'custom': {
      const start = customStartDate.value ? new Date(`${customStartDate.value}T00:00:00`) : null
      const end = customEndDate.value ? new Date(`${customEndDate.value}T23:59:59.999`) : null
      return { start, end }
    }

    case 'all':
    default:
      return { start: null, end: null }
  }
}

const currentRange = computed(() => getDateRange(selectedDatePreset.value))

// ── Overall Fixed KPI Calculations (Today, This Month, Total Debt) ─────
const todayMetrics = computed(() => {
  const { start, end } = getDateRange('today')
  if (!start || !end) return { collected: 0, count: 0 }

  let total = 0
  let count = 0
  props.payments.forEach(p => {
    if (!p.created_at || p.is_discount || p.is_withdrawal) return
    if (!matchesStudentCriteria(p.student_id)) return
    const d = new Date(p.created_at)
    if (d >= start && d <= end) {
      const amt = Number(p.amount) || 0
      if (amt > 0) {
        total += amt
        count++
      }
    }
  })
  return { collected: total, count }
})

const thisMonthMetrics = computed(() => {
  const { start, end } = getDateRange('this_month')
  if (!start || !end) return { collected: 0, count: 0 }

  let total = 0
  let count = 0
  props.payments.forEach(p => {
    if (!p.created_at || p.is_discount || p.is_withdrawal) return
    if (!matchesStudentCriteria(p.student_id)) return
    const d = new Date(p.created_at)
    if (d >= start && d <= end) {
      const amt = Number(p.amount) || 0
      if (amt > 0) {
        total += amt
        count++
      }
    }
  })
  return { collected: total, count }
})

// Debt analysis across active students filtered by selected student criteria
const debtMetrics = computed(() => {
  let totalDebt = 0
  let debtorCount = 0
  let totalAdvance = 0
  let fullyPaidCount = 0
  let totalActiveStudents = 0

  props.students.forEach(s => {
    if (s.is_deleted) return
    if (!matchesStudentCriteria(s.id)) return

    totalActiveStudents++
    const bal = Number(s.balance) || 0
    if (bal < 0) {
      totalDebt += Math.abs(bal)
      debtorCount++
    } else if (bal > 0) {
      totalAdvance += bal
    } else {
      fullyPaidCount++
    }
  })

  return {
    totalDebt,
    debtorCount,
    totalAdvance,
    fullyPaidCount,
    totalActiveStudents
  }
})

// ── Filtered Payments according to selected date range & filters ───────
const filteredPayments = computed(() => {
  const { start, end } = currentRange.value

  return props.payments.filter(p => {
    // 1. Date Range Filter
    if (p.created_at) {
      const d = new Date(p.created_at)
      if (start && d < start) return false
      if (end && d > end) return false
    }

    // 2. Transaction Type Filter
    if (selectedType.value === 'payments') {
      if (p.is_discount || p.is_withdrawal || Number(p.amount) <= 0) return false
    } else if (selectedType.value === 'withdrawals') {
      if (!p.is_withdrawal && Number(p.amount) >= 0) return false
    } else if (selectedType.value === 'discounts') {
      if (!p.is_discount) return false
    }

    // 3. Payment Method Filter
    if (selectedMethod.value !== 'all' && p.method !== selectedMethod.value) {
      return false
    }

    // 4. Receiver Filter
    if (selectedReceiver.value !== 'all' && p.received_by !== selectedReceiver.value) {
      return false
    }

    // 5. Student Criteria Filters (Tariff, Group, Coordinator, Level, ID)
    if (!matchesStudentCriteria(p.student_id)) {
      return false
    }

    // 6. Search Query
    if (searchFinance.value.trim()) {
      const q = searchFinance.value.toLowerCase()
      const matchName = (p.student_full_name || p.student_name || '').toLowerCase().includes(q)
      const matchId = (p.student_id || '').toLowerCase().includes(q)
      const matchReceiver = (p.received_by || '').toLowerCase().includes(q)
      const matchNotes = (p.notes || '').toLowerCase().includes(q)
      if (!matchName && !matchId && !matchReceiver && !matchNotes) return false
    }

    return true
  })
})

// Strictly sort payments descending by created_at
const sortedFilteredPayments = computed(() => {
  return [...filteredPayments.value].sort((a, b) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
    return timeB - timeA
  })
})

// ── Selected Period KPI Summary ───────────────────────────────────────
const periodMetrics = computed(() => {
  let totalCollected = 0
  let totalWithdrawals = 0
  let totalDiscounts = 0
  let collectedTxCount = 0
  let withdrawalTxCount = 0
  let discountTxCount = 0

  filteredPayments.value.forEach(p => {
    const amt = Number(p.amount) || 0
    if (p.is_discount) {
      totalDiscounts += Math.abs(amt)
      discountTxCount++
    } else if (p.is_withdrawal || amt < 0) {
      totalWithdrawals += Math.abs(amt)
      withdrawalTxCount++
    } else {
      totalCollected += amt
      collectedTxCount++
    }
  })

  const netCashflow = totalCollected - totalWithdrawals

  return {
    totalCollected,
    totalWithdrawals,
    totalDiscounts,
    netCashflow,
    collectedTxCount,
    withdrawalTxCount,
    discountTxCount,
    totalTxCount: filteredPayments.value.length
  }
})

// ── Method Breakdown for selected period ──────────────────────────────
const methodBreakdown = computed(() => {
  const map = new Map<string, { amount: number; count: number }>()

  filteredPayments.value.forEach(p => {
    if (p.is_discount || p.is_withdrawal) return
    const amt = Number(p.amount) || 0
    if (amt <= 0) return

    const m = p.method || 'Unspecified'
    const existing = map.get(m) || { amount: 0, count: 0 }
    map.set(m, {
      amount: existing.amount + amt,
      count: existing.count + 1
    })
  })

  const total = periodMetrics.value.totalCollected || 1
  return Array.from(map.entries())
    .map(([method, data]) => ({
      method,
      amount: data.amount,
      count: data.count,
      percent: Math.round((data.amount / total) * 100)
    }))
    .sort((a, b) => b.amount - a.amount)
})

// ── Receiver Breakdown for selected period ────────────────────────────
const receiverBreakdown = computed(() => {
  const map = new Map<string, { amount: number; count: number }>()

  filteredPayments.value.forEach(p => {
    if (p.is_discount || p.is_withdrawal) return
    const amt = Number(p.amount) || 0
    if (amt <= 0) return

    const r = p.received_by || 'Unspecified'
    const existing = map.get(r) || { amount: 0, count: 0 }
    map.set(r, {
      amount: existing.amount + amt,
      count: existing.count + 1
    })
  })

  const total = periodMetrics.value.totalCollected || 1
  return Array.from(map.entries())
    .map(([receiver, data]) => ({
      receiver,
      amount: data.amount,
      count: data.count,
      percent: Math.round((data.amount / total) * 100)
    }))
    .sort((a, b) => b.amount - a.amount)
})

// ── Pagination ────────────────────────────────────────────────────────
const totalPages = computed(() => Math.max(1, Math.ceil(sortedFilteredPayments.value.length / ITEMS_PER_PAGE)))
const paginatedPayments = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return sortedFilteredPayments.value.slice(start, start + ITEMS_PER_PAGE)
})

watch([
  selectedDatePreset, customStartDate, customEndDate, searchFinance,
  selectedMethod, selectedReceiver, selectedType,
  effectiveSelectedTariffs, effectiveSelectedGroups, effectiveSelectedCoordinators,
  effectiveSelectedLevels, effectiveSelectedIds
], () => {
  currentPage.value = 1
})

// Number formatting helper
const formatUZS = (val: number | string | null | undefined) => {
  if (val === null || val === undefined) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('uz-UZ').format(Math.round(num || 0))
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const handlePrint = () => {
  if (typeof window !== 'undefined') {
    window.print()
  }
}

// ── Export Financial Report to Excel ─────────────────────────────────
const exportFinanceReportToExcel = async () => {
  if (sortedFilteredPayments.value.length === 0) {
    alert('No transaction records to export in the selected filter range!')
    return
  }

  const XLSX = await import('xlsx-js-style')

  const pad = (n: number) => String(n).padStart(2, '0')
  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  }

  // Summary Rows
  const summaryRows = [
    { A: 'SALOM CRM - FINANCIAL REPORT' },
    { A: `Report Date Range: ${selectedDatePreset.value.toUpperCase()}` },
    { A: `Generated At: ${formatDateTime(new Date().toISOString())}` },
    { A: '' },
    { A: 'METRIC', B: 'AMOUNT (UZS)', C: 'DETAILS' },
    { A: 'Total Collected (Selected Range)', B: periodMetrics.value.totalCollected, C: `${periodMetrics.value.collectedTxCount} payments` },
    { A: 'Total Collected (Today)', B: todayMetrics.value.collected, C: `${todayMetrics.value.count} payments today` },
    { A: 'Total Collected (This Month)', B: thisMonthMetrics.value.collected, C: `${thisMonthMetrics.value.count} payments this month` },
    { A: 'Total Outstanding Debt', B: debtMetrics.value.totalDebt, C: `${debtMetrics.value.debtorCount} active debtor students` },
    { A: 'Total Discounts Given', B: periodMetrics.value.totalDiscounts, C: `${periodMetrics.value.discountTxCount} discounts` },
    { A: 'Total Withdrawals', B: periodMetrics.value.totalWithdrawals, C: `${periodMetrics.value.withdrawalTxCount} withdrawals` },
    { A: 'Net Cashflow', B: periodMetrics.value.netCashflow, C: 'Collected minus Withdrawals' },
    { A: '' },
    { A: 'ITEMIZED FINANCIAL TRANSACTIONS' }
  ]

  const ledgerData = sortedFilteredPayments.value.map((p, index) => {
    let txType = 'Payment'
    if (p.is_withdrawal) txType = 'Withdrawal'
    else if (p.is_discount) txType = 'Discount'

    const s = getStudent(p.student_id)

    return {
      No: index + 1,
      'Transaction ID': p.id ? String(p.id).toUpperCase() : '',
      'Student ID': p.student_id || '—',
      'Student Name': p.student_full_name || p.student_name || 'General Payment',
      'Tariff': s?.tariff || '—',
      'Group': s?.student_group || '—',
      'Coordinator': s?.coordinator || '—',
      'Level': s?.level || '—',
      'Type': txType,
      'Payment Method': p.method || '—',
      'Received By': p.received_by || '—',
      'Amount (UZS)': Number(p.amount) || 0,
      'Date & Time': formatDateTime(p.created_at),
      'Notes': p.notes || ''
    }
  })

  const wb = XLSX.utils.book_new()

  // 1. Transactions Sheet
  const ws = XLSX.utils.json_to_sheet(ledgerData)
  ws['!cols'] = [
    { wch: 6 },   // No
    { wch: 22 },  // ID
    { wch: 15 },  // Student ID
    { wch: 30 },  // Student Name
    { wch: 18 },  // Tariff
    { wch: 16 },  // Group
    { wch: 18 },  // Coordinator
    { wch: 16 },  // Level
    { wch: 15 },  // Type
    { wch: 18 },  // Method
    { wch: 18 },  // Received By
    { wch: 18 },  // Amount
    { wch: 22 },  // Date
    { wch: 35 }   // Notes
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'Transactions Ledger')

  // 2. Summary Sheet
  const wsSummary = XLSX.utils.json_to_sheet(summaryRows, { skipHeader: true })
  wsSummary['!cols'] = [{ wch: 35 }, { wch: 22 }, { wch: 35 }]
  XLSX.utils.book_append_sheet(wb, wsSummary, 'Financial KPI Summary')

  const dateStr = new Date().toISOString().split('T')[0]
  const filename = `Finance_Report_${selectedDatePreset.value}_${dateStr}.xlsx`
  XLSX.writeFile(wb, filename)
}

// ── KPI Details Modal State ──────────────────────────────────────────
const activeKpiModal = ref<'collected' | 'debt' | 'discount' | 'withdraw' | null>(null)
const kpiSearchType = ref<'all' | 'id' | 'name' | 'phone' | 'method' | 'coordinator' | 'receiver' | 'notes'>('all')
const kpiSearchQuery = ref('')
const kpiDatePreset = ref<DatePreset>('all')
const kpiCustomStartDate = ref('')
const kpiCustomEndDate = ref('')
const kpiSelectedStatuses = ref<string[]>([]) // ['ACTIVE'], ['ARCHIVE']
const kpiSelectedTariffs = ref<string[]>([])
const kpiSelectedGroups = ref<string[]>([])
const kpiSelectedCoordinators = ref<string[]>([])
const kpiSelectedLevels = ref<string[]>([])
const kpiSelectedIds = ref<string[]>([])
const kpiSelectedMethods = ref<string[]>([])
const kpiSelectedReceivers = ref<string[]>([])

// Dropdowns in modal
const isKpiDateDropdownOpen = ref(false)
const isKpiStatusDropdownOpen = ref(false)
const isKpiTariffDropdownOpen = ref(false)
const isKpiGroupDropdownOpen = ref(false)
const isKpiCoordinatorDropdownOpen = ref(false)
const isKpiLevelDropdownOpen = ref(false)
const isKpiIdDropdownOpen = ref(false)
const isKpiMethodDropdownOpen = ref(false)
const isKpiReceiverDropdownOpen = ref(false)

const closeAllKpiDropdowns = () => {
  isKpiDateDropdownOpen.value = false
  isKpiStatusDropdownOpen.value = false
  isKpiTariffDropdownOpen.value = false
  isKpiGroupDropdownOpen.value = false
  isKpiCoordinatorDropdownOpen.value = false
  isKpiLevelDropdownOpen.value = false
  isKpiIdDropdownOpen.value = false
  isKpiMethodDropdownOpen.value = false
  isKpiReceiverDropdownOpen.value = false
}

type KpiDropdownKey = 'date' | 'status' | 'tariff' | 'group' | 'coordinator' | 'level' | 'id' | 'method' | 'receiver'
const kpiDropdownRefs: Record<KpiDropdownKey, typeof isKpiDateDropdownOpen> = {
  date: isKpiDateDropdownOpen,
  status: isKpiStatusDropdownOpen,
  tariff: isKpiTariffDropdownOpen,
  group: isKpiGroupDropdownOpen,
  coordinator: isKpiCoordinatorDropdownOpen,
  level: isKpiLevelDropdownOpen,
  id: isKpiIdDropdownOpen,
  method: isKpiMethodDropdownOpen,
  receiver: isKpiReceiverDropdownOpen,
}
const toggleKpiDropdown = (key: KpiDropdownKey) => {
  const target = kpiDropdownRefs[key]
  const wasOpen = target.value
  closeAllKpiDropdowns()
  target.value = !wasOpen
}

const toggleKpiList = (list: string[], value: string) => {
  const idx = list.indexOf(value)
  if (idx === -1) list.push(value)
  else list.splice(idx, 1)
}

const handleKpiOutsideClick = (e: MouseEvent) => {
  const anyOpen =
    isKpiDateDropdownOpen.value ||
    isKpiStatusDropdownOpen.value ||
    isKpiTariffDropdownOpen.value ||
    isKpiGroupDropdownOpen.value ||
    isKpiCoordinatorDropdownOpen.value ||
    isKpiLevelDropdownOpen.value ||
    isKpiIdDropdownOpen.value ||
    isKpiMethodDropdownOpen.value ||
    isKpiReceiverDropdownOpen.value

  if (!anyOpen) return

  const target = e.target as HTMLElement | null
  if (target?.closest('.kpi-dropdown-container')) {
    return
  }
  closeAllKpiDropdowns()
}

onMounted(() => {
  document.addEventListener('mousedown', handleKpiOutsideClick)
  document.addEventListener('click', handleKpiOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleKpiOutsideClick)
  document.removeEventListener('click', handleKpiOutsideClick)
})

const kpiPage = ref(1)
const kpiPageSize = ref(15)

const openKpiModal = (type: 'collected' | 'debt' | 'discount' | 'withdraw') => {
  activeKpiModal.value = type
  kpiSearchQuery.value = searchFinance.value || ''
  kpiSearchType.value = 'all'
  kpiPage.value = 1
  kpiPageSize.value = 15

  // Inherit active date range from main page filters
  kpiDatePreset.value = selectedDatePreset.value
  kpiCustomStartDate.value = customStartDate.value || ''
  kpiCustomEndDate.value = customEndDate.value || ''

  // Inherit active multi-select student criteria from main page filters
  kpiSelectedStatuses.value = type === 'debt' ? ['ACTIVE'] : []
  kpiSelectedTariffs.value = isAllTariffsSelected.value ? [] : [...effectiveSelectedTariffs.value]
  kpiSelectedGroups.value = isAllGroupsSelected.value ? [] : [...effectiveSelectedGroups.value]
  kpiSelectedCoordinators.value = isAllCoordinatorsSelected.value ? [] : [...effectiveSelectedCoordinators.value]
  kpiSelectedLevels.value = isAllLevelsSelected.value ? [] : [...effectiveSelectedLevels.value]
  kpiSelectedIds.value = isAllIdsSelected.value ? [] : [...effectiveSelectedIds.value]
  kpiSelectedMethods.value = selectedMethod.value === 'all' ? [] : [selectedMethod.value]
  kpiSelectedReceivers.value = selectedReceiver.value === 'all' ? [] : [selectedReceiver.value]
  closeAllKpiDropdowns()
}

const closeKpiModal = () => {
  activeKpiModal.value = null
  closeAllKpiDropdowns()
}

const getKpiDateRange = (preset: DatePreset, customStart?: string, customEnd?: string) => {
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0)
  const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999)

  switch (preset) {
    case 'today':
      return { start: todayStart, end: todayEnd }
    case 'yesterday': {
      const yestStart = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 0, 0, 0, 0)
      const yestEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 23, 59, 59, 999)
      return { start: yestStart, end: yestEnd }
    }
    case 'this_week': {
      const day = now.getDay()
      const diffToMon = day === 0 ? -6 : 1 - day
      const weekStart = new Date(now.getFullYear(), now.getMonth(), now.getDate() + diffToMon, 0, 0, 0, 0)
      return { start: weekStart, end: todayEnd }
    }
    case 'this_month': {
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0, 0)
      return { start: monthStart, end: todayEnd }
    }
    case 'last_month': {
      const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1, 0, 0, 0, 0)
      const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59, 999)
      return { start: lastMonthStart, end: lastMonthEnd }
    }
    case 'this_year': {
      const yearStart = new Date(now.getFullYear(), 0, 1, 0, 0, 0, 0)
      return { start: yearStart, end: todayEnd }
    }
    case 'custom': {
      const start = customStart ? new Date(`${customStart}T00:00:00`) : null
      const end = customEnd ? new Date(`${customEnd}T23:59:59.999`) : null
      return { start, end }
    }
    case 'all':
    default:
      return { start: null, end: null }
  }
}

const matchesKpiStudentCriteria = (studentId?: string | null, studentObj?: Student) => {
  const s = studentObj || getStudent(studentId)

  // Status Filter: Active vs Archive
  if (kpiSelectedStatuses.value.length > 0) {
    const isArchived = s?.is_deleted === true
    const wantsActive = kpiSelectedStatuses.value.includes('ACTIVE')
    const wantsArchive = kpiSelectedStatuses.value.includes('ARCHIVE')
    if (wantsActive && !wantsArchive && isArchived) return false
    if (wantsArchive && !wantsActive && !isArchived) return false
  }

  // Tariff Filter
  if (kpiSelectedTariffs.value.length > 0) {
    const t = s?.tariff || 'No Tariff'
    if (!kpiSelectedTariffs.value.includes(t)) return false
  }

  // Group Filter
  if (kpiSelectedGroups.value.length > 0) {
    const g = s?.student_group || 'No Group'
    if (!kpiSelectedGroups.value.includes(g)) return false
  }

  // Coordinator Filter
  if (kpiSelectedCoordinators.value.length > 0) {
    const c = s?.coordinator || 'No Coordinator'
    if (!kpiSelectedCoordinators.value.includes(c)) return false
  }

  // Level Filter
  if (kpiSelectedLevels.value.length > 0) {
    const l1 = s?.level || 'No Level'
    const l2 = s?.level2 || ''
    const match = kpiSelectedLevels.value.includes(l1) || (l2 && kpiSelectedLevels.value.includes(l2))
    if (!match) return false
  }

  // ID Prefix Filter
  if (kpiSelectedIds.value.length > 0) {
    const prefix = extractIdPrefix(s?.id || studentId)
    if (!kpiSelectedIds.value.includes(prefix)) return false
  }

  return true
}

// 1. Collected Filtered List
const filteredCollectedModalList = computed(() => {
  const { start, end } = getKpiDateRange(kpiDatePreset.value, kpiCustomStartDate.value, kpiCustomEndDate.value)
  const q = kpiSearchQuery.value.trim().toLowerCase()

  return props.payments.filter(p => {
    if (p.is_withdrawal || p.is_discount || Number(p.amount) <= 0) return false

    // Date Range
    if (p.created_at) {
      const d = new Date(p.created_at)
      if (start && d < start) return false
      if (end && d > end) return false
    }

    // Method Filter
    if (kpiSelectedMethods.value.length > 0 && !kpiSelectedMethods.value.includes(p.method || '')) {
      return false
    }

    // Receiver Filter
    if (kpiSelectedReceivers.value.length > 0 && !kpiSelectedReceivers.value.includes(p.received_by || '')) {
      return false
    }

    // Student & Status Filters
    const s = getStudent(p.student_id)
    if (!matchesKpiStudentCriteria(p.student_id, s)) return false

    // Search Query
    if (q) {
      if (kpiSearchType.value === 'id' && !(p.student_id || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'name' && !(p.student_full_name || p.student_name || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'phone' && !(s?.phone1 || '').includes(q) && !(s?.phone2 || '').includes(q)) return false
      if (kpiSearchType.value === 'method' && !(p.method || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'coordinator' && !(s?.coordinator || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'receiver' && !(p.received_by || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'notes' && !(p.notes || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'all') {
        const match =
          (p.student_id || '').toLowerCase().includes(q) ||
          (p.student_full_name || p.student_name || '').toLowerCase().includes(q) ||
          (s?.phone1 || '').includes(q) ||
          (p.method || '').toLowerCase().includes(q) ||
          (p.received_by || '').toLowerCase().includes(q) ||
          (s?.coordinator || '').toLowerCase().includes(q) ||
          (p.notes || '').toLowerCase().includes(q)
        if (!match) return false
      }
    }

    return true
  }).sort((a, b) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
    return timeB - timeA
  })
})
const totalCollectedModalAmount = computed(() => {
  return filteredCollectedModalList.value.reduce((sum, p) => sum + (Number(p.amount) || 0), 0)
})

// 2. Debtor Students Filtered List
const filteredDebtModalList = computed(() => {
  const q = kpiSearchQuery.value.trim().toLowerCase()

  return props.students.filter(s => {
    const bal = Number(s.balance) || 0
    if (bal >= 0) return false

    // Status & Student Criteria
    if (!matchesKpiStudentCriteria(s.id, s)) return false

    // Search Query
    if (q) {
      if (kpiSearchType.value === 'id' && !(s.id || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'name' && !(s.full_name || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'phone' && !(s.phone1 || '').includes(q) && !(s.phone2 || '').includes(q)) return false
      if (kpiSearchType.value === 'coordinator' && !(s.coordinator || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'all') {
        const match =
          (s.id || '').toLowerCase().includes(q) ||
          (s.full_name || '').toLowerCase().includes(q) ||
          (s.phone1 || '').includes(q) ||
          (s.phone2 || '').includes(q) ||
          (s.coordinator || '').toLowerCase().includes(q) ||
          (s.tariff || '').toLowerCase().includes(q) ||
          (s.student_group || '').toLowerCase().includes(q)
        if (!match) return false
      }
    }

    return true
  }).sort((a, b) => (Number(a.balance) || 0) - (Number(b.balance) || 0))
})
const totalDebtModalAmount = computed(() => {
  return filteredDebtModalList.value.reduce((sum, s) => sum + Math.abs(Number(s.balance) || 0), 0)
})

// 3. Discount Filtered List
const filteredDiscountModalList = computed(() => {
  const { start, end } = getKpiDateRange(kpiDatePreset.value, kpiCustomStartDate.value, kpiCustomEndDate.value)
  const q = kpiSearchQuery.value.trim().toLowerCase()

  return props.payments.filter(p => {
    if (!p.is_discount) return false

    // Date Range
    if (p.created_at) {
      const d = new Date(p.created_at)
      if (start && d < start) return false
      if (end && d > end) return false
    }

    // Receiver Filter
    if (kpiSelectedReceivers.value.length > 0 && !kpiSelectedReceivers.value.includes(p.received_by || '')) {
      return false
    }

    // Student & Status Filters
    const s = getStudent(p.student_id)
    if (!matchesKpiStudentCriteria(p.student_id, s)) return false

    // Search Query
    if (q) {
      if (kpiSearchType.value === 'id' && !(p.student_id || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'name' && !(p.student_full_name || p.student_name || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'phone' && !(s?.phone1 || '').includes(q) && !(s?.phone2 || '').includes(q)) return false
      if (kpiSearchType.value === 'coordinator' && !(s?.coordinator || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'receiver' && !(p.received_by || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'notes' && !(p.notes || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'all') {
        const match =
          (p.student_id || '').toLowerCase().includes(q) ||
          (p.student_full_name || p.student_name || '').toLowerCase().includes(q) ||
          (s?.phone1 || '').includes(q) ||
          (p.received_by || '').toLowerCase().includes(q) ||
          (s?.coordinator || '').toLowerCase().includes(q) ||
          (p.notes || '').toLowerCase().includes(q)
        if (!match) return false
      }
    }

    return true
  }).sort((a, b) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
    return timeB - timeA
  })
})
const totalDiscountModalAmount = computed(() => {
  return filteredDiscountModalList.value.reduce((sum, p) => sum + Math.abs(Number(p.amount) || 0), 0)
})

// 4. Withdrawal Filtered List
const filteredWithdrawalModalList = computed(() => {
  const { start, end } = getKpiDateRange(kpiDatePreset.value, kpiCustomStartDate.value, kpiCustomEndDate.value)
  const q = kpiSearchQuery.value.trim().toLowerCase()

  return props.payments.filter(p => {
    if (!p.is_withdrawal && Number(p.amount) >= 0) return false

    // Date Range
    if (p.created_at) {
      const d = new Date(p.created_at)
      if (start && d < start) return false
      if (end && d > end) return false
    }

    // Method Filter
    if (kpiSelectedMethods.value.length > 0 && !kpiSelectedMethods.value.includes(p.method || '')) {
      return false
    }

    // Receiver Filter
    if (kpiSelectedReceivers.value.length > 0 && !kpiSelectedReceivers.value.includes(p.received_by || '')) {
      return false
    }

    // Student & Status Filters
    const s = getStudent(p.student_id)
    if (!matchesKpiStudentCriteria(p.student_id, s)) return false

    // Search Query
    if (q) {
      if (kpiSearchType.value === 'id' && !(p.student_id || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'name' && !(p.student_full_name || p.student_name || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'phone' && !(s?.phone1 || '').includes(q) && !(s?.phone2 || '').includes(q)) return false
      if (kpiSearchType.value === 'method' && !(p.method || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'coordinator' && !(s?.coordinator || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'receiver' && !(p.received_by || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'notes' && !(p.notes || '').toLowerCase().includes(q)) return false
      if (kpiSearchType.value === 'all') {
        const match =
          (p.student_id || '').toLowerCase().includes(q) ||
          (p.student_full_name || p.student_name || '').toLowerCase().includes(q) ||
          (s?.phone1 || '').includes(q) ||
          (p.method || '').toLowerCase().includes(q) ||
          (p.received_by || '').toLowerCase().includes(q) ||
          (s?.coordinator || '').toLowerCase().includes(q) ||
          (p.notes || '').toLowerCase().includes(q)
        if (!match) return false
      }
    }

    return true
  }).sort((a, b) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
    return timeB - timeA
  })
})
const totalWithdrawalModalAmount = computed(() => {
  return filteredWithdrawalModalList.value.reduce((sum, p) => sum + Math.abs(Number(p.amount) || 0), 0)
})

// Pagination
const currentModalTotalRecords = computed(() => {
  if (activeKpiModal.value === 'collected') return filteredCollectedModalList.value.length
  if (activeKpiModal.value === 'debt') return filteredDebtModalList.value.length
  if (activeKpiModal.value === 'discount') return filteredDiscountModalList.value.length
  if (activeKpiModal.value === 'withdraw') return filteredWithdrawalModalList.value.length
  return 0
})

const kpiTotalPages = computed(() => {
  if (kpiPageSize.value === -1) return 1
  return Math.max(1, Math.ceil(currentModalTotalRecords.value / kpiPageSize.value))
})

const paginatedCollectedModalList = computed(() => {
  if (kpiPageSize.value === -1) return filteredCollectedModalList.value
  const start = (kpiPage.value - 1) * kpiPageSize.value
  return filteredCollectedModalList.value.slice(start, start + kpiPageSize.value)
})

const paginatedDebtModalList = computed(() => {
  if (kpiPageSize.value === -1) return filteredDebtModalList.value
  const start = (kpiPage.value - 1) * kpiPageSize.value
  return filteredDebtModalList.value.slice(start, start + kpiPageSize.value)
})

const paginatedDiscountModalList = computed(() => {
  if (kpiPageSize.value === -1) return filteredDiscountModalList.value
  const start = (kpiPage.value - 1) * kpiPageSize.value
  return filteredDiscountModalList.value.slice(start, start + kpiPageSize.value)
})

const paginatedWithdrawalModalList = computed(() => {
  if (kpiPageSize.value === -1) return filteredWithdrawalModalList.value
  const start = (kpiPage.value - 1) * kpiPageSize.value
  return filteredWithdrawalModalList.value.slice(start, start + kpiPageSize.value)
})

// Active Filter Chips
const hasActiveKpiFilters = computed(() => {
  return (
    kpiDatePreset.value !== 'all' ||
    kpiSelectedStatuses.value.length > 0 ||
    kpiSelectedTariffs.value.length > 0 ||
    kpiSelectedGroups.value.length > 0 ||
    kpiSelectedCoordinators.value.length > 0 ||
    kpiSelectedLevels.value.length > 0 ||
    kpiSelectedIds.value.length > 0 ||
    kpiSelectedMethods.value.length > 0 ||
    kpiSelectedReceivers.value.length > 0 ||
    kpiSearchQuery.value.trim() !== ''
  )
})

const activeKpiFilterChips = computed(() => {
  const chips: { key: string; label: string; clear: () => void }[] = []
  if (kpiDatePreset.value !== 'all') {
    chips.push({
      key: 'date',
      label: `Date: ${kpiDatePreset.value.replace('_', ' ').toUpperCase()}`,
      clear: () => { kpiDatePreset.value = 'all'; kpiCustomStartDate.value = ''; kpiCustomEndDate.value = '' }
    })
  }
  if (kpiSelectedStatuses.value.length > 0) {
    chips.push({
      key: 'status',
      label: `Status: ${kpiSelectedStatuses.value.join(', ')}`,
      clear: () => { kpiSelectedStatuses.value = [] }
    })
  }
  if (kpiSelectedTariffs.value.length > 0) {
    chips.push({
      key: 'tariff',
      label: kpiSelectedTariffs.value.length === 1 ? `Tariff: ${kpiSelectedTariffs.value[0]}` : `Tariff (${kpiSelectedTariffs.value.length})`,
      clear: () => { kpiSelectedTariffs.value = [] }
    })
  }
  if (kpiSelectedGroups.value.length > 0) {
    chips.push({
      key: 'group',
      label: kpiSelectedGroups.value.length === 1 ? `Group: ${kpiSelectedGroups.value[0]}` : `Group (${kpiSelectedGroups.value.length})`,
      clear: () => { kpiSelectedGroups.value = [] }
    })
  }
  if (kpiSelectedCoordinators.value.length > 0) {
    chips.push({
      key: 'coordinator',
      label: kpiSelectedCoordinators.value.length === 1 ? `Coordinator: ${kpiSelectedCoordinators.value[0]}` : `Coordinator (${kpiSelectedCoordinators.value.length})`,
      clear: () => { kpiSelectedCoordinators.value = [] }
    })
  }
  if (kpiSelectedLevels.value.length > 0) {
    chips.push({
      key: 'level',
      label: kpiSelectedLevels.value.length === 1 ? `Level: ${kpiSelectedLevels.value[0]}` : `Level (${kpiSelectedLevels.value.length})`,
      clear: () => { kpiSelectedLevels.value = [] }
    })
  }
  if (kpiSelectedIds.value.length > 0) {
    chips.push({
      key: 'id',
      label: `ID: ${kpiSelectedIds.value.join(', ')}`,
      clear: () => { kpiSelectedIds.value = [] }
    })
  }
  if (kpiSelectedMethods.value.length > 0) {
    chips.push({
      key: 'method',
      label: kpiSelectedMethods.value.length === 1 ? `Method: ${kpiSelectedMethods.value[0]}` : `Method (${kpiSelectedMethods.value.length})`,
      clear: () => { kpiSelectedMethods.value = [] }
    })
  }
  if (kpiSelectedReceivers.value.length > 0) {
    chips.push({
      key: 'receiver',
      label: kpiSelectedReceivers.value.length === 1 ? `Receiver: ${kpiSelectedReceivers.value[0]}` : `Receiver (${kpiSelectedReceivers.value.length})`,
      clear: () => { kpiSelectedReceivers.value = [] }
    })
  }
  if (kpiSearchQuery.value.trim() !== '') {
    chips.push({
      key: 'search',
      label: `Search: "${kpiSearchQuery.value.trim()}"`,
      clear: () => { kpiSearchQuery.value = '' }
    })
  }
  return chips
})

const clearAllKpiFilters = () => {
  kpiDatePreset.value = 'all'
  kpiCustomStartDate.value = ''
  kpiCustomEndDate.value = ''
  kpiSelectedStatuses.value = []
  kpiSelectedTariffs.value = []
  kpiSelectedGroups.value = []
  kpiSelectedCoordinators.value = []
  kpiSelectedLevels.value = []
  kpiSelectedIds.value = []
  kpiSelectedMethods.value = []
  kpiSelectedReceivers.value = []
  kpiSearchQuery.value = ''
  kpiSearchType.value = 'all'
  kpiPage.value = 1
}

// ── Export Modal-Specific Excel Files ────────────────────────────────
const exportCollectedExcel = async () => {
  if (filteredCollectedModalList.value.length === 0) {
    alert('No collected payment records to export!')
    return
  }
  const XLSX = await import('xlsx-js-style')
  const pad = (n: number) => String(n).padStart(2, '0')
  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }

  const data = filteredCollectedModalList.value.map((p, index) => {
    const s = getStudent(p.student_id)
    return {
      No: index + 1,
      'Receipt ID': p.id ? String(p.id).toUpperCase() : '',
      'Student ID': p.student_id || '—',
      'Student Full Name': p.student_full_name || p.student_name || 'General',
      'Phone Number': s?.phone1 || '—',
      'Tariff': s?.tariff || '—',
      'Group': s?.student_group || '—',
      'Coordinator': s?.coordinator || '—',
      'Level': s?.level || '—',
      'Status': s?.is_deleted ? 'Archive' : 'Active',
      'Payment Method': p.method || '—',
      'Received By': p.received_by || '—',
      'Amount (UZS)': Number(p.amount) || 0,
      'Date & Time': formatDateTime(p.created_at),
      'Notes': p.notes || ''
    }
  })

  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(data)
  ws['!cols'] = [
    { wch: 6 }, { wch: 20 }, { wch: 14 }, { wch: 30 }, { wch: 18 },
    { wch: 18 }, { wch: 16 }, { wch: 18 }, { wch: 16 }, { wch: 12 },
    { wch: 18 }, { wch: 18 }, { wch: 18 }, { wch: 20 }, { wch: 30 }
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'Total Collected')
  const dateStr = new Date().toISOString().split('T')[0]
  XLSX.writeFile(wb, `Collected_Payments_${kpiDatePreset.value}_${dateStr}.xlsx`)
}

const exportDebtExcel = async () => {
  if (filteredDebtModalList.value.length === 0) {
    alert('No debtor student records to export!')
    return
  }
  const XLSX = await import('xlsx-js-style')
  const data = filteredDebtModalList.value.map((s, index) => {
    return {
      No: index + 1,
      'Student ID': s.id || '—',
      'Student Full Name': s.full_name || '—',
      'Phone Number': s.phone1 || '—',
      'Tariff': s.tariff || '—',
      'Group': s.student_group || '—',
      'Coordinator': s.coordinator || '—',
      'Level': s.level || '—',
      'Outstanding Debt (UZS)': Math.abs(Number(s.balance) || 0),
      'Discount (UZS)': Number(s.discount) || 0,
      'Status': s.is_deleted ? 'Archive' : 'Active'
    }
  })

  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(data)
  ws['!cols'] = [
    { wch: 6 }, { wch: 14 }, { wch: 30 }, { wch: 18 },
    { wch: 18 }, { wch: 16 }, { wch: 18 }, { wch: 16 },
    { wch: 22 }, { wch: 18 }, { wch: 12 }
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'Outstanding Debtors')
  const dateStr = new Date().toISOString().split('T')[0]
  XLSX.writeFile(wb, `Outstanding_Debt_Report_${dateStr}.xlsx`)
}

const exportDiscountExcel = async () => {
  if (filteredDiscountModalList.value.length === 0) {
    alert('No discount records to export!')
    return
  }
  const XLSX = await import('xlsx-js-style')
  const pad = (n: number) => String(n).padStart(2, '0')
  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }

  const data = filteredDiscountModalList.value.map((p, index) => {
    const s = getStudent(p.student_id)
    return {
      No: index + 1,
      'Record ID': p.id ? String(p.id).toUpperCase() : '',
      'Student ID': p.student_id || '—',
      'Student Full Name': p.student_full_name || p.student_name || 'General',
      'Phone Number': s?.phone1 || '—',
      'Tariff': s?.tariff || '—',
      'Group': s?.student_group || '—',
      'Coordinator': s?.coordinator || '—',
      'Status': s?.is_deleted ? 'Archive' : 'Active',
      'Discount Amount (UZS)': Math.abs(Number(p.amount) || 0),
      'Granted By': p.received_by || '—',
      'Date & Time': formatDateTime(p.created_at),
      'Reason / Notes': p.notes || ''
    }
  })

  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(data)
  ws['!cols'] = [
    { wch: 6 }, { wch: 20 }, { wch: 14 }, { wch: 30 }, { wch: 18 },
    { wch: 18 }, { wch: 16 }, { wch: 18 }, { wch: 12 }, { wch: 22 },
    { wch: 18 }, { wch: 20 }, { wch: 30 }
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'Discounts Given')
  const dateStr = new Date().toISOString().split('T')[0]
  XLSX.writeFile(wb, `Discounts_Report_${kpiDatePreset.value}_${dateStr}.xlsx`)
}

const exportWithdrawalExcel = async () => {
  if (filteredWithdrawalModalList.value.length === 0) {
    alert('No withdrawal records to export!')
    return
  }
  const XLSX = await import('xlsx-js-style')
  const pad = (n: number) => String(n).padStart(2, '0')
  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }

  const data = filteredWithdrawalModalList.value.map((p, index) => {
    const s = getStudent(p.student_id)
    return {
      No: index + 1,
      'Withdrawal ID': p.id ? String(p.id).toUpperCase() : '',
      'Student ID': p.student_id || '—',
      'Student Full Name': p.student_full_name || p.student_name || 'General',
      'Phone Number': s?.phone1 || '—',
      'Tariff': s?.tariff || '—',
      'Group': s?.student_group || '—',
      'Coordinator': s?.coordinator || '—',
      'Status': s?.is_deleted ? 'Archive' : 'Active',
      'Payment Method': p.method || '—',
      'Authorized / Processed By': p.received_by || '—',
      'Withdrawal Amount (UZS)': Math.abs(Number(p.amount) || 0),
      'Date & Time': formatDateTime(p.created_at),
      'Reason / Notes': p.notes || ''
    }
  })

  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(data)
  ws['!cols'] = [
    { wch: 6 }, { wch: 20 }, { wch: 14 }, { wch: 30 }, { wch: 18 },
    { wch: 18 }, { wch: 16 }, { wch: 18 }, { wch: 12 }, { wch: 18 },
    { wch: 22 }, { wch: 22 }, { wch: 20 }, { wch: 30 }
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'Withdrawals')
  const dateStr = new Date().toISOString().split('T')[0]
  XLSX.writeFile(wb, `Withdrawals_Report_${kpiDatePreset.value}_${dateStr}.xlsx`)
}
</script>

<template>
  <div class="flex flex-col gap-5 select-none text-xs">
    <!-- ── Top Header Banner with Lock & Export ─────────────────────────── -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-transparent dark:from-blue-950/40 dark:via-indigo-950/30 dark:to-transparent border border-blue-200/60 dark:border-blue-900/40 rounded-2xl p-4 shadow-2xs">
      <div class="flex items-center gap-3">
        <div class="h-10 w-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
          <DollarSign class="h-5 w-5 stroke-[2.5]" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h2 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
              Executive Financial Overview
            </h2>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              Authorized
            </span>
          </div>
          <p class="text-[11px] text-zinc-500 dark:text-zinc-400">
            Real-time analytics, revenue collection, outstanding debt, and cashier reconciliations.
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="exportFinanceReportToExcel"
          class="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl border border-emerald-300 dark:border-emerald-700/60 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-all cursor-pointer shadow-2xs"
          title="Export Filtered Financial Report to Excel"
        >
          <FileSpreadsheet class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <span>Export Excel</span>
        </button>

        <button
          type="button"
          @click="emit('lock-finance')"
          class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all cursor-pointer shadow-2xs"
          title="Lock Finance Dashboard Session"
        >
          <Lock class="h-3.5 w-3.5 text-amber-500" />
          <span>Lock Tab</span>
        </button>
      </div>
    </div>

    <!-- ── KPI Cards Grid ──────────────────────────────────────────────── -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
      <!-- 1. Total Collected (Today & Selected Period) -->
      <div
        @click="openKpiModal('collected')"
        class="rounded-2xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs flex flex-col justify-between relative overflow-hidden cursor-pointer hover:border-blue-400 dark:hover:border-blue-600 hover:shadow-md transition-all group"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-1.5">
              <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                Total Collected
              </span>
              <ExternalLink class="h-3 w-3 text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 font-mono tracking-tight">
                {{ formatUZS(periodMetrics.totalCollected) }}
              </span>
              <span class="text-[11px] font-bold text-zinc-400 font-mono">UZS</span>
            </div>
            <span class="text-[10.5px] font-semibold text-blue-600 dark:text-blue-400">
              {{ selectedDatePreset === 'all' ? `All Time (${periodMetrics.collectedTxCount} payments)` : selectedDatePreset === 'this_month' ? `This Month (${periodMetrics.collectedTxCount} payments)` : `${selectedDatePreset.replace('_', ' ').toUpperCase()} (${periodMetrics.collectedTxCount} payments)` }}
            </span>
          </div>
          <div class="h-9 w-9 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center group-hover:scale-110 transition-transform">
            <TrendingUp class="h-4.5 w-4.5" />
          </div>
        </div>

        <div class="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px]">
          <span class="text-zinc-500 dark:text-zinc-400">Today:</span>
          <span class="font-bold text-emerald-600 dark:text-emerald-400 font-mono">
            +{{ formatUZS(todayMetrics.collected) }} UZS
          </span>
        </div>
      </div>

      <!-- 2. Total Outstanding Debt -->
      <div
        @click="openKpiModal('debt')"
        class="rounded-2xl border border-red-200/60 dark:border-red-950/50 bg-white dark:bg-[#111315] p-4 shadow-2xs flex flex-col justify-between relative overflow-hidden cursor-pointer hover:border-red-400 dark:hover:border-red-600 hover:shadow-md transition-all group"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-1.5">
              <span class="text-[11px] font-bold uppercase tracking-wider text-red-600 dark:text-red-400">
                Outstanding Debt
              </span>
              <ExternalLink class="h-3 w-3 text-red-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-xl font-extrabold text-red-600 dark:text-red-400 font-mono tracking-tight">
                -{{ formatUZS(debtMetrics.totalDebt) }}
              </span>
              <span class="text-[11px] font-bold text-zinc-400 font-mono">UZS</span>
            </div>
            <span class="text-[10.5px] font-semibold text-zinc-500 dark:text-zinc-400">
              Across {{ debtMetrics.debtorCount }} debtor students
            </span>
          </div>
          <div class="h-9 w-9 rounded-xl bg-red-500/10 text-red-600 dark:text-red-400 flex items-center justify-center group-hover:scale-110 transition-transform">
            <AlertCircle class="h-4.5 w-4.5" />
          </div>
        </div>

        <div class="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px]">
          <span class="text-zinc-500 dark:text-zinc-400">Fully Paid:</span>
          <span class="font-bold text-zinc-700 dark:text-zinc-300 font-mono">
            {{ debtMetrics.fullyPaidCount }} of {{ debtMetrics.totalActiveStudents }} active
          </span>
        </div>
      </div>

      <!-- 3. Total Discounts Given -->
      <div
        @click="openKpiModal('discount')"
        class="rounded-2xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs flex flex-col justify-between relative overflow-hidden cursor-pointer hover:border-pink-400 dark:hover:border-pink-600 hover:shadow-md transition-all group"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-1.5">
              <span class="text-[11px] font-bold uppercase tracking-wider text-pink-600 dark:text-pink-400">
                Discounts Given
              </span>
              <ExternalLink class="h-3 w-3 text-pink-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-xl font-extrabold text-pink-600 dark:text-pink-400 font-mono tracking-tight">
                {{ formatUZS(periodMetrics.totalDiscounts) }}
              </span>
              <span class="text-[11px] font-bold text-zinc-400 font-mono">UZS</span>
            </div>
            <span class="text-[10.5px] font-semibold text-zinc-500 dark:text-zinc-400">
              In selected period ({{ periodMetrics.discountTxCount }} promos)
            </span>
          </div>
          <div class="h-9 w-9 rounded-xl bg-pink-500/10 text-pink-600 dark:text-pink-400 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Percent class="h-4.5 w-4.5" />
          </div>
        </div>

        <div class="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px]">
          <span class="text-zinc-500 dark:text-zinc-400">Selected Type:</span>
          <span class="font-bold text-zinc-700 dark:text-zinc-300 capitalize">
            {{ selectedType }}
          </span>
        </div>
      </div>

      <!-- 4. Total Withdrawals & Net Cashflow -->
      <div
        @click="openKpiModal('withdraw')"
        class="rounded-2xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs flex flex-col justify-between relative overflow-hidden cursor-pointer hover:border-amber-400 dark:hover:border-amber-600 hover:shadow-md transition-all group"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-1.5">
              <span class="text-[11px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                Total Withdrawals
              </span>
              <ExternalLink class="h-3 w-3 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-xl font-extrabold text-amber-600 dark:text-amber-400 font-mono tracking-tight">
                -{{ formatUZS(periodMetrics.totalWithdrawals) }}
              </span>
              <span class="text-[11px] font-bold text-zinc-400 font-mono">UZS</span>
            </div>
            <span class="text-[10.5px] font-semibold text-zinc-500 dark:text-zinc-400">
              {{ periodMetrics.withdrawalTxCount }} refunds/deductions
            </span>
          </div>
          <div class="h-9 w-9 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center group-hover:scale-110 transition-transform">
            <TrendingDown class="h-4.5 w-4.5" />
          </div>
        </div>

        <div class="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px]">
          <span class="text-zinc-500 dark:text-zinc-400">Net Period Cashflow:</span>
          <span
            class="font-bold font-mono"
            :class="periodMetrics.netCashflow >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'"
          >
            {{ periodMetrics.netCashflow >= 0 ? '+' : '' }}{{ formatUZS(periodMetrics.netCashflow) }} UZS
          </span>
        </div>
      </div>
    </div>

    <!-- ── Filter Controls Bar ─────────────────────────────────────────── -->
    <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs space-y-3">
      <!-- Row 1: Date Range Presets -->
      <div class="flex flex-wrap items-center justify-between gap-2.5">
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 mr-1 flex items-center gap-1">
            <Calendar class="h-3.5 w-3.5" />
            <span>Range:</span>
          </span>
          <button
            v-for="preset in [
              { key: 'today', label: 'Today' },
              { key: 'yesterday', label: 'Yesterday' },
              { key: 'this_week', label: 'This Week' },
              { key: 'this_month', label: 'This Month' },
              { key: 'last_month', label: 'Last Month' },
              { key: 'this_year', label: 'This Year' },
              { key: 'all', label: 'All Time' },
              { key: 'custom', label: 'Custom Range' }
            ]"
            :key="preset.key"
            type="button"
            @click="selectedDatePreset = preset.key as DatePreset"
            class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer select-none shrink-0"
            :class="selectedDatePreset === preset.key
              ? 'bg-blue-600 text-white shadow-xs'
              : 'border border-zinc-200 dark:border-zinc-750 bg-zinc-50 dark:bg-zinc-850 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'"
          >
            {{ preset.label }}
          </button>
        </div>
      </div>

      <!-- Custom Date Pickers (Shown if Custom Range is active) -->
      <div v-if="selectedDatePreset === 'custom'" class="flex flex-wrap items-center gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800 animate-in fade-in duration-150">
        <div class="flex items-center gap-2">
          <label class="text-[11px] font-bold text-zinc-500 dark:text-zinc-400">From:</label>
          <input
            type="date"
            v-model="customStartDate"
            class="rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 px-2.5 py-1 text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-[11px] font-bold text-zinc-500 dark:text-zinc-400">To:</label>
          <input
            type="date"
            v-model="customEndDate"
            class="rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 px-2.5 py-1 text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <!-- Row 2: Search + Method + Receiver + Type Dropdowns -->
      <div class="flex flex-wrap items-center gap-2.5 pt-2 border-t border-zinc-100 dark:border-zinc-800">
        <!-- Search Input -->
        <div class="relative flex-1 min-w-[200px]">
          <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400 pointer-events-none" />
          <input
            type="text"
            v-model="searchFinance"
            placeholder="Search by student name, ID, receiver, notes..."
            class="w-full pl-9 pr-4 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <!-- Payment Method Filter -->
        <div class="relative min-w-[140px]">
          <select
            v-model="selectedMethod"
            class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 font-semibold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="all">All Methods</option>
            <option v-for="m in paymentMethods" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>

        <!-- Receiver Filter -->
        <div class="relative min-w-[140px]">
          <select
            v-model="selectedReceiver"
            class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 font-semibold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="all">All Receivers</option>
            <option v-for="r in paymentReceivers" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>

        <!-- Transaction Type Filter -->
        <div class="relative min-w-[150px]">
          <select
            v-model="selectedType"
            class="w-full px-3 py-2 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 font-semibold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="all">All Transaction Types</option>
            <option value="payments">Payments Only (+)</option>
            <option value="withdrawals">Withdrawals Only (-)</option>
            <option value="discounts">Discounts Only</option>
          </select>
        </div>
      </div>

      <!-- Row 3: Multi-Select Filter Pills (Tariff, Group, Coordinator, Level, ID) -->
      <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
        <div class="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-zinc-400 mr-1 select-none">
          <Filter class="h-3.5 w-3.5" />
          <span>Filters:</span>
        </div>

        <!-- 1. Tariff Filter Dropdown -->
        <div class="relative" ref="tariffRef">
          <button
            type="button"
            @click="toggleDropdown('tariff')"
            class="px-3 py-1.5 text-xs border rounded-xl cursor-pointer flex items-center justify-between gap-2 min-w-[125px] select-none transition-all shadow-2xs font-semibold"
            :class="[
              isTariffOpen
                ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
                : !isAllTariffsSelected
                  ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/30'
                  : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 text-zinc-700 dark:text-zinc-300 hover:border-blue-400'
            ]"
          >
            <div class="flex items-center gap-1.5 truncate">
              <Tag class="h-3.5 w-3.5 text-zinc-400 shrink-0" />
              <span class="truncate">
                {{ isAllTariffsSelected
                  ? 'All Tariffs'
                  : effectiveSelectedTariffs.length === 0
                    ? 'Tariff (None)'
                    : `Tariff (${effectiveSelectedTariffs.length}/${availableTariffs.length})` }}
              </span>
            </div>
            <ChevronDown
              class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200 shrink-0"
              :class="isTariffOpen ? 'rotate-180 text-blue-600' : ''"
            />
          </button>

          <div
            v-if="isTariffOpen"
            class="absolute left-0 mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 flex flex-col"
          >
            <div v-if="availableTariffs.length > 5" class="px-2.5 pb-1.5">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-400 pointer-events-none" />
                <input
                  type="text"
                  v-model="tariffSearch"
                  placeholder="Search tariff..."
                  class="w-full pl-7 pr-2 py-1 text-[11px] border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div
              @click="toggleAllTariffs"
              class="px-3.5 py-1.5 flex items-center justify-between cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200 select-none"
            >
              <div class="flex items-center gap-2.5">
                <input
                  type="checkbox"
                  :checked="isAllTariffsSelected"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span>Select All</span>
              </div>
              <span class="text-[10.5px] font-mono text-zinc-400 font-normal">
                {{ effectiveSelectedTariffs.length }}/{{ availableTariffs.length }}
              </span>
            </div>

            <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />

            <div class="overflow-y-auto max-h-56">
              <div
                v-for="opt in filteredAvailableTariffs"
                :key="opt"
                @click="toggleTariff(opt)"
                class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-medium text-zinc-700 dark:text-zinc-300 select-none"
              >
                <input
                  type="checkbox"
                  :checked="isTariffSelected(opt)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span class="truncate">{{ opt }}</span>
              </div>
              <div v-if="filteredAvailableTariffs.length === 0" class="px-3.5 py-3 text-center text-[11px] text-zinc-400">
                No matches
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Group Filter Dropdown -->
        <div class="relative" ref="groupRef">
          <button
            type="button"
            @click="toggleDropdown('group')"
            class="px-3 py-1.5 text-xs border rounded-xl cursor-pointer flex items-center justify-between gap-2 min-w-[120px] select-none transition-all shadow-2xs font-semibold"
            :class="[
              isGroupOpen
                ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
                : !isAllGroupsSelected
                  ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/30'
                  : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 text-zinc-700 dark:text-zinc-300 hover:border-blue-400'
            ]"
          >
            <div class="flex items-center gap-1.5 truncate">
              <Users class="h-3.5 w-3.5 text-zinc-400 shrink-0" />
              <span class="truncate">
                {{ isAllGroupsSelected
                  ? 'All Groups'
                  : effectiveSelectedGroups.length === 0
                    ? 'Group (None)'
                    : `Group (${effectiveSelectedGroups.length}/${availableGroups.length})` }}
              </span>
            </div>
            <ChevronDown
              class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200 shrink-0"
              :class="isGroupOpen ? 'rotate-180 text-blue-600' : ''"
            />
          </button>

          <div
            v-if="isGroupOpen"
            class="absolute left-0 mt-1.5 w-56 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 flex flex-col"
          >
            <div v-if="availableGroups.length > 5" class="px-2.5 pb-1.5">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-400 pointer-events-none" />
                <input
                  type="text"
                  v-model="groupSearch"
                  placeholder="Search group..."
                  class="w-full pl-7 pr-2 py-1 text-[11px] border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div
              @click="toggleAllGroups"
              class="px-3.5 py-1.5 flex items-center justify-between cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200 select-none"
            >
              <div class="flex items-center gap-2.5">
                <input
                  type="checkbox"
                  :checked="isAllGroupsSelected"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span>Select All</span>
              </div>
              <span class="text-[10.5px] font-mono text-zinc-400 font-normal">
                {{ effectiveSelectedGroups.length }}/{{ availableGroups.length }}
              </span>
            </div>

            <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />

            <div class="overflow-y-auto max-h-56">
              <div
                v-for="opt in filteredAvailableGroups"
                :key="opt"
                @click="toggleGroup(opt)"
                class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-medium text-zinc-700 dark:text-zinc-300 select-none"
              >
                <input
                  type="checkbox"
                  :checked="isGroupSelected(opt)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span class="truncate">{{ opt }}</span>
              </div>
              <div v-if="filteredAvailableGroups.length === 0" class="px-3.5 py-3 text-center text-[11px] text-zinc-400">
                No matches
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Coordinator Filter Dropdown -->
        <div class="relative" ref="coordinatorRef">
          <button
            type="button"
            @click="toggleDropdown('coordinator')"
            class="px-3 py-1.5 text-xs border rounded-xl cursor-pointer flex items-center justify-between gap-2 min-w-[145px] select-none transition-all shadow-2xs font-semibold"
            :class="[
              isCoordinatorOpen
                ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
                : !isAllCoordinatorsSelected
                  ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/30'
                  : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 text-zinc-700 dark:text-zinc-300 hover:border-blue-400'
            ]"
          >
            <div class="flex items-center gap-1.5 truncate">
              <UserCheck class="h-3.5 w-3.5 text-zinc-400 shrink-0" />
              <span class="truncate">
                {{ isAllCoordinatorsSelected
                  ? 'All Coordinators'
                  : effectiveSelectedCoordinators.length === 0
                    ? 'Coordinator (None)'
                    : `Coordinator (${effectiveSelectedCoordinators.length}/${availableCoordinators.length})` }}
              </span>
            </div>
            <ChevronDown
              class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200 shrink-0"
              :class="isCoordinatorOpen ? 'rotate-180 text-blue-600' : ''"
            />
          </button>

          <div
            v-if="isCoordinatorOpen"
            class="absolute left-0 mt-1.5 w-60 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 flex flex-col"
          >
            <div v-if="availableCoordinators.length > 5" class="px-2.5 pb-1.5">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-400 pointer-events-none" />
                <input
                  type="text"
                  v-model="coordinatorSearch"
                  placeholder="Search coordinator..."
                  class="w-full pl-7 pr-2 py-1 text-[11px] border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div
              @click="toggleAllCoordinators"
              class="px-3.5 py-1.5 flex items-center justify-between cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200 select-none"
            >
              <div class="flex items-center gap-2.5">
                <input
                  type="checkbox"
                  :checked="isAllCoordinatorsSelected"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span>Select All</span>
              </div>
              <span class="text-[10.5px] font-mono text-zinc-400 font-normal">
                {{ effectiveSelectedCoordinators.length }}/{{ availableCoordinators.length }}
              </span>
            </div>

            <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />

            <div class="overflow-y-auto max-h-56">
              <div
                v-for="opt in filteredAvailableCoordinators"
                :key="opt"
                @click="toggleCoordinator(opt)"
                class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-medium text-zinc-700 dark:text-zinc-300 select-none"
              >
                <input
                  type="checkbox"
                  :checked="isCoordinatorSelected(opt)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span class="truncate">{{ opt }}</span>
              </div>
              <div v-if="filteredAvailableCoordinators.length === 0" class="px-3.5 py-3 text-center text-[11px] text-zinc-400">
                No matches
              </div>
            </div>
          </div>
        </div>

        <!-- 4. Level Filter Dropdown -->
        <div class="relative" ref="levelRef">
          <button
            type="button"
            @click="toggleDropdown('level')"
            class="px-3 py-1.5 text-xs border rounded-xl cursor-pointer flex items-center justify-between gap-2 min-w-[120px] select-none transition-all shadow-2xs font-semibold"
            :class="[
              isLevelOpen
                ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
                : !isAllLevelsSelected
                  ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/30'
                  : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 text-zinc-700 dark:text-zinc-300 hover:border-blue-400'
            ]"
          >
            <div class="flex items-center gap-1.5 truncate">
              <GraduationCap class="h-3.5 w-3.5 text-zinc-400 shrink-0" />
              <span class="truncate">
                {{ isAllLevelsSelected
                  ? 'All Levels'
                  : effectiveSelectedLevels.length === 0
                    ? 'Level (None)'
                    : `Level (${effectiveSelectedLevels.length}/${availableLevels.length})` }}
              </span>
            </div>
            <ChevronDown
              class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200 shrink-0"
              :class="isLevelOpen ? 'rotate-180 text-blue-600' : ''"
            />
          </button>

          <div
            v-if="isLevelOpen"
            class="absolute left-0 mt-1.5 w-56 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 flex flex-col"
          >
            <div v-if="availableLevels.length > 5" class="px-2.5 pb-1.5">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-400 pointer-events-none" />
                <input
                  type="text"
                  v-model="levelSearch"
                  placeholder="Search level..."
                  class="w-full pl-7 pr-2 py-1 text-[11px] border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div
              @click="toggleAllLevels"
              class="px-3.5 py-1.5 flex items-center justify-between cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200 select-none"
            >
              <div class="flex items-center gap-2.5">
                <input
                  type="checkbox"
                  :checked="isAllLevelsSelected"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span>Select All</span>
              </div>
              <span class="text-[10.5px] font-mono text-zinc-400 font-normal">
                {{ effectiveSelectedLevels.length }}/{{ availableLevels.length }}
              </span>
            </div>

            <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />

            <div class="overflow-y-auto max-h-56">
              <div
                v-for="opt in filteredAvailableLevels"
                :key="opt"
                @click="toggleLevel(opt)"
                class="px-3.5 py-1.5 flex items-center gap-2.5 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-medium text-zinc-700 dark:text-zinc-300 select-none"
              >
                <input
                  type="checkbox"
                  :checked="isLevelSelected(opt)"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span class="truncate">{{ opt }}</span>
              </div>
              <div v-if="filteredAvailableLevels.length === 0" class="px-3.5 py-3 text-center text-[11px] text-zinc-400">
                No matches
              </div>
            </div>
          </div>
        </div>

        <!-- 5. ID Filter Dropdown -->
        <div class="relative" ref="idRef">
          <button
            type="button"
            @click="toggleDropdown('id')"
            class="px-3 py-1.5 text-xs border rounded-xl cursor-pointer flex items-center justify-between gap-2 min-w-[115px] select-none transition-all shadow-2xs font-semibold"
            :class="[
              isIdOpen
                ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 ring-1 ring-blue-600'
                : !isAllIdsSelected
                  ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/30'
                  : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 text-zinc-700 dark:text-zinc-300 hover:border-blue-400'
            ]"
          >
            <div class="flex items-center gap-1.5 truncate">
              <Hash class="h-3.5 w-3.5 text-zinc-400 shrink-0" />
              <span class="truncate">
                {{ isAllIdsSelected
                  ? 'All IDs'
                  : effectiveSelectedIds.length === 0
                    ? 'ID (None)'
                    : `ID (${effectiveSelectedIds.length}/${availableIds.length})` }}
              </span>
            </div>
            <ChevronDown
              class="h-3.5 w-3.5 text-zinc-400 transition-transform duration-200 shrink-0"
              :class="isIdOpen ? 'rotate-180 text-blue-600' : ''"
            />
          </button>

          <div
            v-if="isIdOpen"
            class="absolute left-0 mt-1.5 w-56 rounded-xl border border-zinc-200 dark:border-zinc-750 bg-white dark:bg-[#181a1d] shadow-xl py-2 z-40 max-h-80 flex flex-col"
          >
            <div class="px-2.5 pb-1.5">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-400 pointer-events-none" />
                <input
                  type="text"
                  v-model="idSearch"
                  placeholder="Search ID prefix (CF, D, YU)..."
                  class="w-full pl-7 pr-2 py-1 text-[11px] border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850 rounded-lg text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div
              @click="toggleAllIds"
              class="px-3.5 py-1.5 flex items-center justify-between cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-bold text-zinc-800 dark:text-zinc-200 select-none"
            >
              <div class="flex items-center gap-2.5">
                <input
                  type="checkbox"
                  :checked="isAllIdsSelected"
                  class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none"
                />
                <span>Select All</span>
              </div>
              <span class="text-[10.5px] font-mono text-zinc-400 font-normal">
                {{ effectiveSelectedIds.length }}/{{ availableIds.length }}
              </span>
            </div>

            <div class="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />

            <div class="overflow-y-auto max-h-56">
              <div
                v-for="opt in filteredAvailableIds"
                :key="opt"
                @click="toggleId(opt)"
                class="px-3.5 py-1.5 flex items-center justify-between gap-2 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-xs font-semibold text-zinc-800 dark:text-zinc-200 select-none"
              >
                <div class="flex items-center gap-2.5 truncate">
                  <input
                    type="checkbox"
                    :checked="isIdSelected(opt)"
                    class="h-3.5 w-3.5 rounded border-zinc-300 text-blue-600 focus:ring-blue-500 cursor-pointer pointer-events-none shrink-0"
                  />
                  <span
                    class="font-mono font-extrabold text-[12.5px]"
                    :class="opt === 'No ID' ? 'text-zinc-400' : 'text-[#0066cc] dark:text-blue-400'"
                  >
                    {{ opt }}
                  </span>
                </div>
                <span class="text-[10.5px] font-mono text-zinc-400 font-normal">
                  {{ idPrefixStudentCounts.get(opt) || 0 }} {{ (idPrefixStudentCounts.get(opt) || 0) === 1 ? 'student' : 'students' }}
                </span>
              </div>
              <div v-if="filteredAvailableIds.length === 0" class="px-3.5 py-3 text-center text-[11px] text-zinc-400">
                No matching ID prefixes
              </div>
            </div>
          </div>
        </div>

        <!-- Reset Student Filters Button -->
        <button
          v-if="hasActiveStudentFilters"
          type="button"
          @click="resetStudentFilters"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-xl border border-red-200 dark:border-red-900/40 bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 transition-all cursor-pointer shadow-2xs"
          title="Reset all 5 student filters back to All"
        >
          <RotateCcw class="h-3.5 w-3.5" />
          <span>Reset Filters</span>
        </button>
      </div>
    </div>

    <!-- ── Breakdown Sections: Method & Cashier Breakdown ──────────────── -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Method Breakdown Card -->
      <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <CreditCard class="h-4 w-4 text-blue-600" />
            <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              Payment Channels Distribution
            </h3>
          </div>
          <span class="text-[11px] font-bold text-zinc-500">
            Total: {{ formatUZS(periodMetrics.totalCollected) }} UZS
          </span>
        </div>

        <div v-if="methodBreakdown.length === 0" class="py-6 text-center text-zinc-400">
          No payment collections recorded in this period.
        </div>
        <div v-else class="space-y-2.5">
          <div
            v-for="item in methodBreakdown"
            :key="item.method"
            class="p-2 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-100 dark:border-zinc-800/80 flex flex-col gap-1.5"
          >
            <div class="flex items-center justify-between text-xs font-bold">
              <span class="text-zinc-800 dark:text-zinc-200 uppercase">{{ item.method }}</span>
              <div class="flex items-center gap-2 font-mono">
                <span class="text-zinc-900 dark:text-zinc-100">{{ formatUZS(item.amount) }} UZS</span>
                <span class="text-[10.5px] text-zinc-400 font-sans">({{ item.count }} tx / {{ item.percent }}%)</span>
              </div>
            </div>
            <!-- Progress Bar -->
            <div class="h-1.5 w-full rounded-full bg-zinc-200 dark:bg-zinc-750 overflow-hidden">
              <div
                class="h-full rounded-full bg-blue-600 transition-all duration-300"
                :style="{ width: `${item.percent}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Receiver / Cashier Breakdown Card -->
      <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] p-4 shadow-2xs">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <Users class="h-4 w-4 text-emerald-600" />
            <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              Cashier & Receiver Breakdown
            </h3>
          </div>
          <span class="text-[11px] font-bold text-zinc-500">
            {{ receiverBreakdown.length }} active receivers
          </span>
        </div>

        <div v-if="receiverBreakdown.length === 0" class="py-6 text-center text-zinc-400">
          No cashier records in this period.
        </div>
        <div v-else class="space-y-2.5">
          <div
            v-for="item in receiverBreakdown"
            :key="item.receiver"
            class="p-2 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-100 dark:border-zinc-800/80 flex flex-col gap-1.5"
          >
            <div class="flex items-center justify-between text-xs font-bold">
              <span class="text-zinc-800 dark:text-zinc-200 uppercase">{{ item.receiver }}</span>
              <div class="flex items-center gap-2 font-mono">
                <span class="text-zinc-900 dark:text-zinc-100">{{ formatUZS(item.amount) }} UZS</span>
                <span class="text-[10.5px] text-zinc-400 font-sans">({{ item.count }} tx / {{ item.percent }}%)</span>
              </div>
            </div>
            <!-- Progress Bar -->
            <div class="h-1.5 w-full rounded-full bg-zinc-200 dark:bg-zinc-750 overflow-hidden">
              <div
                class="h-full rounded-full bg-emerald-600 transition-all duration-300"
                :style="{ width: `${item.percent}%` }"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Financial Transactions Ledger Table ─────────────────────────── -->
    <div class="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] overflow-hidden shadow-2xs">
      <div class="px-5 py-3.5 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-800 dark:text-zinc-200">
            Financial Transactions Ledger
          </h3>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-mono">
            {{ sortedFilteredPayments.length }} records
          </span>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850/60 text-[11.5px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300 select-none">
              <th class="px-4 py-3 w-12 text-center">No</th>
              <th class="px-4 py-3 w-[26%]">Student / Full Name</th>
              <th class="px-4 py-3 w-[12%]">Type</th>
              <th class="px-4 py-3 w-[15%]">Method / Channel</th>
              <th class="px-4 py-3 w-[13%]">Received By</th>
              <th class="px-4 py-3 w-[16%] text-right">Amount</th>
              <th class="px-4 py-3 w-[14%]">Date & Time</th>
              <th class="px-4 py-3 text-center w-14">Receipt</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800 text-[13px]">
            <tr
              v-for="(p, idx) in paginatedPayments"
              :key="p.id"
              class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors text-zinc-800 dark:text-zinc-200"
            >
              <!-- Index -->
              <td class="px-4 py-3 text-center text-zinc-400 font-mono text-[11px]">
                {{ (currentPage - 1) * ITEMS_PER_PAGE + idx + 1 }}
              </td>

              <!-- Student Full Name & Info Badges -->
              <td class="px-4 py-3">
                <div class="flex flex-col gap-0.5">
                  <span class="font-bold uppercase tracking-wide text-zinc-900 dark:text-zinc-100 truncate">
                    {{ p.student_full_name || p.student_name || 'General Payment' }}
                  </span>
                  <div class="flex flex-wrap items-center gap-1.5 mt-0.5">
                    <span class="font-mono text-[11px] font-bold text-[#0066cc] dark:text-blue-400">
                      {{ p.student_id || '—' }}
                    </span>
                    <span
                      v-if="getStudent(p.student_id)?.tariff"
                      class="px-1.5 py-0.2 rounded text-[9.5px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 uppercase"
                    >
                      {{ getStudent(p.student_id)?.tariff }}
                    </span>
                    <span
                      v-if="getStudent(p.student_id)?.student_group"
                      class="px-1.5 py-0.2 rounded text-[9.5px] font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 uppercase"
                    >
                      {{ getStudent(p.student_id)?.student_group }}
                    </span>
                    <span
                      v-if="getStudent(p.student_id)?.coordinator"
                      class="px-1.5 py-0.2 rounded text-[9.5px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 uppercase"
                    >
                      {{ getStudent(p.student_id)?.coordinator }}
                    </span>
                  </div>
                </div>
              </td>

              <!-- Transaction Type Badge -->
              <td class="px-4 py-3">
                <span
                  v-if="p.is_withdrawal"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-[5px] text-[11px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                >
                  <ArrowDownRight class="h-3 w-3" />
                  <span>Withdrawal</span>
                </span>
                <span
                  v-else-if="p.is_discount"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-[5px] text-[11px] font-bold bg-pink-500/10 text-pink-600 dark:text-pink-400 border border-pink-500/20"
                >
                  <Percent class="h-3 w-3" />
                  <span>Discount</span>
                </span>
                <span
                  v-else
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-[5px] text-[11px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                >
                  <ArrowUpRight class="h-3 w-3" />
                  <span>Payment</span>
                </span>
              </td>

              <!-- Method -->
              <td class="px-4 py-3 font-semibold uppercase text-zinc-700 dark:text-zinc-300">
                {{ p.method || '—' }}
              </td>

              <!-- Receiver -->
              <td class="px-4 py-3 font-medium uppercase text-zinc-500 dark:text-zinc-400">
                {{ p.received_by || '—' }}
              </td>

              <!-- Amount -->
              <td class="px-4 py-3 text-right font-mono font-extrabold text-[13.5px]">
                <span
                  :class="p.is_withdrawal ? 'text-amber-600 dark:text-amber-400' : p.is_discount ? 'text-pink-600 dark:text-pink-400' : 'text-emerald-600 dark:text-emerald-400'"
                >
                  {{ p.is_withdrawal ? '-' : p.is_discount ? '' : '+' }}{{ formatUZS(Math.abs(Number(p.amount))) }} UZS
                </span>
              </td>

              <!-- Date & Time -->
              <td class="px-4 py-3 text-zinc-500 dark:text-zinc-400 font-mono text-[11.5px]">
                {{ formatDate(p.created_at) }}
              </td>

              <!-- Receipt View -->
              <td class="px-4 py-3 text-center">
                <button
                  type="button"
                  @click="viewingPayment = p"
                  class="p-1.5 rounded-lg text-zinc-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 transition-colors cursor-pointer"
                  title="View / Print Receipt"
                >
                  <Printer class="h-4 w-4" />
                </button>
              </td>
            </tr>

            <!-- Empty State -->
            <tr v-if="paginatedPayments.length === 0">
              <td colspan="8" class="px-6 py-12 text-center text-zinc-400">
                No financial transactions matching the selected filters.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div v-if="totalPages > 1" class="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
        <span class="text-xs text-zinc-500 font-mono">
          Page {{ currentPage }} of {{ totalPages }} ({{ sortedFilteredPayments.length }} records)
        </span>
        <div class="flex items-center gap-1.5">
          <button
            :disabled="currentPage === 1"
            @click="currentPage--"
            class="px-3 py-1 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 disabled:opacity-40 cursor-pointer text-zinc-700 dark:text-zinc-300"
          >
            Prev
          </button>
          <button
            :disabled="currentPage === totalPages"
            @click="currentPage++"
            class="px-3 py-1 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 disabled:opacity-40 cursor-pointer text-zinc-700 dark:text-zinc-300"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- ── Receipt Modal ───────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="viewingPayment"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none"
      >
        <div class="relative w-full max-w-lg rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#15171a] p-6 shadow-2xl space-y-4">
          <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
            <div class="flex items-center gap-2">
              <Printer class="h-5 w-5 text-blue-600" />
              <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                Official Payment Receipt
              </h3>
            </div>
            <button
              type="button"
              @click="viewingPayment = null"
              class="p-1 rounded-lg text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 cursor-pointer"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <div class="space-y-2.5 text-xs">
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Receipt ID:</span>
              <span class="font-mono font-bold">{{ viewingPayment.id }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Student ID:</span>
              <span class="font-mono font-bold text-blue-600">{{ viewingPayment.student_id || '—' }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Student Name:</span>
              <span class="font-bold uppercase">{{ viewingPayment.student_full_name || viewingPayment.student_name || 'General' }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Amount:</span>
              <span class="font-mono font-extrabold text-sm text-emerald-600 dark:text-emerald-400">
                {{ formatUZS(Math.abs(Number(viewingPayment.amount))) }} UZS
              </span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Payment Channel:</span>
              <span class="font-bold uppercase">{{ viewingPayment.method }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Cashier / Receiver:</span>
              <span class="font-bold uppercase">{{ viewingPayment.received_by }}</span>
            </div>
            <div class="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500">Date & Time:</span>
              <span class="font-mono">{{ formatDate(viewingPayment.created_at) }}</span>
            </div>
            <div v-if="viewingPayment.notes" class="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-850">
              <span class="text-zinc-500 block mb-1">Notes:</span>
              <p class="font-medium text-zinc-800 dark:text-zinc-200">{{ viewingPayment.notes }}</p>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
            <button
              type="button"
              @click="handlePrint"
              class="flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-colors cursor-pointer"
            >
              <Printer class="h-4 w-4" />
              <span>Print Receipt</span>
            </button>
            <button
              type="button"
              @click="viewingPayment = null"
              class="px-4 py-2 text-xs font-bold rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── KPI Detail Modal (Collected / Debt / Discount / Withdraw) ──────── -->
    <Teleport to="body">
      <div
        v-if="activeKpiModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/65 backdrop-blur-xs select-none"
        @click.self="closeKpiModal"
      >
        <div
          class="relative w-full max-w-6xl h-[90vh] max-h-[90vh] rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#111315] shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150"
          @click="closeAllKpiDropdowns"
        >
          <!-- 1. Modal Header (shrink-0) -->
          <div class="px-5 py-3.5 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between gap-4 bg-zinc-50/70 dark:bg-zinc-900/40 shrink-0">
            <div class="flex items-center gap-3">
              <div
                class="h-10 w-10 rounded-xl flex items-center justify-center shadow-xs shrink-0"
                :class="[
                  activeKpiModal === 'collected' ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400' :
                  activeKpiModal === 'debt' ? 'bg-red-500/10 text-red-600 dark:text-red-400' :
                  activeKpiModal === 'discount' ? 'bg-pink-500/10 text-pink-600 dark:text-pink-400' :
                  'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                ]"
              >
                <TrendingUp v-if="activeKpiModal === 'collected'" class="h-5 w-5" />
                <AlertCircle v-else-if="activeKpiModal === 'debt'" class="h-5 w-5" />
                <Percent v-else-if="activeKpiModal === 'discount'" class="h-5 w-5" />
                <TrendingDown v-else-if="activeKpiModal === 'withdraw'" class="h-5 w-5" />
              </div>

              <div>
                <div class="flex items-center gap-2">
                  <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                    {{
                      activeKpiModal === 'collected' ? 'Total Collected Payments Breakdown' :
                      activeKpiModal === 'debt' ? 'Outstanding Debtors Register' :
                      activeKpiModal === 'discount' ? 'Discounts Given Breakdown' :
                      'Total Withdrawals & Refunds'
                    }}
                  </h3>
                  <span
                    class="px-2 py-0.5 rounded-full text-[10.5px] font-mono font-bold"
                    :class="[
                      activeKpiModal === 'collected' ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400' :
                      activeKpiModal === 'debt' ? 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400' :
                      activeKpiModal === 'discount' ? 'bg-pink-50 dark:bg-pink-950/40 text-pink-600 dark:text-pink-400' :
                      'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400'
                    ]"
                  >
                    {{ currentModalTotalRecords }} records
                  </span>
                </div>
                <p class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                  <span v-if="activeKpiModal !== 'debt'">
                    Date Range: <strong class="capitalize text-zinc-700 dark:text-zinc-300">{{ kpiDatePreset.replace('_', ' ') }}</strong> ·
                  </span>
                  Use filters and search to drill down and export to Excel.
                </p>
              </div>
            </div>

            <!-- Header Actions: Total Sum Badge, Download Excel, Close -->
            <div class="flex items-center gap-3">
              <div class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-850 shadow-2xs">
                <span class="text-zinc-500 text-[11px] font-medium">Total:</span>
                <span
                  class="font-mono font-extrabold text-xs"
                  :class="[
                    activeKpiModal === 'collected' ? 'text-emerald-600 dark:text-emerald-400' :
                    activeKpiModal === 'debt' ? 'text-red-600 dark:text-red-400' :
                    activeKpiModal === 'discount' ? 'text-pink-600 dark:text-pink-400' :
                    'text-amber-600 dark:text-amber-400'
                  ]"
                >
                  {{
                    activeKpiModal === 'collected' ? `+${formatUZS(totalCollectedModalAmount)} UZS` :
                    activeKpiModal === 'debt' ? `-${formatUZS(totalDebtModalAmount)} UZS` :
                    activeKpiModal === 'discount' ? `${formatUZS(totalDiscountModalAmount)} UZS` :
                    `-${formatUZS(totalWithdrawalModalAmount)} UZS`
                  }}
                </span>
              </div>

              <button
                type="button"
                @click="
                  activeKpiModal === 'collected' ? exportCollectedExcel() :
                  activeKpiModal === 'debt' ? exportDebtExcel() :
                  activeKpiModal === 'discount' ? exportDiscountExcel() :
                  exportWithdrawalExcel()
                "
                class="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold rounded-xl border border-emerald-300 dark:border-emerald-700/60 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-all cursor-pointer shadow-2xs"
                title="Download Filtered Excel Workbook"
              >
                <Download class="h-3.5 w-3.5" />
                <span>Download Excel</span>
              </button>

              <button
                type="button"
                @click="closeKpiModal"
                class="p-1.5 rounded-xl text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
              >
                <X class="h-5 w-5" />
              </button>
            </div>
          </div>

          <!-- 2. Search & Filter Controls Bar (shrink-0, exactly matching /students Download Excel Modal) -->
          <div class="p-3.5 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-850/40 space-y-2.5 shrink-0">
            
            <!-- Search Row with Type Selector -->
            <div class="flex items-stretch gap-0 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 overflow-hidden focus-within:border-blue-500 transition-colors shadow-2xs">
              <div class="relative shrink-0 border-r border-zinc-200 dark:border-zinc-700">
                <select
                  v-model="kpiSearchType"
                  class="h-9 pl-3 pr-7 bg-transparent text-xs font-bold text-zinc-600 dark:text-zinc-300 focus:outline-none cursor-pointer appearance-none"
                >
                  <option value="all">All Fields</option>
                  <option value="id">Student ID</option>
                  <option value="name">Student Name</option>
                  <option value="phone">Phone Number</option>
                  <option v-if="activeKpiModal === 'collected' || activeKpiModal === 'withdraw'" value="method">Payment Method</option>
                  <option value="coordinator">Coordinator</option>
                  <option v-if="activeKpiModal !== 'debt'" value="receiver">Receiver / Staff</option>
                  <option value="notes">Notes / Reason</option>
                </select>
                <ChevronDown class="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-zinc-400 pointer-events-none" />
              </div>
              <div class="relative flex-1">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
                <input
                  v-model="kpiSearchQuery"
                  type="text"
                  placeholder="Search by student name, ID, phone, method, receiver, notes..."
                  class="w-full h-9 pl-9 pr-3 bg-transparent text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none placeholder:text-zinc-400"
                />
              </div>
            </div>

            <!-- Multi-Select Filters Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-2 text-xs">
              
              <!-- 1. Date Preset Filter (for collected, discount, withdraw) -->
              <div v-if="activeKpiModal !== 'debt'" class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('date')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiDatePreset !== 'all'
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Calendar class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate capitalize">{{ kpiDatePreset.replace('_', ' ') }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiDateDropdownOpen"
                  class="absolute left-0 mt-1 w-52 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1.5 z-40 text-xs"
                  @click.stop
                >
                  <button
                    v-for="p in [
                      { key: 'this_month', label: 'This Month' },
                      { key: 'today', label: 'Today' },
                      { key: 'yesterday', label: 'Yesterday' },
                      { key: 'this_week', label: 'This Week' },
                      { key: 'last_month', label: 'Last Month' },
                      { key: 'this_year', label: 'This Year' },
                      { key: 'all', label: 'All Time' },
                      { key: 'custom', label: 'Custom Range...' }
                    ]"
                    :key="p.key"
                    type="button"
                    @click="kpiDatePreset = p.key as DatePreset; if (p.key !== 'custom') isKpiDateDropdownOpen = false"
                    class="w-full px-3 py-1.5 flex items-center justify-between text-left hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer"
                    :class="kpiDatePreset === p.key ? 'font-bold text-blue-600 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-950/30' : 'text-zinc-700 dark:text-zinc-300'"
                  >
                    <span>{{ p.label }}</span>
                    <Check v-if="kpiDatePreset === p.key" class="w-3.5 h-3.5 text-blue-600" />
                  </button>

                  <div v-if="kpiDatePreset === 'custom'" class="p-2 border-t border-zinc-100 dark:border-zinc-700 mt-1 space-y-1.5">
                    <label class="text-[10px] text-zinc-400 font-bold block">Start Date</label>
                    <input type="date" v-model="kpiCustomStartDate" class="w-full px-2 py-1 text-xs border border-zinc-200 dark:border-zinc-700 rounded-lg bg-zinc-50 dark:bg-zinc-850" />
                    <label class="text-[10px] text-zinc-400 font-bold block">End Date</label>
                    <input type="date" v-model="kpiCustomEndDate" class="w-full px-2 py-1 text-xs border border-zinc-200 dark:border-zinc-700 rounded-lg bg-zinc-50 dark:bg-zinc-850" />
                  </div>
                </div>
              </div>

              <!-- 2. Status Filter (Active / Archive) -->
              <div class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('status')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiSelectedStatuses.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <UserCheck class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ kpiSelectedStatuses.length === 0 ? 'Status' : `Status (${kpiSelectedStatuses.join(', ')})` }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiStatusDropdownOpen"
                  class="absolute left-0 mt-1 w-44 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 text-xs"
                  @click.stop
                >
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="kpiSelectedStatuses.length === 0" @change="kpiSelectedStatuses = []" class="rounded text-blue-600" />
                    <span>All Statuses</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedStatuses.includes('ACTIVE')" @change="toggleKpiList(kpiSelectedStatuses, 'ACTIVE')" class="rounded text-blue-600" />
                    <span>Active</span>
                  </label>
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedStatuses.includes('ARCHIVE')" @change="toggleKpiList(kpiSelectedStatuses, 'ARCHIVE')" class="rounded text-blue-600" />
                    <span>Archive</span>
                  </label>
                </div>
              </div>

              <!-- 3. Tariff Filter Dropdown -->
              <div class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('tariff')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiSelectedTariffs.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Award class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ kpiSelectedTariffs.length === 0 ? 'Tariff' : kpiSelectedTariffs.length === 1 ? `Tariff (${kpiSelectedTariffs[0]})` : `Tariff · ${kpiSelectedTariffs.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiTariffDropdownOpen"
                  class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
                  @click.stop
                >
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="kpiSelectedTariffs.length === 0" @change="kpiSelectedTariffs = []" class="rounded text-blue-600" />
                    <span>All Tariffs</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="t in availableTariffs" :key="t" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedTariffs.includes(t)" @change="toggleKpiList(kpiSelectedTariffs, t)" class="rounded text-blue-600" />
                    <span class="truncate">{{ t }}</span>
                  </label>
                </div>
              </div>

              <!-- 4. Group Filter Dropdown -->
              <div class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('group')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiSelectedGroups.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Users class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ kpiSelectedGroups.length === 0 ? 'Group' : kpiSelectedGroups.length === 1 ? `Group (${kpiSelectedGroups[0]})` : `Group · ${kpiSelectedGroups.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiGroupDropdownOpen"
                  class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
                  @click.stop
                >
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="kpiSelectedGroups.length === 0" @change="kpiSelectedGroups = []" class="rounded text-blue-600" />
                    <span>All Groups</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="g in availableGroups" :key="g" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedGroups.includes(g)" @change="toggleKpiList(kpiSelectedGroups, g)" class="rounded text-blue-600" />
                    <span class="truncate">{{ g }}</span>
                  </label>
                </div>
              </div>

              <!-- 5. Coordinator Filter Dropdown -->
              <div class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('coordinator')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiSelectedCoordinators.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Contact class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ kpiSelectedCoordinators.length === 0 ? 'Coordinator' : kpiSelectedCoordinators.length === 1 ? `Coord (${kpiSelectedCoordinators[0]})` : `Coord · ${kpiSelectedCoordinators.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiCoordinatorDropdownOpen"
                  class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
                  @click.stop
                >
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="kpiSelectedCoordinators.length === 0" @change="kpiSelectedCoordinators = []" class="rounded text-blue-600" />
                    <span>All Coordinators</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="c in availableCoordinators" :key="c" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedCoordinators.includes(c)" @change="toggleKpiList(kpiSelectedCoordinators, c)" class="rounded text-blue-600" />
                    <span class="truncate">{{ c }}</span>
                  </label>
                </div>
              </div>

              <!-- 6. Level Filter Dropdown -->
              <div class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('level')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiSelectedLevels.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <GraduationCap class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ kpiSelectedLevels.length === 0 ? 'Level' : kpiSelectedLevels.length === 1 ? `Level (${kpiSelectedLevels[0]})` : `Level · ${kpiSelectedLevels.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiLevelDropdownOpen"
                  class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
                  @click.stop
                >
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="kpiSelectedLevels.length === 0" @change="kpiSelectedLevels = []" class="rounded text-blue-600" />
                    <span>All Levels</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="l in availableLevels" :key="l" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedLevels.includes(l)" @change="toggleKpiList(kpiSelectedLevels, l)" class="rounded text-blue-600" />
                    <span class="truncate">{{ l }}</span>
                  </label>
                </div>
              </div>

              <!-- 7. ID Prefix Filter Dropdown -->
              <div class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('id')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiSelectedIds.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Hash class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ kpiSelectedIds.length === 0 ? 'ID Prefix' : `ID (${kpiSelectedIds.join(', ')})` }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiIdDropdownOpen"
                  class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
                  @click.stop
                >
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="kpiSelectedIds.length === 0" @change="kpiSelectedIds = []" class="rounded text-blue-600" />
                    <span>All ID Prefixes</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="idOpt in availableIds" :key="idOpt" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedIds.includes(idOpt)" @change="toggleKpiList(kpiSelectedIds, idOpt)" class="rounded text-blue-600" />
                    <span class="truncate font-mono font-bold">{{ idOpt }}</span>
                  </label>
                </div>
              </div>

              <!-- 8. Payment Method Filter (for collected & withdraw) -->
              <div v-if="activeKpiModal === 'collected' || activeKpiModal === 'withdraw'" class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('method')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiSelectedMethods.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <CreditCard class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ kpiSelectedMethods.length === 0 ? 'Method' : kpiSelectedMethods.length === 1 ? `Method (${kpiSelectedMethods[0]})` : `Method · ${kpiSelectedMethods.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiMethodDropdownOpen"
                  class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
                  @click.stop
                >
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="kpiSelectedMethods.length === 0" @change="kpiSelectedMethods = []" class="rounded text-blue-600" />
                    <span>All Methods</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="m in paymentMethods" :key="m" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedMethods.includes(m)" @change="toggleKpiList(kpiSelectedMethods, m)" class="rounded text-blue-600" />
                    <span class="truncate uppercase">{{ m }}</span>
                  </label>
                </div>
              </div>

              <!-- 9. Receiver / Staff Filter (for collected, discount, withdraw) -->
              <div v-if="activeKpiModal !== 'debt'" class="kpi-dropdown-container relative">
                <button
                  type="button"
                  @click.stop="toggleKpiDropdown('receiver')"
                  class="w-full h-8 px-2 rounded-lg font-semibold flex items-center justify-between cursor-pointer border transition-colors"
                  :class="kpiSelectedReceivers.length > 0
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300'"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Contact class="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span class="truncate">{{ kpiSelectedReceivers.length === 0 ? 'Receiver' : kpiSelectedReceivers.length === 1 ? `Rec (${kpiSelectedReceivers[0]})` : `Rec · ${kpiSelectedReceivers.length}` }}</span>
                  </div>
                  <ChevronDown class="w-3 h-3 shrink-0 ml-0.5 opacity-60" />
                </button>

                <div
                  v-if="isKpiReceiverDropdownOpen"
                  class="absolute left-0 mt-1 w-48 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow-xl py-1 z-40 max-h-60 overflow-y-auto text-xs"
                  @click.stop
                >
                  <label class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer font-bold">
                    <input type="checkbox" :checked="kpiSelectedReceivers.length === 0" @change="kpiSelectedReceivers = []" class="rounded text-blue-600" />
                    <span>All Receivers</span>
                  </label>
                  <div class="h-px bg-zinc-100 dark:bg-zinc-700 my-1" />
                  <label v-for="r in paymentReceivers" :key="r" class="px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-700 cursor-pointer">
                    <input type="checkbox" :checked="kpiSelectedReceivers.includes(r)" @change="toggleKpiList(kpiSelectedReceivers, r)" class="rounded text-blue-600" />
                    <span class="truncate uppercase">{{ r }}</span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Active Filter Chips Bar -->
            <div v-if="hasActiveKpiFilters" class="flex items-center gap-1.5 flex-wrap pt-0.5">
              <span
                v-for="chip in activeKpiFilterChips"
                :key="chip.key"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
              >
                {{ chip.label }}
                <X class="w-2.5 h-2.5 cursor-pointer hover:text-rose-500" @click="chip.clear()" />
              </span>
              <button
                type="button"
                @click="clearAllKpiFilters"
                class="text-[10.5px] font-bold text-rose-600 dark:text-rose-400 hover:underline cursor-pointer ml-1"
              >
                Clear All Filters
              </button>
            </div>
          </div>

          <!-- 3. Modal Table Body (flex-1 min-h-0 overflow-y-auto) -->
          <div class="flex-1 min-h-0 overflow-y-auto overflow-x-auto text-xs">
            
            <!-- 1. Collected Table -->
            <table v-if="activeKpiModal === 'collected'" class="w-full border-collapse text-left">
              <thead class="sticky top-0 z-10 bg-zinc-50 dark:bg-zinc-850/95 backdrop-blur-xs border-b border-zinc-200 dark:border-zinc-800 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 select-none">
                <tr>
                  <th class="px-4 py-2.5 w-12 text-center">No</th>
                  <th class="px-4 py-2.5">Student / Full Name</th>
                  <th class="px-4 py-2.5">Phone Number</th>
                  <th class="px-4 py-2.5">Method</th>
                  <th class="px-4 py-2.5">Received By</th>
                  <th class="px-4 py-2.5 text-right">Amount</th>
                  <th class="px-4 py-2.5">Date & Time</th>
                  <th class="px-4 py-2.5 text-center w-14">Receipt</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
                <tr
                  v-for="(p, idx) in paginatedCollectedModalList"
                  :key="p.id"
                  class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors"
                >
                  <td class="px-4 py-2.5 text-center font-mono text-zinc-400 text-[11px]">
                    {{ kpiPageSize === -1 ? idx + 1 : (kpiPage - 1) * kpiPageSize + idx + 1 }}
                  </td>
                  <td class="px-4 py-2.5">
                    <div class="flex flex-col gap-0.5">
                      <div class="flex items-center gap-1.5">
                        <span class="font-bold uppercase text-zinc-900 dark:text-zinc-100 truncate">
                          {{ p.student_full_name || p.student_name || 'General' }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.is_deleted" class="px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">
                          Archive
                        </span>
                      </div>
                      <div class="flex flex-wrap items-center gap-1.5">
                        <span class="font-mono font-bold text-[#0066cc] dark:text-blue-400 text-[11px]">
                          {{ p.student_id || '—' }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.tariff" class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 uppercase">
                          {{ getStudent(p.student_id)?.tariff }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.student_group" class="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 uppercase">
                          {{ getStudent(p.student_id)?.student_group }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.coordinator" class="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 uppercase">
                          {{ getStudent(p.student_id)?.coordinator }}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-2.5 font-mono text-zinc-600 dark:text-zinc-400 text-[11.5px]">
                    {{ getStudent(p.student_id)?.phone1 || '—' }}
                  </td>
                  <td class="px-4 py-2.5 font-semibold uppercase text-zinc-700 dark:text-zinc-300">
                    {{ p.method || '—' }}
                  </td>
                  <td class="px-4 py-2.5 font-medium uppercase text-zinc-500 dark:text-zinc-400">
                    {{ p.received_by || '—' }}
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono font-extrabold text-emerald-600 dark:text-emerald-400 text-[13px]">
                    +{{ formatUZS(Number(p.amount)) }} UZS
                  </td>
                  <td class="px-4 py-2.5 font-mono text-[11px] text-zinc-500 dark:text-zinc-400">
                    {{ formatDate(p.created_at) }}
                  </td>
                  <td class="px-4 py-2.5 text-center">
                    <button
                      type="button"
                      @click="viewingPayment = p"
                      class="p-1.5 rounded-lg text-zinc-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 cursor-pointer"
                      title="View Receipt"
                    >
                      <Printer class="h-4 w-4" />
                    </button>
                  </td>
                </tr>
                <tr v-if="filteredCollectedModalList.length === 0">
                  <td colspan="8" class="px-4 py-12 text-center text-zinc-400">
                    No collected payments found matching the selected filter criteria.
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- 2. Debt Table -->
            <table v-else-if="activeKpiModal === 'debt'" class="w-full border-collapse text-left">
              <thead class="sticky top-0 z-10 bg-zinc-50 dark:bg-zinc-850/95 backdrop-blur-xs border-b border-zinc-200 dark:border-zinc-800 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 select-none">
                <tr>
                  <th class="px-4 py-2.5 w-12 text-center">No</th>
                  <th class="px-4 py-2.5">Student / Full Name</th>
                  <th class="px-4 py-2.5">Phone Number</th>
                  <th class="px-4 py-2.5">Coordinator</th>
                  <th class="px-4 py-2.5 text-right">Outstanding Debt</th>
                  <th class="px-4 py-2.5 text-right">Discounts</th>
                  <th class="px-4 py-2.5 text-center w-28">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
                <tr
                  v-for="(s, idx) in paginatedDebtModalList"
                  :key="s.id"
                  class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors"
                >
                  <td class="px-4 py-2.5 text-center font-mono text-zinc-400 text-[11px]">
                    {{ kpiPageSize === -1 ? idx + 1 : (kpiPage - 1) * kpiPageSize + idx + 1 }}
                  </td>
                  <td class="px-4 py-2.5">
                    <div class="flex flex-col gap-0.5">
                      <div class="flex items-center gap-1.5">
                        <span class="font-bold uppercase text-zinc-900 dark:text-zinc-100 truncate">
                          {{ s.full_name }}
                        </span>
                        <span v-if="s.is_deleted" class="px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">
                          Archive
                        </span>
                      </div>
                      <div class="flex flex-wrap items-center gap-1.5">
                        <span class="font-mono font-bold text-[#0066cc] dark:text-blue-400 text-[11px]">
                          {{ s.id }}
                        </span>
                        <span v-if="s.tariff" class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 uppercase">
                          {{ s.tariff }}
                        </span>
                        <span v-if="s.student_group" class="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 uppercase">
                          {{ s.student_group }}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-2.5 font-mono text-zinc-600 dark:text-zinc-400 text-[11.5px]">
                    {{ s.phone1 || s.phone2 || '—' }}
                  </td>
                  <td class="px-4 py-2.5 font-semibold text-purple-600 dark:text-purple-400 uppercase">
                    {{ s.coordinator || '—' }}
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono font-extrabold text-red-600 dark:text-red-400 text-[13.5px]">
                    -{{ formatUZS(Math.abs(Number(s.balance))) }} UZS
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono text-zinc-500">
                    {{ formatUZS(Number(s.discount) || 0) }} UZS
                  </td>
                  <td class="px-4 py-2.5 text-center">
                    <button
                      type="button"
                      @click="emit('open-add-payment', s.id); closeKpiModal()"
                      class="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors cursor-pointer shadow-xs"
                    >
                      <span>Pay</span>
                      <ArrowRight class="h-3 w-3" />
                    </button>
                  </td>
                </tr>
                <tr v-if="filteredDebtModalList.length === 0">
                  <td colspan="7" class="px-4 py-12 text-center text-zinc-400">
                    No debtor students found matching the selected filter criteria.
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- 3. Discount Table -->
            <table v-else-if="activeKpiModal === 'discount'" class="w-full border-collapse text-left">
              <thead class="sticky top-0 z-10 bg-zinc-50 dark:bg-zinc-850/95 backdrop-blur-xs border-b border-zinc-200 dark:border-zinc-800 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 select-none">
                <tr>
                  <th class="px-4 py-2.5 w-12 text-center">No</th>
                  <th class="px-4 py-2.5">Student / Full Name</th>
                  <th class="px-4 py-2.5 text-right">Discount Amount</th>
                  <th class="px-4 py-2.5">Granted By</th>
                  <th class="px-4 py-2.5">Reason / Notes</th>
                  <th class="px-4 py-2.5">Date & Time</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
                <tr
                  v-for="(p, idx) in paginatedDiscountModalList"
                  :key="p.id"
                  class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors"
                >
                  <td class="px-4 py-2.5 text-center font-mono text-zinc-400 text-[11px]">
                    {{ kpiPageSize === -1 ? idx + 1 : (kpiPage - 1) * kpiPageSize + idx + 1 }}
                  </td>
                  <td class="px-4 py-2.5">
                    <div class="flex flex-col gap-0.5">
                      <div class="flex items-center gap-1.5">
                        <span class="font-bold uppercase text-zinc-900 dark:text-zinc-100 truncate">
                          {{ p.student_full_name || p.student_name || 'General' }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.is_deleted" class="px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">
                          Archive
                        </span>
                      </div>
                      <div class="flex flex-wrap items-center gap-1.5">
                        <span class="font-mono font-bold text-[#0066cc] dark:text-blue-400 text-[11px]">
                          {{ p.student_id || '—' }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.tariff" class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 uppercase">
                          {{ getStudent(p.student_id)?.tariff }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.coordinator" class="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 uppercase">
                          {{ getStudent(p.student_id)?.coordinator }}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono font-extrabold text-pink-600 dark:text-pink-400 text-[13px]">
                    {{ formatUZS(Math.abs(Number(p.amount))) }} UZS
                  </td>
                  <td class="px-4 py-2.5 font-medium uppercase text-zinc-500 dark:text-zinc-400">
                    {{ p.received_by || '—' }}
                  </td>
                  <td class="px-4 py-2.5 text-zinc-700 dark:text-zinc-300">
                    {{ p.notes || '—' }}
                  </td>
                  <td class="px-4 py-2.5 font-mono text-[11px] text-zinc-500 dark:text-zinc-400">
                    {{ formatDate(p.created_at) }}
                  </td>
                </tr>
                <tr v-if="filteredDiscountModalList.length === 0">
                  <td colspan="6" class="px-4 py-12 text-center text-zinc-400">
                    No discount records found matching the filter criteria.
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- 4. Withdrawals Table -->
            <table v-else-if="activeKpiModal === 'withdraw'" class="w-full border-collapse text-left">
              <thead class="sticky top-0 z-10 bg-zinc-50 dark:bg-zinc-850/95 backdrop-blur-xs border-b border-zinc-200 dark:border-zinc-800 text-[11px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 select-none">
                <tr>
                  <th class="px-4 py-2.5 w-12 text-center">No</th>
                  <th class="px-4 py-2.5">Student / Full Name</th>
                  <th class="px-4 py-2.5">Method</th>
                  <th class="px-4 py-2.5">Processed By</th>
                  <th class="px-4 py-2.5 text-right">Withdrawal Amount</th>
                  <th class="px-4 py-2.5">Reason / Notes</th>
                  <th class="px-4 py-2.5">Date & Time</th>
                  <th class="px-4 py-2.5 text-center w-14">Receipt</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
                <tr
                  v-for="(p, idx) in paginatedWithdrawalModalList"
                  :key="p.id"
                  class="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/60 transition-colors"
                >
                  <td class="px-4 py-2.5 text-center font-mono text-zinc-400 text-[11px]">
                    {{ kpiPageSize === -1 ? idx + 1 : (kpiPage - 1) * kpiPageSize + idx + 1 }}
                  </td>
                  <td class="px-4 py-2.5">
                    <div class="flex flex-col gap-0.5">
                      <div class="flex items-center gap-1.5">
                        <span class="font-bold uppercase text-zinc-900 dark:text-zinc-100 truncate">
                          {{ p.student_full_name || p.student_name || 'General' }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.is_deleted" class="px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">
                          Archive
                        </span>
                      </div>
                      <div class="flex flex-wrap items-center gap-1.5">
                        <span class="font-mono font-bold text-[#0066cc] dark:text-blue-400 text-[11px]">
                          {{ p.student_id || '—' }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.tariff" class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 uppercase">
                          {{ getStudent(p.student_id)?.tariff }}
                        </span>
                        <span v-if="getStudent(p.student_id)?.coordinator" class="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 uppercase">
                          {{ getStudent(p.student_id)?.coordinator }}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-2.5 font-semibold uppercase text-zinc-700 dark:text-zinc-300">
                    {{ p.method || '—' }}
                  </td>
                  <td class="px-4 py-2.5 font-medium uppercase text-zinc-500 dark:text-zinc-400">
                    {{ p.received_by || '—' }}
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono font-extrabold text-amber-600 dark:text-amber-400 text-[13.5px]">
                    -{{ formatUZS(Math.abs(Number(p.amount))) }} UZS
                  </td>
                  <td class="px-4 py-2.5 text-zinc-700 dark:text-zinc-300">
                    {{ p.notes || '—' }}
                  </td>
                  <td class="px-4 py-2.5 font-mono text-[11px] text-zinc-500 dark:text-zinc-400">
                    {{ formatDate(p.created_at) }}
                  </td>
                  <td class="px-4 py-2.5 text-center">
                    <button
                      type="button"
                      @click="viewingPayment = p"
                      class="p-1.5 rounded-lg text-zinc-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 cursor-pointer"
                      title="View Receipt"
                    >
                      <Printer class="h-4 w-4" />
                    </button>
                  </td>
                </tr>
                <tr v-if="filteredWithdrawalModalList.length === 0">
                  <td colspan="8" class="px-4 py-12 text-center text-zinc-400">
                    No withdrawals recorded matching the filter criteria.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 4. Robust Modal Pagination Footer (shrink-0, ALWAYS visible) -->
          <div class="px-5 py-3 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-[#15171a] flex flex-wrap items-center justify-between gap-3 shrink-0 select-none">
            <!-- Left: Page Size Selector & Record Count -->
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400 font-medium">
                <span>Show:</span>
                <select
                  v-model="kpiPageSize"
                  class="px-2 py-1 text-xs font-bold border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 cursor-pointer focus:outline-none"
                >
                  <option :value="15">15 rows</option>
                  <option :value="30">30 rows</option>
                  <option :value="50">50 rows</option>
                  <option :value="100">100 rows</option>
                  <option :value="-1">All records</option>
                </select>
              </div>

              <span class="text-xs text-zinc-500 dark:text-zinc-400 font-mono">
                <template v-if="kpiPageSize === -1">
                  Showing all {{ currentModalTotalRecords }} records
                </template>
                <template v-else>
                  Showing {{ currentModalTotalRecords === 0 ? 0 : (kpiPage - 1) * kpiPageSize + 1 }} - {{ Math.min(kpiPage * kpiPageSize, currentModalTotalRecords) }} of {{ currentModalTotalRecords }} records
                </template>
              </span>
            </div>

            <!-- Right: Interactive Page Numbers and Nav Buttons -->
            <div v-if="kpiPageSize !== -1 && kpiTotalPages > 1" class="flex items-center gap-1">
              <!-- First Page -->
              <button
                type="button"
                :disabled="kpiPage <= 1"
                @click="kpiPage = 1"
                class="p-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-100 dark:hover:bg-zinc-700 cursor-pointer transition-colors text-zinc-700 dark:text-zinc-300"
                title="First Page"
              >
                <ChevronsLeft class="w-3.5 h-3.5" />
              </button>

              <!-- Previous Page -->
              <button
                type="button"
                :disabled="kpiPage <= 1"
                @click="kpiPage--"
                class="px-2.5 py-1 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-100 dark:hover:bg-zinc-700 cursor-pointer transition-colors text-zinc-700 dark:text-zinc-300 flex items-center gap-1"
              >
                <ChevronLeft class="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>

              <!-- Page Indicator / Number Buttons -->
              <div class="flex items-center gap-1 px-1">
                <template v-for="pageNum in Array.from({ length: kpiTotalPages }, (_, i) => i + 1)" :key="pageNum">
                  <button
                    v-if="pageNum === 1 || pageNum === kpiTotalPages || (pageNum >= kpiPage - 1 && pageNum <= kpiPage + 1)"
                    type="button"
                    @click="kpiPage = pageNum"
                    class="h-7 w-7 rounded-lg text-xs font-mono font-bold cursor-pointer transition-colors flex items-center justify-center"
                    :class="pageNum === kpiPage
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700'"
                  >
                    {{ pageNum }}
                  </button>
                  <span
                    v-else-if="(pageNum === kpiPage - 2 && pageNum > 1) || (pageNum === kpiPage + 2 && pageNum < kpiTotalPages)"
                    class="px-1 text-zinc-400 text-xs select-none"
                  >
                    ...
                  </span>
                </template>
              </div>

              <!-- Next Page -->
              <button
                type="button"
                :disabled="kpiPage >= kpiTotalPages"
                @click="kpiPage++"
                class="px-2.5 py-1 text-xs font-bold rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-100 dark:hover:bg-zinc-700 cursor-pointer transition-colors text-zinc-700 dark:text-zinc-300 flex items-center gap-1"
              >
                <span>Next</span>
                <ChevronRight class="w-3.5 h-3.5" />
              </button>

              <!-- Last Page -->
              <button
                type="button"
                :disabled="kpiPage >= kpiTotalPages"
                @click="kpiPage = kpiTotalPages"
                class="p-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-100 dark:hover:bg-zinc-700 cursor-pointer transition-colors text-zinc-700 dark:text-zinc-300"
                title="Last Page"
              >
                <ChevronsRight class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
