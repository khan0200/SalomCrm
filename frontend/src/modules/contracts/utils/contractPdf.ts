import type { jsPDF as JsPdfType } from 'jspdf'
import {
  isCanvasDocumentJson,
  deserializeCanvasDocument,
  convertCanvasDocumentToHtml,
} from './contractCanvasConverter'
import { replaceVariablesInHtml } from './contractVariables'

/**
 * jsPDF and html2canvas together weigh ~600 KB. They are only needed at the
 * moment a PDF is actually generated, so they are pulled in on demand instead
 * of being bundled into every route that merely imports this module.
 */
let pdfLibsPromise: Promise<{
  jsPDF: typeof JsPdfType
  html2canvas: typeof import('html2canvas').default
}> | null = null

function loadPdfLibs() {
  if (!pdfLibsPromise) {
    pdfLibsPromise = Promise.all([
      import('jspdf'),
      import('html2canvas'),
    ]).then(([jspdfMod, html2canvasMod]) => ({
      jsPDF: jspdfMod.jsPDF,
      html2canvas: html2canvasMod.default,
    }))
  }
  return pdfLibsPromise
}

export interface PdfMarginOptions {
  top?: number // in mm
  right?: number // in mm
  bottom?: number // in mm
  left?: number // in mm
}

/**
 * The "Elektron Imzolangan Shartnoma" banner used to hard-code the word
 * VERIFIED regardless of the contract's actual status, so a rejected or
 * cancelled contract's PDF still claimed to be verified. Every caller
 * already passes verificationMeta.status - this just makes the banner
 * read it.
 */
function statusBadge(status?: string): { label: string; color: string } {
  const s = (status || 'verified').toLowerCase()
  if (s === 'verified') return { label: 'VERIFIED', color: '#059669' }
  if (s === 'cancelled') return { label: 'CANCELLED', color: '#dc2626' }
  if (s === 'rejected') return { label: 'REJECTED', color: '#dc2626' }
  if (s === 'pending') return { label: 'PENDING', color: '#d97706' }
  return { label: s.toUpperCase(), color: '#52525b' }
}

/**
 * Detects whether the current device is a mobile or tablet device.
 * Used to apply slight typography / scale adjustments (font-size, line-height,
 * margins) so dense contracts authored on desktop PC fit reliably within A4 page
 * boundaries on mobile browsers without overflowing or cutting off.
 */
export function isMobileDevice(): boolean {
  if (typeof window === 'undefined') return false
  const ua = navigator.userAgent || ''
  const isMobileUa = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile/i.test(ua)
  const hasTouch = (navigator.maxTouchPoints && navigator.maxTouchPoints > 0) || 'ontouchstart' in window
  const isNarrowScreen = window.innerWidth <= 900 || (typeof screen !== 'undefined' && screen.width <= 900)
  return isMobileUa || (hasTouch && isNarrowScreen)
}

/**
 * Format raw contract text to clean HTML if not already HTML
 */
