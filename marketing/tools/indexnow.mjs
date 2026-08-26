#!/usr/bin/env node
/**
 * IndexNow submission for the SalomCRM marketing site.
 *
 * IndexNow lets a site tell participating engines that URLs have changed,
 * instead of waiting to be recrawled. Bing, Yandex, Seznam and Naver consume
 * it; Google does not participate, and reads the sitemap instead.
 *
 *   node marketing/tools/indexnow.mjs             # dry run — prints, sends nothing
 *   node marketing/tools/indexnow.mjs --submit    # actually notifies the engines
 *
 * Submitting is an outward-facing action, so it never happens by accident:
 * without --submit this only reports what would be sent.
 *
 * Ownership is proved by a file at the site root named <key>.txt containing
 * the key. `build.mjs` writes it, so it ships with every build — but it only
 * proves ownership once the site is actually live at site.url.
 */

import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { site } from '../site.config.mjs'

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const SUBMIT = process.argv.includes('--submit')

// api.indexnow.org fans a submission out to every participating engine. The
// engine-specific endpoints are listed for reference; submitting to one is
// enough, and submitting to all of them is not faster.
const ENDPOINT = 'https://api.indexnow.org/indexnow'

async function readSitemapUrls() {
  const xml = await readFile(path.join(root, 'dist', 'sitemap.xml'), 'utf8')
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])
}

async function main() {
  const host = new URL(site.url).hostname
  const keyLocation = `${site.url}/${site.indexNowKey}.txt`
  const urlList = await readSitemapUrls()

  if (!urlList.length) {
    console.error('No URLs in marketing/dist/sitemap.xml — run `node marketing/build.mjs` first.')
    process.exit(1)
  }

  const payload = { host, key: site.indexNowKey, keyLocation, urlList }

  console.log(`\n  IndexNow → ${ENDPOINT}`)
  console.log(`  host:        ${host}`)
  console.log(`  keyLocation: ${keyLocation}`)
  console.log(`  ${urlList.length} URL(s):`)
  for (const u of urlList) console.log(`    ${u}`)

  if (!SUBMIT) {
    console.log('\n  Dry run. Re-run with --submit to notify the engines.\n')
    return
  }

  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(payload),
  })

  // 200 accepted, 202 accepted but key still being validated. 403 means the
  // key file is not reachable at keyLocation; 422 means the URLs do not match
  // the declared host.
  const body = await res.text()
  console.log(`\n  ${res.status} ${res.statusText}${body ? ` — ${body.trim()}` : ''}`)

  if (res.status === 403) {
    console.log(`  The key file is not readable. Check that ${keyLocation} returns the key as plain text.`)
  }
  console.log('')

  if (!res.ok && res.status !== 202) process.exit(1)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
