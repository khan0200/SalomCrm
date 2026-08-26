#!/usr/bin/env node
/**
 * Static site generator for the SalomCRM marketing site.
 *
 * Produces `dist/` containing plain HTML with no client-side rendering:
 * every page's full content is in the source, so Google, Bing, Yandex and any
 * crawler that does not execute JavaScript see exactly what a visitor sees.
 *
 *   node marketing/build.mjs           build
 *   node marketing/build.mjs --check   build, then fail on any SEO defect
 *
 * The check pass is the guard against SEO regressions: duplicate titles or
 * descriptions, internal links pointing at nothing, orphaned pages, missing
 * canonicals, stray noindex, or invalid JSON-LD all fail the build.
 */

import { readFile, writeFile, mkdir, rm, copyFile, readdir, stat } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { site, pages } from './site.config.mjs'
import { render } from './lib/layout.mjs'

const root = path.dirname(fileURLToPath(import.meta.url))
const dist = path.join(root, 'dist')
const CHECK = process.argv.includes('--check')

const warnings = []
const errors = []

/* ── page rendering ───────────────────────────────────────────────────────── */

async function loadPages() {
  const built = []

  for (const entry of pages) {
    const mod = await import(`./content/${entry.module}.mjs`)
    const page = mod.default(site)
    if (page.warn) warnings.push(page.warn)
    built.push({
      ...page,
      path: entry.path,
      priority: entry.priority,
      changefreq: entry.changefreq,
      outFile: entry.path === '/' ? 'index.html' : path.join(entry.path.slice(1), 'index.html'),
    })
  }

  // 404 is rendered but never listed in the sitemap.
  const nf = (await import('./content/notfound.mjs')).default(site)
  built.push({ ...nf, outFile: '404.html', excludeFromSitemap: true })

  return built
}

/* ── sitemap ──────────────────────────────────────────────────────────────── */

// The one namespace every search engine accepts. Getting this wrong silently
// invalidates the entire sitemap, so it is a named constant and asserted below.
const SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'

