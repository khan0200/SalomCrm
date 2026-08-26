import { esc } from '../lib/html.mjs'

/**
 * About page — the entity page.
 *
 * This is where the brand, the operating company and the region are stated
 * plainly in prose. Google leans on a page like this when deciding what the
 * "SalomCRM" entity is and who stands behind it, which is also what makes the
 * Organization structured data credible rather than unsupported.
 */
export default function about(site) {
  const a = site.contact.address
  const place = [a.city, a.countryName].filter(Boolean).join(', ')

  const body = `
      <section class="hero" style="padding-bottom:36px">
        <div class="wrap">
          <h1>About ${esc(site.brand)}</h1>
          <p class="lead">
            ${esc(site.brand)} is a student recruitment CRM built and operated by
            ${esc(site.legalName)}${place ? `, an education agency based in ${esc(place)}` : ''}.
          </p>
        </div>
      </section>

      <section style="padding-top:0">
        <div class="wrap prose">
          <h2>Built from the work, not for a market</h2>
          <p>
            ${esc(site.brand)} started as the internal system ${esc(site.legalName)} needed
            to run its own placements. Off-the-shelf CRMs handle leads and deals; they do
            not understand tariffs that change with a language certificate, KDB deposit
            windows that decide whether a placement survives, or embassy document sets
            that must be complete before anything else can move.
          </p>
          <p>
            So the tooling was built around the actual sequence an education agency
            works through, and then made available to other agencies running the same
            process.
          </p>

          <h2>What we care about in the product</h2>
          <p>
            <strong>Numbers that cannot be fudged.</strong> Balances are derived from
            payment history rather than stored as an editable figure. If the ledger and
            reality disagree, the ledger is wrong for a reason you can trace.
          </p>
          <p>
            <strong>Isolation that is real.</strong> Multi-tenancy is enforced in every
            database query, not by hiding rows in the interface. An agency's data is not
            reachable by another agency, and that is a property of the system rather
            than a promise in a policy document.
          </p>
          <p>
            <strong>Deadlines in the open.</strong> The information that decides whether
            a placement succeeds should be on a shared board, not in one person's head.
          </p>

          <h2>Where we work</h2>
          <p>
            ${esc(site.legalName)} operates ${place ? `from ${esc(place)}` : 'in Uzbekistan'},
            focused on placing students into Korean universities. The product reflects
            that: ${esc(site.currency)} pricing, KDB deposit handling, and the embassy
            document flow that route actually requires.
          </p>
          <p>
            Agencies working other corridors use ${esc(site.brand)} too — the student,
            payment and document modules are not Korea-specific — but the deadline and
            deposit tracking was built for this one first.
          </p>

          <h2>Get in touch</h2>
          <p>
            To see the product against your own process, <a href="/contact/">contact us</a>.
            To understand what it does first, read the
            <a href="/features/">features overview</a> or the
            <a href="/docs/">documentation</a>.
          </p>
        </div>
      </section>`

  return {
    title: `About ${site.brand} — Built by ${site.legalName}`,
    description: `${site.brand} is a student recruitment CRM built and operated by ${site.legalName}${place ? ` in ${place}` : ''}, made for education agencies placing students in Korean universities.`,
    trail: [
      { href: '/', label: 'Home' },
      { href: '/about/', label: 'About' },
    ],
    body,
  }
}
