// Node-compatible replacement for frontend/src/modules/contracts/utils/qrCode.ts.
//
// The original rasterizes qrcode-generator's module matrix via
// document.createElement('canvas'), which doesn't exist in plain Node.
// qrcode-generator's matrix logic itself (addData/make/getModuleCount/
// isDark) is pure, DOM-free data - only the "paint pixels" step needs a
// canvas. pngjs provides that same pixel-buffer-to-PNG step without one,
// keeping this fully synchronous so it's a drop-in replacement for
// contractVariables.ts's `import { generateQrCodeDataUrl } from './qrCode'`
// (same name, same signature, same data-URL return shape) - zero changes
// needed in the vendored contractVariables.ts.
import qrcodegen from 'qrcode-generator'
import { PNG } from 'pngjs'

export interface QrOptions {
  size?: number
  color?: string
  background?: string
  margin?: number
}

function hexToRgb(hex: string): [number, number, number] {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex.trim())
  if (!m) return [0, 0, 0]
  return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)]
}

export function generateQrCodeDataUrl(text: string, options?: QrOptions): string {
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

  const [fr, fg, fb] = hexToRgb(color)
  const [br, bg, bb] = hexToRgb(background)

  const png = new PNG({ width: size, height: size })
  // Fill background first - same order as the original canvas version
  // (fillRect background, then fillRect each dark module on top).
  for (let i = 0; i < png.data.length; i += 4) {
    png.data[i] = br
    png.data[i + 1] = bg
    png.data[i + 2] = bb
    png.data[i + 3] = 255
  }

  const setPixel = (x: number, y: number) => {
    if (x < 0 || y < 0 || x >= size || y >= size) return
    const idx = (size * y + x) << 2
    png.data[idx] = fr
    png.data[idx + 1] = fg
    png.data[idx + 2] = fb
    png.data[idx + 3] = 255
  }

  for (let row = 0; row < moduleCount; row++) {
    for (let col = 0; col < moduleCount; col++) {
      if (!qr.isDark(row, col)) continue
      const x0 = Math.round((col + margin) * cellSize)
      const y0 = Math.round((row + margin) * cellSize)
      const w = Math.ceil(cellSize)
      for (let dy = 0; dy < w; dy++) {
        for (let dx = 0; dx < w; dx++) {
          setPixel(x0 + dx, y0 + dy)
        }
      }
    }
  }

  const buffer = PNG.sync.write(png)
  return `data:image/png;base64,${buffer.toString('base64')}`
}
