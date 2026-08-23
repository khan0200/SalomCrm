import { ref, computed } from 'vue'
import { settingsApi, type CustomTag } from '@/api/settings'

const DEFAULT_TAGS: CustomTag[] = [
  { name: 'HAL', icon: '✅' },
  { name: 'JEONJU REG', icon: '📋' },
  { name: 'KDB', icon: '💳' },
  { name: 'Natija kutilmoqda', icon: '⏳' },
  { name: 'Topik 2', icon: '🏷️' },
  { name: 'til kursi', icon: '🏷️' },
  { name: 'BUFS TIL KURSI', icon: '🚩' },
  { name: 'BUFS APPFEE', icon: '🎫' },
  { name: 'AeroSpace', icon: '✈️' },
  { name: 'GIMCHEON OK', icon: '🏷️' },
  { name: 'WOOSUK APPFEE', icon: '💳' },
  { name: 'Documents Pending', icon: '📄' },
  { name: 'Visa Processing', icon: '🎫' },
  { name: 'Visa Approved', icon: '🛂' },
  { name: 'Departure', icon: '✈️' },
  { name: 'Arrived', icon: '📍' },
  { name: 'Scholarship Awarded', icon: '💎' },
  { name: 'Call', icon: '📞' },
  { name: 'Apply', icon: '🎓' },
  { name: 'Documents', icon: '📄' },
  { name: 'Payment', icon: '💰' },
]

// Global reactive state shared across all components & views
const tagsRegistry = ref<CustomTag[]>([...DEFAULT_TAGS])
const isFetched = ref(false)
const isLoading = ref(false)

export function useCustomTags() {
  const loadFromCache = () => {
    const saved = localStorage.getItem('customTagsRegistry')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) {
          const map = new Map<string, CustomTag>()
          DEFAULT_TAGS.forEach(t => map.set(t.name.toUpperCase(), t))
          parsed.forEach((t: any) => {
            if (t && t.name) map.set(String(t.name).toUpperCase(), { id: t.id, name: t.name, icon: t.icon || '🏷️' })
          })
          tagsRegistry.value = Array.from(map.values())
        }
      } catch (e) {
        console.error('Failed to parse cached customTagsRegistry', e)
      }
    }
  }

  const fetchTags = async (force = false) => {
    if (isFetched.value && !force) return
    try {
      isLoading.value = true
      const data = await settingsApi.getTags()
      if (Array.isArray(data) && data.length > 0) {
        tagsRegistry.value = data
        localStorage.setItem('customTagsRegistry', JSON.stringify(data))
      } else {
        tagsRegistry.value = [...DEFAULT_TAGS]
      }
      isFetched.value = true
    } catch (e) {
      console.warn('Could not fetch tags from server, using cached registry', e)
      loadFromCache()
    } finally {
      isLoading.value = false
    }
  }

  // Fast map lookup by tag name (case-insensitive)
  const tagIconMap = computed(() => {
    const map: Record<string, string> = {}
    // Seed defaults first
    DEFAULT_TAGS.forEach(t => {
      map[t.name.toLowerCase()] = t.icon
      map[t.name] = t.icon
    })
    // Overlay database registry tags
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
    
    // Quick special check for common aliases
    if (clean.toUpperCase() === 'HAL' || clean.toUpperCase() === 'DONE') return '✅'
    return '🏷️'
  }

  // Initialize from cache immediately
  if (!isFetched.value && tagsRegistry.value.length === DEFAULT_TAGS.length) {
    loadFromCache()
  }

  return {
    tagsRegistry,
    isLoading,
    isFetched,
    fetchTags,
    getTagIcon,
    tagIconMap,
    DEFAULT_TAGS,
  }
}
