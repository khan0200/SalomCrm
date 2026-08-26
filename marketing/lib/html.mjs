/** Small HTML helpers shared by the layout and the page modules. */

/** Escape text destined for an HTML text node or a double-quoted attribute. */
export function esc(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * Escape a string for embedding inside a <script type="application/ld+json">
 * block. JSON-LD is parsed as raw text, so the only sequence that can break
 * out is `</script`; `<` is escaped to be safe against that and against
 * `<!--` comment tricks.
 */
export function jsonLd(data) {
  return JSON.stringify(data, null, 2).replace(/</g, '\\u003c')
}

/** Join class names, dropping falsy entries. */
export function cx(...parts) {
  return parts.filter(Boolean).join(' ')
}

/** Absolute URL for a site-relative path. */
export function abs(base, path) {
  return new URL(path, base.endsWith('/') ? base : base + '/').href
}

/**
 * Render a list of `{href, label, external}` links.
 * Anchor text is the label itself — descriptive anchor text is what tells
 * Google what the target page is about, so labels are never "click here".
 */
export function linkList(links) {
  return links
    .map((l) => {
      const rel = l.external ? ' rel="noopener"' : ''
      return `<li><a href="${esc(l.href)}"${rel}>${esc(l.label)}</a></li>`
    })
    .join('\n')
}
