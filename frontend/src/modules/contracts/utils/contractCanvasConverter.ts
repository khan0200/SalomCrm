import type {
  ContractDocumentModel,
  CanvasPageModel,
  CanvasElement,
  TextCanvasElement,
  TableCanvasElement,
  TableCellModel,
  PageMargins,
} from '../types/contractCanvas'
import { replaceVariablesInHtml } from './contractVariables'

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
 * Parses a real `<table>` element (our own exported HTML, or one pasted
 * straight from Word/Excel/Sheets) into a dense rows×cols grid, using the
 * standard "occupancy cursor" reconstruction: a browser doesn't require - and
 * Word/Excel don't emit - a `<td>` for a grid slot a colspan/rowspan from
 * earlier already claims, so this walks each row's actual `<td>`s while
 * skipping any column position a still-open rowspan occupies, which is the
 * only way to recover true column indices from raw rowspan/colspan HTML.
 *
 * Column widths come from an authored `<colgroup>` (round-tripping our own
 * export) when present, else from Word/Excel's unitless-pixel `td[width]`
 * attributes on the first row, scaled to fit `contentWidth`, else split evenly.
 */
export function parseHtmlTable(
  tableEl: HTMLTableElement,
  contentWidth: number
): { rows: number; cols: number; colWidths: number[]; rowHeights: number[]; cells: TableCellModel[][] } {
  const rowEls = Array.from(tableEl.rows) // flattens thead/tbody/tfoot in document order, like a browser lays them out
  const cells: TableCellModel[][] = []
  const occupied: boolean[][] = []
  let maxCols = 0

  const readBorderSide = (el: HTMLElement, prop: 'borderTop' | 'borderRight' | 'borderBottom' | 'borderLeft'): string | undefined => {
    const v = (el.style as any)[prop]
    return v && v.trim() ? v.trim() : undefined
  }

  rowEls.forEach((tr, r) => {
    if (!occupied[r]) occupied[r] = []
    if (!cells[r]) cells[r] = []
    const domCells = Array.from(tr.cells)
    let c = 0
    let domIdx = 0

    while (domIdx < domCells.length || occupied[r][c]) {
      if (occupied[r][c]) { c++; continue }
      const htmlCell = domCells[domIdx] as HTMLElement
      domIdx++
      const colSpan = Math.max(1, parseInt(htmlCell.getAttribute('colspan') || '1', 10) || 1)
      const rowSpan = Math.max(1, parseInt(htmlCell.getAttribute('rowspan') || '1', 10) || 1)
      const borders = {
        top: readBorderSide(htmlCell, 'borderTop'),
        right: readBorderSide(htmlCell, 'borderRight'),
        bottom: readBorderSide(htmlCell, 'borderBottom'),
        left: readBorderSide(htmlCell, 'borderLeft'),
      }
      const hasBorders = Object.values(borders).some(Boolean)

      cells[r][c] = {
        id: generateId('cell'),
        content: htmlCell.innerHTML.trim() || '&nbsp;',
        backgroundColor: htmlCell.style.backgroundColor || undefined,
        textAlign: (htmlCell.style.textAlign as any) || 'left',
        verticalAlign: (htmlCell.style.verticalAlign as any) || 'top',
        color: htmlCell.style.color || undefined,
        fontSize: parseFloat(htmlCell.style.fontSize) || undefined,
        fontWeight: htmlCell.style.fontWeight || undefined,
        fontStyle: (htmlCell.style.fontStyle as 'normal' | 'italic') || undefined,
        textDecoration: htmlCell.style.textDecoration || undefined,
        colSpan: colSpan > 1 ? colSpan : undefined,
        rowSpan: rowSpan > 1 ? rowSpan : undefined,
        borders: hasBorders ? borders : undefined,
      }

      for (let rr = r; rr < r + rowSpan; rr++) {
        if (!occupied[rr]) occupied[rr] = []
        if (!cells[rr]) cells[rr] = []
        for (let cc = c; cc < c + colSpan; cc++) {
          occupied[rr][cc] = true
          if (rr === r && cc === c) continue
          cells[rr][cc] = { id: generateId('cell'), content: '', coveredBy: { r, c } }
        }
      }
      maxCols = Math.max(maxCols, c + colSpan)
      c += colSpan
    }
  })

  const rows = cells.length
  const colCount = Math.max(1, maxCols)
  // Malformed/ragged source HTML can leave short rows - pad rather than let a
  // later `cells[r][c]` access go out of bounds anywhere downstream.
  for (let r = 0; r < rows; r++) {
    if (!cells[r]) cells[r] = []
    for (let c = 0; c < colCount; c++) {
      if (!cells[r][c]) cells[r][c] = { id: generateId('cell'), content: '&nbsp;' }
    }
  }

  // Column widths: authored <colgroup> (our own export) first.
  const colEls = Array.from(tableEl.querySelectorAll('col'))
  const authoredWidths = colEls
    .map(c => parseFloat((c as HTMLElement).style.width))
    .filter(w => Number.isFinite(w) && w > 0)

  let colWidths: number[]
  if (authoredWidths.length === colCount) {
    colWidths = authoredWidths
  } else {
    // Word/Excel paste: unitless `width` attributes on the first row's <td>s
    // are pixels, kept in proportion but scaled to fit the page.
    const firstRowCells = rowEls[0] ? Array.from(rowEls[0].cells) : []
    const pxWidths = firstRowCells.map(td => parseFloat(td.getAttribute('width') || '')).filter(w => Number.isFinite(w) && w > 0)
    if (pxWidths.length === colCount) {
      const naturalMm = pxWidths.map(px => px * 0.264583) // 96px/inch -> 25.4mm/inch
      const naturalTotal = naturalMm.reduce((a, b) => a + b, 0)
      const scale = naturalTotal > contentWidth ? contentWidth / naturalTotal : 1
      colWidths = naturalMm.map(w => Math.round(w * scale * 10) / 10)
    } else {
      const even = Math.round((contentWidth / colCount) * 10) / 10
      colWidths = Array(colCount).fill(even)
    }
  }

  const rowHeights = rowEls.map(tr => {
    const h = parseFloat((tr as HTMLElement).style.height)
    return Number.isFinite(h) && h > 0 ? h : 10
  })

  return { rows, cols: colCount, colWidths, rowHeights, cells }
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

  // Iterate over child elements. Word/Google Docs/Sheets wrap clipboard
  // content in one or more plain `<div>`s (e.g. `<div><table>...</table></div>`),
  // so a shallow `body.children` walk never reaches the table at all - it
  // sees one div, falls into the generic paragraph/div branch below, and
  // swallows the whole table as inert text. Unwrap any div that contains a
  // recognisable block child (table/heading/paragraph/list/div) down to its
  // real content first; a div with only inline/text content is left alone
  // and still handled as a single block by the default branch.
  const BLOCK_TAGS = new Set(['table', 'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol'])
  function flattenWrapperDivs(nodes: Element[]): Element[] {
    const out: Element[] = []
    for (const node of nodes) {
      if (node.tagName.toLowerCase() === 'div' && Array.from(node.children).some(c => BLOCK_TAGS.has(c.tagName.toLowerCase()))) {
        out.push(...flattenWrapperDivs(Array.from(node.children) as Element[]))
      } else {
        out.push(node)
      }
    }
    return out
  }
  const children = flattenWrapperDivs(Array.from(body.children) as Element[])

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
        const parsed = parseHtmlTable(child as HTMLTableElement, contentWidth)
        const estimatedTableHeight = Math.max(20, parsed.rowHeights.reduce((sum, h) => sum + h, 0))

        addElement(
          {
            id: generateId('table'),
            type: 'table',
            x: margins.left,
            y: currentY,
            width: parsed.colWidths.reduce((sum, w) => sum + w, 0),
            height: estimatedTableHeight,
            zIndex: 1,
            rows: parsed.rows,
            cols: parsed.cols,
            colWidths: parsed.colWidths,
            rowHeights: parsed.rowHeights,
            cells: parsed.cells,
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

    // Collect all variables used explicitly on this page
    const pageVars = new Set<string>()
    page.elements.forEach(el => {
      if (el.hidden) return
      const anyEl = el as any
      if (anyEl.variableKey) {
        pageVars.add(String(anyEl.variableKey).replace(/^\{\{|\}\}$/g, '').trim().toLowerCase())
      }
      if (typeof anyEl.content === 'string') {
        const matches = anyEl.content.match(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g)
        if (matches) {
          matches.forEach((m: string) => {
            pageVars.add(m.replace(/[\{\}\s]/g, '').toLowerCase())
          })
        }
      }
      if (el.type === 'table') {
        const tbl = el as TableCanvasElement
        tbl.cells?.forEach(row => {
          row?.forEach(cell => {
            if (cell.content) {
              const cMatches = cell.content.match(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g)
              if (cMatches) {
                cMatches.forEach((m: string) => pageVars.add(m.replace(/[\{\}\s]/g, '').toLowerCase()))
              }
            }
          })
        })
      }
    })

    // {{page_number}}/{{total_pages}} resolve per page, not from the passed-in
    // document-wide variableValues map: the exact same element, copy/pasted
    // onto several pages, shows each page's own number.
    const pageVariableValues = {
      ...(variableValues || {}),
      page_number: String(pageIdx + 1),
      total_pages: String(doc.pages.length),
    }

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
        const cellPadding =
          table.density === 'compact' ? '4px 6px' : table.density === 'spacious' ? '10px 14px' : '6px 10px'
        const defaultBorder = `${table.borderWidth || '1px'} ${table.borderStyle || 'solid'} ${table.borderColor || '#94a3b8'}`

        // Column widths only survive into the PDF/print/signing output if they
        // are emitted as a <colgroup>: `table-layout: fixed` alone distributes
        // every column evenly, which silently discarded whatever widths the
        // editor had been showing.
        const colgroup = table.colWidths?.length
          ? `<colgroup>${table.colWidths
              .map(w => `<col style="width: ${Math.round(w * 100) / 100}mm;" />`)
              .join('')}</colgroup>`
          : ''

        let rowsHtml = ''
        table.cells.forEach((row, rowIdx) => {
          let colsHtml = ''
          row.forEach(cell => {
            // A merge's covered slots carry no content of their own - the
            // master's colspan/rowspan already claims their grid space, so a
            // real HTML table (like the browser that renders it) must not see
            // a <td> for them at all.
            if (cell.coveredBy) return

            const cellContent = replaceVariablesInHtml(cell.content || '', pageVariableValues, {
              skipHeuristics: pageVars.size > 0,
              excludedVariables: pageVars,
            })

            const isHeaderCell = Boolean(table.headerRow) && rowIdx === 0
            const bodyRowIdx = table.headerRow ? rowIdx - 1 : rowIdx
            const isZebraRow = Boolean(table.zebra) && bodyRowIdx >= 0 && bodyRowIdx % 2 === 1
            const effectiveBg =
              cell.backgroundColor ||
              (isHeaderCell ? table.headerColor || '#e5e7eb' : '') ||
              (isZebraRow ? table.zebraColor || '#f8fafc' : '') ||
              table.tableBackground || ''
            const effectiveWeight = cell.fontWeight || (isHeaderCell ? 'bold' : '')

            const bg = effectiveBg ? `background-color: ${effectiveBg};` : ''
            const align = cell.textAlign ? `text-align: ${cell.textAlign};` : ''
            const vAlign = cell.verticalAlign ? `vertical-align: ${cell.verticalAlign};` : ''
            const color = cell.color ? `color: ${cell.color};` : ''
            const fontSize = cell.fontSize ? `font-size: ${cell.fontSize}pt;` : ''
            const fontWeight = effectiveWeight ? `font-weight: ${effectiveWeight};` : ''
            const fontStyle = cell.fontStyle ? `font-style: ${cell.fontStyle};` : ''
            const textDecoration = cell.textDecoration ? `text-decoration: ${cell.textDecoration};` : ''
            const borders = [
              `border-top: ${cell.borders?.top ?? defaultBorder};`,
              `border-right: ${cell.borders?.right ?? defaultBorder};`,
              `border-bottom: ${cell.borders?.bottom ?? defaultBorder};`,
              `border-left: ${cell.borders?.left ?? defaultBorder};`,
            ].join('')
            const spanAttrs = `${cell.colSpan && cell.colSpan > 1 ? `colspan="${cell.colSpan}"` : ''} ${cell.rowSpan && cell.rowSpan > 1 ? `rowspan="${cell.rowSpan}"` : ''}`

            colsHtml += `<td ${spanAttrs} style="${borders}padding: ${cellPadding}; ${bg}${align}${vAlign}${color}${fontSize}${fontWeight}${fontStyle}${textDecoration}">${cellContent}</td>`
          })
          // Row heights are authored in mm like every other canvas dimension.
          // `height` (not `min-height`) is what a table row actually honours.
          const rowH = table.rowHeights?.[rowIdx]
          rowsHtml += `<tr${rowH ? ` style="height: ${Math.round(rowH * 100) / 100}mm;"` : ''}>${colsHtml}</tr>`
        })

        innerContent = `<table style="width: 100%; border-collapse: collapse; table-layout: fixed;">${colgroup}${rowsHtml}</table>`
      } else if (el.type === 'line') {
        const line = el as any
        const borderProp = line.orientation === 'vertical' ? 'border-left' : 'border-top'
        innerContent = `<div style="width: 100%; height: 100%; ${borderProp}: ${line.strokeWidth || 1}px ${line.strokeStyle || 'solid'} ${line.strokeColor || '#000'};"></div>`
      } else if (el.type === 'checkbox') {
        const cb = el as any
        const st = cb.style || {}
        const checkedBox = cb.checked ? '☑' : '☐'
        const fontSize = st.fontSize || cb.fontSize || 12
        const color = st.color || cb.color || '#111827'
        const fontWeight = st.fontWeight || 'normal'
        const fontStyle = st.fontStyle || 'normal'
        const textDecoration = st.textDecoration || 'none'
        const fontFamily = st.fontFamily || 'Times New Roman'
        const letterSpacing = typeof st.letterSpacing === 'number' && st.letterSpacing !== 0 ? `${st.letterSpacing}px` : 'normal'
        const bg = st.backgroundColor && st.backgroundColor !== 'transparent' && st.backgroundColor !== '#ffffff' ? `background-color: ${st.backgroundColor};` : ''
        innerContent = `<div style="display: flex; align-items: center; gap: 6px; font-family: ${fontFamily}, Times, serif; font-size: ${fontSize}pt; font-weight: ${fontWeight}; font-style: ${fontStyle}; text-decoration: ${textDecoration}; color: ${color}; letter-spacing: ${letterSpacing}; ${bg}"><span>${checkedBox}</span><span>${cb.label || ''}</span></div>`
      } else {
        // Text / Heading / Paragraph
        const textEl = el as TextCanvasElement
        let content = replaceVariablesInHtml(textEl.content || '', pageVariableValues, {
          skipHeuristics: pageVars.size > 0,
          excludedVariables: pageVars,
        })
        const st = textEl.style || {}
        let textColor = st.color || '#111827'
        if (variableValues && Object.keys(variableValues).length > 0) {
          if (textColor === '#2563eb' || textColor === '#1d4ed8' || textColor === 'rgb(37, 99, 235)' || textColor === 'rgb(29, 78, 216)') {
            textColor = '#000000'
          }
        }
        const fontStyle = `
          font-family: ${st.fontFamily || 'Times New Roman'}, Times, serif;
          font-size: ${st.fontSize || 12}pt;
          font-weight: ${st.fontWeight || 'normal'};
          font-style: ${st.fontStyle || 'normal'};
          text-decoration: ${st.textDecoration || 'none'};
          color: ${textColor};
          background-color: ${st.backgroundColor || 'transparent'};
          text-align: ${st.textAlign || 'left'};
          line-height: ${st.lineHeight || 1.5};
          letter-spacing: ${typeof st.letterSpacing === 'number' && st.letterSpacing !== 0 ? `${st.letterSpacing}px` : 'normal'};
          padding: ${st.padding || 0}mm;
          overflow-wrap: break-word;
          box-sizing: border-box;
        `
        innerContent = `<div class="canvas-text-element" style="${fontStyle}">${content}</div>`
      }

      elementsHtml += `
        <div style="position: absolute; left: ${leftMm}mm; top: ${topMm}mm; width: ${widthMm}mm; min-height: ${heightMm}mm; z-index: ${el.zIndex || 1}; box-sizing: border-box; ${transformCss}">
          ${innerContent}
        </div>
      `
    })

    // Every page carries the public verification link in its footer, once
    // the contract has a verification code (assigned by the agency after
    // signing). Before that there is nothing to link to, so it's omitted.
    const verificationUrl = variableValues?.verification_url || variableValues?.verification_link || ''
    const footerHtml = verificationUrl
      ? `<div style="position: absolute; left: 0; right: 0; bottom: 6mm; text-align: center; font-family: 'Times New Roman', serif; font-size: 7.5pt; color: #2563eb;">${verificationUrl}</div>`
      : ''

    const pageWrapper = `
      <div class="canvas-a4-page-print" style="position: relative; width: ${PAGE_WIDTH_MM}mm; height: ${PAGE_HEIGHT_MM}mm; background: #ffffff; overflow: hidden; page-break-after: ${isLastPage ? 'auto' : 'always'}; break-after: ${isLastPage ? 'auto' : 'page'};">
        <style>
          .canvas-a4-page-print p { margin: 0.2em 0; }
          .canvas-a4-page-print p:first-child { margin-top: 0 !important; }
          .canvas-a4-page-print p:last-child { margin-bottom: 0 !important; }
          .canvas-a4-page-print img { display: inline-block !important; vertical-align: baseline !important; }
          .canvas-a4-page-print span[style*="border-bottom"],
          .canvas-a4-page-print p[style*="border-bottom"] {
            padding-bottom: 2px !important;
          }
          /* List styling travels with the HTML itself (instead of living only
             in CanvasTextElement.vue's global style block) so bulleted/numbered
             lists render identically wherever this converter's output is
             injected via v-html - including modules that never load the
             canvas editor component, like the student-facing contract viewer. */
          .canvas-text-element ol {
            list-style-type: decimal !important;
            padding-left: 1.8em !important;
            margin: 0.3em 0 !important;
            font-family: inherit !important;
          }
          .canvas-text-element ol ol {
            list-style-type: lower-alpha !important;
            padding-left: 1.6em !important;
            margin: 0.15em 0 !important;
          }
          .canvas-text-element ol ol ol {
            list-style-type: lower-roman !important;
            padding-left: 1.6em !important;
            margin: 0.15em 0 !important;
          }
          .canvas-text-element ul {
            list-style-type: disc !important;
            padding-left: 1.8em !important;
            margin: 0.3em 0 !important;
            font-family: inherit !important;
          }
          .canvas-text-element ul ul {
            list-style-type: circle !important;
            padding-left: 1.6em !important;
            margin: 0.15em 0 !important;
          }
          .canvas-text-element ul ul ul {
            list-style-type: square !important;
            padding-left: 1.6em !important;
            margin: 0.15em 0 !important;
          }
          .canvas-text-element li {
            margin: 0.15em 0 !important;
            font-family: inherit !important;
            line-height: inherit !important;
          }
        </style>
        ${elementsHtml}
        ${footerHtml}
      </div>
    `
    pageHtmls.push(pageWrapper)
  })

  return pageHtmls.join('\n')
}