function buildSitemap(built, lastmod) {
  const urls = built
    .filter((p) => !p.excludeFromSitemap && !p.noindex)
    .map((p) => {
      const loc = new URL(p.path, site.url).href
      return `  <url>
    <loc>${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${p.changefreq}</changefreq>
    <priority>${p.priority}</priority>
  </url>`
    })
    .join('\n')

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="${SITEMAP_NS}"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="${SITEMAP_NS} ${SITEMAP_NS}/sitemap.xsd">
${urls}
</urlset>
`
}

/* ── robots.txt ───────────────────────────────────────────────────────────── */

function buildRobots() {
  // Open to every crawler. The only exclusions are the IndexNow key file and
  // query-string variants, which would otherwise create duplicate URLs.
  return `# robots.txt for ${site.url}
# ${site.brand} — ${site.tagline}

User-agent: *
Allow: /

# Tracking parameters create duplicate URLs with identical content.
Disallow: /*?utm_
Disallow: /*?ref=
Disallow: /*?fbclid=

# Yandex reads Clean-param to fold parameterised URLs into the canonical one.
User-agent: Yandex
Allow: /
Clean-param: utm_source&utm_medium&utm_campaign&utm_term&utm_content&ref&fbclid

Sitemap: ${site.url}/sitemap.xml
`
}

/* ── web app manifest ─────────────────────────────────────────────────────── */

function buildManifest() {
  return JSON.stringify(
    {
      name: `${site.brand} — ${site.tagline}`,
      short_name: site.brand,
      description: site.description,
      start_url: '/',
      scope: '/',
      display: 'browser',
      background_color: '#ffffff',
      theme_color: '#0f172a',
      lang: site.locale,
      icons: [
        { src: '/assets/salomcrm-logo-192.png', sizes: '192x192', type: 'image/png' },
        { src: '/assets/salomcrm-logo-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      ],
    },
    null,
    2
  )
}

/* ── validation ───────────────────────────────────────────────────────────── */

/**
 * Check the sitemap and robots.txt themselves. Both are single points of
 * failure: a malformed sitemap is ignored wholesale, and a stray Disallow in
 * robots.txt can deindex the site.
 */
function validateSiteFiles(built, sitemap, robots) {
  if (!sitemap.includes(`xmlns="${SITEMAP_NS}"`)) {
    errors.push(`sitemap.xml: wrong urlset namespace, must be ${SITEMAP_NS}`)
  }

  const locs = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])
  const expected = built.filter((p) => !p.excludeFromSitemap && !p.noindex)

  if (locs.length !== expected.length) {
    errors.push(`sitemap.xml: lists ${locs.length} URLs but ${expected.length} pages are indexable`)
  }
  for (const loc of locs) {
    if (!loc.startsWith(`${site.url}/`)) errors.push(`sitemap.xml: ${loc} is not on ${site.url}`)
    // Every listed URL must be the canonical form — the trailing slash matters,
    // because /features and /features/ would otherwise be two URLs.
    if (!loc.endsWith('/')) errors.push(`sitemap.xml: ${loc} is missing its trailing slash`)
  }
  for (const page of expected) {
    const url = new URL(page.path, site.url).href
    if (!locs.includes(url)) errors.push(`sitemap.xml: ${page.path} is indexable but not listed`)
  }

  if (!robots.includes(`Sitemap: ${site.url}/sitemap.xml`)) {
    errors.push('robots.txt: does not point at the sitemap')
  }
  // A bare "Disallow: /" under the wildcard agent would deindex everything.
  if (/^\s*User-agent:\s*\*\s*$[\s\S]*?^\s*Disallow:\s*\/\s*$/m.test(robots)) {
    errors.push('robots.txt: blanket Disallow: / would deindex the whole site')
  }
}

function validate(built, rendered) {
  const seenTitles = new Map()
  const seenDescriptions = new Map()

  for (const page of built) {
    const html = rendered.get(page.outFile)
    const where = page.path || page.outFile

    // Unique, length-sane title and description.
    if (!page.title) errors.push(`${where}: missing <title>`)
    if (!page.description) errors.push(`${where}: missing meta description`)

    if (seenTitles.has(page.title)) {
      errors.push(`${where}: duplicate <title>, same as ${seenTitles.get(page.title)}`)
    } else seenTitles.set(page.title, where)

    if (seenDescriptions.has(page.description)) {
      errors.push(`${where}: duplicate meta description, same as ${seenDescriptions.get(page.description)}`)
    } else seenDescriptions.set(page.description, where)

    if (page.title.length > 65) warnings.push(`${where}: title is ${page.title.length} chars, may be truncated in results`)
    if (page.description.length > 165) warnings.push(`${where}: meta description is ${page.description.length} chars, may be truncated`)
    if (page.description.length < 70) warnings.push(`${where}: meta description is only ${page.description.length} chars, likely too thin`)

    // Exactly one H1.
    const h1s = html.match(/<h1[\s>]/g) || []
    if (h1s.length !== 1) errors.push(`${where}: expected exactly 1 <h1>, found ${h1s.length}`)

    // Heading order must not skip a level.
    const levels = [...html.matchAll(/<h([1-6])[\s>]/g)].map((m) => Number(m[1]))
    for (let i = 1; i < levels.length; i++) {
      if (levels[i] - levels[i - 1] > 1) {
        warnings.push(`${where}: heading jumps from h${levels[i - 1]} to h${levels[i]}`)
        break
      }
    }

    // Canonical present and self-referencing.
    const canonical = html.match(/<link rel="canonical" href="([^"]+)"/)
    if (!canonical) errors.push(`${where}: missing canonical`)
    else {
      const expected = new URL(page.path || '/404.html', site.url).href
      if (canonical[1] !== expected) errors.push(`${where}: canonical is ${canonical[1]}, expected ${expected}`)
    }

    // No accidental noindex on an indexable page.
    if (!page.noindex && /content="[^"]*noindex/.test(html)) {
      errors.push(`${where}: page is meant to be indexable but carries noindex`)
    }
    if (page.noindex && !/content="noindex/.test(html)) {
      errors.push(`${where}: page is meant to be noindex but the directive is missing`)
    }

    // Structured data must parse.
    const ld = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)
    if (!ld) errors.push(`${where}: no JSON-LD block`)
    else {
      try {
        const parsed = JSON.parse(ld[1].replace(/\\u003c/g, '<'))
        if (!parsed['@graph']?.length) errors.push(`${where}: JSON-LD @graph is empty`)
      } catch (e) {
        errors.push(`${where}: JSON-LD does not parse — ${e.message}`)
      }
    }

    // Every image needs an alt attribute (empty alt is valid for decorative).
    for (const img of html.match(/<img\b[^>]*>/g) || []) {
      if (!/\balt=/.test(img)) errors.push(`${where}: <img> without alt — ${img.slice(0, 70)}`)
      if (!/\bwidth=/.test(img) || !/\bheight=/.test(img)) {
        warnings.push(`${where}: <img> without explicit width/height, risks layout shift`)
      }
    }
  }

  /* Internal links: every in-site href must resolve to a real page or asset,
     and every page must be reachable from another page. */
  const known = new Set(built.filter((p) => p.path).map((p) => p.path))
  const inbound = new Map([...known].map((p) => [p, 0]))

  for (const page of built) {
    const html = rendered.get(page.outFile)
    const hrefs = [...html.matchAll(/href="([^"]+)"/g)].map((m) => m[1])

    for (const href of hrefs) {
      if (/^(https?:|mailto:|tel:|#)/.test(href)) continue

      const [pathname] = href.split('#')
      if (!pathname) continue

      if (known.has(pathname)) {
        // Do not let a page's own nav count as an inbound link to itself.
        if (pathname !== page.path) inbound.set(pathname, inbound.get(pathname) + 1)
        continue
      }

      // Otherwise it must be a real file in dist.
      const asset = path.join(dist, pathname)
      if (!existsSync(asset)) errors.push(`${page.path || page.outFile}: broken internal link → ${href}`)
    }
  }

  // Orphan check covers indexable pages only. The 404 is reachable by status
  // code rather than by a link, and linking to it from the nav would be wrong.
  const indexablePaths = new Set(built.filter((p) => p.path && !p.noindex).map((p) => p.path))
  for (const [p, count] of inbound) {
    if (p !== '/' && indexablePaths.has(p) && count === 0) {
      errors.push(`${p}: orphaned — no other page links to it`)
    }
  }
}

/* ── assets ───────────────────────────────────────────────────────────────── */

async function copyDir(src, dest) {
  if (!existsSync(src)) return
  await mkdir(dest, { recursive: true })
  for (const entry of await readdir(src)) {
    const s = path.join(src, entry)
    const d = path.join(dest, entry)
    if ((await stat(s)).isDirectory()) await copyDir(s, d)
    else await copyFile(s, d)
  }
}

/* ── main ─────────────────────────────────────────────────────────────────── */

async function main() {
  await rm(dist, { recursive: true, force: true })
  await mkdir(dist, { recursive: true })

  // Static files first, so the link checker can see them.
  await copyDir(path.join(root, 'public'), dist)

  const css = (await readFile(path.join(root, 'assets', 'styles.css'), 'utf8'))
    // Cheap minification: strip comments and collapse whitespace. Enough for a
    // stylesheet this size, and avoids pulling in a build dependency.
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\s+/g, ' ')
    .replace(/\s*([{}:;,>])\s*/g, '$1')
    .trim()

  const built = await loadPages()
  const rendered = new Map()

  for (const page of built) {
    const html = render(site, page, css)
    rendered.set(page.outFile, html)

    const outPath = path.join(dist, page.outFile)
    await mkdir(path.dirname(outPath), { recursive: true })
    await writeFile(outPath, html, 'utf8')
  }

  const lastmod = new Date().toISOString().slice(0, 10)
  const sitemap = buildSitemap(built, lastmod)
  const robots = buildRobots()

  await writeFile(path.join(dist, 'sitemap.xml'), sitemap, 'utf8')
  await writeFile(path.join(dist, 'robots.txt'), robots, 'utf8')
  await writeFile(path.join(dist, 'site.webmanifest'), buildManifest(), 'utf8')

  // IndexNow ownership proof: a file at the site root named <key>.txt whose
  // contents are the key itself.
  await writeFile(path.join(dist, `${site.indexNowKey}.txt`), site.indexNowKey, 'utf8')

  validate(built, rendered)
  validateSiteFiles(built, sitemap, robots)

  /* ── report ─────────────────────────────────────────────────────────────── */

  const indexable = built.filter((p) => !p.noindex).length
  console.log(`\n  ${site.brand} marketing site → marketing/dist`)
  console.log(`  ${indexable} indexable pages, ${built.length} rendered\n`)
  for (const p of built) {
    console.log(`    ${p.noindex ? '·' : '✓'} /${p.outFile.replace(/index\.html$/, '')}`.padEnd(28) + p.title)
  }

  if (warnings.length) {
    console.log(`\n  ${warnings.length} warning(s):`)
    for (const w of warnings) console.log(`    ! ${w}`)
  }

  if (errors.length) {
    console.log(`\n  ${errors.length} error(s):`)
    for (const e of errors) console.log(`    ✗ ${e}`)
    if (CHECK) {
      console.log('')
      process.exit(1)
    }
  } else {
    console.log('\n  No SEO errors.\n')
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
