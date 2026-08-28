import { ref, computed } from 'vue'
import { settingsApi, type CustomTag } from '@/api/settings'

// Fallback icon hints for standard keyword tags if not explicitly defined in tenant's custom registry
const FALLBACK_TAG_ICONS: Record<string, string> = {
  'HAL': '✅',
  'DONE': '✅',
  'CALL': '📞',
  'APPLY': '🎓',
  'DOCUMENTS': '📄',
  'DOCUMENTS PENDING': '📄',
  'PAYMENT': '💰',
  'VISA': '🎫',
  'VISA PROCESSING': '🎫',
  'VISA APPROVED': '🛂',
  'DEPARTURE': '✈️',
  'ARRIVED': '📍',
  'SCHOLARSHIP': '💎',
  'SCHOLARSHIP AWARDED': '💎',
  'PASSPORT': '🛂',
  'KDB': '💳',
  'REGISTRATION': '📋',
}

// Global reactive state strictly synced with backend per tenant
const tagsRegistry = ref<CustomTag[]>([])
const isFetched = ref(false)
const isLoading = ref(false)

export function useCustomTags() {
  const fetchTags = async (force = false) => {
    if (isFetched.value && !force) return
    try {
      isLoading.value = true
      const data = await settingsApi.getTags()
      tagsRegistry.value = Array.isArray(data) ? data : []
      isFetched.value = true
    } catch (e) {
      console.warn('Could not fetch custom tags from server', e)
    } finally {
      isLoading.value = false
    }
  }

  const setTags = (tags: CustomTag[]) => {
    tagsRegistry.value = Array.isArray(tags) ? tags : []
    isFetched.value = true
  }

  const clearTags = () => {
    tagsRegistry.value = []
    isFetched.value = false
  }

  // Fast map lookup by tag name (case-insensitive)
  const tagIconMap = computed(() => {
    const map: Record<string, string> = {}
    // 1. Fill from fallback dictionary
    Object.entries(FALLBACK_TAG_ICONS).forEach(([k, icon]) => {
      map[k.toLowerCase()] = icon
      map[k] = icon
    })
    // 2. Overlay tenant's custom registered tags
    tagsRegistry.value.forEach(t => {
      if (t && t.name) {
        map[t.name.toLowerCase()] = t.icon
        map[t.name] = t.icon
      }
    })
    return map
  })

  const getTagIcon = (tagName: string): string => {
    if (!tagName) return '🏷️'
    const clean = String(tagName).trim()
    if (tagIconMap.value[clean]) return tagIconMap.value[clean]
    if (tagIconMap.value[clean.toLowerCase()]) return tagIconMap.value[clean.toLowerCase()]
    return '🏷️'
  }

  return {
    tagsRegistry,
    isLoading,
    isFetched,
    fetchTags,
    setTags,
    clearTags,
    getTagIcon,
    tagIconMap,
  }
}
