import type { VisaStudent } from '@/api/visa'

/**
 * Formats any date string (ISO, dot-separated, slash-separated) to standard YYYY-MM-DD format.
 */
export function formatDateYmd(raw?: string | null): string {
  if (!raw) return ''
  const str = raw.trim()
  if (!str || str === '--' || str.toLowerCase() === 'null' || str.toLowerCase() === 'undefined') {
    return ''
  }

  // Format 1: YYYY.MM.DD or YYYY-MM-DD or YYYY/MM/DD
  const m = str.match(/^(\d{4})[./-](\d{1,2})[./-](\d{1,2})/)
  if (m && m[1] && m[2] && m[3]) {
    const year = m[1]
    const month = m[2].padStart(2, '0')
    const day = m[3].padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  // Format 2: ISO timestamp e.g. 2026-03-09T14:20:00Z
  const ts = Date.parse(str)
  if (!isNaN(ts)) {
    const d = new Date(ts)
    const y = d.getFullYear()
    const mo = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${mo}-${day}`
  }

  return str.slice(0, 10)
}

/**
 * Returns the date when the current visa status was applied/entered (in YYYY-MM-DD format).
 * Returns empty string for 'PENDING', 'UNKNOWN', or when no date is available.
 */
export function getStatusAppliedDate(student: VisaStudent, normalizedStatus?: string): string {
  const s = (normalizedStatus || student.status || '').toUpperCase()

  // Exclude pending, unknown, or empty statuses
  if (
    !s ||
    s === 'PENDING' ||
    s === 'UNKNOWN' ||
    s.includes('NOT FOUND') ||
    s.includes('TOPILMADI') ||
    s.includes('NO APPLICATION') ||
    s.includes('MAVJUD EMAS')
  ) {
    return ''
  }

  // For Approved: status_date is when the visa was approved/issued (entry/judgment date)
  if (s.includes('APPROV') || s.includes('PASSED') || s.includes('ISSUED') || s.includes('허가')) {
    return formatDateYmd(student.status_date || student.application_date || student.updated_at || student.created_at)
  }

  // For Cancelled / Rejected: status_date is when the decision was recorded
  if (s.includes('REJECT') || s.includes('CANCEL') || s.includes('RETURN') || s.includes('EXPIRED') || s.includes('불허')) {
    return formatDateYmd(student.status_date || student.application_date || student.updated_at || student.created_at)
  }

  // For Under Review / Received / Supplement / Application:
  // status_date if available (e.g. review/supplement update), otherwise application_date (when applied/received)
  return formatDateYmd(student.status_date || student.application_date || student.updated_at || student.created_at)
}
