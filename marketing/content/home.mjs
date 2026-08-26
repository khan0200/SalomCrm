import { esc } from '../lib/html.mjs'

/**
 * Home page.
 *
 * Answers, in the first screen of markup, the four things Google needs to
 * associate the brand with the product: what SalomCRM is, who it is for, what
 * it solves, and who operates it. Every claim here is a capability that
 * actually exists in the product.
 */
export default function home(site) {
  const body = `
      <section class="hero">
        <div class="wrap">
          <h1>Student recruitment CRM for education agencies</h1>
          <p class="lead">
            ${esc(site.brand)} is the system ${esc(site.legalName)} uses to run student
            placements to Korean universities — applications, payments, KDB deposits,
            visa paperwork and embassy status tracked in one place instead of across
            a dozen spreadsheets.
          </p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="/contact/">Request a demo</a>
            <a class="btn btn-ghost" href="/features/">See what it does</a>
          </div>
          <p class="hero-note">
            Already a customer? <a href="${esc(site.appUrl)}/login" rel="noopener">Log in to ${esc(site.brand)}</a>.
          </p>
        </div>
      </section>

      <section class="section-soft">
        <div class="wrap">
          <h2>The problem it solves</h2>
          <p class="lead">
            An education agency loses money in the gaps between systems. A student's
            tariff lives in one spreadsheet, their payments in another, their KDB
            deposit deadline in someone's head, and their embassy documents in a
            shared folder nobody has opened in a week.
          </p>
          <div class="grid grid-3" style="margin-top:32px">
            <div class="card">
              <h3>Money that does not reconcile</h3>
              <p>
                Tariffs, discounts, part payments and refunds get tracked by hand, so
                nobody can say what a student actually owes today.
                <a href="/features/#payments">How the ledger works</a>.
              </p>
            </div>
            <div class="card">
              <h3>Deadlines that pass silently</h3>
              <p>
                A missed KDB deposit window costs a placement. Without a shared board,
                urgency lives in individual memory.
                <a href="/features/#status">See the status board</a>.
              </p>
            </div>
            <div class="card">
              <h3>Paperwork nobody can audit</h3>
              <p>
                Visa and embassy document sets are assembled ad hoc, and when a file is
                missing there is no record of who was responsible.
                <a href="/features/#documents">See document tracking</a>.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div class="wrap">
          <h2>What ${esc(site.brand)} gives you</h2>
          <div class="grid grid-2" style="margin-top:28px">
            <div class="card">
              <h3>A single student record</h3>
              <p>
                Every student carries their own agency ID, tariff, payment history,
                university choice, document set and visa state. Opening one record
                answers every question about that placement.
              </p>
            </div>
            <div class="card">
              <h3>A financial ledger that balances itself</h3>
              <p>
                Balance is derived, never typed: payments plus discounts minus the
                tariff. Editing or deleting a payment recalculates the student's
                position atomically, so the books cannot drift.
              </p>
            </div>
            <div class="card">
              <h3>Deadline pressure made visible</h3>
              <p>
                KDB deposit dates drive a shared urgency state — overdue, critical,
                urgent, normal — so the whole team sees the same priorities without
                a morning meeting.
              </p>
            </div>
            <div class="card">
              <h3>Strict separation between branches</h3>
              <p>
                Each agency is a tenant with its own isolated data. Staff see their own
                agency's students and nothing else, enforced on the server rather than
                hidden in the interface.
              </p>
            </div>
          </div>
          <p style="margin-top:28px">
            The <a href="/features/">features page</a> covers each area in detail, and the
            <a href="/docs/">documentation</a> walks through roles and daily workflows.
          </p>
        </div>
      </section>

      <section class="section-soft">
        <div class="wrap">
          <h2>Who it is for</h2>
          <dl class="dl" style="margin-top:24px;max-width:74ch">
            <div>
              <dt>Education agencies placing students abroad</dt>
              <dd>
                Especially agencies working Uzbekistan-to-Korea placements, where KDB
                deposit rules and embassy document sets drive the timeline.
              </dd>
            </div>
            <div>
              <dt>Head managers who own the numbers</dt>
              <dd>
                Full visibility of every student's balance, every payment and every
                withdrawal, with an audit log behind it.
              </dd>
            </div>
            <div>
              <dt>Managers handling day-to-day placements</dt>
              <dd>
                A working queue scoped to their own agency, with the document and visa
                state they need and nothing they should not see.
              </dd>
            </div>
            <div>
              <dt>Multi-branch operators</dt>
              <dd>
                Run several agencies as separate tenants under one platform, with
                administration across all of them.
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section>
        <div class="wrap">
          <div class="cta-band">
            <h2>See ${esc(site.brand)} on your own intake</h2>
            <p class="muted">
              We will walk through your current process and show where the system fits.
            </p>
            <div class="hero-actions">
              <a class="btn btn-primary" href="/contact/">Get in touch</a>
              <a class="btn btn-ghost" href="/pricing/">View pricing</a>
            </div>
          </div>
        </div>
      </section>`

  return {
    // Brand first: the strongest signal for branded queries, and the anchor
    // Google uses when deciding what the site's main result is called.
    title: `${site.brand} — Student Recruitment CRM for Education Agencies`,
    description: site.description,
    trail: null, // no breadcrumb on the root
    software: true, // SoftwareApplication schema belongs on the product's home
    body,
  }
}
