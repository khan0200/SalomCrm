/**
 * "Times New Roman" doesn't exist on most non-Windows/Mac devices (notably
 * Android), so the OS substitutes a different serif font with different
 * metrics - the exact same element, at the exact same authored height,
 * wraps onto more lines there than it did wherever the height was
 * originally estimated, overflowing into whatever is positioned below it.
 * "Tinos" is Google's metric-compatible open replacement for Times New
 * Roman; loading it as a web font (see index.html) makes every device
 * render the identical glyphs, closing that gap for good. Author-chosen
 * fonts other than Times New Roman are left untouched.
 */
export function resolveFontFamilyCss(fontFamily?: string): string {
  if (!fontFamily || fontFamily === 'Times New Roman') {
    return "'Tinos', 'Times New Roman', Times, serif"
  }
  return `${fontFamily}, Times, serif`
}
