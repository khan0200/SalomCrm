// Stage 2 canary: server-side canonical PDF rendering for a finalized
// online contract.
//
// Invocation contract (called by Django's contract_pdf_service.py via
// subprocess): reads one JSON object from stdin, writes the rendered PDF's
// bytes to the file path given in that JSON's `outputPath`, and prints one
// JSON line to stdout on success/failure. Never touches the network or any
// database - all contract data must already be resolved by the caller, so
// this process cannot be tricked into rendering a different contract than
// the one Django authorized.
//
// Input shape (stdin, one JSON object):
//   {
//     "canvasSource": "<canvas-contract JSON string, or ''>",
//     "content": "<legacy HTML string, used only if canvasSource is empty>",
//     "guardianContent": "<guardian consent appendix HTML, or ''>",
//     "student": { ...raw Contract fields, same shape buildVariableValues() expects... },
//     "contractMeta": { contractNumber, templateName, price, discount, signatureData, ... },
//     "guardianStudent": { ...student with guardian_* promoted, for the appendix doc... },
//     "outputPath": "/abs/path/to/output.pdf",
//     "timeoutMs": 15000
//   }
//
// `student`/`contractMeta` are passed through to the REAL buildVariableValues()
// (vendored verbatim from contractVariables.ts) rather than Django
// pre-resolving a flat token map itself - this is deliberate: that function
// has ~250 lines of fallback-key and formatting logic (phone prefixing,
// currency formatting, balance math, requisite selection). Reimplementing it
// in Python would be a second copy of that logic to keep in sync forever;
// calling the original here guarantees server output matches the editor's
// own preview byte-for-byte on every token, not just the ones a Python port
// happened to remember.
import { chromium } from 'playwright'
import * as fs from 'fs'
import {
  isCanvasDocumentJson,
  deserializeCanvasDocument,
  convertCanvasDocumentToHtml,
} from './vendor/contractCanvasConverter'
import { buildVariableValues } from './vendor/contractVariables'

interface RenderInput {
  canvasSource: string
  content: string
  guardianContent?: string
  student: Record<string, unknown>
  contractMeta: Record<string, unknown>
  guardianStudent?: Record<string, unknown>
  outputPath: string
  timeoutMs?: number
}

function readStdin(): Promise<string> {
  return new Promise((resolve, reject) => {
    let data = ''
    process.stdin.setEncoding('utf8')
    process.stdin.on('data', chunk => { data += chunk })
    process.stdin.on('end', () => resolve(data))
    process.stdin.on('error', reject)
  })
}

// Builds one document's full-page HTML (all pages concatenated, each an
// absolutely-positioned 210x297mm block) exactly the way contractPdf.ts's
// renderDocumentIntoPdf() does for the canvas-document case - except here
// Chromium prints the real HTML natively instead of screenshotting it.
function buildDocumentHtml(rawOrHtml: string, student: Record<string, unknown>, contractMeta: Record<string, unknown>): string {
  const variableValues = buildVariableValues(student, contractMeta as any)
  if (isCanvasDocumentJson(rawOrHtml)) {
    const doc = deserializeCanvasDocument(rawOrHtml)
    if (doc) {
      return convertCanvasDocumentToHtml(doc, variableValues)
    }
  }
  // Legacy plain-HTML/text tariffs have no canvas document - contractPdf.ts's
  // prepareContractHtml() handles that path on the frontend by flowing text
  // into <p>/<h3> tags inside one continuously-flowing container rather than
  // fixed 210x297mm pages. That legacy path is intentionally NOT ported here
  // for the Stage 2 canary - canvas-contract is the only format exercised by
  // this test, per the project's own ContractDocumentEditor being canvas-only
  // for all current templates (see Stage 2 report's "Scope" note).
  throw new Error('Input is not a canvas-contract document - legacy plain-HTML rendering is out of scope for the Stage 2 canary.')
}

