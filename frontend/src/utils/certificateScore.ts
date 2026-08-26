// Certificate scores are free-text in the database, so the same score can be
// stored as "7" or "7.0" depending on how it was typed. The filter UI only
// offers the decimal form ("7.0", "6.5", ...), so a plain string comparison
// silently excludes students whose score was saved without the decimal —
// this normalizes both sides to the same numeric form before comparing.
// Non-numeric values (e.g. "EXPECTED") pass through unchanged.
export const normalizeCertificateScore = (value?: string | null): string => {
  const trimmed = (value || '').trim()
  if (!trimmed) return ''
  const num = Number(trimmed)
  if (Number.isNaN(num)) return trimmed.toLowerCase()
  return String(num)
}
