export interface ParsedRejectionReason {
  number?: string
  text: string
}

const CIRCLED_DIGITS_MAP: Record<string, string> = {
  '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
  '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10',
  '⑪': '11', '⑫': '12', '⑬': '13', '⑭': '14', '⑮': '15',
  '⑯': '16', '⑰': '17', '⑱': '18', '⑲': '19', '⑳': '20'
}

/**
 * Parses raw rejection reason string into an array of structured reasons with numbers.
 * Supports:
 * - "4. 입국목적을 소명할... 5. 대한민국..."
 * - "4 입국목적을 소명할... 5 대한민국..."
 * - "④ 입국목적을... ⑤ 대한민국..."
 * - "Rejected: 7. 입국목적을... 8. 가족관계..."
 */
export function parseRejectionReasons(raw: string | undefined | null): ParsedRejectionReason[] {
  if (!raw || typeof raw !== 'string') return []

  let str = raw.trim().replace(/^Rejected:\s*/i, '').replace(/^Sabab:\s*/i, '').trim()
  if (!str) return []

  // Replace unicode circled numbers with standardized spacing
  for (const [circled, num] of Object.entries(CIRCLED_DIGITS_MAP)) {
    str = str.split(circled).join(` ${num}. `)
  }

  // Check if string contains multiple numbered clauses
  const regex = /(?:^|\s+|[\n\r]+)(?:[\(\[\{]?(\d{1,2})[\.\)\:\s\]\}]+)\s*([\s\S]+?)(?=(?:[\n\r]+|\s+)(?:[\(\[\{]?\d{1,2}[\.\)\:\s\]\}]+)|$)/g
  const matches = Array.from(str.matchAll(regex))

  if (matches.length > 0) {
    const results: ParsedRejectionReason[] = []
    for (const match of matches) {
      const num = match[1]?.trim()
      const text = match[2]?.trim().replace(/^[\.\,\;\:\-\s]+/, '').trim()
      if (text) {
        results.push({ number: num, text })
      }
    }
    if (results.length > 0) return results
  }

  // Line-by-line fallback
  const lines = str.split(/[\n\r]+/).map(l => l.trim()).filter(Boolean)
  if (lines.length > 1) {
    return lines.map(line => {
      const m = line.match(/^[\(\[]?(\d{1,2})[\.\)\:\s\]]?\s*(.*)$/)
      if (m && m[2]) {
        return { number: m[1], text: m[2].trim() }
      }
      return { text: line }
    })
  }

  // Single line with leading number fallback
  const singleMatch = str.match(/^[\(\[]?(\d{1,2})[\.\)\:\s\]]?\s*(.*)$/)
  if (singleMatch && singleMatch[2]) {
    return [{ number: singleMatch[1], text: singleMatch[2].trim() }]
  }

  return [{ text: str }]
}
