/**
 * Clipboard utilities for the Contract Document Editor
 * Handles clean HTML/text extraction, stripping external dark-mode styles (e.g. Telegram Desktop),
 * and calculating text block dimensions for A4 sheet placement.
 */

export const CANVAS_ELEMENT_CLIPBOARD_KEY = '__crm_type'
export const CANVAS_ELEMENT_CLIPBOARD_VALUE = 'contract_canvas_elements'

/**
 * Basic HTML escaping
 */
export function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * Check if a color string represents a white or near-white shade
 * (common from Telegram Desktop Dark Mode / dark theme apps)
 */
function isWhiteOrNearWhite(colorStr: string): boolean {
  const c = colorStr.toLowerCase().trim()
  if (!c) return false
  if (c === 'white' || c === '#fff' || c === '#ffffff' || c === '#fbfbfb' || c === '#fafafa') {
    return true
  }
  // Match rgb / rgba with high luminance
  const rgbMatch = c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/)
  if (rgbMatch) {
    const r = parseInt(rgbMatch[1], 10)
    const g = parseInt(rgbMatch[2], 10)
    const b = parseInt(rgbMatch[3], 10)
    // If all channels are bright (> 200), treat as white/light
    if (r > 200 && g > 200 && b > 200) {
      return true
    }
  }
  return false
}

/**
 * Format plain text into clean HTML paragraphs (<p>...</p>)
 */
export function formatPlainTextToHtml(text: string): string {
  if (!text || !text.trim()) return '<p></p>'

  const normalized = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  // Split on double newlines (paragraphs)
  const rawParagraphs = normalized.split(/\n{2,}/)

  const htmlParagraphs = rawParagraphs
    .map(p => p.trim())
    .filter(p => p.length > 0)
    .map(p => {
      // Within each paragraph, convert single newlines to <br>
      const withBr = escapeHtml(p).replace(/\n/g, '<br>')
      return `<p>${withBr}</p>`
    })

  return htmlParagraphs.length > 0 ? htmlParagraphs.join('') : `<p>${escapeHtml(normalized)}</p>`
}

/**
 * Clean and sanitize clipboard content (HTML or plain text)
 * Strips white text, dark backgrounds, foreign font families, and unwanted styling
 * while preserving rich text formatting like bold, italic, underline, links, and paragraphs.
 */
