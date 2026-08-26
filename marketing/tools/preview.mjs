#!/usr/bin/env node
/**
 * Local preview server for the built marketing site.
 *
 *   npm run site:preview      # builds, then serves on http://localhost:4321
 *
 * It mirrors the production nginx rules that affect SEO, so what you check
 * locally is what crawlers will see:
 *
 *   • `/features` 301-redirects to `/features/` (one canonical URL per page)
 *   • `/features/index.html` 301-redirects to `/features/`
 *   • an unknown URL returns a real 404 with the 404 page, never a 200 fallback
 *
 * That last rule is the important one. A static server that answers 200 for
 * everything would hide exactly the soft-404 problem this setup exists to fix.
 */

import { createServer } from 'node:http'
import { readFile, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const dist = path.join(path.dirname(path.dirname(fileURLToPath(import.meta.url))), 'dist')
const PORT = Number(process.env.PORT) || 4321

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
}

async function exists(p) {
  try {
    return await stat(p)
  } catch {
    return null
  }
}

const server = createServer(async (req, res) => {
  const { pathname } = new URL(req.url, `http://localhost:${PORT}`)

  const send = (code, body, type = 'text/html; charset=utf-8') => {
    res.writeHead(code, { 'Content-Type': type, 'X-Robots-Tag': 'noindex' })
    res.end(body)
    console.log(`  ${code}  ${pathname}`)
  }

  const redirect = (to) => {
    res.writeHead(301, { Location: to })
    res.end()
    console.log(`  301  ${pathname} → ${to}`)
  }

  // index.html is never a canonical URL.
  if (pathname.endsWith('/index.html')) {
    return redirect(pathname.slice(0, -'index.html'.length))
  }

  const target = path.join(dist, decodeURIComponent(pathname))

  // Guard against path traversal escaping dist.
  if (!target.startsWith(dist)) return send(403, 'Forbidden')

  const info = await exists(target)

  if (info?.isDirectory()) {
    if (!pathname.endsWith('/')) return redirect(pathname + '/')
    const index = path.join(target, 'index.html')
    if (await exists(index)) {
      return send(200, await readFile(index), TYPES['.html'])
    }
  } else if (info?.isFile()) {
    return send(200, await readFile(target), TYPES[path.extname(target)] || 'application/octet-stream')
  } else if (!pathname.endsWith('/')) {
    // `/features` when `/features/` exists — redirect rather than 404.
    if ((await exists(target + path.sep))?.isDirectory?.()) return redirect(pathname + '/')
    const asDir = await exists(path.join(dist, pathname, 'index.html'))
    if (asDir) return redirect(pathname + '/')
  }

  const notFound = await exists(path.join(dist, '404.html'))
  return send(404, notFound ? await readFile(path.join(dist, '404.html')) : 'Not found', TYPES['.html'])
})

server.listen(PORT, () => {
  console.log(`\n  SalomCRM marketing site → http://localhost:${PORT}\n`)
})
