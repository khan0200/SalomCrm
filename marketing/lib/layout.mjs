/**
 * The HTML shell every marketing page is rendered into.
 *
 * The output is complete, static HTML: all content is present in the source,
 * there is no client-side rendering, and the only <script> on the page is the
 * JSON-LD block (which is data, not code). The mobile navigation is CSS-only,
 * so the site is fully usable — and fully crawlable — with JavaScript off.
 */

import { esc, jsonLd, abs } from './html.mjs'
import { graph } from './schema.mjs'
import { primaryNav } from '../site.config.mjs'

/** Verification meta tags, omitted individually when the token is unset. */
function verificationTags(site) {
  const v = site.verification
  return [
    v.google && `<meta name="google-site-verification" content="${esc(v.google)}" />`,
    v.bing && `<meta name="msvalidate.01" content="${esc(v.bing)}" />`,
    v.yandex && `<meta name="yandex-verification" content="${esc(v.yandex)}" />`,
  ]
    .filter(Boolean)
    .join('\n    ')
}

function header(site, currentPath) {
  const items = primaryNav
    .map((item) => {
      const current = item.href === currentPath
      // aria-current marks the active page for assistive tech; the same state
      // drives the visual highlight, so the two can never disagree.
      return `<li><a href="${esc(item.href)}"${current ? ' aria-current="page"' : ''}>${esc(item.label)}</a></li>`
    })
    .join('\n            ')

  return `<a class="skip" href="#main">Skip to main content</a>
    <header class="site-header">
      <div class="wrap header-inner">
        <a class="brand" href="/" aria-label="${esc(site.brand)} home">
          <img src="/assets/salomcrm-logo-64.png" width="32" height="32" alt="" fetchpriority="high" decoding="async" />
          <span>${esc(site.brand)}</span>
        </a>
        <input type="checkbox" id="nav-toggle" class="nav-toggle" />
        <label for="nav-toggle" class="nav-burger" aria-hidden="true"><span></span></label>
        <nav class="site-nav" aria-label="Primary">
          <ul>
            ${items}
          </ul>
        </nav>
        <a class="btn btn-sm btn-primary header-cta" href="${esc(site.appUrl)}/login" rel="noopener">Log in</a>
      </div>
    </header>`
}

/** Visible breadcrumb trail; its markup mirrors the BreadcrumbList exactly. */
function breadcrumbNav(trail) {
  if (!trail || trail.length < 2) return ''
  const crumbs = trail
    .map((c, i) => {
      const last = i === trail.length - 1
      return last
        ? `<li><span aria-current="page">${esc(c.label)}</span></li>`
        : `<li><a href="${esc(c.href)}">${esc(c.label)}</a></li>`
    })
    .join('\n          ')
  return `<nav class="breadcrumbs" aria-label="Breadcrumb">
      <div class="wrap">
        <ol>
          ${crumbs}
        </ol>
      </div>
    </nav>`
}