export function prepareContractHtml(
  rawOrHtml: string,
  variableValues?: Record<string, string>,
  signatureData?: string,
  verificationMeta?: {
    contractNumber?: string
    studentId?: string
    verifiedAt?: string
    studentName?: string
    status?: string
  }
): string {
  if (!rawOrHtml) return '<p></p>'

  const mergedVars: Record<string, string> = { ...(variableValues || {}) }
  const badge = statusBadge(verificationMeta?.status)

  // Inject signature variable if provided
  if (signatureData) {
    const sigImg = `<img src="${signatureData}" style="max-height: 55px; max-width: 170px; object-fit: contain; vertical-align: bottom; display: inline-block;" alt="Talaba Imzosi" />`
    mergedVars['student_signature'] = sigImg
    mergedVars['signature'] = sigImg
    mergedVars['imzo'] = sigImg
    mergedVars['signature_data'] = signatureData
  }

  // If it's a Canva Canvas JSON document
  if (isCanvasDocumentJson(rawOrHtml)) {
    const doc = deserializeCanvasDocument(rawOrHtml)
    if (doc) {
      let canvasHtml = convertCanvasDocumentToHtml(doc, mergedVars)
      // If signature is provided and not already rendered in canvas HTML
      if (signatureData && !canvasHtml.includes('alt="Talaba Imzosi"') && !canvasHtml.includes('alt="Imzo"')) {
        canvasHtml += `
          <div style="margin: 20px 0; padding: 14px 18px; border: 1.5px solid #059669; border-radius: 10px; background: #f0fdf4; font-family: 'Times New Roman', serif; font-size: 11pt; color: #064e3b; page-break-inside: avoid;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-weight: bold; font-size: 11.5pt; text-transform: uppercase; color: #065f46;">Elektron Imzolangan Shartnoma</div>
                <div style="margin-top: 2px;">Shartnoma / Talaba ID: <strong>${verificationMeta?.contractNumber || verificationMeta?.studentId || mergedVars['contract_number'] || '—'}</strong></div>
                <div>Talaba: <strong>${verificationMeta?.studentName || mergedVars['student_name'] || '—'}</strong></div>
                <div>Holati: <strong style="color: ${badge.color};">${badge.label}</strong> (${verificationMeta?.verifiedAt || new Date().toLocaleDateString('uz-UZ')})</div>
              </div>
              <div style="text-align: right;">
                <div style="font-size: 9pt; color: #64748b; margin-bottom: 2px;">Talaba imzosi:</div>
                <img src="${signatureData}" style="max-height: 50px; max-width: 160px; object-fit: contain; background: white; padding: 2px 6px; border: 1px dashed #cbd5e1; border-radius: 4px;" alt="Talaba Imzosi" />
              </div>
            </div>
          </div>
        `
      }
      return canvasHtml
    }
  }

  let text = rawOrHtml.trim()

  // Clean old ASCII header markers
  text = text.replace(/═{5,}\s*1-BET\s*═{5,}/gi, '')
  text = text.replace(/═{5,}\s*\d+-BET\s*═{5,}/gi, '<div class="html2pdf__page-break page-break-always"></div>')

  // Robust universal variable substitution
  text = replaceVariablesInHtml(text, mergedVars)

  let processedHtml = ''
  if (text.startsWith('<') || /<[a-z][\s\S]*>/i.test(text)) {
    // Replace <hr> tags with html2pdf page break markers
    processedHtml = text.replace(/<hr[^>]*\/?>/gi, '<div class="html2pdf__page-break page-break-always"></div>')
  } else {
    const lines = text.split('\n')
    const htmlParts: string[] = []

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) {
        htmlParts.push('<p class="empty-line"><br></p>')
      } else if (trimmed.startsWith('═') || trimmed.startsWith('---') || trimmed.includes('-BET')) {
        htmlParts.push('<div class="html2pdf__page-break page-break-always"></div>')
      } else if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
        htmlParts.push(`<li>${trimmed.replace(/^[•\-]\s*/, '')}</li>`)
      } else if (trimmed === trimmed.toUpperCase() && trimmed.length > 5 && trimmed.length < 70 && !trimmed.includes(':')) {
        htmlParts.push(`<h3><strong>${trimmed}</strong></h3>`)
      } else {
        htmlParts.push(`<p>${trimmed}</p>`)
      }
    }
    processedHtml = htmlParts.join('')
  }

  // If signature is provided and not already rendered
  if (signatureData && !processedHtml.includes('alt="Talaba Imzosi"')) {
    processedHtml += `
      <div style="margin-top: 24px; padding: 14px 18px; border: 1.5px solid #059669; border-radius: 10px; background: #f0fdf4; font-family: 'Times New Roman', serif; font-size: 11pt; color: #064e3b; page-break-inside: avoid;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-weight: bold; font-size: 11.5pt; text-transform: uppercase; color: #065f46;">Elektron Imzolangan Shartnoma</div>
            <div style="margin-top: 2px;">Shartnoma / Talaba ID: <strong>${verificationMeta?.contractNumber || verificationMeta?.studentId || mergedVars['contract_number'] || '—'}</strong></div>
            <div>Talaba: <strong>${verificationMeta?.studentName || mergedVars['student_name'] || '—'}</strong></div>
            <div>Holati: <strong style="color: ${badge.color};">${badge.label}</strong> (${verificationMeta?.verifiedAt || new Date().toLocaleDateString('uz-UZ')})</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 9pt; color: #64748b; margin-bottom: 2px;">Talaba imzosi:</div>
            <img src="${signatureData}" style="max-height: 50px; max-width: 160px; object-fit: contain; background: white; padding: 2px 6px; border: 1px dashed #cbd5e1; border-radius: 4px;" alt="Talaba Imzosi" />
          </div>
        </div>
      </div>
    `
  }

  return processedHtml
}

