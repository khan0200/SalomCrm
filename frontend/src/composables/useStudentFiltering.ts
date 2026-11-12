import { computed, type Ref } from 'vue'
import type { Student } from '@/types'
import { useDocumentHelpers } from '@/composables/useDocumentHelpers'
import { normalizeCertificateScore } from '@/utils/certificateScore'

export interface StudentFilterCriteria {
  searchQuery: string
  searchMode: 'all' | 'id'
  selectedTariffs: string[]
  selectedLevels: string[]
  selectedGroups: string[]
  selectedBranches: string[]
  selectedCerts: string[]
  selectedScores: string[]
  selectedCertScores?: Record<string, string[]>
  selectedTags: string[]
  selectedLeads: string[]
  selectedCoordinators?: string[]
  selectedMissingDocs: string[]
}

/**
 * Universal certificate & score matcher used across all views (Students,
 * Documents, Status, Payments) to guarantee identical filtering results.
 */
export function matchesCertificate(
  student: Student,
  selectedCerts: string[],
  selectedCertScores?: Record<string, string[]>,
  selectedScores?: string[]
): boolean {
  if (selectedCerts.includes('__NONE__')) return false

  const certsToCheck = selectedCerts.length > 0 ? selectedCerts : null
  const hasCertScores = !!selectedCertScores && Object.keys(selectedCertScores).length > 0
  const hasScores = !!selectedScores && selectedScores.length > 0

  if (!certsToCheck && !hasCertScores && !hasScores) return true

  // 1. Check students with no certificate
  const isNoCert = (!student.language_certificate || student.language_certificate === 'NO CERTIFICATE') &&
                   (!student.language_certificate_2 || student.language_certificate_2 === 'NO CERTIFICATE') &&
                   (!student.language_certificate_3 || student.language_certificate_3 === 'NO CERTIFICATE')
  if (isNoCert) {
    return certsToCheck ? certsToCheck.includes('NO CERTIFICATE') : true
  }

  // 2. Check EXPECTED as a cert slot or score
  if (certsToCheck?.includes('EXPECTED')) {
    const hasExpected = (student.certificate_score || '').toUpperCase() === 'EXPECTED' ||
                        (student.certificate_score_2 || '').toUpperCase() === 'EXPECTED' ||
                        (student.certificate_score_3 || '').toUpperCase() === 'EXPECTED'
    if (hasExpected) return true
  }

  // 3. Check slots 1, 2, 3
  const slots = [
    { cert: student.language_certificate, score: student.certificate_score },
    { cert: student.language_certificate_2, score: student.certificate_score_2 },
    { cert: student.language_certificate_3, score: student.certificate_score_3 },
  ]

  return slots.some(({ cert, score }) => {
    if (!cert || cert === 'NO CERTIFICATE') return false
    const cleanCert = cert.trim()

    // Certificate type must match if filtered
    if (certsToCheck && !certsToCheck.includes(cleanCert)) return false

    // Check certificate-specific scores (e.g. TOPIK 3, IELTS 6.5)
    const allowedScores = selectedCertScores?.[cleanCert]
    if (allowedScores && allowedScores.length > 0) {
      if (allowedScores.includes('__NONE__')) return false
      const normScore = normalizeCertificateScore(score)
      const normAllowed = allowedScores.map(normalizeCertificateScore)
      if (!normAllowed.includes(normScore)) return false
    }

    // Check legacy global selectedScores
    if ((!allowedScores || allowedScores.length === 0) && selectedScores && selectedScores.length > 0) {
      if (selectedScores.includes('__NONE__')) return false
      const normScore = normalizeCertificateScore(score)
      const normSelected = selectedScores.map(normalizeCertificateScore)
      if (!normSelected.includes(normScore)) return false
    }

    return true
  })
}

