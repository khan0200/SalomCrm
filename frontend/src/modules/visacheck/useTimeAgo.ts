import { ref } from 'vue'

// Reactive global timestamp updated every 30 seconds
export const currentTimestamp = ref(Date.now())

if (typeof window !== 'undefined') {
  setInterval(() => {
    currentTimestamp.value = Date.now()
  }, 30000)
}

/**
 * Formats a timestamp into a compact relative time string:
 * - < 1 min: "Just now"
 * - 1..59 mins: "X min. ago"
 * - 1..23 hours: "X hr. ago"
 * - 1..6 days: "X d. ago"
 * - >= 7 days: "DD/MM/YY"
 * Automatically reactive when used in Vue templates.
 */
export function formatTimestampCompact(ts: string | undefined | null): string {
  if (!ts) return '—'
  // Read reactive ref so Vue tracks it as a dependency for real-time updates
  const now = currentTimestamp.value

  try {
    const d = new Date(ts)
    const time = d.getTime()
    if (isNaN(time)) return String(ts)

    const diff = now - time
    if (diff < 0) return 'Just now'

    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins} min. ago`

    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours} hr. ago`

    const days = Math.floor(hours / 24)
    if (days < 7) return `${days} d. ago`

    return d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: '2-digit' })
  } catch {
    return String(ts)
  }
}
