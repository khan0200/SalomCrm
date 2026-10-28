import { computed } from 'vue'
import type { Student } from '@/types'

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

/**
 * Returns tenant-isolated quick note suggestions combining:
 * 1. Existing quick notes used across the current tenant's students.
 * 2. Curated standard agency default templates.
 */
export function getQuickNoteSuggestions(allTenantStudents: Student[], query = ''): string[] {
  const tenantSet = new Set<string>()
  const q = query.trim().toLowerCase()

  // 1. Gather all past quick notes belonging to the current tenant's students
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

  const tenantList = Array.from(tenantSet)

  // 2. Combine tenant records first, then standard defaults (without duplicates)
  const combined = [...tenantList]
  for (const def of DEFAULT_QUICK_NOTE_SUGGESTIONS) {
    if (!combined.some(item => item.toLowerCase() === def.toLowerCase())) {
      combined.push(def)
    }
  }

  // 3. Filter by search query if user is typing
  if (!q) {
    return combined
  }

  return combined.filter(item => item.toLowerCase().includes(q))
}

