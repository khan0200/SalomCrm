/**
 * Signature canvases are drawn on a large square/rectangular pad, and the
 * user's actual strokes can end up anywhere inside it (top, bottom, off to
 * one side). Exporting the canvas as-is bakes that empty margin into the
 * PNG, so the ink lands in a different spot on the document every time
 * depending on where it happened to be drawn on the pad.
 *
 * This trims the export to the ink's own bounding box (plus a small
 * padding) so the resulting image is just the signature, consistently
 * anchored when placed into the contract's {{signature}} slot.
 */
export function trimSignatureCanvas(canvas: HTMLCanvasElement, padding = 10): string {
  const ctx = canvas.getContext('2d')
  if (!ctx) return canvas.toDataURL('image/png')

  const { width, height } = canvas
  const { data } = ctx.getImageData(0, 0, width, height)

  let minX = width
  let minY = height
  let maxX = -1
  let maxY = -1

  const ALPHA_THRESHOLD = 10
  for (let y = 0; y < height; y++) {
    const rowOffset = y * width * 4
    for (let x = 0; x < width; x++) {
      const alpha = data[rowOffset + x * 4 + 3]
      if (alpha > ALPHA_THRESHOLD) {
        if (x < minX) minX = x
        if (x > maxX) maxX = x
        if (y < minY) minY = y
        if (y > maxY) maxY = y
      }
    }
  }

  // Nothing drawn - fall back to the raw (empty) canvas.
  if (maxX < minX || maxY < minY) return canvas.toDataURL('image/png')

  minX = Math.max(0, minX - padding)
  minY = Math.max(0, minY - padding)
  maxX = Math.min(width - 1, maxX + padding)
  maxY = Math.min(height - 1, maxY + padding)

  const trimmedWidth = maxX - minX + 1
  const trimmedHeight = maxY - minY + 1

  const trimmed = document.createElement('canvas')
  trimmed.width = trimmedWidth
  trimmed.height = trimmedHeight
  const trimmedCtx = trimmed.getContext('2d')
  if (!trimmedCtx) return canvas.toDataURL('image/png')

  trimmedCtx.drawImage(
    canvas,
    minX, minY, trimmedWidth, trimmedHeight,
    0, 0, trimmedWidth, trimmedHeight
  )

  return trimmed.toDataURL('image/png')
}