async function main() {
  const raw = await readStdin()
  const input: RenderInput = JSON.parse(raw)

  if (!input.outputPath) {
    throw new Error('outputPath is required')
  }

  const mainHtml = buildDocumentHtml(input.canvasSource || input.content, input.student || {}, input.contractMeta || {})
  const guardianHtml = input.guardianContent
    ? buildDocumentHtml(input.guardianContent, input.guardianStudent || input.student || {}, input.contractMeta || {})
    : ''

  // Deterministic print document: A4 pages stacked in reading order, each
  // page's own absolutely-positioned content untouched from the converter's
  // output. No responsive breakpoints, no device metrics - every render of
  // the same input produces byte-identical layout regardless of what
  // machine runs this script.
  const fullHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: #ffffff; }
  @page { size: 210mm 297mm; margin: 0; }
  @media print {
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; animation: none !important; transition: none !important; }
  }
  .canvas-a4-page-print p { margin: 0.2em 0; }
  .canvas-a4-page-print p:first-child { margin-top: 0 !important; }
  .canvas-a4-page-print p:last-child { margin-bottom: 0 !important; }
  .canvas-text-element ol { list-style-type: decimal !important; padding-left: 1.8em !important; margin: 0.3em 0 !important; }
  .canvas-text-element ol ol { list-style-type: lower-alpha !important; padding-left: 1.6em !important; margin: 0.15em 0 !important; }
  .canvas-text-element ol ol ol { list-style-type: lower-roman !important; padding-left: 1.6em !important; margin: 0.15em 0 !important; }
  .canvas-text-element ul { list-style-type: disc !important; padding-left: 1.8em !important; margin: 0.3em 0 !important; }
  .canvas-text-element ul ul { list-style-type: circle !important; padding-left: 1.6em !important; margin: 0.15em 0 !important; }
  .canvas-text-element li { margin: 0.15em 0 !important; }
</style>
</head>
<body>
${mainHtml}
${guardianHtml}
</body>
</html>`

  const browser = await chromium.launch({
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  })
  try {
    const page = await browser.newPage()
    const timeoutMs = input.timeoutMs ?? 15000
    page.setDefaultTimeout(timeoutMs)

    await page.setContent(fullHtml, { waitUntil: 'load', timeout: timeoutMs })
    // Explicit wait for every <img> (signature, stamp, logo, QR) to finish
    // decoding before printing - setContent's 'load' event fires once the
    // HTML document itself is parsed, not once every embedded image has
    // finished loading its data-URL bytes.
    await page.evaluate(async () => {
      const imgs = Array.from(document.querySelectorAll('img'))
      await Promise.all(
        imgs.map(img => {
          if (img.complete) return Promise.resolve()
          return new Promise<void>(resolve => {
            img.onload = () => resolve()
            img.onerror = () => resolve()
          })
        })
      )
    })
    await page.evaluate(() => document.fonts ? document.fonts.ready : Promise.resolve())

    await page.pdf({
      path: input.outputPath,
      width: '210mm',
      height: '297mm',
      printBackground: true,
      margin: { top: '0mm', right: '0mm', bottom: '0mm', left: '0mm' },
      preferCSSPageSize: true,
      timeout: timeoutMs,
    })

    const stats = fs.statSync(input.outputPath)
    console.log(JSON.stringify({ ok: true, bytes: stats.size }))
  } finally {
    // The PDF is already fully written to disk by this point (page.pdf()
    // above only resolves once the file is flushed) - a crash/hang while
    // tearing down Chromium itself must never turn a successful render
    // into a reported failure. Observed in production under the gunicorn
    // worker environment specifically (not reproducible via an interactive
    // shell or `python manage.py shell`): browser.close() intermittently
    // kills the Node process with SIGABRT after the real work is done,
    // which the parent (contract_pdf_service.py) then saw as exit=-6 even
    // though stdout already contained a valid {"ok":true} line. Wrapping
    // in try/catch plus a hard timeout stops a slow/crashing close() from
    // undoing a render that already succeeded.
    try {
      await Promise.race([
        browser.close(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('browser.close() timed out')), 5000)),
      ])
    } catch (closeErr) {
      console.error('browser.close() failed (render already succeeded, ignoring):', closeErr)
    }
  }
}

main().catch(err => {
  console.log(JSON.stringify({ ok: false, error: String(err && err.message || err) }))
  process.exit(1)
})
