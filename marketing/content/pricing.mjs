import { esc } from '../lib/html.mjs'

/**
 * Pricing page.
 *
 * When a plan has no `amount` in site.config.mjs the card renders "Request a
 * quote" rather than a placeholder figure, and the plan is left out of the
 * Offer structured data. Nothing false is ever published, and filling in the
 * config is all it takes to switch a plan to a real advertised price.
 */
function formatPrice(site, plan) {
  if (typeof plan.amount !== 'number' || plan.amount <= 0) {
    return `<p class="plan-price">Request a quote</p>`
  }
  const formatted = new Intl.NumberFormat('en-US').format(plan.amount)
  return `<p class="plan-price">${esc(formatted)} ${esc(site.currency)} <small>/ ${esc(plan.period)}</small></p>`
}

export default function pricing(site) {
  const anyPriced = site.plans.some((p) => typeof p.amount === 'number' && p.amount > 0)

  const cards = site.plans
    .map(
      (plan) => `
            <div class="card plan${plan.featured ? ' is-featured' : ''}">
              ${plan.featured ? '<span class="plan-badge">Most chosen</span>' : ''}
              <h3>${esc(plan.name)}</h3>
              <p class="muted">${esc(plan.summary)}</p>
              ${formatPrice(site, plan)}
              <p class="plan-seats">${esc(plan.seats)}</p>
              <ul class="check">
                ${plan.features.map((f) => `<li>${esc(f)}</li>`).join('\n                ')}
              </ul>
              <a class="btn ${plan.featured ? 'btn-primary' : 'btn-ghost'}" href="/contact/">Talk to us about ${esc(plan.name)}</a>
            </div>`
    )
    .join('\n')

  // Answers to questions the sales conversation actually raises. They are
  // rendered visibly below, which is what makes the FAQPage markup legitimate.
  const faqs = [
    {
      q: `How is ${site.brand} priced?`,
      a: `${site.brand} is licensed per agency, with plan tiers based on how many staff accounts you need. Every plan includes the full student, payment, status and document modules — tiers differ in team size, multi-tenant support and level of onboarding, not in core functionality.`,
    },
    {
      q: 'Is there a limit on how many students I can manage?',
      a: 'No. Plans are bounded by staff accounts rather than student records, so a busy intake does not change what you pay.',
    },
    {
      q: 'Can several branches use one account?',
      a: 'Branches are set up as separate tenants with strictly isolated data, administered together. That arrangement is covered by the Network plan.',
    },
    {
      q: 'Can I move our existing student data in?',
      a: 'Yes. Existing records are usually imported from spreadsheets during onboarding. Tell us what you currently keep and in what format when you get in touch.',
    },
    {
      q: 'What support is included?',
      a: 'Every plan includes support for setup and day-to-day questions. Higher tiers add priority response and hands-on onboarding, including data migration.',
    },
  ]

  const faqHtml = faqs
    .map(
      (f) => `
            <div class="faq-item">
              <h3>${esc(f.q)}</h3>
              <p>${esc(f.a)}</p>
            </div>`
    )
    .join('\n')

  const body = `
      <section class="hero" style="padding-bottom:36px">
        <div class="wrap">
          <h1>Pricing</h1>
          <p class="lead">
            One licence per agency, priced by team size. Every plan includes the full
            product — <a href="/features/#students">students</a>,
            <a href="/features/#payments">payments</a>,
            <a href="/features/#status">status tracking</a> and
            <a href="/features/#documents">documents</a>.
          </p>
        </div>
      </section>

      <section style="padding-top:0">
        <div class="wrap">
          <h2>Plans</h2>
          <div class="grid grid-3" style="margin-top:24px">
${cards}
          </div>
          ${
            anyPriced
              ? `<p class="muted" style="margin-top:24px;font-size:.92rem">Prices are shown in ${esc(site.currency)} and exclude any applicable taxes.</p>`
              : `<p class="muted" style="margin-top:24px;font-size:.92rem">We quote per agency based on team size and onboarding needs. <a href="/contact/">Ask for a quote</a> and we will come back with a figure.</p>`
          }
        </div>
      </section>

      <section class="section-soft">
        <div class="wrap">
          <h2>Pricing questions</h2>
          <div class="faq" style="margin-top:24px">
${faqHtml}
          </div>
        </div>
      </section>

      <section>
        <div class="wrap">
          <div class="cta-band">
            <h2>Not sure which plan fits?</h2>
            <p class="muted">Tell us how your agency is structured and we will point you at the right one.</p>
            <div class="hero-actions">
              <a class="btn btn-primary" href="/contact/">Contact ${esc(site.brand)}</a>
              <a class="btn btn-ghost" href="/docs/">Read the documentation</a>
            </div>
          </div>
        </div>
      </section>`

  return {
    title: `${site.brand} Pricing — Plans for Education Agencies`,
    description: `${site.brand} pricing for education agencies. Plans by team size, with every module included in each tier. Request a quote for your agency.`,
    trail: [
      { href: '/', label: 'Home' },
      { href: '/pricing/', label: 'Pricing' },
    ],
    software: true,
    faqs,
    body,
  }
}
