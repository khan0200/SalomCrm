import { ref, computed } from 'vue'
import apiClient from '@/api/client'
import type { Student } from '@/types'

export interface QuickNoteSuggestionItem {
  id: string | number
  text: string
  sort_order?: number
  created_at?: string
}

export const DEFAULT_QUICK_NOTE_SUGGESTIONS: string[] = [
  "O'tgan semestrda atkazi bor",
  "IELTS ning Listening va Reading qismida 5.0 bor",
  "TOPIK endi oladi",
  "Til sertifikati endi oladi",
  "Telefonini olmadi",
  "Emaili noto'g'ri ekan",
  "Zagrani hali chiqmadi",
  "8-band bilan atkaz olgan",
  "Bank schet o'zi qo'yadi",
  "OTA-ONA rasmiy ish haqi yo'q (qilish kerak)",
  "Ota-ona ajrim bo'lgan",
  "Diplom / Attestat apostil qilinmagan",
  "App fee o'zi to'laydi",
  "1% lik universitet kerak",
  "Hujjatlarini to'liq olib kelmadi",
  "Shartnoma to'lovi qilinmagan",
  "Qayta qo'ng'iroq qilish kerak",
  "Viza chiqsa to'laydi",
  "IELTS section problem (E-viza)",
  "Natija kutilmoqda",
]

// Shared singleton reactive state across the app
const suggestions = ref<QuickNoteSuggestionItem[]>([])
const isLoading = ref(false)
const hasLoaded = ref(false)

export function useQuickNoteSuggestions() {
  const fetchSuggestions = async (force = false) => {
    if (hasLoaded.value && !force) return
    isLoading.value = true
    try {
      const res = await apiClient.get('/quick-note-suggestions/')
      const items: QuickNoteSuggestionItem[] = Array.isArray(res.data) ? res.data : (res.data?.results || [])
      suggestions.value = items
      hasLoaded.value = true
    } catch (err) {
      console.error('Failed to fetch quick note suggestions:', err)
      // If table is not accessible or offline, fallback to defaults
      if (suggestions.value.length === 0) {
        suggestions.value = DEFAULT_QUICK_NOTE_SUGGESTIONS.map((text, idx) => ({
          id: `def-${idx}`,
          text,
        }))
      }
    } finally {
      isLoading.value = false
    }
  }

  const addSuggestion = async (text: string): Promise<QuickNoteSuggestionItem | null> => {
    const trimmed = text.trim()
    if (!trimmed) return null

    // Prevent duplicate entries
    const existing = suggestions.value.find(s => s.text.toLowerCase() === trimmed.toLowerCase())
    if (existing) return existing

    try {
      const res = await apiClient.post('/quick-note-suggestions/', { text: trimmed })
      const created: QuickNoteSuggestionItem = res.data
      suggestions.value.unshift(created)
      return created
    } catch (err) {
      console.error('Failed to add suggestion:', err)
      // Fallback local add
      const fallbackItem: QuickNoteSuggestionItem = {
        id: `local-${Date.now()}`,
        text: trimmed,
      }
      suggestions.value.unshift(fallbackItem)
      return fallbackItem
    }
  }

  const updateSuggestion = async (id: string | number, newText: string): Promise<boolean> => {
    const trimmed = newText.trim()
    if (!trimmed) return false

    const item = suggestions.value.find(s => String(s.id) === String(id))
    if (!item) return false

    const oldText = item.text
    // Optimistic local update
    item.text = trimmed

    if (String(id).startsWith('def-') || String(id).startsWith('local-')) {
      // Local-only template, try saving to backend as new
      try {
        const res = await apiClient.post('/quick-note-suggestions/', { text: trimmed })
        item.id = res.data.id
        return true
      } catch (e) {
        return true
      }
    }

    try {
      await apiClient.patch(`/quick-note-suggestions/${id}/`, { text: trimmed })
      return true
    } catch (err) {
      console.error('Failed to update suggestion:', err)
      item.text = oldText // Rollback on failure
      return false
    }
  }

  const deleteSuggestion = async (id: string | number): Promise<boolean> => {
    const idx = suggestions.value.findIndex(s => String(s.id) === String(id))
    if (idx === -1) return false

    const removed = suggestions.value.splice(idx, 1)[0]

    if (String(id).startsWith('def-') || String(id).startsWith('local-')) {
      return true
    }

    try {
      await apiClient.delete(`/quick-note-suggestions/${id}/`)
      return true
    } catch (err) {
      console.error('Failed to delete suggestion:', err)
      suggestions.value.splice(idx, 0, removed) // Rollback on failure
      return false
    }
  }

  const getFilteredSuggestions = (query = '') => {
    const q = query.trim().toLowerCase()
    if (!q) return suggestions.value
    return suggestions.value.filter(s => s.text.toLowerCase().includes(q))
  }

  return {
    suggestions,
    isLoading,
    hasLoaded,
    fetchSuggestions,
    addSuggestion,
    updateSuggestion,
    deleteSuggestion,
    getFilteredSuggestions,
  }
}

/**
 * Legacy compatibility helper for quick note suggestions
 */
export function getQuickNoteSuggestions(allTenantStudents: Student[] = [], query = ''): string[] {
  const { suggestions, getFilteredSuggestions } = useQuickNoteSuggestions()
  if (suggestions.value.length > 0) {
    return getFilteredSuggestions(query).map(s => s.text)
  }

  const tenantSet = new Set<string>()
  const q = query.trim().toLowerCase()

  if (Array.isArray(allTenantStudents)) {
    for (const s of allTenantStudents) {
      if (s.quick_notes && typeof s.quick_notes === 'string') {
        const text = s.quick_notes.trim()
        if (text) {
          tenantSet.add(text)
        }
      }
    }
  }

  const combined = Array.from(tenantSet)
  for (const def of DEFAULT_QUICK_NOTE_SUGGESTIONS) {
    if (!combined.some(item => item.toLowerCase() === def.toLowerCase())) {
      combined.push(def)
    }
  }

  if (!q) return combined
  return combined.filter(item => item.toLowerCase().includes(q))
}
