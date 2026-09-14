import type {
  ContractDocumentModel,
  CanvasPageModel,
  CanvasElement,
  TextCanvasElement,
  TableCanvasElement,
  TableCellModel,
  PageMargins,
} from '../types/contractCanvas'

const DEFAULT_MARGINS: PageMargins = {
  top: 20,
  right: 15,
  bottom: 20,
  left: 25,
}

const PAGE_WIDTH_MM = 210
const PAGE_HEIGHT_MM = 297

function generateId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Check if a raw string is already a serialized canvas document JSON
 */
export function isCanvasDocumentJson(content: string): boolean {
  if (!content) return false
  const trimmed = content.trim()
  if (!trimmed.startsWith('{') || !trimmed.endsWith('}')) return false
  try {
    const parsed = JSON.parse(trimmed)
    return (
      parsed &&
      (parsed.type === 'canvas-contract' || (parsed.version === 2 && Array.isArray(parsed.pages)))
    )
  } catch {
    return false
  }
}

/**
 * Deserialize string into ContractDocumentModel or null
 */
export function deserializeCanvasDocument(content: string): ContractDocumentModel | null {
  if (!content) return null
  try {
    const parsed = JSON.parse(content)
    if (parsed && Array.isArray(parsed.pages) && parsed.pageSize) {
      return parsed as ContractDocumentModel
    }
  } catch {
    // Not valid JSON
  }
  return null
}

/**
 * Serialize ContractDocumentModel to JSON string
 */
export function serializeCanvasDocument(doc: ContractDocumentModel): string {
  return JSON.stringify(doc)
}

/**
 * Convert legacy HTML or plain text into a structured Canva-style ContractDocumentModel
 */
