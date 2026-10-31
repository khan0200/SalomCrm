import { ref } from 'vue'
import { settingsApi } from '@/api/settings'

export interface StatusColorOption {
  key: string
  label: string
  dotClass: string
  badgeClass: string
  hex: string
}

export const STATUS_COLOR_OPTIONS: StatusColorOption[] = [
  { key: 'blue', label: 'Blue', dotClass: 'bg-blue-500', badgeClass: 'bg-[#0052cc] text-white border-[#0052cc]', hex: '#0052cc' },
  { key: 'amber', label: 'Amber', dotClass: 'bg-amber-500', badgeClass: 'bg-[#ffab00] text-zinc-950 border-[#ffab00]', hex: '#ffab00' },
  { key: 'orange', label: 'Orange', dotClass: 'bg-orange-500', badgeClass: 'bg-[#ff8b00] text-white border-[#ff8b00]', hex: '#ff8b00' },
  { key: 'emerald', label: 'Emerald', dotClass: 'bg-emerald-500', badgeClass: 'bg-[#36b37e] text-white border-[#36b37e]', hex: '#36b37e' },
  { key: 'green', label: 'Green', dotClass: 'bg-green-500', badgeClass: 'bg-[#00875a] text-white border-[#00875a]', hex: '#00875a' },
  { key: 'rose', label: 'Rose / Red', dotClass: 'bg-rose-500', badgeClass: 'bg-[#ff5630] text-white border-[#ff5630]', hex: '#ff5630' },
  { key: 'purple', label: 'Purple', dotClass: 'bg-purple-500', badgeClass: 'bg-[#6554c0] text-white border-[#6554c0]', hex: '#6554c0' },
  { key: 'indigo', label: 'Indigo', dotClass: 'bg-indigo-500', badgeClass: 'bg-[#4c9aff] text-white border-[#4c9aff]', hex: '#4c9aff' },
  { key: 'cyan', label: 'Cyan / Sky', dotClass: 'bg-cyan-500', badgeClass: 'bg-[#00b8d9] text-white border-[#00b8d9]', hex: '#00b8d9' },
  { key: 'teal', label: 'Teal', dotClass: 'bg-teal-500', badgeClass: 'bg-[#00a3bf] text-white border-[#00a3bf]', hex: '#00a3bf' },
  { key: 'pink', label: 'Pink', dotClass: 'bg-pink-500', badgeClass: 'bg-[#e235d9] text-white border-[#e235d9]', hex: '#e235d9' },
  { key: 'zinc', label: 'Zinc / Gray', dotClass: 'bg-zinc-500', badgeClass: 'bg-[#6b778c] text-white border-[#6b778c]', hex: '#6b778c' },
]

export interface UniversityStatusItem {
  id: string
  name: string
  color_class?: string
  sort_priority?: number
}

// Mirrors UniversityStatusOption.sort_priority's model default: an unknown
// or newly added status ranks mid-pack rather than jumping above Accepted or
// sinking below Failed.
export const DEFAULT_SORT_PRIORITY = 50

// Used only until the registry loads, so a first paint still ranks sensibly
// instead of flashing slot order. The server values win once fetched.
const FALLBACK_PRIORITIES: Record<string, number> = {
  ACCEPTED: 1,
  APPLIED: 2,
  CHOSEN: 3,
  FAILED: 99,
}

const statusesRegistry = ref<UniversityStatusItem[]>([])
let isFetched = false

