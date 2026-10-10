import type { Student } from '@/types'

export type WorkflowStage = 'student' | 'apply' | 'invoice' | 'coa' | 'visa'

export const WORKFLOW_STAGES: { key: WorkflowStage; label: string }[] = [
  { key: 'student', label: 'Student' },
  { key: 'apply', label: 'Apply' },
  { key: 'invoice', label: 'Invoice' },
  { key: 'coa', label: 'COA' },
  { key: 'visa', label: 'VISA' },
]

// Legacy `embassy` rows saved before the Kanban redesign only ever used
// APPROVED/CANCELLED. CANCELLED is treated as REJECTED-equivalent here, in
// the backend's compute_workflow_stage (apps/students/services.py), and in
// EmbassyDocumentsDrawer.vue's visa selector - all three must agree.
const WORKFLOW_VISA_VALUES = new Set(['APPLIED', 'APPROVED', 'REJECTED', 'CANCELLED'])

/**
 * Pure function mirroring the backend's compute_workflow_stage
 * (backend/apps/students/services.py) - KEEP IN SYNC manually, Python and TS
 * can't share this logic directly. Priority order top-down, first match
 * wins: VISA > COA > INVOICE > APPLY > STUDENT. Every input shape has a
 * defined result (default 'student') - there is no invalid combination, so
 * unexpected/garbage values simply fall through to the earliest stage.
 */
export function calculateStudentWorkflowStage(student: Student): WorkflowStage {
  const visaStatus = student.embassy?.trim().toUpperCase()
  if (visaStatus && WORKFLOW_VISA_VALUES.has(visaStatus)) {
    return 'visa'
  }

  const coaVal = student.coa?.trim().toUpperCase()
  if (coaVal && coaVal !== 'NOT TAKEN') {
    return 'coa'
  }

  const isAnyUniAccepted = [
    student.university_1_status,
    student.university_2_status,
    student.university_3_status,
    student.university_4_status,
    student.university_5_status,
  ].some(status => status?.trim().toUpperCase() === 'ACCEPTED')

  const invoiceVal = student.invoice?.trim().toUpperCase()
  const hasActiveInvoice = Boolean(invoiceVal && invoiceVal !== 'NOT TAKEN')

  if (isAnyUniAccepted || hasActiveInvoice) {
    return 'invoice'
  }

  const isAnyUniApplied = [student.university_1_status, student.university_2_status]
    .some(status => status?.trim().toUpperCase() === 'APPLIED')

  if (isAnyUniApplied) {
    return 'apply'
  }

  return 'student'
}
