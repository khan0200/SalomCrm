import html2pdf from 'html2pdf.js'
import {
  isCanvasDocumentJson,
  deserializeCanvasDocument,
  convertCanvasDocumentToHtml,
} from './contractCanvasConverter'
import { replaceVariablesInHtml } from './contractVariables'

export interface PdfMarginOptions {
  top?: number // in mm
  right?: number // in mm
  bottom?: number // in mm
  left?: number // in mm
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

  // Inject signature variable if provided
  if (signatureData) {
    const sigImg = `<img src="${signatureData}" style="max-height: 55px; max-width: 170px; object-fit: contain; vertical-align: middle; display: inline-block;" alt="Talaba Imzosi" />`
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
                <div>Holati: <strong style="color: #059669;">VERIFIED</strong> (${verificationMeta?.verifiedAt || new Date().toLocaleDateString('uz-UZ')})</div>
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
            <div>Holati: <strong style="color: #059669;">VERIFIED</strong> (${verificationMeta?.verifiedAt || new Date().toLocaleDateString('uz-UZ')})</div>
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

/**
 * Download document directly as PDF file
 */
export async function downloadContractAsPdf(
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
): Promise<void> {
  const safeTitle = (title || 'shartnoma').replace(/[/\\?%*:|"<>]/g, '_')
  const isCanvas = isCanvasDocumentJson(rawOrHtml)
  const bodyHtml = prepareContractHtml(rawOrHtml, variableValues, signatureData, verificationMeta)

  // For canvas, margins are already baked into the absolute mm coordinates of each sheet
  const marginTop = isCanvas ? 0 : (margins.top ?? 20)
  const marginRight = isCanvas ? 0 : (margins.right ?? 15)
  const marginBottom = isCanvas ? 0 : (margins.bottom ?? 20)
  const marginLeft = isCanvas ? 0 : (margins.left ?? 25)

  // Create temporary off-screen container for rendering
  const container = document.createElement('div')
  container.className = 'contract-pdf-render-container'
  container.style.cssText = `
    position: fixed;
    left: -9999px;
    top: 0;
    width: 794px; /* Exact A4 width at 96 DPI: 210mm ≈ 794px */
    background: #ffffff;
    color: #111827;
    font-family: 'Times New Roman', Times, serif;
    font-size: 13px;
    line-height: 1.6;
    box-sizing: border-box;
    padding: 0;
  `

  container.innerHTML = `
    <style>
      .contract-pdf-content {
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 13.5px;
        line-height: 1.65;
        color: #111827 !important;
        box-sizing: border-box;
      }
      .contract-pdf-content p {
        margin: 5px 0;
        text-align: justify;
      }
      .contract-pdf-content h1 {
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        margin: 14px 0 8px;
      }
      .contract-pdf-content h2 {
        font-size: 16px;
        font-weight: bold;
        margin: 12px 0 6px;
      }
      .contract-pdf-content h3 {
        font-size: 14px;
        font-weight: bold;
        margin: 10px 0 4px;
      }
      .contract-pdf-content ol {
        list-style-type: decimal !important;
        padding-left: 1.8em !important;
        margin: 4px 0 !important;
      }
      .contract-pdf-content ol ol {
        list-style-type: lower-alpha !important;
        padding-left: 1.6em !important;
        margin: 2px 0 !important;
      }
      .contract-pdf-content ol ol ol {
        list-style-type: lower-roman !important;
        padding-left: 1.6em !important;
        margin: 2px 0 !important;
      }
      .contract-pdf-content ul {
        list-style-type: disc !important;
        padding-left: 1.8em !important;
        margin: 4px 0 !important;
      }
      .contract-pdf-content ul ul {
        list-style-type: circle !important;
        padding-left: 1.6em !important;
        margin: 2px 0 !important;
      }
      .contract-pdf-content ul ul ul {
        list-style-type: square !important;
        padding-left: 1.6em !important;
        margin: 2px 0 !important;
      }
      .contract-pdf-content li {
        margin: 2px 0 !important;
      }
      .contract-pdf-content table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 10px 0 !important;
        page-break-inside: avoid;
      }
      .contract-pdf-content td,
      .contract-pdf-content th {
        border: 1px solid #94a3b8 !important;
        padding: 6px 10px !important;
        font-size: 12px !important;
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
    </style>
    <div class="contract-pdf-content">
      ${bodyHtml}
    </div>
  `

  document.body.appendChild(container)

  const opt = {
    margin: [marginTop, marginLeft, marginBottom, marginRight] as [number, number, number, number],
    filename: `${safeTitle}.pdf`,
    image: { type: 'jpeg' as const, quality: 0.98 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      letterRendering: true,
      logging: false,
      scrollX: 0,
      scrollY: 0,
    },
    jsPDF: {
      unit: 'mm' as const,
      format: 'a4' as const,
      orientation: 'portrait' as const,
    },
    pagebreak: {
      mode: ['css', 'legacy'] as ('css' | 'legacy')[],
      before: '.page-break-always, .html2pdf__page-break',
    },
  }

  try {
    await html2pdf().set(opt).from(container).save()
  } finally {
    if (container.parentNode) {
      container.parentNode.removeChild(container)
    }
  }
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
          font-family: 'Times New Roman', Times, serif;
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