export function useUniversityStatuses() {
  const setStatuses = (data: any[]) => {
    statusesRegistry.value = Array.isArray(data)
      ? data.map((item: any) => ({
          id: String(item.id),
          name: item.name,
          color_class: item.color_class || 'blue',
          sort_priority: typeof item.sort_priority === 'number' ? item.sort_priority : DEFAULT_SORT_PRIORITY
        }))
      : []
    isFetched = true
  }

  const fetchStatuses = async (force = false) => {
    if (isFetched && !force) return
    try {
      const data = await settingsApi.getUniversityStatuses()
      setStatuses(Array.isArray(data) ? data : [])
      isFetched = true
    } catch (err) {
      console.error('Failed to fetch university statuses:', err)
    }
  }

  const resolveColor = (colorClassOrKey?: string): StatusColorOption => {
    if (!colorClassOrKey) return STATUS_COLOR_OPTIONS[0]
    const clean = colorClassOrKey.toLowerCase().replace(/^(text-|bg-)/, '').split('-')[0].trim()
    const found = STATUS_COLOR_OPTIONS.find(c => c.key === clean || clean.includes(c.key))
    return found || STATUS_COLOR_OPTIONS[0]
  }

  const getStatusItem = (statusName?: string | null): UniversityStatusItem | undefined => {
    if (!statusName) return undefined
    const norm = statusName.trim().toUpperCase()
    return statusesRegistry.value.find(s => s.name.trim().toUpperCase() === norm)
  }

  const getStatusColorOption = (statusNameOrColor?: string | null): StatusColorOption => {
    if (!statusNameOrColor) return STATUS_COLOR_OPTIONS[0]
    
    // Check if directly a known color key (e.g. 'pink', 'text-pink-500')
    const directColor = STATUS_COLOR_OPTIONS.find(c => c.key === statusNameOrColor.toLowerCase().replace(/^(text-|bg-)/, '').split('-')[0])
    if (directColor && !statusesRegistry.value.some(s => s.name.toLowerCase() === statusNameOrColor.toLowerCase())) {
      return directColor
    }

    // Check registry by name
    const item = getStatusItem(statusNameOrColor)
    if (item && item.color_class) {
      return resolveColor(item.color_class)
    }

    // Fallback based on known names
    const norm = statusNameOrColor.trim().toUpperCase()
    if (norm === 'ACCEPTED' || norm === 'FINISHED' || norm === 'ADMITTED') return resolveColor('emerald')
    if (norm === 'FAILED' || norm === 'REJECTED') return resolveColor('rose')
    if (norm === 'APPLIED') return resolveColor('orange')
    if (norm === 'CHOSEN') return resolveColor('blue')
    return STATUS_COLOR_OPTIONS[0]
  }

  // Emoji badge for a status. Only the four well-known names get a glyph;
  // agency-defined statuses fall through to undefined so callers render the
  // registry-coloured dot instead of a glyph that contradicts their colour.
  const STATUS_ICONS: Record<string, string> = {
    ACCEPTED: '✅',
    ADMITTED: '✅',
    FINISHED: '✅',
    APPLIED: '🟡',
    FAILED: '❌',
    REJECTED: '❌',
    CHOSEN: '🔷',
  }

  const getStatusIcon = (statusName?: string | null): string | undefined => {
    const norm = (statusName || '').trim().toUpperCase()
    if (!norm) return undefined
    return STATUS_ICONS[norm]
  }

  const getStatusDotClass = (statusNameOrColor?: string | null): string => {
    return getStatusColorOption(statusNameOrColor).dotClass
  }

  const getStatusBadgeClass = (statusNameOrColor?: string | null): string => {
    return getStatusColorOption(statusNameOrColor).badgeClass
  }

  // Rank for one status name. Falls back to the built-in table before the
  // registry loads, then to the mid-pack default for custom statuses.
  const getStatusPriority = (statusName?: string | null): number => {
    const norm = (statusName || '').trim().toUpperCase()
    if (!norm) return DEFAULT_SORT_PRIORITY
    const item = getStatusItem(norm)
    if (item && typeof item.sort_priority === 'number') return item.sort_priority
    return FALLBACK_PRIORITIES[norm] ?? DEFAULT_SORT_PRIORITY
  }

  // Order a student's university slots for display: by status rank first,
  // slot number second. The slot number tiebreak is what keeps universities
  // sharing a status in their existing order instead of shuffling. Returns
  // slot numbers only - the stored university_N columns are never reordered,
  // so editing and gap-compaction keep working off a stable identity.
  const sortUniversitySlots = (
    slots: number[],
    statusOf: (slot: number) => string | null | undefined
  ): number[] =>
    [...slots].sort((a, b) => {
      const diff = getStatusPriority(statusOf(a)) - getStatusPriority(statusOf(b))
      return diff !== 0 ? diff : a - b
    })

  return {
    statusesRegistry,
    setStatuses,
    getStatusPriority,
    sortUniversitySlots,
    fetchStatuses,
    resolveColor,
    getStatusItem,
    getStatusColorOption,
    getStatusIcon,
    getStatusDotClass,
    getStatusBadgeClass,
    STATUS_COLOR_OPTIONS
  }
}
