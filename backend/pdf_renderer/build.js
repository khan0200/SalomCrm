// Syncs the 3 frontend source files this renderer depends on, then bundles
// them (via esbuild) into a single CommonJS file Node can require directly.
//
// Why copy instead of importing straight from ../../frontend/src: esbuild's
// bundler still needs these physically resolvable from pdf_renderer's own
// node_modules (qrcode-generator) - vendoring the 3 small source files here
// avoids reaching across the repo boundary with a fragile relative path
// that would break if the frontend tree ever moves. The sync step means a
// change to the real source is never silently stale for more than one build.
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

const FRONTEND_UTILS = path.join(__dirname, '..', '..', 'frontend', 'src', 'modules', 'contracts', 'utils')
const FRONTEND_TYPES = path.join(__dirname, '..', '..', 'frontend', 'src', 'modules', 'contracts', 'types')
const VENDOR_DIR = path.join(__dirname, 'src', 'vendor')

fs.mkdirSync(VENDOR_DIR, { recursive: true })
fs.mkdirSync(path.join(VENDOR_DIR, 'types'), { recursive: true })

fs.copyFileSync(
  path.join(FRONTEND_UTILS, 'contractCanvasConverter.ts'),
  path.join(VENDOR_DIR, 'contractCanvasConverter.ts')
)
fs.copyFileSync(
  path.join(FRONTEND_TYPES, 'contractCanvas.ts'),
  path.join(VENDOR_DIR, 'types', 'contractCanvas.ts')
)

// contractVariables.ts is synced with exactly one line rewritten: its
// `from './qrCode'` import is redirected to qrCodeNode.ts (same directory,
// same export signature - generateQrCodeDataUrl(text, options) returning a
// PNG data URL). The original qrCode.ts calls
// document.createElement('canvas'), unavailable in plain Node; qrCodeNode.ts
// does the same module-matrix rasterization via pngjs instead. esbuild's
// `alias` option can't redirect relative specifiers like './qrCode' (only
// bare package names), so the rewrite happens here at sync time instead -
// one line, done automatically on every build rather than hand-patched.
const variablesSrc = fs.readFileSync(path.join(FRONTEND_UTILS, 'contractVariables.ts'), 'utf8')
const patched = variablesSrc.replace(
  "import { generateQrCodeDataUrl } from './qrCode'",
  "import { generateQrCodeDataUrl } from './qrCodeNode'"
)
if (patched === variablesSrc) {
  throw new Error("Expected import line not found in contractVariables.ts - frontend source may have changed shape; update build.js's patch accordingly.")
}
fs.writeFileSync(path.join(VENDOR_DIR, 'contractVariables.ts'), patched)

// qrCodeNode.ts is hand-written (not vendored from frontend/) - it lives in
// src/ as the actual source of truth and is copied alongside the vendored
// files purely so contractVariables.ts's relative import (`./qrCodeNode`)
// resolves within the same directory.
fs.copyFileSync(
  path.join(__dirname, 'src', 'qrCodeNode.ts'),
  path.join(VENDOR_DIR, 'qrCodeNode.ts')
)

console.log('Synced contractCanvasConverter.ts + contractVariables.ts (qrCode import patched) + contractCanvas.ts from frontend/.')

esbuild.buildSync({
  entryPoints: [path.join(__dirname, 'src', 'render.ts')],
  bundle: true,
  platform: 'node',
  target: 'node18',
  format: 'cjs',
  outfile: path.join(__dirname, 'dist', 'render.js'),
  external: ['playwright'],
  logLevel: 'info',
})
console.log('Built dist/render.js')