function footer(site) {
  const c = site.contact
  const nav = primaryNav
    .map((i) => `<li><a href="${esc(i.href)}">${esc(i.label)}</a></li>`)
    .join('\n              ')

  const contactBits = [
    c.email && `<li><a href="mailto:${esc(c.email)}">${esc(c.email)}</a></li>`,
    c.phone && `<li><a href="tel:${esc(c.phone)}">${esc(c.phone)}</a></li>`,
    c.telegram && `<li><a href="${esc(c.telegram)}" rel="noopener">Telegram</a></li>`,
    c.address.city && `<li>${esc([c.address.city, c.address.countryName].filter(Boolean).join(', '))}</li>`,
  ]
    .filter(Boolean)
    .join('\n              ')

  const social = site.sameAs.length
    ? `<ul class="footer-social">${site.sameAs
        .map((u) => {
          const label = new URL(u).hostname.replace(/^www\./, '')
          return `<li><a href="${esc(u)}" rel="noopener me">${esc(label)}</a></li>`
        })
        .join('')}</ul>`
    : ''

  return `<footer class="site-footer">
      <div class="wrap footer-grid">
        <div class="footer-brand">
          <a class="brand" href="/">
            <img src="/assets/salomcrm-logo-64.png" width="28" height="28" alt="" loading="lazy" decoding="async" />
            <span>${esc(site.brand)}</span>
          </a>
          <p>${esc(site.tagline)}.</p>
          ${social}
        </div>
        <div>
          <h2>Site</h2>
          <ul>
            ${nav}
          </ul>
        </div>
        <div>
          <h2>Product</h2>
          <ul>
            <li><a href="/features/">Features</a></li>
            <li><a href="/pricing/">Pricing</a></li>
            <li><a href="/docs/">Documentation</a></li>
            <li><a href="${esc(site.appUrl)}/login" rel="noopener">Log in to SalomCRM</a></li>
          </ul>
        </div>
        <div>
          <h2>Contact</h2>
          <ul>
            ${contactBits || '<li><a href="/contact/">Get in touch</a></li>'}
          </ul>
        </div>
      </div>
      <div class="wrap footer-legal">
        <p>&copy; ${new Date().getFullYear()} ${esc(site.legalName)}. ${esc(site.brand)} is operated by ${esc(site.legalName)}, ${esc(site.contact.address.countryName)}.</p>
      </div>
    </footer>`
}

/**
 * Render a complete page.
 *
 * @param site      resolved site config
 * @param page      { path, title, description, h1, trail, body, software, faqs,
 *                    ogType, noindex }
 * @param css       the stylesheet, inlined to avoid a render-blocking request
 */
export function render(site, page, css) {
  const canonical = abs(site.url, page.path)
  const ogImage = abs(site.url, '/assets/salomcrm-og.png')
  const robots = page.noindex
    ? 'noindex, nofollow'
    : 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1'

  const verify = verificationTags(site)

  return `<!doctype html>
<html lang="${esc(site.locale)}">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${esc(page.title)}</title>
    <meta name="description" content="${esc(page.description)}" />
    <link rel="canonical" href="${esc(canonical)}" />
    <meta name="robots" content="${robots}" />

    <meta property="og:type" content="${esc(page.ogType || 'website')}" />
    <meta property="og:site_name" content="${esc(site.brand)}" />
    <meta property="og:title" content="${esc(page.ogTitle || page.title)}" />
    <meta property="og:description" content="${esc(page.description)}" />
    <meta property="og:url" content="${esc(canonical)}" />
    <meta property="og:locale" content="${esc(site.localeTag)}" />
    <meta property="og:image" content="${esc(ogImage)}" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="${esc(site.brand)} — ${esc(site.tagline)}" />

    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="${esc(page.ogTitle || page.title)}" />
    <meta name="twitter:description" content="${esc(page.description)}" />
    <meta name="twitter:image" content="${esc(ogImage)}" />
    <meta name="twitter:image:alt" content="${esc(site.brand)} — ${esc(site.tagline)}" />

    <meta name="application-name" content="${esc(site.brand)}" />
    <meta name="theme-color" content="#0f172a" media="(prefers-color-scheme: dark)" />
    <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)" />
    <meta name="format-detection" content="telephone=no" />
    ${verify}

    <link rel="icon" href="/favicon.ico" sizes="any" />
    <link rel="icon" href="/assets/salomcrm-logo-64.png" type="image/png" sizes="64x64" />
    <link rel="apple-touch-icon" href="/assets/salomcrm-logo-180.png" />
    <link rel="manifest" href="/site.webmanifest" />

    <style>${css}</style>

    <script type="application/ld+json">
${jsonLd(graph(site, page))}
    </script>
  </head>
  <body>
    ${header(site, page.path)}
    ${breadcrumbNav(page.trail)}
    <main id="main">
${page.body}
    </main>
    ${footer(site)}
  </body>
</html>
`
}