export function convertHtmlToCanvasDocument(
  rawOrHtml: string,
  customMargins?: Partial<PageMargins>
): ContractDocumentModel {
  const margins: PageMargins = {
    ...DEFAULT_MARGINS,
    ...(customMargins || {}),
  }

  // If it's already a valid CanvasDocument JSON, return it
  const existingDoc = deserializeCanvasDocument(rawOrHtml)
  if (existingDoc) {
    return existingDoc
  }

  const contentWidth = PAGE_WIDTH_MM - margins.left - margins.right // default 170 mm
  const maxPageHeight = PAGE_HEIGHT_MM - margins.bottom // default 277 mm

  // Default empty document if content is empty
  if (!rawOrHtml || !rawOrHtml.trim()) {
    return {
      version: 2,
      type: 'canvas-contract',
      pageSize: { width: PAGE_WIDTH_MM, height: PAGE_HEIGHT_MM, unit: 'mm' },
      margins,
      defaultFontFamily: 'Times New Roman',
      defaultFontSize: 12,
      pages: [
        {
          id: generateId('page'),
          pageNumber: 1,
          elements: [
            {
              id: generateId('text'),
              type: 'text',
              x: margins.left,
              y: margins.top,
              width: contentWidth,
              height: 25,
              zIndex: 1,
              content: '<p>Shartnoma matnini bu yerga yozing...</p>',
              style: {
                fontFamily: 'Times New Roman',
                fontSize: 14,
                color: '#000000',
                textAlign: 'left',
                lineHeight: 1.5,
              },
            },
          ],
        },
      ],
    }
  }

  // Pre-process HTML: normalize page breaks
  let cleaned = rawOrHtml
    .replace(/═{5,}\s*1-BET\s*═{5,}/gi, '')
    .replace(/═{5,}\s*(\d+)-BET\s*═{5,}/gi, '<hr data-page-break="true" />')
    .replace(/class="[^"]*html2pdf__page-break[^"]*"/gi, 'data-page-break="true"')

  // Parse HTML using DOMParser
  const parser = new DOMParser()
  const doc = parser.parseFromString(`<body>${cleaned}</body>`, 'text/html')
  const body = doc.body

  const pages: CanvasPageModel[] = []
  let currentPageIndex = 1
  let currentElements: CanvasElement[] = []
  let currentY = margins.top
  let currentZIndex = 1

  function finishCurrentPage() {
    pages.push({
      id: generateId(`page_${currentPageIndex}`),
      pageNumber: currentPageIndex,
      elements: currentElements,
    })
    currentPageIndex++
    currentElements = []
    currentY = margins.top
    currentZIndex = 1
  }

  // Helper to append an element, creating a new page if it exceeds maxPageHeight
  function addElement(el: CanvasElement, estimatedHeightMm: number) {
    if (currentY + estimatedHeightMm > maxPageHeight && currentElements.length > 0) {
      finishCurrentPage()
      el.y = margins.top
      currentY = margins.top
    } else {
      el.y = currentY
    }
    el.zIndex = currentZIndex++
    currentElements.push(el)
    currentY += estimatedHeightMm + 4 // 4mm gap between stacked blocks
  }

  // Iterate over child elements
  const children = Array.from(body.children)

  if (children.length === 0 && body.textContent?.trim()) {
    // It's raw plain text without tags
    const paragraphs = body.textContent.split('\n\n').filter(p => p.trim())
    for (const p of paragraphs) {
      const estimatedH = Math.max(12, Math.ceil(p.length / 80) * 6)
      addElement(
        {
          id: generateId('text'),
          type: 'text',
          x: margins.left,
          y: currentY,
          width: contentWidth,
          height: estimatedH,
          zIndex: 1,
          content: `<p>${p.trim()}</p>`,
          style: {
            fontFamily: 'Times New Roman',
            fontSize: 12,
            color: '#111827',
            textAlign: 'justify',
            lineHeight: 1.5,
          },
        },
        estimatedH
      )
    }
  } else {
    for (const child of children) {
      const tagName = child.tagName.toLowerCase()

      // Check for explicit page break
      if (tagName === 'hr' && (child.getAttribute('data-page-break') || child.className.includes('page-break'))) {
        finishCurrentPage()
        continue
      }

      if (child.getAttribute('data-page-break') === 'true' || child.classList.contains('html2pdf__page-break')) {
        finishCurrentPage()
        continue
      }

      // Check for Table
      if (tagName === 'table') {
        const tableEl = child as HTMLTableElement
        const trs = Array.from(tableEl.querySelectorAll('tr'))
        const rowCount = trs.length
        let maxCols = 1

        trs.forEach(tr => {
          const cells = tr.querySelectorAll('td, th')
          let colSpanSum = 0
          cells.forEach(c => {
            colSpanSum += parseInt(c.getAttribute('colspan') || '1', 10)
          })
          maxCols = Math.max(maxCols, colSpanSum)
        })

        const cells: TableCellModel[][] = []
        trs.forEach(tr => {
          const rowCells: TableCellModel[] = []
          const cellEls = Array.from(tr.querySelectorAll('td, th'))
          cellEls.forEach(c => {
            const htmlCell = c as HTMLElement
            const bg = htmlCell.style.backgroundColor || ''
            const align = (htmlCell.style.textAlign as any) || 'left'
            const vAlign = (htmlCell.style.verticalAlign as any) || 'top'
            const colSpan = parseInt(htmlCell.getAttribute('colspan') || '1', 10)
            const rowSpan = parseInt(htmlCell.getAttribute('rowspan') || '1', 10)

            rowCells.push({
              id: generateId('cell'),
              content: htmlCell.innerHTML.trim() || '&nbsp;',
              backgroundColor: bg || undefined,
              textAlign: align,
              verticalAlign: vAlign,
              colSpan: colSpan > 1 ? colSpan : undefined,
              rowSpan: rowSpan > 1 ? rowSpan : undefined,
            })
          })
          cells.push(rowCells)
        })

        const colW = contentWidth / maxCols
        const colWidths = Array(maxCols).fill(colW)
        const rowH = 10
        const rowHeights = Array(rowCount).fill(rowH)
        const estimatedTableHeight = Math.max(20, rowCount * 12)

        addElement(
          {
            id: generateId('table'),
            type: 'table',
            x: margins.left,
            y: currentY,
            width: contentWidth,
            height: estimatedTableHeight,
            zIndex: 1,
            rows: rowCount,
            cols: maxCols,
            colWidths,
            rowHeights,
            cells,
            borderWidth: '1px',
            borderColor: '#94a3b8',
            borderStyle: 'solid',
            density: 'normal',
          },
          estimatedTableHeight
        )
        continue
      }

      // Check for Headings
      if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
        const level = parseInt(tagName.replace('h', ''), 10) as 1 | 2 | 3
        const hFontSize = level === 1 ? 16 : level === 2 ? 14 : 13
        const estimatedH = 14

        addElement(
          {
            id: generateId('heading'),
            type: 'heading',
            headingLevel: level,
            x: margins.left,
            y: currentY,
            width: contentWidth,
            height: estimatedH,
            zIndex: 1,
            content: child.outerHTML,
            style: {
              fontFamily: 'Times New Roman',
              fontSize: hFontSize,
              fontWeight: 'bold',
              color: '#111827',
              textAlign: (child as HTMLElement).style.textAlign as any || (level === 1 ? 'center' : 'left'),
              lineHeight: 1.3,
            },
          },
          estimatedH
        )
        continue
      }

      // Default: Paragraph, list, div, etc.
      const htmlContent = child.outerHTML
      const textLen = child.textContent?.length || 10
      const estimatedH = Math.max(8, Math.ceil(textLen / 75) * 5.5)

      addElement(
        {
          id: generateId('text'),
          type: 'text',
          x: margins.left,
          y: currentY,
          width: contentWidth,
          height: estimatedH,
          zIndex: 1,
          content: htmlContent,
          style: {
            fontFamily: 'Times New Roman',
            fontSize: 12,
            color: '#111827',
            textAlign: ((child as HTMLElement).style.textAlign as any) || 'justify',
            lineHeight: 1.55,
          },
        },
        estimatedH
      )
    }
  }

  // Push final page if not empty
  if (currentElements.length > 0) {
    finishCurrentPage()
  }

  // Ensure at least one page exists
  if (pages.length === 0) {
    pages.push({
      id: generateId('page'),
      pageNumber: 1,
      elements: [],
    })
  }

  return {
    version: 2,
    type: 'canvas-contract',
    pageSize: { width: PAGE_WIDTH_MM, height: PAGE_HEIGHT_MM, unit: 'mm' },
    margins,
    defaultFontFamily: 'Times New Roman',
    defaultFontSize: 12,
    pages,
  }
}

