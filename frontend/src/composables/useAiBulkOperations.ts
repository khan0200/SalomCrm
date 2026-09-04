import { ref, nextTick } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useRouter, useRoute } from 'vue-router'
import { studentsApi } from '@/api/students'
import { useStudentDashboardStore } from '@/stores/studentDashboard'
import { useUiStore } from '@/stores/ui'
import type { Student, Folder } from '@/types'
import { normalizeCertificateScore } from '@/utils/certificateScore'

export interface UniversityChoice {
  slot: number
  name: string
  status?: string | null
  major?: string | null
}

export interface StudentUniversitySummary {
  student: Student
  universities: UniversityChoice[]
  hasAny: boolean
}

export interface ClarificationState {
  isOpen: boolean
  question: string
  field: 'university' | string
  studentIds: string[]
  selectedUniversity: string
}

export interface BulkOperationResult {
  type: 'delete' | 'excel' | 'show_university' | 'set_university' | 'open_folder' | 'create_folder' | 'folder_add' | 'set_row_color' | 'filter' | 'clarification' | 'info' | 'error'
  title: string
  message: string
  details?: string[]
  universitySummaries?: StudentUniversitySummary[]
  rawStudents?: Student[]
  success: boolean
}

// Acronym / Common short name mapping for South Korean Universities
const KNOWN_ACRONYMS: Record<string, string> = {
  BUFS: 'BUSAN UNIVERSITY OF FOREIGN STUDIES',
  SNU: 'SEOUL NATIONAL UNIVERSITY',
  KU: 'KOREA UNIVERSITY',
  YU: 'YONSEI UNIVERSITY',
  CAU: 'CHUNG-ANG UNIVERSITY',
  SKKU: 'SUNGKYUNKWAN UNIVERSITY',
  HYU: 'HANYANG UNIVERSITY',
  PNU: 'PUSAN NATIONAL UNIVERSITY',
  KNU: 'KYUNGPOOK NATIONAL UNIVERSITY',
  CNU: 'CHONNAM NATIONAL UNIVERSITY',
  KAIST: 'KAIST',
  POSTECH: 'POHANG UNIVERSITY OF SCIENCE AND TECHNOLOGY',
  UNIST: 'ULSAN NATIONAL INSTITUTE OF SCIENCE AND TECHNOLOGY',
  JNU: 'JEONBUK NATIONAL UNIVERSITY',
  KMU: 'KOOKMIN UNIVERSITY',
  SMIT: 'SEOUL MEDIA INSTITUTE OF TECHNOLOGY',
  JBU: 'JOONGBU UNIVERSITY',
}

