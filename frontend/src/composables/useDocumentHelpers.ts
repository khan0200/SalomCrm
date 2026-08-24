import type { Student } from '@/types'

/**
 * Normalizes and checks if a field has a valid, non-empty, non-dashed value.
 */
export const isFieldFilled = (val: any): boolean => {
  if (val === null || val === undefined) return false
  if (typeof val !== 'string') {
    return !!val
  }
  const trimmed = val.trim()
  return trimmed !== '' && trimmed !== '-'
}

/**
 * The full checklist of pickable "missing document" tags.
 */
export const PICK_NEEDED_LIST = [
  'APOSTILLE', 'BIRTH CERTIFICATE', 'MARRIAGE CERTIFICATE', 'AJRASHGANLIK',
  'Foreign passport', 'Student ID', 'Mother passport', 'MOTHER DEATH',
  'Father passport', 'FATHER DEATH', 'IELTS', 'TOEFL', 'SKA', 'TOPIK',
  'SAT', 'CEFR', '3.5x4.5', '2 ta nomer', 'Email', 'Manzil', 'Edu-Level', 'FULL OK'
]

/**
 * Physical copy documents tracked with an "in hand" counter.
 */
export const HAND_COUNT_DOCS = [
  { name: 'BIRTH CERTIFICATE', label: 'BC', key: 'bc_hand_count' },
  { name: 'MARRIAGE CERTIFICATE', label: 'MC', key: 'mc_hand_count' },
  { name: 'APOSTILLE', label: 'APOS', key: 'apos_hand_count' },
  { name: '3.5x4.5', label: 'PIC', key: 'pic_hand_count' },
] as const

/**
 * Centralized validation that automatically synchronizes a student's
 * profile fields with their Missing Documents (pick_needed) array.
 */
export function syncMissingDocuments(student: Student): string[] {
  const currentPick = student && Array.isArray(student.pick_needed) ? [...student.pick_needed] : []

  // If "FULL OK" is in the checklist, it overrides all missing documents
  if (currentPick.includes('FULL OK')) {
    return ['FULL OK']
  }

  // 1. "2 ta nomer" (Needs at least 2 valid phone numbers total)
  const phoneFields = [student.phone1, student.phone2, student.father_phone, student.mother_phone]
  const filledPhones = phoneFields.filter(isFieldFilled).length
  const needs2Nomer = filledPhones < 2

  // 2. "Email" (Email is required)
  const needsEmail = !isFieldFilled(student.email)

  // 3. "Foreign passport" (Passport number is required)
  const needsPassport = !isFieldFilled(student.passport)

  // 4. "Manzil" (Address is required)
  const needsAddress = !isFieldFilled(student.address)

  // 5. "Edu-Level" (Education Level is required)
  const needsLevel = !isFieldFilled(student.level)

  let updated = [...currentPick]

  const updateDoc = (docName: string, condition: boolean) => {
    if (condition) {
      if (!updated.includes(docName)) {
        updated.push(docName)
      }
    } else {
      updated = updated.filter(d => d !== docName)
    }
  }

  updateDoc('2 ta nomer', needs2Nomer)
  updateDoc('Email', needsEmail)
  updateDoc('Foreign passport', needsPassport)
  updateDoc('Manzil', needsAddress)
  updateDoc('Edu-Level', needsLevel)

  return updated
}

export function useDocumentHelpers() {
  const getEffectiveMissingDocs = (s: Student): string[] => syncMissingDocuments(s)

  const getDocColor = (docName: string) => {
    if (docName === 'FULL OK') {
      return { bg: '#10b981', text: '#ffffff', border: 'rgba(255,255,255,0.15)' }
    }
    const colors = [
      { bg: '#ef4444', text: '#ffffff', border: 'rgba(255,255,255,0.15)' },
      { bg: '#10b981', text: '#ffffff', border: 'rgba(255,255,255,0.15)' },
      { bg: '#f59e0b', text: '#ffffff', border: 'rgba(255,255,255,0.15)' },
      { bg: '#6366f1', text: '#ffffff', border: 'rgba(255,255,255,0.15)' },
      { bg: '#db2777', text: '#ffffff', border: 'rgba(255,255,255,0.15)' },
      { bg: '#ea580c', text: '#ffffff', border: 'rgba(255,255,255,0.15)' },
      { bg: '#2563eb', text: '#ffffff', border: 'rgba(255,255,255,0.15)' },
      { bg: '#8b5cf6', text: '#ffffff', border: 'rgba(255,255,255,0.15)' },
    ]
    let hash = 0
    for (let i = 0; i < docName.length; i++) {
      hash = docName.charCodeAt(i) + ((hash << 5) - hash)
    }
    return colors[Math.abs(hash) % colors.length]
  }

  const getDocRemainingCount = (s: Student, docName: string): number => {
    const missingList = getEffectiveMissingDocs(s)
    const isFullOk = missingList.includes('FULL OK')
    const isMissing = !isFullOk && missingList.includes(docName)

    if (isMissing) return 0

    let key: keyof Student
    if (docName === 'BIRTH CERTIFICATE') key = 'bc_hand_count'
    else if (docName === 'MARRIAGE CERTIFICATE') key = 'mc_hand_count'
    else if (docName === 'APOSTILLE') key = 'apos_hand_count'
    else if (docName === '3.5x4.5') key = 'pic_hand_count'
    else return 0

    const val = s[key]
    if (val !== undefined && val !== null) {
      return Number(val)
    }

    let used = 0
    if (s.university_1 && s.university_1.trim() !== '') used++
    if (s.university_2 && s.university_2.trim() !== '') used++
    if (s.university_3 && s.university_3.trim() !== '') used++
    if (s.university_4 && s.university_4.trim() !== '') used++
    if (s.university_5 && s.university_5.trim() !== '') used++
    return Math.max(0, 5 - used)
  }

  const getShortLabel = (d: string): string => {
    if (d === 'BIRTH CERTIFICATE') return 'BC'
    if (d === 'MARRIAGE CERTIFICATE') return 'MC'
    if (d === 'APOSTILLE') return 'APOS'
    if (d === '3.5x4.5') return 'PIC'
    return d
  }

  return {
    getEffectiveMissingDocs,
    getDocColor,
    getDocRemainingCount,
    getShortLabel,
    syncMissingDocuments,
    isFieldFilled,
    PICK_NEEDED_LIST,
    HAND_COUNT_DOCS,
  }
}