/**
 * Convert CanvasDocumentModel into clean HTML for PDF rendering & print
 */
export function convertCanvasDocumentToHtml(
  doc: ContractDocumentModel,
  variableValues?: Record<string, string>
): string {
  if (!doc || !doc.pages) return '<p></p>'

  const pageHtmls: string[] = []

  doc.pages.forEach((page, pageIdx) => {
    const isLastPage = pageIdx === doc.pages.length - 1

    let elementsHtml = ''

    // Sort elements by zIndex
    const sorted = [...page.elements].sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0))

    sorted.forEach(el => {
      if (el.hidden) return

      const leftMm = el.x
      const topMm = el.y
      const widthMm = el.width
      const heightMm = el.height
      const rot = el.rotation || 0
      const transformCss = rot ? `transform: rotate(${rot}deg); transform-origin: center center;` : ''

      let innerContent = ''

      if (el.type === 'table') {
        const table = el as TableCanvasElement
        let rowsHtml = ''
        table.cells.forEach(row => {
          let colsHtml = ''
          row.forEach(cell => {
            let cellContent = cell.content
            if (variableValues) {
              for (const [key, val] of Object.entries(variableValues)) {
                cellContent = cellContent.split(key).join(val)
              }
            }
            const bg = cell.backgroundColor ? `background-color: ${cell.backgroundColor};` : ''
            const align = cell.textAlign ? `text-align: ${cell.textAlign};` : ''
            const vAlign = cell.verticalAlign ? `vertical-align: ${cell.verticalAlign};` : ''
            const spanAttrs = `${cell.colSpan ? `colspan="${cell.colSpan}"` : ''} ${cell.rowSpan ? `rowspan="${cell.rowSpan}"` : ''}`

            colsHtml += `<td ${spanAttrs} style="border: ${table.borderWidth || '1px'} ${table.borderStyle || 'solid'} ${table.borderColor || '#94a3b8'}; padding: ${table.density === 'compact' ? '4px 6px' : table.density === 'spacious' ? '10px 14px' : '6px 10px'}; ${bg} ${align} ${vAlign}">${cellContent}</td>`
          })
          rowsHtml += `<tr>${colsHtml}</tr>`
        })

        innerContent = `<table style="width: 100%; height: 100%; border-collapse: collapse; table-layout: fixed;">${rowsHtml}</table>`
      } else if (el.type === 'line') {
        const line = el as any
        const borderProp = line.orientation === 'vertical' ? 'border-left' : 'border-top'
        innerContent = `<div style="width: 100%; height: 100%; ${borderProp}: ${line.strokeWidth || 1}px ${line.strokeStyle || 'solid'} ${line.strokeColor || '#000'};"></div>`
      } else if (el.type === 'checkbox') {
        const cb = el as any
        const checkedBox = cb.checked ? '☑' : '☐'
        innerContent = `<div style="display: flex; align-items: center; gap: 6px; font-size: ${cb.fontSize || 12}pt; color: ${cb.color || '#111827'};"><span>${checkedBox}</span><span>${cb.label || ''}</span></div>`
      } else {
        // Text / Heading / Paragraph
        const textEl = el as TextCanvasElement
        let content = textEl.content
        if (variableValues) {
          for (const [key, val] of Object.entries(variableValues)) {
            content = content.split(key).join(val)
          }
        }
        const st = textEl.style || {}
        const fontStyle = `
          font-family: ${st.fontFamily || 'Times New Roman'}, Times, serif;
          font-size: ${st.fontSize || 12}pt;
          font-weight: ${st.fontWeight || 'normal'};
          font-style: ${st.fontStyle || 'normal'};
          text-decoration: ${st.textDecoration || 'none'};
          color: ${st.color || '#111827'};
          background-color: ${st.backgroundColor || 'transparent'};
          text-align: ${st.textAlign || 'left'};
          line-height: ${st.lineHeight || 1.5};
          letter-spacing: ${typeof st.letterSpacing === 'number' && st.letterSpacing !== 0 ? `${st.letterSpacing}px` : 'normal'};
          padding: ${st.padding || 0}mm;
        `
        innerContent = `<div style="${fontStyle}">${content}</div>`
      }

      elementsHtml += `
        <div style="position: absolute; left: ${leftMm}mm; top: ${topMm}mm; width: ${widthMm}mm; min-height: ${heightMm}mm; z-index: ${el.zIndex || 1}; box-sizing: border-box; ${transformCss}">
          ${innerContent}
        </div>
      `
    })

    const pageWrapper = `
      <div class="canvas-a4-page-print" style="position: relative; width: ${PAGE_WIDTH_MM}mm; height: ${PAGE_HEIGHT_MM}mm; background: #ffffff; overflow: hidden; page-break-after: ${isLastPage ? 'auto' : 'always'}; break-after: ${isLastPage ? 'auto' : 'page'};">
        ${elementsHtml}
      </div>
    `
    pageHtmls.push(pageWrapper)
  })

  return pageHtmls.join('\n')
}
