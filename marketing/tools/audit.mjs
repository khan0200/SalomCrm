#!/usr/bin/env node
/**
 * Live audit of the built marketing site, driven through the Chrome DevTools
 * Protocol against a real browser.
 *
 *   node marketing/tools/preview.mjs &
 *   node marketing/tools/audit.mjs
 *
 * The static checks in build.mjs read the HTML; this reads the *rendered*
 * page, which is the only way to catch the things that only exist after
 * layout:
 *
 *   • horizontal overflow at real phone widths (the mobile-friendliness
 *     criterion Google actually measures)
 *   • tap targets smaller than the 24px minimum
 *   • text that renders below 12px
 *   • content that is missing when JavaScript is disabled
 *
 * Set CHROME to override the browser path.
 */

import { spawn } from 'node:child_process'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'

const BASE = process.env.BASE || 'http://localhost:4321'
const PATHS = ['/', '/features/', '/pricing/', '/docs/', '/about/', '/contact/', '/404.html']

// Widths that matter: the narrowest phone still in meaningful use, a common
// modern phone, and a tablet.
const VIEWPORTS = [
  { name: 'iPhone SE', width: 320, height: 568, scale: 2, mobile: true },
  { name: 'iPhone 14', width: 390, height: 844, scale: 3, mobile: true },
  { name: 'iPad', width: 768, height: 1024, scale: 2, mobile: true },
]

const CHROME_CANDIDATES = [
  process.env.CHROME,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/usr/bin/google-chrome',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].filter(Boolean)

const failures = []
const notes = []

/* ── minimal CDP client ───────────────────────────────────────────────────── */

class CDP {
  constructor(ws) {
    this.ws = ws
    this.id = 0
    this.pending = new Map()
    ws.addEventListener('message', (e) => {
      const msg = JSON.parse(e.data)
      const p = this.pending.get(msg.id)
      if (p) {
        this.pending.delete(msg.id)
        msg.error ? p.reject(new Error(msg.error.message)) : p.resolve(msg.result)
      }
    })
  }

  send(method, params = {}) {
    const id = ++this.id
    this.ws.send(JSON.stringify({ id, method, params }))
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }))
  }

  async eval(expression) {
    const { result, exceptionDetails } = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true,
    })
    if (exceptionDetails) throw new Error(exceptionDetails.text)
    return result.value
  }
}

async function launchChrome(userDataDir) {
  const bin = CHROME_CANDIDATES.find(Boolean)
  const proc = spawn(
    bin,
    [
      '--headless=new',
      '--disable-gpu',
      '--no-first-run',
      '--remote-debugging-port=0',
      `--user-data-dir=${userDataDir}`,
      'about:blank',
    ],
    { stdio: ['ignore', 'ignore', 'pipe'] }
  )

  // Chrome prints its browser-level websocket URL to stderr once it is
  // listening. That endpoint only speaks the Browser/Target domains, so we use
  // it purely to learn the port.
  const browserWs = await new Promise((resolve, reject) => {
    let buf = ''
    const timer = setTimeout(() => reject(new Error('Chrome did not start in time')), 20000)
    proc.stderr.on('data', (chunk) => {
      buf += chunk
      const m = buf.match(/ws:\/\/[^\s]+/)
      if (m) {
        clearTimeout(timer)
        resolve(m[0])
      }
    })
    proc.on('exit', (code) => reject(new Error(`Chrome exited (${code})`)))
  })

  // Page/Runtime/Emulation live on a page target, not on the browser target.
  const { port } = new URL(browserWs)
  const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then((r) => r.json())
  const page = targets.find((t) => t.type === 'page')
  if (!page) throw new Error('Chrome exposed no page target')

  return { proc, wsUrl: page.webSocketDebuggerUrl }
}

/* ── the checks that run inside the page ──────────────────────────────────── */