type Html2Canvas = typeof import('html2canvas').default

interface VerificationMeta {
  contractNumber?: string
  studentId?: string
  verifiedAt?: string
  studentName?: string
  status?: string
}

/**
 * Draws one logical document (canvas-JSON or plain HTML, whichever
 * `rawOrHtml` turns out to be) onto pages of an already-created `pdf`
 * instance, without ever calling `.save()` on it - that stays the caller's
 * job, so a second document (e.g. the guardian consent appendix) can be
 * drawn straight after the first onto the very same PDF file.
 *
 * `startNewPage` controls only whether THIS document's own first page needs
 * an explicit `pdf.addPage()` before it: false for whichever document goes
 * first in the file (jsPDF's constructor already gives it a blank page to
 * draw on), true for every document appended after another one.
 */
async function renderDocumentIntoPdf(
  pdf: JsPdfType,
  html2canvas: Html2Canvas,
  rawOrHtml: string,
  margins: PdfMarginOptions,
  variableValues: Record<string, string> | undefined,
  signatureData: string | undefined,
  verificationMeta: VerificationMeta | undefined,
  startNewPage: boolean
): Promise<void> {
  const mergedVars: Record<string, string> = { ...(variableValues || {}) }
  const badge = statusBadge(verificationMeta?.status)

  if (signatureData) {
    const sigImg = `<img src="${signatureData}" style="max-height: 55px; max-width: 170px; object-fit: contain; vertical-align: bottom; display: inline-block;" alt="Talaba Imzosi" />`
    mergedVars['student_signature'] = sigImg
    mergedVars['signature'] = sigImg
    mergedVars['imzo'] = sigImg
    mergedVars['signature_data'] = signatureData
  }

  const verificationBanner = signatureData ? `
    <div style="margin: 20px 0 0; padding: 14px 18px; border: 1.5px solid #059669; border-radius: 10px; background: #f0fdf4; font-family: 'Times New Roman', serif; font-size: 11pt; color: #064e3b; page-break-inside: avoid;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <div style="font-weight: bold; font-size: 11.5pt; text-transform: uppercase; color: #065f46;">Elektron Imzolangan Shartnoma</div>
          <div style="margin-top: 2px;">Shartnoma / Talaba ID: <strong>${verificationMeta?.contractNumber || verificationMeta?.studentId || mergedVars['contract_number'] || '—'}</strong></div>
          <div>Talaba: <strong>${verificationMeta?.studentName || mergedVars['student_name'] || '—'}</strong></div>
          <div>Holati: <strong style="color: ${badge.color};">${badge.label}</strong> (${verificationMeta?.verifiedAt || new Date().toLocaleDateString('uz-UZ')})</div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 9pt; color: #64748b; margin-bottom: 2px;">Talaba imzosi:</div>
          <img src="${signatureData}" style="max-height: 50px; max-width: 160px; object-fit: contain; background: white; padding: 2px 6px; border: 1px dashed #cbd5e1; border-radius: 4px;" alt="Talaba Imzosi" />
        </div>
      </div>
    </div>
  ` : ''

  // CASE 1: Canva Canvas Document
  // CASE 1: Canva Canvas Document
  if (isCanvasDocumentJson(rawOrHtml)) {
    const doc = deserializeCanvasDocument(rawOrHtml)
    if (doc && Array.isArray(doc.pages) && doc.pages.length > 0) {
      let signatureRendered = false
      const isMobile = isMobileDevice()
      const fontScale = isMobile ? 0.92 : 1.0

      const totalPages = doc.pages.length
      for (let pageIdx = 0; pageIdx < doc.pages.length; pageIdx++) {
        const isLastPage = pageIdx === doc.pages.length - 1
        const singlePageDoc = { ...doc, pages: [doc.pages[pageIdx]] }
        let pageHtml = convertCanvasDocumentToHtml(singlePageDoc, mergedVars, {
          pageOffset: pageIdx,
          totalPages,
          fontScale,
        })

        if (pageHtml.includes('alt="Talaba Imzosi"') || pageHtml.includes('alt="Imzo"')) {
          signatureRendered = true
        }

        if (isLastPage && signatureData && !signatureRendered && verificationBanner) {
          pageHtml += verificationBanner
        }

        const pageContainer = document.createElement('div')
        pageContainer.className = 'canvas-pdf-render-page'
        pageContainer.style.cssText = `
          position: fixed;
          top: 0;
          left: 0;
          width: 210mm;
          min-height: 297mm;
          background: #ffffff;
          overflow: hidden;
          z-index: -99999;
          pointer-events: none;
          box-sizing: border-box;
          padding: 0;
          margin: 0;
          -webkit-text-size-adjust: 100%;
          text-size-adjust: 100%;
        `
        pageContainer.innerHTML = `
          <style>
            .canvas-a4-page-print, .canvas-a4-page-print * {
              -webkit-text-size-adjust: 100% !important;
              text-size-adjust: 100% !important;
            }
            .canvas-a4-page-print p { margin: ${isMobile ? '0.12em 0' : '0.2em 0'}; }
            .canvas-a4-page-print p:first-child { margin-top: 0 !important; }
            .canvas-a4-page-print p:last-child { margin-bottom: 0 !important; }
            ${isMobile ? `
              .canvas-a4-page-print .canvas-text-element p { margin: 0.12em 0 !important; }
              .canvas-a4-page-print .canvas-text-element ol, .canvas-a4-page-print .canvas-text-element ul { margin: 0.2em 0 !important; }
              .canvas-a4-page-print .canvas-text-element li { margin: 1px 0 !important; }
            ` : ''}
          </style>
          ${pageHtml}
        `
        document.body.appendChild(pageContainer)

        try {
          const images = Array.from(pageContainer.querySelectorAll('img'))
          if (images.length > 0) {
            await Promise.all(
              images.map(
                img =>
                  new Promise<void>(resolve => {
                    if (img.complete) return resolve()
                    img.onload = () => resolve()
                    img.onerror = () => resolve()
                  })
              )
            )
          }

          // Without an explicit windowHeight, html2canvas falls back to
          // the real window.innerHeight as its virtual viewport - on a
          // phone that's often 600-800px, far short of this A4 page's
          // ~1123px (297mm @ 96dpi) or more if this page's own content
          // overflows its nominal height. Anything below that line never
          // made it into the screenshot and was silently cut off when
          // addImage stretched the (shorter) capture to fill a full
          // 297mm-tall PDF page. pageContainer.scrollHeight is this
          // element's own actual rendered height, so it's always tall
          // enough regardless of device or content length.
          const windowHeight = Math.max(1200, pageContainer.scrollHeight)

          const canvas = await html2canvas(pageContainer, {
            scale: 2.5,
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff',
            scrollX: 0,
            scrollY: 0,
            windowWidth: 794,
            windowHeight,
            onclone: (clonedDoc: Document) => {
              const fixStyle = clonedDoc.createElement('style')
              fixStyle.textContent = `
                html, body, * {
                  -webkit-text-size-adjust: 100% !important;
                  text-size-adjust: 100% !important;
                }
                img {
                  display: inline-block !important;
                  vertical-align: baseline !important;
                }
                .canvas-text-element span[style*="border-bottom"],
                .canvas-text-element p[style*="border-bottom"] {
                  padding-bottom: 2px !important;
                }
                ${isMobile ? `
                  .canvas-a4-page-print .canvas-text-element p { margin: 0.12em 0 !important; }
                  .canvas-a4-page-print .canvas-text-element ol, .canvas-a4-page-print .canvas-text-element ul { margin: 0.2em 0 !important; }
                  .canvas-a4-page-print .canvas-text-element li { margin: 1px 0 !important; }
                ` : ''}
              `
              clonedDoc.head.appendChild(fixStyle)
            },
          })

          if (pageIdx > 0 || startNewPage) {
            pdf.addPage()
          }

          // JPEG at high quality keeps text crisp while landing at a
          // fraction of lossless PNG's size (a 4-page contract was 90+ MB
          // as PNG/NONE - unusable on a slow connection). 0.92 is visually
          // indistinguishable from PNG for flat text/line art like a
          // contract page.
          const imgData = canvas.toDataURL('image/jpeg', 0.92)
          pdf.addImage(imgData, 'JPEG', 0, 0, 210, 297, undefined, 'FAST')
        } finally {
          if (pageContainer.parentNode) {
            pageContainer.parentNode.removeChild(pageContainer)
          }
        }
      }
      return
    }
  }

  // CASE 2: Standard HTML / Text Document
  const isMobile = isMobileDevice()
  const bodyHtml = prepareContractHtml(rawOrHtml, mergedVars, signatureData, verificationMeta)
  const marginTop = isMobile ? (margins.top ? Math.min(margins.top, 16) : 16) : (margins.top ?? 20)
  const marginRight = margins.right ?? 15
  const marginBottom = isMobile ? (margins.bottom ? Math.min(margins.bottom, 16) : 16) : (margins.bottom ?? 20)
  const marginLeft = margins.left ?? 25

  const contentWidthMm = 210 - marginLeft - marginRight
  const contentHeightMm = 297 - marginTop - marginBottom

  const container = document.createElement('div')
  container.className = 'contract-pdf-render-container'
  container.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 794px;
    background: #ffffff;
    color: #111827;
    font-family: 'Times New Roman', serif;
    font-size: ${isMobile ? '12.2px' : '13.5px'};
    line-height: ${isMobile ? '1.48' : '1.65'};
    box-sizing: border-box;
    padding: 0;
    margin: 0;
    z-index: -99999;
    pointer-events: none;
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
  `
  container.innerHTML = `
    <style>
      .contract-pdf-content, .contract-pdf-content * {
        -webkit-text-size-adjust: 100% !important;
        text-size-adjust: 100% !important;
      }
      .contract-pdf-content {
        font-family: 'Times New Roman', Times, serif !important;
        font-size: ${isMobile ? '12.2px' : '13.5px'} !important;
        line-height: ${isMobile ? '1.48' : '1.65'} !important;
        color: #111827 !important;
        box-sizing: border-box;
        padding: 0;
      }
      .contract-pdf-content p {
        margin: ${isMobile ? '3.5px 0' : '5px 0'} !important;
        text-align: justify;
      }
      .contract-pdf-content h1 {
        font-size: ${isMobile ? '16px' : '18px'} !important;
        font-weight: bold;
        text-align: center;
        margin: ${isMobile ? '10px 0 6px' : '14px 0 8px'} !important;
      }
      .contract-pdf-content h2 {
        font-size: ${isMobile ? '14.5px' : '16px'} !important;
        font-weight: bold;
        margin: ${isMobile ? '8px 0 4px' : '12px 0 6px'} !important;
      }
      .contract-pdf-content h3 {
        font-size: ${isMobile ? '13px' : '14px'} !important;
        font-weight: bold;
        margin: ${isMobile ? '6px 0 3px' : '10px 0 4px'} !important;
      }
      .contract-pdf-content ol {
        list-style-type: decimal !important;
        padding-left: 1.8em !important;
        margin: ${isMobile ? '3px 0' : '4px 0'} !important;
      }
      .contract-pdf-content ol ol {
        list-style-type: lower-alpha !important;
        padding-left: 1.6em !important;
        margin: ${isMobile ? '1.5px 0' : '2px 0'} !important;
      }
      .contract-pdf-content ol ol ol {
        list-style-type: lower-roman !important;
        padding-left: 1.6em !important;
        margin: ${isMobile ? '1.5px 0' : '2px 0'} !important;
      }
      .contract-pdf-content ul {
        list-style-type: disc !important;
        padding-left: 1.8em !important;
        margin: ${isMobile ? '3px 0' : '4px 0'} !important;
      }
      .contract-pdf-content ul ul {
        list-style-type: circle !important;
        padding-left: 1.6em !important;
        margin: ${isMobile ? '1.5px 0' : '2px 0'} !important;
      }
      .contract-pdf-content ul ul ul {
        list-style-type: square !important;
        padding-left: 1.6em !important;
        margin: ${isMobile ? '1.5px 0' : '2px 0'} !important;
      }
      .contract-pdf-content li {
        margin: ${isMobile ? '1.5px 0' : '2px 0'} !important;
        line-height: ${isMobile ? '1.48' : 'inherit'} !important;
      }
      .contract-pdf-content table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: ${isMobile ? '6px 0' : '10px 0'} !important;
      }
      .contract-pdf-content td,
      .contract-pdf-content th {
        border: 1px solid #94a3b8 !important;
        padding: ${isMobile ? '4px 8px' : '6px 10px'} !important;
        font-size: ${isMobile ? '11px' : '12px'} !important;
        vertical-align: top !important;
        box-sizing: border-box;
      }
      .contract-pdf-content th {
        background-color: #f1f5f9 !important;
        font-weight: bold !important;
      }
      .contract-pdf-content table.table-border-none td,
      .contract-pdf-content table.table-border-none th {
        border: none !important;
      }
      .contract-pdf-content table.table-border-horizontal td,
      .contract-pdf-content table.table-border-horizontal th {
        border-left: none !important;
        border-right: none !important;
        border-top: 1px solid #94a3b8 !important;
        border-bottom: 1px solid #94a3b8 !important;
      }
      .contract-pdf-content [data-first-line-indent="true"] {
        text-indent: 1.25cm !important;
      }
      .contract-pdf-content [data-indent="1"] { margin-left: 1.25cm !important; }
      .contract-pdf-content [data-indent="2"] { margin-left: 2.5cm !important; }
      .contract-pdf-content [data-indent="3"] { margin-left: 3.75cm !important; }
      .contract-pdf-content [data-indent="4"] { margin-left: 5cm !important; }
      .contract-pdf-content [data-indent="5"] { margin-left: 6.25cm !important; }
      .contract-pdf-content [data-indent="6"] { margin-left: 7.5cm !important; }
      .page-break-always,
      .html2pdf__page-break {
        page-break-before: always !important;
        break-before: page !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        display: block !important;
      }
      ${isMobile ? `
        .contract-pdf-content span[style*="background:#111"],
        .contract-pdf-content span[style*="background: #111"],
        .contract-pdf-content span[style*="background:#000"],
        .contract-pdf-content span[style*="background: #000"] {
          padding: 4px 14px !important;
          font-size: 11.5px !important;
        }
      ` : ''}
    </style>
    <div class="contract-pdf-content">
      ${bodyHtml}
    </div>
  `
  document.body.appendChild(container)

  try {
    const images = Array.from(container.querySelectorAll('img'))
    if (images.length > 0) {
      await Promise.all(
        images.map(
          img =>
            new Promise<void>(resolve => {
              if (img.complete) return resolve()
              img.onload = () => resolve()
              img.onerror = () => resolve()
            })
        )
      )
    }

    // Same reasoning as the canvas-document path above: without an
    // explicit windowHeight, html2canvas falls back to the real
    // window.innerHeight (often well under 800px on a phone) as its
    // virtual viewport, silently cutting off anything below that line in
    // this single tall flowing container before it's later sliced into
    // pages. container.scrollHeight is this element's own actual
    // rendered height, so it's always tall enough regardless of content
    // length or device.
    const windowHeight = Math.max(1200, container.scrollHeight)

    const canvas = await html2canvas(container, {
      scale: 2.5,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
      scrollX: 0,
      scrollY: 0,
      windowWidth: 794,
      windowHeight,
      onclone: (clonedDoc: Document) => {
        const fixStyle = clonedDoc.createElement('style')
        fixStyle.textContent = `
          html, body, * {
            -webkit-text-size-adjust: 100% !important;
            text-size-adjust: 100% !important;
          }
          img {
            display: inline-block !important;
            vertical-align: baseline !important;
          }
          .contract-pdf-content span[style*="border-bottom"],
          .contract-pdf-content p[style*="border-bottom"] {
            padding-bottom: 2px !important;
          }
          ${isMobile ? `
            .contract-pdf-content, .contract-pdf-content * {
              -webkit-text-size-adjust: 100% !important;
              text-size-adjust: 100% !important;
            }
            .contract-pdf-content {
              font-size: 12.2px !important;
              line-height: 1.48 !important;
            }
            .contract-pdf-content p {
              margin: 3.5px 0 !important;
              line-height: 1.48 !important;
            }
            .contract-pdf-content li {
              margin: 1.5px 0 !important;
              line-height: 1.48 !important;
            }
            .contract-pdf-content ul, .contract-pdf-content ol {
              margin: 3px 0 !important;
            }
            .contract-pdf-content table {
              margin: 6px 0 !important;
            }
            .contract-pdf-content td, .contract-pdf-content th {
              padding: 4px 8px !important;
              font-size: 11px !important;
            }
            .contract-pdf-content span[style*="background:#111"],
            .contract-pdf-content span[style*="background: #111"],
            .contract-pdf-content span[style*="background:#000"],
            .contract-pdf-content span[style*="background: #000"] {
              padding: 4px 14px !important;
              font-size: 11.5px !important;
            }
          ` : ''}
        `
        clonedDoc.head.appendChild(fixStyle)
      },
    })

    const imgWidth = canvas.width
    const imgHeight = canvas.height
    // JPEG at high quality instead of lossless PNG - see the canvas-document
    // path above for why (same 90+ MB problem on multi-page contracts).
    const fullImgData = canvas.toDataURL('image/jpeg', 0.92)
    const scaledPdfHeight = (imgHeight * contentWidthMm) / imgWidth

    if (scaledPdfHeight <= contentHeightMm) {
      if (startNewPage) pdf.addPage()
      pdf.addImage(fullImgData, 'JPEG', marginLeft, marginTop, contentWidthMm, scaledPdfHeight, undefined, 'FAST')
    } else {
      const pageCanvasHeight = (imgWidth * contentHeightMm) / contentWidthMm
      let heightLeft = imgHeight
      let position = 0
      let isFirstSlice = true

      while (heightLeft > 0) {
        const sliceCanvas = document.createElement('canvas')
        sliceCanvas.width = imgWidth
        const currentSliceHeight = Math.min(heightLeft, pageCanvasHeight)
        sliceCanvas.height = currentSliceHeight
        const sliceCtx = sliceCanvas.getContext('2d')
        if (sliceCtx) {
          sliceCtx.fillStyle = '#ffffff'
          sliceCtx.fillRect(0, 0, imgWidth, currentSliceHeight)
          sliceCtx.drawImage(canvas, 0, position, imgWidth, currentSliceHeight, 0, 0, imgWidth, currentSliceHeight)
        }

        if (!isFirstSlice || startNewPage) pdf.addPage()
        isFirstSlice = false
        const sliceData = sliceCanvas.toDataURL('image/jpeg', 0.92)
        const slicePdfHeight = (currentSliceHeight * contentWidthMm) / imgWidth
        pdf.addImage(sliceData, 'JPEG', marginLeft, marginTop, contentWidthMm, slicePdfHeight, undefined, 'FAST')

        position += currentSliceHeight
        heightLeft -= currentSliceHeight
      }
    }
  } finally {
    if (container.parentNode) {
      container.parentNode.removeChild(container)
    }
  }
}

/**
 * Download document directly as PDF file. When `appendix` is given (the
 * guardian/kafillik consent template for a minor's contract), it is rendered
 * as extra pages onto the SAME pdf, starting on a fresh page after the main
 * document ends - one downloaded file, not two.
 */
export async function downloadContractAsPdf(
  title: string,
  rawOrHtml: string,
  margins: PdfMarginOptions = { top: 20, right: 15, bottom: 20, left: 25 },
  variableValues?: Record<string, string>,
  signatureData?: string,
  verificationMeta?: VerificationMeta,
  appendix?: { content: string; variableValues?: Record<string, string> }
): Promise<void> {
  const { jsPDF, html2canvas } = await loadPdfLibs()
  const safeTitle = (title || 'shartnoma').replace(/[/\\?%*:|"<>]/g, '_')

  const pdf = new jsPDF({
    unit: 'mm',
    format: 'a4',
    orientation: 'portrait',
    compress: true,
  })

  await renderDocumentIntoPdf(pdf, html2canvas, rawOrHtml, margins, variableValues, signatureData, verificationMeta, false)

  if (appendix?.content && appendix.content.trim()) {
    await renderDocumentIntoPdf(pdf, html2canvas, appendix.content, margins, appendix.variableValues ?? variableValues, undefined, undefined, true)
  }

  pdf.save(`${safeTitle}.pdf`)
}

/**
 * Native Browser Print-to-PDF Dialog helper (Printers & Save as PDF)
 */
export function printContractAsPdf(
  title: string,
  rawOrHtml: string,
  margins: PdfMarginOptions = { top: 20, right: 15, bottom: 20, left: 25 },
  variableValues?: Record<string, string>,
  signatureData?: string,
  verificationMeta?: {
    contractNumber?: string
    studentId?: string
    verifiedAt?: string
    studentName?: string
    status?: string
  }
): void {
  const safeTitle = (title || 'shartnoma').replace(/[/\\?%*:|"<>]/g, '_')
  const isCanvas = isCanvasDocumentJson(rawOrHtml)
  const bodyHtml = prepareContractHtml(rawOrHtml, variableValues, signatureData, verificationMeta)

  const marginTop = isCanvas ? 0 : (margins.top ?? 20)
  const marginRight = isCanvas ? 0 : (margins.right ?? 15)
  const marginBottom = isCanvas ? 0 : (margins.bottom ?? 20)
  const marginLeft = isCanvas ? 0 : (margins.left ?? 25)

  const printWindow = window.open('', '_blank', 'width=900,height=800')
  if (!printWindow) {
    // Popup blocked, fallback to window.print() on current page
    window.print()
    return
  }

  printWindow.document.open()
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>${safeTitle}</title>
      <style>
        @page {
          size: A4 portrait;
          margin: ${marginTop}mm ${marginRight}mm ${marginBottom}mm ${marginLeft}mm;
        }
        body {
          margin: 0;
          padding: 0;
          font-family: 'Times New Roman', serif;
          font-size: 13.5px;
          line-height: 1.65;
          color: #000;
          background: #fff;
        }
        p { margin: 6px 0; text-align: justify; }
        h1 { font-size: 18px; text-align: center; margin: 12px 0 6px; }
        h2 { font-size: 16px; margin: 10px 0 5px; }
        h3 { font-size: 14px; margin: 8px 0 4px; }
        ol { list-style-type: decimal !important; padding-left: 1.8em !important; margin: 4px 0 !important; }
        ol ol { list-style-type: lower-alpha !important; padding-left: 1.6em !important; margin: 2px 0 !important; }
        ol ol ol { list-style-type: lower-roman !important; padding-left: 1.6em !important; margin: 2px 0 !important; }
        ul { list-style-type: disc !important; padding-left: 1.8em !important; margin: 4px 0 !important; }
        ul ul { list-style-type: circle !important; padding-left: 1.6em !important; margin: 2px 0 !important; }
        ul ul ul { list-style-type: square !important; padding-left: 1.6em !important; margin: 2px 0 !important; }
        li { margin: 2px 0 !important; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; page-break-inside: avoid; }
        td, th { border: 1px solid #333; padding: 6px 10px; font-size: 12px; }
        th { background: #f4f4f5; }
        table.table-border-none td, table.table-border-none th { border: none !important; }
        table.table-border-horizontal td, table.table-border-horizontal th {
          border-left: none !important;
          border-right: none !important;
          border-top: 1px solid #333 !important;
          border-bottom: 1px solid #333 !important;
        }
        [data-first-line-indent="true"] { text-indent: 1.25cm !important; }
        [data-indent="1"] { margin-left: 1.25cm !important; }
        [data-indent="2"] { margin-left: 2.5cm !important; }
        [data-indent="3"] { margin-left: 3.75cm !important; }
        [data-indent="4"] { margin-left: 5cm !important; }
        .page-break-always { page-break-before: always !important; break-before: page !important; }
      </style>
    </head>
    <body>
      ${bodyHtml}
      <script>
        window.onload = function() {
          window.focus();
          window.print();
          setTimeout(function() { window.close(); }, 500);
        };
      </script>
    </body>
    </html>
  `)
  printWindow.document.close()
}