/**
 * Shared search + 9-criteria filter logic used by both StudentsPage.vue and
 * PaymentsPage.vue against the same ['all-students-master'] roster, so the
 * two pages' Filter panel (StudentFilters.vue) behaves identically instead
 * of silently no-op'ing or duplicating slightly-different matching rules.
 *
 * `criteria` must be a Ref/computed (not a plain object snapshot) so changes
 * to the underlying dashboardStore fields re-trigger these computeds.
 *
 * Does NOT apply folder scope or permanently-deleted exclusion - callers
 * that have those concepts (StudentsPage.vue's folders; Payments' permanent
 * deletion exclusion) apply them before/after calling this.
 */
export function useStudentFiltering(students: Ref<Student[]>, criteria: Ref<StudentFilterCriteria>) {
  const { getEffectiveMissingDocs } = useDocumentHelpers()

  const searchedStudents = computed(() => {
    const c = criteria.value
    const q = c.searchQuery.trim().toLowerCase()
    if (!q) return students.value

    if (c.searchMode === 'id') {
      return students.value.filter(s => (s.id || '').toLowerCase().includes(q))
    }

    return students.value.filter(s => {
      const idMatch = (s.id || '').toLowerCase().includes(q)
      const nameMatch = (s.full_name || '').toLowerCase().includes(q)
      const passportMatch = (s.passport || '').toLowerCase().includes(q)
      const phone1Match = (s.phone1 || '').toLowerCase().includes(q)
      const phone2Match = (s.phone2 || '').toLowerCase().includes(q)
      const uni1Match = (s.university_1 || '').toLowerCase().includes(q)
      const uni2Match = (s.university_2 || '').toLowerCase().includes(q)
      const uni3Match = (s.university_3 || '').toLowerCase().includes(q)
      const uni4Match = (s.university_4 || '').toLowerCase().includes(q)
      const uni5Match = (s.university_5 || '').toLowerCase().includes(q)
      return idMatch || nameMatch || passportMatch || phone1Match || phone2Match || uni1Match || uni2Match || uni3Match || uni4Match || uni5Match
    })
  })

  const filteredStudents = computed(() => {
    const c = criteria.value
    let list = searchedStudents.value

    if (c.selectedTariffs.length > 0) {
      if (c.selectedTariffs.includes('__NONE__')) return []
      const hasNoTariff = c.selectedTariffs.includes('NO_TARIFF') || c.selectedTariffs.includes('No Tariff')
      const cleanTariffs = c.selectedTariffs.filter(t => t !== 'NO_TARIFF' && t !== 'No Tariff')
      list = list.filter(s => {
        if (hasNoTariff && (!s.tariff || cleanTariffs.includes(s.tariff))) return true
        return !!s.tariff && cleanTariffs.includes(s.tariff)
      })
    }

    if (c.selectedLevels.length > 0) {
      if (c.selectedLevels.includes('__NONE__')) return []
      const hasNoLevel = c.selectedLevels.includes('NO_LEVEL') || c.selectedLevels.includes('No Level')
      const cleanLevels = c.selectedLevels.filter(l => l !== 'NO_LEVEL' && l !== 'No Level')
      list = list.filter(s => {
        if (hasNoLevel && (!s.level || cleanLevels.includes(s.level) || cleanLevels.includes(s.level2 || ''))) return true
        return (!!s.level && cleanLevels.includes(s.level)) || (!!s.level2 && cleanLevels.includes(s.level2))
      })
    }

    if (c.selectedGroups.length > 0) {
      if (c.selectedGroups.includes('__NONE__')) return []
      const hasNoGroup = c.selectedGroups.includes('NO_GROUP') || c.selectedGroups.includes('No Group')
      const cleanGroups = c.selectedGroups.filter(g => g !== 'NO_GROUP' && g !== 'No Group')
      list = list.filter(s => {
        if (hasNoGroup && (!s.student_group || cleanGroups.includes(s.student_group))) return true
        return !!s.student_group && cleanGroups.includes(s.student_group)
      })
    }

    if (c.selectedBranches.length > 0) {
      if (c.selectedBranches.includes('__NONE__')) return []
      const hasNoBranch = c.selectedBranches.includes('NO_BRANCH') || c.selectedBranches.includes('No Branch')
      const cleanBranches = c.selectedBranches.filter(b => b !== 'NO_BRANCH' && b !== 'No Branch').map(b => b.trim().toLowerCase())
      list = list.filter(s => {
        if (!s.office) return hasNoBranch
        const sOffice = s.office.trim().toLowerCase()
        const sOfficeBase = sOffice.replace(/\s+offis$/i, '').replace(/\s+office$/i, '').trim()
        const matchesSelected = cleanBranches.some(b => {
          const bBase = b.replace(/\s+offis$/i, '').replace(/\s+office$/i, '').trim()
          return sOffice === b || sOfficeBase === bBase || sOffice.startsWith(b) || b.startsWith(sOffice)
        })
        if (hasNoBranch && matchesSelected) return true
        return matchesSelected
      })
    }

    // Unified certificate and score filtering
    if (c.selectedCerts.length > 0 || (c.selectedCertScores && Object.keys(c.selectedCertScores).length > 0) || c.selectedScores.length > 0) {
      list = list.filter(s => matchesCertificate(s, c.selectedCerts, c.selectedCertScores, c.selectedScores))
    }

    if (c.selectedTags.length > 0) {
      if (c.selectedTags.includes('__NONE__')) return []
      const hasNoTags = c.selectedTags.includes('NO_TAGS') || c.selectedTags.includes('No Tags')
      const cleanTags = c.selectedTags.filter(t => t !== 'NO_TAGS' && t !== 'No Tags')
      list = list.filter(s => {
        const studentTags = Array.isArray(s.task_tags) ? s.task_tags : []
        if (hasNoTags && studentTags.length === 0) return true
        return cleanTags.some(t => studentTags.includes(t))
      })
    }

    if (c.selectedLeads.length > 0) {
      const hasNoLead = c.selectedLeads.includes('NO_LEADBY') || c.selectedLeads.includes('No Lead by')
      const cleanLeads = c.selectedLeads.filter(l => l !== 'NO_LEADBY' && l !== 'No Lead by')
      // lead_by is free-text, so the same source can be saved with different
      // casing (e.g. "Ali Uncle" vs "ALI UNCLE") -- compare case-insensitively
      // or a student silently drops out of the filtered results.
      const cleanLeadsLower = cleanLeads.map(l => l.toLowerCase())
      list = list.filter(s => {
        if (hasNoLead && (!s.lead_by || cleanLeadsLower.includes(s.lead_by.toLowerCase()))) return true
        return !!s.lead_by && cleanLeadsLower.includes(s.lead_by.toLowerCase())
      })
    }

    if (c.selectedCoordinators && c.selectedCoordinators.length > 0) {
      if (c.selectedCoordinators.includes('__NONE__')) return []
      const hasNoCoord = c.selectedCoordinators.includes('NO_COORDINATOR') || c.selectedCoordinators.includes('No Coordinator')
      const cleanCoords = c.selectedCoordinators.filter(co => co !== 'NO_COORDINATOR' && co !== 'No Coordinator')
      const cleanCoordsLower = cleanCoords.map(co => co.toLowerCase())
      list = list.filter(s => {
        if (hasNoCoord && (!s.coordinator || cleanCoordsLower.includes(s.coordinator.toLowerCase()))) return true
        return !!s.coordinator && cleanCoordsLower.includes(s.coordinator.toLowerCase())
      })
    }

    if (c.selectedMissingDocs.length > 0) {
      list = list.filter(s => {
        const missingList = getEffectiveMissingDocs(s)
        return c.selectedMissingDocs.some(d => missingList.includes(d))
      })
    }

    return list
  })

  return { searchedStudents, filteredStudents }
}
