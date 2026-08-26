import { esc } from '../lib/html.mjs'
import { primaryNav } from '../site.config.mjs'

/**
 * 404 page. Served with a real 404 status by nginx and marked noindex, so a
 * mistyped URL never becomes an indexable soft-404. It still offers the full
 * navigation, which keeps a lost crawler (or visitor) one click from a real page.
 */
export default function notfound(site) {
  const links = primaryNav
    .map((i) => `<li><a href="${esc(i.href)}">${esc(i.label)}</a></li>`)
    .join('\n              ')

  const body = `
      <section class="notfound">
        <div class="wrap">
          <h1>Page not found</h1>
          <p class="lead" style="margin-inline:auto">
            That URL does not exist on the ${esc(site.brand)} site. It may have moved, or
            the link that brought you here may be out of date.
          </p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="/">Go to the home page</a>
            <a class="btn btn-ghost" href="/contact/">Contact us</a>
          </div>
          <nav aria-label="Site pages" style="margin-top:38px">
            <ul class="site-nav-fallback" style="display:flex;flex-wrap:wrap;gap:16px;justify-content:center;list-style:none;padding:0;font-size:.95rem">
              ${links}
            </ul>
          </nav>
        </div>
      </section>`

  return {
    path: '/404.html',
    title: `Page not found — ${site.brand}`,
    description: `That page does not exist on the ${site.brand} site. Browse features, pricing, documentation and contact details from here instead.`,
    trail: null,
    noindex: true,
    body,
  }
}