export function useAiBulkOperations() {
  const queryClient = useQueryClient()
  const router = useRouter()
  const route = useRoute()
  const dashboardStore = useStudentDashboardStore()
  const uiStore = useUiStore()

  const isExecuting = ref(false)
  const lastResult = ref<BulkOperationResult | null>(null)
  const officialUniversities = ref<string[]>([])
  const cachedFolders = ref<Folder[]>([])
  const clarificationState = ref<ClarificationState>({
    isOpen: false,
    question: '',
    field: 'university',
    studentIds: [],
    selectedUniversity: ''
  })

  // ── 1. Fetch Official Universities from DB ──────────────────────────────────
  const getOfficialUniversities = async (): Promise<string[]> => {
    if (officialUniversities.value.length > 0) {
      return officialUniversities.value
    }

    // Check query cache
    const cachedOptions = queryClient.getQueryData<any>(['student-options'])
    if (cachedOptions && Array.isArray(cachedOptions.universities) && cachedOptions.universities.length > 0) {
      officialUniversities.value = Array.from(new Set(cachedOptions.universities))
      return officialUniversities.value
    }

    try {
      const opts = await studentsApi.getOptions()
      if (opts && Array.isArray(opts.universities)) {
        officialUniversities.value = Array.from(new Set(opts.universities))
        queryClient.setQueryData(['student-options'], opts)
        return officialUniversities.value
      }
    } catch (err) {
      console.warn('Failed to load official universities:', err)
    }
    return []
  }

  // ── 1b. Fetch Folders from DB ───────────────────────────────────────────────
  const getFolders = async (): Promise<Folder[]> => {
    if (cachedFolders.value.length > 0) return cachedFolders.value
    const cached = queryClient.getQueryData<Folder[]>(['folders'])
    if (cached && cached.length > 0) {
      cachedFolders.value = cached
      return cached
    }
    try {
      const folders = await studentsApi.getFolders()
      cachedFolders.value = folders
      queryClient.setQueryData(['folders'], folders)
      return folders
    } catch (err) {
      console.warn('Failed to load folders:', err)
    }
    return []
  }

  // ── 1c. Smart Folder Name Matcher ──────────────────────────────────────────
  const matchFolder = (rawName: string, folders: Folder[]): Folder | undefined => {
    const q = rawName.trim().toUpperCase()
    return (
      folders.find(f => f.name.toUpperCase() === q) ||
      folders.find(f => f.name.toUpperCase().startsWith(q)) ||
      folders.find(f => f.name.toUpperCase().includes(q))
    )
  }

  // ── 2. Smart University Name Resolver (Acronyms & DB Search) ───────────────
  const resolveOfficialUniversity = (rawInput: string, universities: string[]): string => {
    const query = rawInput.trim().toUpperCase()
    if (!query) return ''

    // 1. Acronym expansion
    if (KNOWN_ACRONYMS[query]) {
      const target = KNOWN_ACRONYMS[query].toUpperCase()
      const found = universities.find(u => u.toUpperCase().includes(target))
      if (found) return found
    }

    // 2. Exact match
    const exact = universities.find(u => u.toUpperCase() === query)
    if (exact) return exact

    // 3. Prefix match (e.g. "JOONGBU" in "JOONGBU UNIVERSITY ...")
    const prefix = universities.find(u => {
      const uUp = u.toUpperCase()
      return uUp.startsWith(query + ' ') || uUp.startsWith(query + '(')
    })
    if (prefix) return prefix

    // 4. Substring match
    const sub = universities.find(u => u.toUpperCase().includes(query))
    if (sub) return sub

    // 5. Generated acronym match
    const acronymMatch = universities.find(u => {
      const words = u.split(/[\s,()]+/).filter(w => w.length > 0 && !['OF', 'AND', 'THE', '&'].includes(w.toUpperCase()))
      const acr = words.map(w => w[0].toUpperCase()).join('')
      return acr === query
    })
    if (acronymMatch) return acronymMatch

    // Fallback: title-case what user typed
    return rawInput.trim()
      .split(' ')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(' ')
  }

  // ── 3. Duplicate University Checker ────────────────────────────────────────
  const isDuplicateUniversity = (existingName: string | null | undefined, targetName: string): boolean => {
    if (!existingName) return false
    const clean = (s: string) => s.toUpperCase()
      .replace(/\([^)]*\)/g, '')
      .replace(/UNIVERSITY|COLLEGE|INSTITUTE|CAMPUS/gi, '')
      .replace(/[^A-Z0-9]/g, '')
      .trim()

    const c1 = clean(existingName)
    const c2 = clean(targetName)
    if (!c1 || !c2) return existingName.trim().toUpperCase() === targetName.trim().toUpperCase()
    return c1 === c2 || c1.includes(c2) || c2.includes(c1)
  }

  // ── 4. Helper: Fetch or Retrieve All Students ──────────────────────────────
  const getAllStudents = async (): Promise<Student[]> => {
    const cached = queryClient.getQueryData<{ results: Student[] } | Student[]>(['all-students-master'])
    if (cached) {
      if (Array.isArray(cached)) return cached
      if (cached.results && Array.isArray(cached.results)) return cached.results
    }

    try {
      const resp = await studentsApi.getStudents({
        page: 1,
        page_size: 5000,
        folder: 'all',
        include_archive: true
      })
      if (resp && resp.results) {
        queryClient.setQueryData(['all-students-master'], resp)
        return resp.results
      }
    } catch (err) {
      console.error('Failed to load students for AI operation:', err)
    }
    return []
  }

  const STOP_WORDS = new Set([
    'only', 'me', 'for', 'student', 'students', 'to', 'in', 'and', 'the', 'these',
    'row', 'color', 'changes', 'my', 'mine'
  ])

  // ── 5. Helper: Extract and Parse Student IDs ──────────────────────────────
  const parseStudentIds = (text: string): string[] => {
    if (!text) return []
    const tokens = text
      .split(/[\s,;\n]+/)
      .map(t => t.trim().replace(/^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$/g, ''))
      .filter(t => t && !STOP_WORDS.has(t.toLowerCase()))

    return Array.from(new Set(tokens))
  }

  // ── 6. Helper: Match Tokens Against Master Students (Case-Insensitive) ─────
  const matchStudents = (tokens: string[], allStudents: Student[]): { matched: Student[]; unmatched: string[] } => {
    const matched: Student[] = []
    const matchedIds = new Set<string>()
    const unmatched: string[] = []

    for (const token of tokens) {
      const lower = token.toLowerCase()
      const found = allStudents.find(s => (s.id || '').toLowerCase() === lower)
      if (found) {
        if (!matchedIds.has(found.id)) {
          matched.push(found)
          matchedIds.add(found.id)
        }
      } else {
        unmatched.push(token)
      }
    }

    return { matched, unmatched }
  }

  // ── 7. Operation: /delete <ids...> ─────────────────────────────────────────
  const executeDelete = async (rawIdsStr: string): Promise<BulkOperationResult> => {
    const tokens = parseStudentIds(rawIdsStr)
    if (tokens.length === 0) {
      return {
        type: 'error',
        title: 'No Student IDs Provided',
        message: 'Please provide at least one student ID to delete (e.g. /delete f1, f2, f3).',
        success: false
      }
    }

    const allStudents = await getAllStudents()
    const { matched, unmatched } = matchStudents(tokens, allStudents)

    if (matched.length === 0) {
      return {
        type: 'error',
        title: 'Students Not Found',
        message: `Could not find any students matching: ${tokens.join(', ')}`,
        success: false
      }
    }

    const details: string[] = []
    let successCount = 0

    for (const student of matched) {
      try {
        await studentsApi.archiveStudent(student.id)
        queryClient.setQueryData<any>(['all-students-master'], (old: any) => {
          if (!old) return old
          if (Array.isArray(old)) {
            return old.map(s => s.id === student.id ? { ...s, is_deleted: true } : s)
          }
          if (old.results && Array.isArray(old.results)) {
            return {
              ...old,
              results: old.results.map((s: Student) => s.id === student.id ? { ...s, is_deleted: true } : s)
            }
          }
          return old
        })
        details.push(`✓ ${student.id} — ${student.full_name} moved to archive`)
        successCount++
      } catch (err: any) {
        details.push(`✗ ${student.id} — ${student.full_name} failed: ${err.message || 'Error'}`)
      }
    }

    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    queryClient.invalidateQueries({ queryKey: ['folders'] })

    if (unmatched.length > 0) {
      details.push(`⚠️ Not found: ${unmatched.join(', ')}`)
    }

    uiStore.addToast({
      type: successCount > 0 ? 'success' : 'error',
      title: 'Bulk Delete Completed',
      message: `Archived ${successCount} of ${matched.length} students.`
    })

    return {
      type: 'delete',
      title: `Archived ${successCount} Student${successCount === 1 ? '' : 's'}`,
      message: `Successfully processed ${successCount} of ${matched.length} student records.`,
      details,
      rawStudents: matched,
      success: successCount > 0
    }
  }

  // ── 8. Operation: /excel <ids...> ──────────────────────────────────────────
  const executeExcel = async (rawIdsStr: string): Promise<BulkOperationResult> => {
    const tokens = parseStudentIds(rawIdsStr)
    if (tokens.length === 0) {
      return {
        type: 'error',
        title: 'No Student IDs Provided',
        message: 'Please provide at least one student ID to export (e.g. /excel f5, f6, f7).',
        success: false
      }
    }

    const allStudents = await getAllStudents()
    const { matched, unmatched } = matchStudents(tokens, allStudents)

    if (matched.length === 0) {
      return {
        type: 'error',
        title: 'Students Not Found',
        message: `Could not find any students matching: ${tokens.join(', ')}`,
        success: false
      }
    }

    const matchedIds = matched.map(s => s.id)

    // Ensure we are on students or status page
    if (route.path !== '/students' && route.path !== '/status') {
      await router.push('/students')
      await nextTick()
    }

    dashboardStore.excelInitialSelectedIds = matchedIds
    dashboardStore.excelAutoOpenFieldPicker = true
    dashboardStore.isExcelModalOpen = true

    if (typeof (dashboardStore as any).openExportWithSelection === 'function') {
      try {
        (dashboardStore as any).openExportWithSelection(matchedIds, true)
      } catch (err) {
        console.warn('openExportWithSelection call failed:', err)
      }
    }

    const details = [
      `Selected students: ${matched.map(s => `${s.id} (${s.full_name})`).join(', ')}`
    ]
    if (unmatched.length > 0) {
      details.push(`⚠️ Not found: ${unmatched.join(', ')}`)
    }

    uiStore.addToast({
      type: 'info',
      title: 'Excel Export Prepared',
      message: `Selected ${matched.length} students. Choose fields to export.`
    })

    return {
      type: 'excel',
      title: `Exporting ${matched.length} Students to Excel`,
      message: `Preselected ${matched.length} students and opened the "Choose Fields to Export" menu.`,
      details,
      rawStudents: matched,
      success: true
    }
  }

  // ── 9. Operation: show university for <ids...> ─────────────────────────────
  const executeShowUniversity = async (rawIdsStr: string): Promise<BulkOperationResult> => {
    const tokens = parseStudentIds(rawIdsStr)
    if (tokens.length === 0) {
      return {
        type: 'error',
        title: 'No Student ID Provided',
        message: 'Please provide student ID (e.g. show university for f5).',
        success: false
      }
    }

    const allStudents = await getAllStudents()
    const { matched, unmatched } = matchStudents(tokens, allStudents)

    if (matched.length === 0) {
      return {
        type: 'error',
        title: 'Student Not Found',
        message: `Could not find any student matching: ${tokens.join(', ')}`,
        success: false
      }
    }

    const summaries: StudentUniversitySummary[] = matched.map(student => {
      const choices: UniversityChoice[] = []
      for (let i = 1; i <= 5; i++) {
        const name = ((student as any)[`university_${i}`] || '').trim()
        const status = (student as any)[`university_${i}_status`] || null
        const major = (student as any)[`university_${i}_major`] || null
        if (name) {
          choices.push({ slot: i, name, status, major })
        }
      }
      return {
        student,
        universities: choices,
        hasAny: choices.length > 0
      }
    })

    const details: string[] = []
    summaries.forEach(({ student, universities }) => {
      if (universities.length === 0) {
        details.push(`${student.id} — ${student.full_name}: No universities chosen yet`)
      } else {
        const uniText = universities
          .map(u => `Slot ${u.slot}: ${u.name}${u.status ? ` [${u.status}]` : ''}${u.major ? ` (${u.major})` : ''}`)
          .join(', ')
        details.push(`${student.id} — ${student.full_name}: ${uniText}`)
      }
    })

    if (unmatched.length > 0) {
      details.push(`⚠️ Not found: ${unmatched.join(', ')}`)
    }

    return {
      type: 'show_university',
      title: `University Choices (${matched.length} Student${matched.length === 1 ? '' : 's'})`,
      message: `Showing chosen universities for ${matched.map(s => s.id).join(', ')}.`,
      universitySummaries: summaries,
      rawStudents: matched,
      details,
      success: true
    }
  }

  // ── 10. Operation: set university <name> for <ids...> ──────────────────────
  const executeSetUniversity = async (uniNameRaw: string, rawIdsStr: string): Promise<BulkOperationResult> => {
    const unis = await getOfficialUniversities()
    const resolvedUniName = resolveOfficialUniversity(uniNameRaw, unis)

    if (!resolvedUniName) {
      return {
        type: 'error',
        title: 'Missing University Name',
        message: 'Please specify the university name (e.g. set university Inha for f6, g6, g15).',
        success: false
      }
    }

    const tokens = parseStudentIds(rawIdsStr)
    if (tokens.length === 0) {
      return {
        type: 'error',
        title: 'No Student IDs Provided',
        message: `Please specify student IDs to assign ${resolvedUniName} to.`,
        success: false
      }
    }

    const allStudents = await getAllStudents()
    const { matched, unmatched } = matchStudents(tokens, allStudents)

    if (matched.length === 0) {
      return {
        type: 'error',
        title: 'Students Not Found',
        message: `Could not find any students matching: ${tokens.join(', ')}`,
        success: false
      }
    }

    const details: string[] = []
    let updatedCount = 0
    let skippedDuplicateCount = 0

    for (const student of matched) {
      // 1. SMART DUPLICATE CHECK: Does student ALREADY have this university?
      let alreadySlot: number | null = null
      let alreadyExistingName: string | null = null
      for (let i = 1; i <= 5; i++) {
        const existing = ((student as any)[`university_${i}`] || '').trim()
        if (existing && isDuplicateUniversity(existing, resolvedUniName)) {
          alreadySlot = i
          alreadyExistingName = existing
          break
        }
      }

      if (alreadySlot !== null) {
        details.push(`⚠️ ${student.id} (${student.full_name}): Already has "${alreadyExistingName}" in Slot ${alreadySlot} (Skipped duplicate)`)
        skippedDuplicateCount++
        continue
      }

      // 2. Find first empty slot (1 to 5)
      let emptySlot: number | null = null
      for (let i = 1; i <= 5; i++) {
        const val = ((student as any)[`university_${i}`] || '').trim()
        if (!val) {
          emptySlot = i
          break
        }
      }

      if (emptySlot === null) {
        details.push(`⚠️ ${student.id} (${student.full_name}): All 5 university slots are already occupied`)
        continue
      }

      const updateField = `university_${emptySlot}`
      try {
        await studentsApi.updateStudent(student.id, {
          [updateField]: resolvedUniName
        })

        // Optimistically update queryClient cache
        queryClient.setQueryData<any>(['all-students-master'], (old: any) => {
          if (!old) return old
          const patch = (s: Student) => s.id === student.id ? { ...s, [updateField]: resolvedUniName } : s
          if (Array.isArray(old)) return old.map(patch)
          if (old.results && Array.isArray(old.results)) {
            return { ...old, results: old.results.map(patch) }
          }
          return old
        })

        const occupiedNote = emptySlot > 1
          ? ` (slots 1-${emptySlot - 1} had previous choices)`
          : ''
        details.push(`✓ ${student.id} (${student.full_name}): Set University ${emptySlot} -> ${resolvedUniName}${occupiedNote}`)
        updatedCount++
      } catch (err: any) {
        details.push(`✗ ${student.id} (${student.full_name}): Failed to update (${err.message || 'Error'})`)
      }
    }

    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })

    if (unmatched.length > 0) {
      details.push(`⚠️ Not found: ${unmatched.join(', ')}`)
    }

    uiStore.addToast({
      type: updatedCount > 0 ? 'success' : 'warning',
      title: 'University Assignment Complete',
      message: `Assigned ${resolvedUniName} to ${updatedCount} students (${skippedDuplicateCount} skipped duplicates).`
    })

    return {
      type: 'set_university',
      title: `Set University: ${resolvedUniName}`,
      message: `Assigned ${resolvedUniName} to ${updatedCount} student(s) · ${skippedDuplicateCount} skipped duplicates.`,
      details,
      rawStudents: matched,
      success: updatedCount > 0
    }
  }

  // ── 11. Operation: create folder <name> (User: "OPEN FOLDER BUSAN means create new folder names BUSAN not navigating") ──
  const executeFolderCreate = async (rawFolderName: string): Promise<BulkOperationResult> => {
    const trimmed = rawFolderName.trim().toUpperCase()
    if (!trimmed) {
      return {
        type: 'error',
        title: 'Folder Name Required',
        message: 'Please provide a folder name (e.g. open folder busan).',
        success: false
      }
    }

    const folders = await getFolders()
    const existing = folders.find(f => f.name.trim().toUpperCase() === trimmed)
    if (existing) {
      return {
        type: 'info',
        title: `Folder "${existing.name}" Already Exists`,
        message: `Folder "${existing.name}" already exists in the system.`,
        details: [`Folder ID: ${existing.id}`, `Name: ${existing.name}`],
        success: true
      }
    }

    try {
      const created = await studentsApi.createFolder(trimmed)
      if (created) {
        cachedFolders.value = [...folders, created]
        queryClient.setQueryData(['folders'], cachedFolders.value)
      }
      queryClient.invalidateQueries({ queryKey: ['folders'] })
      queryClient.invalidateQueries({ queryKey: ['student-options'] })
      queryClient.invalidateQueries({ queryKey: ['all-students-master'] })

      uiStore.addToast({
        type: 'success',
        title: 'Folder Created',
        message: `Created new folder "${trimmed}".`
      })

      return {
        type: 'create_folder',
        title: `Folder Created: ${trimmed}`,
        message: `Successfully created new folder "${trimmed}". Current view remains unchanged.`,
        details: [`New Folder: ${trimmed}`],
        success: true
      }
    } catch (err: any) {
      return {
        type: 'error',
        title: 'Failed to Create Folder',
        message: err.message || `Could not create folder "${trimmed}".`,
        success: false
      }
    }
  }

  // ── 11b. Operation: open folder <name> (explicit navigation) ─────────────
  const executeFolderOpen = async (rawFolderName: string): Promise<BulkOperationResult> => {
    const specialFolders = ['all', 'archive', 'deleted', 'hidden', 'except']
    const isSpecial = specialFolders.includes(rawFolderName.trim().toLowerCase())
    let folderDisplayName = ''

    if (isSpecial) {
      folderDisplayName = rawFolderName.trim()
    } else {
      const folders = await getFolders()
      const matched = matchFolder(rawFolderName, folders)

      if (!matched) {
        return {
          type: 'error',
          title: 'Folder Not Found',
          message: `Could not find a folder matching "${rawFolderName}". Available folders: ${folders.map(f => f.name).join(', ') || 'none'}`,
          success: false
        }
      }
      folderDisplayName = matched.name
    }

    // Navigate to /students if not already there
    if (route.path !== '/students') {
      await router.push('/students')
      await nextTick()
    }

    // Signal StudentsPage to switch folder
    dashboardStore.aiRequestedFolder = folderDisplayName

    uiStore.addToast({
      type: 'success',
      title: 'Folder Opened',
      message: `Navigated to folder: ${folderDisplayName}`
    })

    return {
      type: 'open_folder',
      title: `Opened Folder: ${folderDisplayName}`,
      message: `Switched to folder "${folderDisplayName}".`,
      details: [`Folder: ${folderDisplayName}`],
      success: true
    }
  }

  // ── 12. Operation: folder <name> add <ids> ────────────────────────────────
  const executeFolderAdd = async (rawFolderName: string, rawIdsStr: string): Promise<BulkOperationResult> => {
    const folders = await getFolders()
    let matched = matchFolder(rawFolderName, folders)

    // Auto-create folder if it doesn't exist yet
    if (!matched) {
      try {
        const created = await studentsApi.createFolder(rawFolderName.trim().toUpperCase())
        if (created) {
          cachedFolders.value = [...folders, created]
          queryClient.setQueryData(['folders'], cachedFolders.value)
          matched = created
        }
        queryClient.invalidateQueries({ queryKey: ['folders'] })
        queryClient.invalidateQueries({ queryKey: ['student-options'] })
      } catch (err) {
        // continue
      }
    }

    if (!matched) {
      return {
        type: 'error',
        title: 'Folder Not Found',
        message: `Could not find or create a folder matching "${rawFolderName}".`,
        success: false
      }
    }

    const tokens = parseStudentIds(rawIdsStr)
    if (tokens.length === 0) {
      return {
        type: 'error',
        title: 'No Student IDs Provided',
        message: `Please provide at least one student ID to add to folder "${matched.name}".`,
        success: false
      }
    }

    const allStudents = await getAllStudents()
    const { matched: students, unmatched } = matchStudents(tokens, allStudents)

    if (students.length === 0) {
      return {
        type: 'error',
        title: 'Students Not Found',
        message: `Could not find any students matching: ${tokens.join(', ')}`,
        success: false
      }
    }

    const studentIds = students.map(s => s.id)

    try {
      await studentsApi.addStudentsToFolder(matched.id, studentIds)

      // Optimistically update the student cache (add folder id to folder_ids)
      queryClient.setQueryData<any>(['all-students-master'], (old: any) => {
        if (!old) return old
        const patch = (s: Student) =>
          studentIds.includes(s.id)
            ? { ...s, folder_ids: Array.from(new Set([...(s.folder_ids || []), matched.id])) }
            : s
        if (Array.isArray(old)) return old.map(patch)
        if (old.results && Array.isArray(old.results)) return { ...old, results: old.results.map(patch) }
        return old
      })

      queryClient.invalidateQueries({ queryKey: ['folders'] })
      queryClient.invalidateQueries({ queryKey: ['all-students-master'] })
    } catch (err: any) {
      return {
        type: 'error',
        title: 'Failed to Add to Folder',
        message: err.message || 'An error occurred while adding students to the folder.',
        success: false
      }
    }

    const details: string[] = [
      `Added to folder "${matched.name}": ${students.map(s => `${s.id} (${s.full_name})`).join(', ')}`
    ]
    if (unmatched.length > 0) details.push(`⚠️ Not found: ${unmatched.join(', ')}`)

    uiStore.addToast({
      type: 'success',
      title: 'Added to Folder',
      message: `Added ${students.length} student(s) to "${matched.name}".`
    })

    return {
      type: 'folder_add',
      title: `Added to Folder: ${matched.name}`,
      message: `Successfully added ${students.length} student(s) to "${matched.name}".`,
      details,
      rawStudents: students,
      success: true
    }
  }

  // ── 13. Operation: set row color <color> <ids> ────────────────────────────
  const executeSetRowColor = async (color: string | null, rawIdsStr: string): Promise<BulkOperationResult> => {
    const tokens = parseStudentIds(rawIdsStr)
    if (tokens.length === 0) {
      return {
        type: 'error',
        title: 'No Student IDs Provided',
        message: 'Please provide at least one student ID (e.g. set row color red f1,f8,f2).',
        success: false
      }
    }

    const allStudents = await getAllStudents()
    const { matched, unmatched } = matchStudents(tokens, allStudents)

    if (matched.length === 0) {
      return {
        type: 'error',
        title: 'Students Not Found',
        message: `Could not find any students matching: ${tokens.join(', ')}`,
        success: false
      }
    }

    const details: string[] = []
    let successCount = 0

    for (const student of matched) {
      try {
        await studentsApi.setColor(student.id, { row_color: color, scope: 'mine' })

        // Optimistic cache update (Only Me row color)
        queryClient.setQueryData<any>(['all-students-master'], (old: any) => {
          if (!old) return old
          const patch = (s: Student) => s.id === student.id
            ? { ...s, my_row_color: color, ...(color === null ? { row_color: null } : {}) }
            : s
          if (Array.isArray(old)) return old.map(patch)
          if (old.results && Array.isArray(old.results)) return { ...old, results: old.results.map(patch) }
          return old
        })
        queryClient.setQueryData<Student | undefined>(
          ['student-detail', student.id],
          (old) => old ? { ...old, my_row_color: color, ...(color === null ? { row_color: null } : {}) } : undefined
        )

        const colorLabel = color || 'none (cleared)'
        details.push(`✓ ${student.id} (${student.full_name}): row color → ${colorLabel}`)
        successCount++
      } catch (err: any) {
        details.push(`✗ ${student.id} (${student.full_name}): failed (${err.message || 'Error'})`)
      }
    }

    if (unmatched.length > 0) details.push(`⚠️ Not found: ${unmatched.join(', ')}`)

    queryClient.invalidateQueries({ queryKey: ['all-students-master'] })

    const colorLabel = color ? color : 'cleared'
    uiStore.addToast({
      type: successCount > 0 ? 'success' : 'error',
      title: 'Row Color Updated',
      message: `Set row color (${colorLabel}) for ${successCount} student(s). Visible only to you.`
    })

    return {
      type: 'set_row_color',
      title: `Row Color: ${colorLabel}`,
      message: `Updated row color for ${successCount} student(s). This is visible only to you ("Only Me" scope).`,
      details,
      rawStudents: matched,
      success: successCount > 0
    }
  }

  // ── 14. Operation: filter students by certificate and score ────────────────
  const executeFilterStudents = async (cert?: string | null, rawScore?: string | null): Promise<BulkOperationResult> => {
    // Navigate to /students if not already there
    if (route.path !== '/students') {
      await router.push('/students')
      await nextTick()
    }

    let normalizedCert: string | null = cert ? cert.trim().toUpperCase() : null
    let normalizedScore: string | null = rawScore ? rawScore.trim() : null

    if (normalizedCert === 'NO CERT' || normalizedCert === 'NO_CERT' || normalizedCert === 'NO CERTIFICATE') {
      normalizedCert = 'NO CERTIFICATE'
    }

    if (normalizedCert === 'IELTS' && normalizedScore && !normalizedScore.includes('.') && !isNaN(Number(normalizedScore))) {
      normalizedScore = `${normalizedScore}.0`
    }

    // Apply filters to dashboardStore
    if (normalizedCert) {
      dashboardStore.selectedCerts = [normalizedCert]
    } else {
      dashboardStore.selectedCerts = []
    }

    if (normalizedScore) {
      dashboardStore.selectedScores = [normalizedScore]
    } else {
      dashboardStore.selectedScores = []
    }

    // Get all students to report matching count
    const allStudents = await getAllStudents()
    const matching = allStudents.filter(s => {
      // Check certificate
      if (normalizedCert) {
        let certMatch = false
        if (normalizedCert === 'NO CERTIFICATE') {
          certMatch = !s.language_certificate || s.language_certificate === 'NO CERTIFICATE'
        } else {
          certMatch = s.language_certificate === normalizedCert ||
                      s.language_certificate_2 === normalizedCert ||
                      s.language_certificate_3 === normalizedCert
        }
        if (!certMatch) return false
      }

      // Check score
      if (normalizedScore) {
        const studentScores = [s.certificate_score, s.certificate_score_2, s.certificate_score_3]
          .map(normalizeCertificateScore)
          .filter(Boolean)
        const targetNormalized = normalizeCertificateScore(normalizedScore)
        if (!studentScores.includes(targetNormalized)) return false
      }

      return true
    })

    const filterDesc = [
      normalizedCert ? `Cert: ${normalizedCert}` : null,
      normalizedScore ? `Score: ${normalizedScore}` : null
    ].filter(Boolean).join(', ')

    uiStore.addToast({
      type: 'success',
      title: 'Filter Applied',
      message: `Filtered roster by ${filterDesc} (${matching.length} student${matching.length === 1 ? '' : 's'}).`
    })

    const details = matching.slice(0, 15).map(s => {
      const scores = [s.certificate_score, s.certificate_score_2, s.certificate_score_3].filter(Boolean).join(', ')
      const scoreStr = scores ? ` [${scores}]` : ''
      return `${s.id} — ${s.full_name} (${s.language_certificate || 'None'}${scoreStr})`
    })
    if (matching.length > 15) {
      details.push(`... and ${matching.length - 15} more`)
    }

    return {
      type: 'filter',
      title: `Filter: ${filterDesc}`,
      message: `Found ${matching.length} student${matching.length === 1 ? '' : 's'} matching ${filterDesc}.`,
      details,
      rawStudents: matching,
      success: true
    }
  }

  // ── 14. Main Dispatcher: Real AI & Smart Fallbacks ────────────────────────
  const executeOperation = async (rawInput: string): Promise<BulkOperationResult> => {
    const input = rawInput.trim()
    if (!input) {
      return {
        type: 'error',
        title: 'Empty Command',
        message: 'Please enter a command or prompt to execute.',
        success: false
      }
    }

    isExecuting.value = true
    clarificationState.value.isOpen = false

    try {
      const unis = await getOfficialUniversities()
      const folders = await getFolders()
      const folderDtos = folders.map(f => ({ id: f.id, name: f.name }))

      // Quick Heuristic Check: "set university for f4,f5,f6" (explicit missing university)
      const missingUniMatch = input.match(/^(?:set|add)\s+universit(?:y)?\s+for\s+([a-zA-Z0-9\s,;]+)$/i)
      if (missingUniMatch) {
        const tokens = parseStudentIds(missingUniMatch[1])
        if (tokens.length > 0) {
          clarificationState.value = {
            isOpen: true,
            question: `Which university would you like to set for ${tokens.join(', ')}?`,
            field: 'university',
            studentIds: tokens,
            selectedUniversity: ''
          }
          const res: BulkOperationResult = {
            type: 'clarification',
            title: 'Which university to set?',
            message: `Please select the university to assign to ${tokens.join(', ')} below:`,
            details: [`Target students: ${tokens.join(', ')}`],
            success: true
          }
          lastResult.value = res
          return res
        }
      }

      // Try OpenAI Interpretation via Backend API
      try {
        const aiResp = await studentsApi.interpretAiCommand(input, unis, folderDtos)
        if (aiResp && aiResp.action) {
          // A. Clarification requested by AI
          if (aiResp.needs_clarification) {
            const studentIds = aiResp.student_ids || []
            clarificationState.value = {
              isOpen: true,
              question: aiResp.clarification_question || `Which university would you like to set for ${studentIds.join(', ')}?`,
              field: aiResp.clarification_field || 'university',
              studentIds,
              selectedUniversity: ''
            }
            const res: BulkOperationResult = {
              type: 'clarification',
              title: 'Clarification Needed',
              message: aiResp.clarification_question || `Please choose a university for ${studentIds.join(', ')}:`,
              details: [aiResp.message || 'Choose or search a university from the list below.'],
              success: true
            }
            lastResult.value = res
            return res
          }

          // B. Action: set_university
          if (aiResp.action === 'set_university' && aiResp.university_name && aiResp.student_ids?.length) {
            const res = await executeSetUniversity(aiResp.university_name, aiResp.student_ids.join(','))
            lastResult.value = res
            return res
          }

          // C. Action: show_university
          if (aiResp.action === 'show_university' && aiResp.student_ids?.length) {
            const res = await executeShowUniversity(aiResp.student_ids.join(','))
            lastResult.value = res
            return res
          }

          // D. Action: excel_export
          if (aiResp.action === 'excel_export' && aiResp.student_ids?.length) {
            const res = await executeExcel(aiResp.student_ids.join(','))
            lastResult.value = res
            return res
          }

          // E. Action: delete_students
          if (aiResp.action === 'delete_students' && aiResp.student_ids?.length) {
            const res = await executeDelete(aiResp.student_ids.join(','))
            lastResult.value = res
            return res
          }

          // F. Action: create_folder or open_folder (User: "OPEN FOLDER BUSAN means create new folder names BUSAN not navigating")
          if ((aiResp.action === 'create_folder' || aiResp.action === 'open_folder') && aiResp.folder_name) {
            const res = await executeFolderCreate(aiResp.folder_name)
            lastResult.value = res
            return res
          }

          // G. Action: add_to_folder
          if (aiResp.action === 'add_to_folder' && aiResp.folder_name && aiResp.student_ids?.length) {
            const res = await executeFolderAdd(aiResp.folder_name, aiResp.student_ids.join(','))
            lastResult.value = res
            return res
          }

          // H. Action: set_row_color
          if (aiResp.action === 'set_row_color' && aiResp.student_ids?.length) {
            const color = aiResp.color !== undefined ? aiResp.color : null
            const res = await executeSetRowColor(color, aiResp.student_ids.join(','))
            lastResult.value = res
            return res
          }

          // I. Action: filter_students
          if (aiResp.action === 'filter_students' && (aiResp.cert || aiResp.score)) {
            const res = await executeFilterStudents(aiResp.cert, aiResp.score)
            lastResult.value = res
            return res
          }

          // I. Action: other / response
          if (aiResp.action === 'other' && aiResp.message) {
            const res: BulkOperationResult = {
              type: 'info',
              title: 'AI Assistant',
              message: aiResp.message,
              success: true
            }
            lastResult.value = res
            return res
          }
        }
      } catch (aiErr) {
        console.warn('Backend AI interpretation failed, using smart local fallback:', aiErr)
      }

      // Local Smart Fallback Engine:
      // 1. /delete <ids...>
      const deleteMatch = input.match(/^\/delete\s+(.+)$/i)
      if (deleteMatch) {
        const res = await executeDelete(deleteMatch[1])
        lastResult.value = res
        return res
      }

      // 2. /excel <ids...>
      const excelMatch = input.match(/^\/excel\s+(.+)$/i)
      if (excelMatch) {
        const res = await executeExcel(excelMatch[1])
        lastResult.value = res
        return res
      }

      // 3. show university [for] <ids...>
      const showUniMatch = input.match(/^(?:show|get|view)\s+universit(?:y|ies)(?:\s+for)?\s+(.+)$/i)
      if (showUniMatch) {
        const res = await executeShowUniversity(showUniMatch[1])
        lastResult.value = res
        return res
      }

      // 4. set university <name> for <ids...>
      const setUniMatch = input.match(/^set\s+universit(?:y)?\s+(.+?)\s+for\s+(.+)$/i)
      if (setUniMatch) {
        const res = await executeSetUniversity(setUniMatch[1], setUniMatch[2])
        lastResult.value = res
        return res
      }

      // 5. open/create/new folder <name> (User: "OPEN FOLDER BUSAN means create new folder names BUSAN not navigating")
      const folderCreateMatch = input.match(/^(?:open|create|new|make)\s+(?:folder\s+)?(.+?)(?:\s+folder)?$/i)
      if (folderCreateMatch) {
        const res = await executeFolderCreate(folderCreateMatch[1].trim())
        lastResult.value = res
        return res
      }

      // 5b. Explicit navigation: go to / navigate to folder <name>
      const navFolderMatch = input.match(/^(?:go\s+to|navigate\s+to)\s+(?:folder\s+)?(.+?)(?:\s+folder)?$/i)
      if (navFolderMatch) {
        const res = await executeFolderOpen(navFolderMatch[1].trim())
        lastResult.value = res
        return res
      }

      // 6. folder <name> add <ids>  OR  add <ids> to folder <name>  (local fallback)
      const folderAddMatch1 = input.match(/^folder\s+(.+?)\s+add\s+(.+)$/i)
      if (folderAddMatch1) {
        const res = await executeFolderAdd(folderAddMatch1[1].trim(), folderAddMatch1[2].trim())
        lastResult.value = res
        return res
      }
      const folderAddMatch2 = input.match(/^add\s+(.+?)\s+to\s+(?:folder\s+)?(.+)$/i)
      if (folderAddMatch2) {
        const res = await executeFolderAdd(folderAddMatch2[2].trim(), folderAddMatch2[1].trim())
        lastResult.value = res
        return res
      }

      // 7. set/color row color <color> <ids>  (local fallback)
      const colorMatch = input.match(/^(?:set\s+(?:row\s+)?color|color)\s+(\w+)\s+(?:for\s+)?(.+)$/i)
      if (colorMatch) {
        const rawColor = colorMatch[1].trim().toLowerCase()
        const colorMap: Record<string, string | null> = {
          red: 'red', orange: 'orange', yellow: 'yellow', green: 'green',
          blue: 'blue', purple: 'purple', pink: 'pink', gray: 'gray', grey: 'gray',
          none: null, clear: null, remove: null, reset: null
        }
        const color = rawColor in colorMap ? colorMap[rawColor] : rawColor
        const res = await executeSetRowColor(color, colorMatch[2].trim())
        lastResult.value = res
        return res
      }

      // 8. clear/remove color <ids>  (local fallback)
      const clearColorMatch = input.match(/^(?:clear|remove|reset)\s+(?:row\s+)?color\s+(?:for\s+)?(.+)$/i)
      if (clearColorMatch) {
        const res = await executeSetRowColor(null, clearColorMatch[1].trim())
        lastResult.value = res
        return res
      }

      // 9. Filter by Certificate & Score (e.g. "filter ielts 6", "filter topik 2", "who has sat")
      const certFilterMatch = input.match(/^(?:filter|show|find|search|who\s+has|who\s+got)\s+(?:students?\s+with\s+|cert(?:ificate)?\s+)?(ielts|topik|sat|toefl|cefr|ska|no\s+certificate)\s*([0-9]+(?:\.[0-9]+)?)?$/i)
      if (certFilterMatch) {
        const res = await executeFilterStudents(certFilterMatch[1].trim(), certFilterMatch[2]?.trim())
        lastResult.value = res
        return res
      }

      const quickCertMatch = input.match(/^(ielts|topik|sat|toefl|cefr|ska)\s*([0-9]+(?:\.[0-9]+)?)?$/i)
      if (quickCertMatch) {
        const res = await executeFilterStudents(quickCertMatch[1].trim(), quickCertMatch[2]?.trim())
        lastResult.value = res
        return res
      }

      if (input.match(/^(?:clear|reset)\s+(?:all\s+)?filters?$/i)) {
        dashboardStore.resetAllFilters()
        const res: BulkOperationResult = {
          type: 'info',
          title: 'Filters Cleared',
          message: 'All roster filters have been reset to default.',
          success: true
        }
        lastResult.value = res
        return res
      }

      const res: BulkOperationResult = {
        type: 'info',
        title: 'Command Syntax Guide',
        message: 'Available bulk operations:',
        details: [
          '• /delete f1,f2,f3 — Archive/delete specified students',
          '• /excel f5,f6,f7 — Pre-select students and open "Choose Fields to Export"',
          '• show university for f5 — View chosen universities for student',
          '• set university inha for f6,g6,g15 — Assign university into first empty slot',
          '• set university for f4,f5,f6 — AI asks which university via dropdown',
          '• open folder busan — Navigate to the Busan folder',
          '• folder busan add f1,f5,f6 — Add students to a folder',
          '• set row color red f1,f8,f2 — Set personal row color (only you can see it)',
          '• clear color f1,f2 — Remove personal row color'
        ],
        success: false
      }
      lastResult.value = res
      return res
    } finally {
      isExecuting.value = false
    }
  }

  // Handle user completing an interactive clarification dropdown
  const submitClarification = async () => {
    if (!clarificationState.value.selectedUniversity || clarificationState.value.studentIds.length === 0) {
      return
    }
    const chosenUni = clarificationState.value.selectedUniversity
    const ids = clarificationState.value.studentIds.join(', ')
    clarificationState.value.isOpen = false
    isExecuting.value = true
    try {
      const res = await executeSetUniversity(chosenUni, ids)
      lastResult.value = res
    } finally {
      isExecuting.value = false
    }
  }

  return {
    isExecuting,
    lastResult,
    officialUniversities,
    clarificationState,
    getOfficialUniversities,
    getFolders,
    executeOperation,
    submitClarification,
    executeDelete,
    executeExcel,
    executeShowUniversity,
    executeSetUniversity,
    executeFolderCreate,
    executeFolderOpen,
    executeFolderAdd,
    executeSetRowColor,
    executeFilterStudents,
  }
}
