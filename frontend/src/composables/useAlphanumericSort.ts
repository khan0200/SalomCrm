export function useAlphanumericSort() {
  const compareStudentIds = (idA: string = '', idB: string = '', order: 'asc' | 'desc' = 'asc'): number => {
    const parseId = (idStr: string) => {
      const str = idStr.trim()
      const match = str.match(/^([A-Za-z\s_-]*)(\d*)$/)
      if (match) {
        return {
          prefix: match[1] || '',
          num: match[2] ? parseInt(match[2], 10) : null,
        }
      }
      return { prefix: str, num: null }
    }

    const valA = parseId(idA)
    const valB = parseId(idB)

    const prefixComp = valA.prefix.localeCompare(valB.prefix, undefined, { sensitivity: 'base' })
    if (prefixComp !== 0) {
      return order === 'asc' ? prefixComp : -prefixComp
    }

    if (valA.num !== null && valB.num !== null) {
      return order === 'asc' ? valA.num - valB.num : valB.num - valA.num
    } else if (valA.num !== null) {
      return order === 'asc' ? 1 : -1
    } else if (valB.num !== null) {
      return order === 'asc' ? -1 : 1
    }

    return order === 'asc' ? idA.localeCompare(idB) : idB.localeCompare(idA)
  }

  return {
    compareStudentIds,
  }
}
