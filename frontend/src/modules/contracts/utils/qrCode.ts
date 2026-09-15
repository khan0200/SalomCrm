import qrcodegen from 'qrcode-generator'

/**
 * Renders a QR code as a PNG data URL by drawing the module matrix onto an
 * off-screen canvas ourselves. This (rather than the library's own SVG/PNG
 * helpers, which are hard-coded to black) is what lets the code be tinted
 * to the brand blue, and a plain <canvas>-derived PNG is the safest format
 * across every render path that consumes it (html2canvas screenshots,
 * direct jsPDF.addImage, and plain <img> preview).
 */
export function generateQrCodeDataUrl(
  text: string,
  options?: { size?: number; color?: string; background?: string; margin?: number }
): string {
  const size = options?.size ?? 160
  const color = options?.color ?? '#2563eb'
  const background = options?.background ?? '#ffffff'
  const margin = options?.margin ?? 1

  const qr = qrcodegen(0, 'M')
  qr.addData(text)
  qr.make()

  const moduleCount = qr.getModuleCount()
  const totalModules = moduleCount + margin * 2
  const cellSize = size / totalModules

  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) return ''

  ctx.fillStyle = background
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = color

  for (let row = 0; row < moduleCount; row++) {
    for (let col = 0; col < moduleCount; col++) {
      if (qr.isDark(row, col)) {
        const x = Math.round((col + margin) * cellSize)
        const y = Math.round((row + margin) * cellSize)
        const w = Math.ceil(cellSize)
        ctx.fillRect(x, y, w, w)
      }
    }
  }

  return canvas.toDataURL('image/png')
}
