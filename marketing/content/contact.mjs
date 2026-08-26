import { esc } from '../lib/html.mjs'

/**
 * Contact page.
 *
 * Renders only the channels that are actually configured. If no channel is set
 * the page says so honestly rather than showing a placeholder address — and
 * the build prints a warning, because a contact page with no way to make
 * contact is the one page on the site that must not ship half-finished.
 */
export default function contact(site) {
  const c = site.contact
  const a = c.address
  const place = [a.street, a.city, a.region, a.postalCode, a.countryName].filter(Boolean).join(', ')

  const channels = [
    c.email && {
      title: 'Email',
      body: `<p><a href="mailto:${esc(c.email)}">${esc(c.email)}</a></p>
              <p class="muted">Best for demo requests, pricing questions and onboarding.</p>`,
    },
    c.phone && {
      title: 'Phone',
      body: `<p><a href="tel:${esc(c.phone)}">${esc(c.phone)}</a></p>
              ${c.hours ? `<p class="muted">${esc(c.hours)}</p>` : ''}`,
    },
    c.telegram && {
      title: 'Telegram',
      body: `<p><a href="${esc(c.telegram)}" rel="noopener">Message us on Telegram</a></p>
              <p class="muted">Usually the fastest way to reach us.</p>`,
    },
    place && {
      title: 'Office',
      body: `<address style="font-style:normal">${esc(place)}</address>`,
    },
  ].filter(Boolean)

  const channelCards = channels
    .map(
      (ch) => `
            <div class="card">
              <h3>${esc(ch.title)}</h3>
              ${ch.body}
            </div>`
    )
    .join('\n')

  const hasDirectChannel = Boolean(c.email || c.phone || c.telegram)

  const body = `
      <section class="hero" style="padding-bottom:36px">
        <div class="wrap">
          <h1>Contact ${esc(site.brand)}</h1>
          <p class="lead">
            For a demo, a quote, or help with an existing account — here is how to reach
            ${esc(site.legalName)}.
          </p>
        </div>
      </section>

      <section style="padding-top:0">
        <div class="wrap">
          <h2>How to reach us</h2>
          <div class="grid grid-2" style="margin-top:24px">
${channelCards}
          </div>
          ${
            hasDirectChannel
              ? ''
              : `<p class="muted" style="margin-top:24px">
            Direct contact channels are being finalised. In the meantime, existing
            customers can raise questions from inside the application after
            <a href="${esc(site.appUrl)}/login" rel="noopener">signing in</a>.
          </p>`
          }
        </div>
      </section>

      <section class="section-soft">
        <div class="wrap">
          <h2>What to tell us</h2>
          <p class="lead">
            A walkthrough is more useful when we know your situation. It helps to
            mention:
          </p>
          <ul class="check" style="margin-top:20px;max-width:62ch">
            <li>How many staff would use ${esc(site.brand)}</li>
            <li>Roughly how many students you handle per intake</li>
            <li>Whether you run one office or several branches</li>
            <li>What you currently track payments in</li>
            <li>Which placement corridors you work</li>
          </ul>
          <p style="margin-top:24px">
            If you would rather read first, the <a href="/features/">features overview</a>
            and <a href="/pricing/">pricing</a> cover most of it, and the
            <a href="/docs/">documentation</a> explains roles and workflow.
          </p>
        </div>
      </section>

      <section>
        <div class="wrap">
          <div class="cta-band">
            <h2>Already using ${esc(site.brand)}?</h2>
            <p class="muted">Sign in to your agency's workspace.</p>
            <div class="hero-actions">
              <a class="btn btn-primary" href="${esc(site.appUrl)}/login" rel="noopener">Log in</a>
            </div>
          </div>
        </div>
      </section>`

  return {
    title: `Contact ${site.brand} — Demos, Pricing & Support`,
    description: `Get in touch with ${site.legalName} about ${site.brand}: request a demo, ask for a quote for your education agency, or get support with an existing account.`,
    trail: [
      { href: '/', label: 'Home' },
      { href: '/contact/', label: 'Contact' },
    ],
    body,
    // Surfaced by the build so an unfinished contact page cannot ship silently.
    warn: hasDirectChannel
      ? null
      : 'contact: no email, phone or Telegram set in site.config.mjs — the contact page has no direct channel.',
  }
}
