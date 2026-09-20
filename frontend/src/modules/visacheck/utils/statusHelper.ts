export function formatStatusName(statusValue: string | undefined | null): string {
  const raw = (statusValue || '').toUpperCase().trim()
  if (raw.includes('APPROV') || raw.includes('PASSED') || raw.includes('ISSUED') || raw.includes('허가') || raw.includes('TASDIQ')) return 'Approved'
  if (raw.includes('REJECT') || raw.includes('CANCEL') || raw.includes('RETURN') || raw.includes('EXPIRED') || raw.includes('불허') || raw.includes('RAD') || raw.includes('BEKOR')) return 'Cancelled'
  if (raw.includes('REVIEW') || raw.includes('PROCESSING') || raw.includes('SIMSA') || raw.includes('심사')) return 'Under Review'
  if (raw.includes('SUPPLEM') || raw.includes('보완')) return 'Supplement Needed'
  if (raw.includes('RECEIV') || raw.includes('SUBMIT') || raw.includes('JEOMSU') || raw.includes('접수') || raw.includes('APP')) return 'Application'
  if (!raw || raw.includes('PEND') || raw === 'UNKNOWN') return 'Pending'
  return raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase()
}