export function cleanClipboardContent(
  clipboardData: DataTransfer,
  defaultColor = '#000000'
): string {
  const html = clipboardData.getData('text/html')
  const plainText = clipboardData.getData('text/plain')

  // If HTML is present on clipboard, sanitize it
  if (html && html.trim()) {
    try {
      const parser = new DOMParser()
      const doc = parser.parseFromString(html, 'text/html')

      // Remove unwanted and dangerous tags
      const dangerousTags = doc.querySelectorAll('script, style, link, meta, title, head')
      dangerousTags.forEach(el => el.remove())

      // Unwrap semantic formatting tags (<b>, <strong>, <em>, <i>, <u>, <s>, <strike>)
      // so they don't visually override the element-level toolbar bold/italic/underline state.
      // Their text content is kept; only the tag itself is removed.
      const semanticFormatTags = doc.body.querySelectorAll('b, strong, em, i, u, s, strike')
      semanticFormatTags.forEach(el => {
        const parent = el.parentNode
        if (!parent) return
        // Move all children before the tag, then remove the tag itself
        while (el.firstChild) {
          parent.insertBefore(el.firstChild, el)
        }
        parent.removeChild(el)
      })

      // Clean all elements
      const elements = doc.body.querySelectorAll('*')
      elements.forEach(el => {
        const hEl = el as HTMLElement

        // Remove attributes that set colors, fonts, or styling
        hEl.removeAttribute('color')
        hEl.removeAttribute('bgcolor')
        hEl.removeAttribute('face')
        hEl.removeAttribute('size')
        hEl.removeAttribute('class')
        hEl.removeAttribute('id')

        // Clean inline styles
        if (hEl.style) {
          const color = hEl.style.color
          if (color && isWhiteOrNearWhite(color)) {
            hEl.style.color = defaultColor
          } else {
            // Strip color so it inherits the document's font color
            hEl.style.removeProperty('color')
          }

          // Strip backgrounds, fonts, and inline text-style overrides so that the
          // element-level toolbar controls (bold / italic / underline) remain the
          // single source of truth and the toolbar state always matches what renders.
          hEl.style.removeProperty('background')
          hEl.style.removeProperty('background-color')
          hEl.style.removeProperty('font-family')
          hEl.style.removeProperty('font-size')
          hEl.style.removeProperty('font-weight')
          hEl.style.removeProperty('font-style')
          hEl.style.removeProperty('text-decoration')
          hEl.style.removeProperty('line-height')
          hEl.style.removeProperty('letter-spacing')
          hEl.style.removeProperty('white-space')
          hEl.style.removeProperty('display')
          hEl.style.removeProperty('float')

          // If style attribute is now empty, remove it completely
          if (!hEl.getAttribute('style') || hEl.getAttribute('style')?.trim() === '') {
            hEl.removeAttribute('style')
          }
        }
      })

      // If the body content is wrapped only in non-semantic spans/divs with no other elements,
      // extract text and structure cleanly
      let bodyHtml = doc.body.innerHTML.trim()

      // Normalize any stray white color styles that might have slipped by
      bodyHtml = bodyHtml
        .replace(/color:\s*(#fff(fff)?|white|rgba?\(25[0-5],\s*25[0-5],\s*25[0-5][^)]*\))/gi, `color: ${defaultColor}`)
        .replace(/background-color:[^;"]+;?/gi, '')

      // Check if bodyHtml contains any paragraph or block tags
      const hasBlockTags = /<(p|div|table|ul|ol|h[1-6]|blockquote)/i.test(bodyHtml)
      if (!hasBlockTags && bodyHtml.length > 0) {
        // If it's just inline spans/text with <br>, wrap in <p>
        const parts = bodyHtml.split(/<br\s*\/?>\s*<br\s*\/?>/i)
        bodyHtml = parts
          .map(part => part.trim())
          .filter(part => part.length > 0)
          .map(part => `<p>${part}</p>`)
          .join('')
      }

      if (bodyHtml && bodyHtml !== '<p></p>' && bodyHtml !== '<br>') {
        return bodyHtml
      }
    } catch (err) {
      console.warn('Failed to sanitize HTML from clipboard, falling back to plain text:', err)
    }
  }

  // Fallback to plain text
  return formatPlainTextToHtml(plainText)
}

/**
 * Estimate required element height in mm based on text content, width, and font size
 * Default A4 text width is ~170mm (210 - 25 - 15) with 14pt Times New Roman.
 */
export function estimateTextHeightMm(
  textOrHtml: string,
  widthMm = 170,
  fontSizePt = 14
): number {
  if (!textOrHtml) return 16

  // Strip HTML tags to measure raw characters and paragraphs
  const rawText = textOrHtml
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .trim()

  const lines = rawText.split('\n')
  // In Times New Roman 14pt at ~170mm printable width, ~85 characters fit per line
  const charsPerLine = Math.max(40, Math.floor(widthMm * (85 / 170) * (14 / fontSizePt)))

  let totalLines = 0
  lines.forEach(line => {
    const trimmed = line.trim()
    if (trimmed.length === 0) {
      totalLines += 0.6 // empty line spacing
    } else {
      totalLines += Math.max(1, Math.ceil(trimmed.length / charsPerLine))
    }
  })

  totalLines = Math.max(1, Math.ceil(totalLines))
  // At 14pt (approx 4.9mm font height) with 1.5 line height, each line is ~7.4mm
  const mmPerLine = (fontSizePt * 0.352778) * 1.5
  const estimatedMm = Math.ceil(totalLines * mmPerLine + 6)

  // Clamp height between 16mm and 260mm (leaving room for A4 margins)
  return Math.max(16, Math.min(260, estimatedMm))
}