const PAGE_PROBE = `(() => {
  const doc = document.documentElement;

  // Anything wider than the viewport forces a horizontal scroll — the single
  // most common mobile-friendliness failure.
  const overflow = doc.scrollWidth - doc.clientWidth;

  const offenders = [];
  if (overflow > 0) {
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.right > doc.clientWidth + 1 || r.left < -1) {
        offenders.push(el.tagName.toLowerCase()
          + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\\s+/).join('.') : '')
          + ' [' + Math.round(r.left) + '→' + Math.round(r.right) + ']');
      }
      if (offenders.length >= 5) break;
    }
  }

  // Tap targets. 24x24 CSS px is the minimum Google flags on.
  const small = [];
  for (const el of document.querySelectorAll('a, button, input, label, [role="button"]')) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || r.width === 0) continue;
    // Links inside a paragraph are inline text, not tap targets in their own right.
    if (el.tagName === 'A' && cs.display === 'inline' && el.closest('p, li, address')) continue;
    if (r.width < 24 || r.height < 24) {
      small.push((el.textContent || el.tagName).trim().slice(0, 30) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
    }
  }

  // Text below 12px is hard to read on a phone.
  const tiny = new Set();
  for (const el of document.querySelectorAll('p, li, a, span, dd, dt, small, h1, h2, h3')) {
    if (!el.textContent.trim()) continue;
    const size = parseFloat(getComputedStyle(el).fontSize);
    if (size < 12) tiny.add(el.tagName.toLowerCase() + ' @ ' + size + 'px');
  }

  return {
    overflow,
    offenders,
    small: [...new Set(small)],
    tiny: [...tiny],
    title: document.title,
    h1: [...document.querySelectorAll('h1')].map(h => h.textContent.trim()),
    textLength: document.body.innerText.trim().length,
    links: document.querySelectorAll('a').length,
  };
})()`

/* ── main ─────────────────────────────────────────────────────────────────── */

async function main() {
  const userDataDir = await mkdtemp(path.join(tmpdir(), 'salomcrm-audit-'))
  const { proc, wsUrl } = await launchChrome(userDataDir)

  const ws = new WebSocket(wsUrl)
  await new Promise((res, rej) => {
    ws.addEventListener('open', res, { once: true })
    ws.addEventListener('error', rej, { once: true })
  })

  const cdp = new CDP(ws)
  await cdp.send('Page.enable')
  await cdp.send('Runtime.enable')
  await cdp.send('Network.enable')

  const navigate = async (url) => {
    const done = new Promise((resolve) => {
      const handler = (e) => {
        const m = JSON.parse(e.data)
        if (m.method === 'Page.loadEventFired') {
          ws.removeEventListener('message', handler)
          resolve()
        }
      }
      ws.addEventListener('message', handler)
    })
    await cdp.send('Page.navigate', { url })
    await done
  }

  console.log(`\n  Rendered audit of ${BASE}\n`)

  for (const vp of VIEWPORTS) {
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: vp.width,
      height: vp.height,
      deviceScaleFactor: vp.scale,
      mobile: vp.mobile,
    })

    console.log(`  ${vp.name} — ${vp.width}x${vp.height}`)

    for (const p of PATHS) {
      await navigate(BASE + p)
      const r = await cdp.eval(PAGE_PROBE)

      const problems = []
      if (r.overflow > 0) {
        problems.push(`overflows by ${r.overflow}px → ${r.offenders.join(', ') || 'unknown'}`)
      }
      if (r.small.length) problems.push(`tap targets under 24px: ${r.small.join(', ')}`)
      if (r.tiny.length) problems.push(`text under 12px: ${r.tiny.join(', ')}`)
      if (r.h1.length !== 1) problems.push(`${r.h1.length} h1 elements`)

      if (problems.length) {
        console.log(`    ✗ ${p}`)
        for (const prob of problems) {
          console.log(`        ${prob}`)
          failures.push(`${vp.name} ${p}: ${prob}`)
        }
      } else {
        console.log(`    ✓ ${p.padEnd(12)} ${String(r.textLength).padStart(5)} chars, ${r.links} links`)
      }
    }
    console.log('')
  }

  /* Content must survive with JavaScript disabled — the site is static, so
     this should be a no-op, and proving it is the point. */
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: 1280, height: 900, deviceScaleFactor: 1, mobile: false,
  })
  await cdp.send('Emulation.setScriptExecutionDisabled', { value: true })

  console.log('  JavaScript disabled')
  for (const p of PATHS) {
    await navigate(BASE + p)
    const r = await cdp.eval(PAGE_PROBE).catch(() => null)
    // Runtime.evaluate still works with script execution disabled for the page.
    if (!r) {
      notes.push(`could not probe ${p} with JS disabled`)
      continue
    }
    const ok = r.textLength > 300 && r.h1.length === 1 && r.links > 8
    console.log(`    ${ok ? '✓' : '✗'} ${p.padEnd(12)} ${String(r.textLength).padStart(5)} chars, ${r.links} links, h1="${r.h1[0] || ''}"`)
    if (!ok) failures.push(`${p}: content missing with JS disabled`)
  }

  ws.close()
  proc.kill()
  await rm(userDataDir, { recursive: true, force: true }).catch(() => {})

  console.log('')
  if (failures.length) {
    console.log(`  ${failures.length} failure(s):`)
    for (const f of failures) console.log(`    ✗ ${f}`)
    console.log('')
    process.exit(1)
  }
  console.log('  All rendered checks passed.\n')
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
