// Canvas Zoom Scaling & Style Utilities

/**
 * Normalizes legacy company requisites HTML to use relative 'em' units
 * instead of hardcoded '12pt', '10pt', or fixed 'px' margins.
 */
export function normalizeLegacyRequisites(html: string): string {
  if (!html || typeof html !== 'string') return ''
  if (!html.includes('BAJARUVCHI') && !html.includes('(M.O\')')) return html

  return html
    .replace(/font-size:\s*12pt;?/gi, '')
    .replace(/font-size:\s*10pt;?/gi, 'font-size: 0.85em;')
    .replace(/margin:\s*4px 0 10px;?/gi, 'margin: 0.3em 0 0.8em;')
    .replace(/margin:\s*4px 0;?/gi, 'margin: 0.28em 0;')
}

/**
 * Scales inline styles with absolute units (px, pt) by the current zoomLevel / 100.
 * Relative units like 'em', 'rem', '%', and unitless values are left intact so they
 * scale naturally with the container's font-size.
 */
export function scaleInlineStyles(html: string, zoomLevel: number): string {
  if (!html || typeof html !== 'string' || zoomLevel === 100) return html
  const scale = zoomLevel / 100

  // First normalize any legacy requisites blocks
  let result = normalizeLegacyRequisites(html)

  // 1. Scale font-size with explicit px or pt
  result = result.replace(/font-size:\s*([0-9.]+)(px|pt)/gi, (_, numStr, unit) => {
    const val = parseFloat(numStr)
    if (isNaN(val)) return _
    const scaled = Math.round(val * scale * 100) / 100
    return `font-size: ${scaled}${unit}`
  })

  // 2. Scale line-height with explicit units (px, pt)
  result = result.replace(/line-height:\s*([0-9.]+)(px|pt)/gi, (_, numStr, unit) => {
    const val = parseFloat(numStr)
    if (isNaN(val)) return _
    const scaled = Math.round(val * scale * 100) / 100
    return `line-height: ${scaled}${unit}`
  })

  // 3. Scale letter-spacing (px, pt)
  result = result.replace(/letter-spacing:\s*([0-9.]+)(px|pt)/gi, (_, numStr, unit) => {
    const val = parseFloat(numStr)
    if (isNaN(val)) return _
    const scaled = Math.round(val * scale * 100) / 100
    return `letter-spacing: ${scaled}${unit}`
  })

  // 4. Scale margin and padding properties (e.g. margin: 4px 0 10px; padding: 6px 18px;)
  result = result.replace(/(margin(?:-(?:top|bottom|left|right))?|padding(?:-(?:top|bottom|left|right))?):\s*([^;"]+)/gi, (fullMatch, prop, valuesStr) => {
    const scaledVals = valuesStr.replace(/([0-9.]+)(px|pt)/gi, (m: string, numStr: string, unit: string) => {
      const val = parseFloat(numStr)
      if (isNaN(val)) return m
      const scaled = Math.round(val * scale * 10) / 10
      return `${scaled}${unit}`
    })
    return `${prop}: ${scaledVals}`
  })

  // 5. Scale dimensions (width, height, min-width, max-width, min-height, max-height, border-radius)
  result = result.replace(/((?:min-|max-)?(?:width|height)|border-radius):\s*([0-9.]+)(px|pt)/gi, (_, prop, numStr, unit) => {
    const val = parseFloat(numStr)
    if (isNaN(val)) return _
    const scaled = Math.round(val * scale * 10) / 10
    return `${prop}: ${scaled}${unit}`
  })

  return result
}
