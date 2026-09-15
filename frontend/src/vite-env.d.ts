/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '*.png' {
  const src: string
  export default src
}

declare module '*.jpg' {
  const src: string
  export default src
}

declare module '*.svg' {
  const src: string
  export default src
}

declare module 'html2pdf.js' {
  const html2pdf: any
  export default html2pdf
}

declare module 'jspdf' {
  export const jsPDF: any
}

declare module 'html2canvas' {
  const html2canvas: any
  export default html2canvas
}

declare module 'qrcode-generator' {
  interface QRCode {
    addData(data: string, mode?: string): void
    make(): void
    getModuleCount(): number
    isDark(row: number, col: number): boolean
  }
  function qrcode(typeNumber: number, errorCorrectionLevel: 'L' | 'M' | 'Q' | 'H'): QRCode
  export default qrcode
}
