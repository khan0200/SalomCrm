import { esc } from '../lib/html.mjs'

/**
 * Documentation / help hub.
 *
 * Deliberately a real, self-contained help page rather than a stub linking
 * into the app: an authenticated help centre cannot be crawled, so the public
 * explanation of roles and workflows lives here.
 */
export default function docs(site) {
  const faqs = [
    {
      q: `Who can see which students in ${site.brand}?`,
      a: 'Staff only ever see students belonging to their own agency. Isolation is enforced on the server for every query, so it holds regardless of what the interface shows or what a request asks for.',
    },
    {
      q: 'How is a student balance calculated?',
      a: 'Balance equals total payments plus total discounts, minus the tariff price. It is derived on read rather than stored as an editable field, so it always reflects the payment history.',
    },
    {
      q: 'What do the KDB urgency levels mean?',
      a: 'Each student with a KDB deposit date is classified by how much time remains: normal, urgent, critical, or overdue once the date has passed. The status board sorts by this classification so the most pressing cases surface first.',
    },
    {
      q: `Can I export data out of ${site.brand}?`,
      a: 'Yes. Both the student list and the payment ledger export to Excel, and the student export lets you choose which columns and which students are included.',
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
          <h1>Documentation</h1>
          <p class="lead">
            How ${esc(site.brand)} is structured, what each role can do, and how a
            placement moves through the system from intake to visa.
          </p>
        </div>
      </section>

      <section style="padding-top:0">
        <div class="wrap prose">
          <h2 id="roles">Roles and permissions</h2>
          <p>
            ${esc(site.brand)} has three levels of access. Each is enforced server-side;
            the interface reflects permissions rather than defining them.
          </p>
          <dl class="dl" style="margin:20px 0 8px">
            <div>
              <dt>Manager</dt>
              <dd>
                Works placements for their own agency: student records, documents,
                visa and status tracking. Does not see agency-wide financial totals.
              </dd>
            </div>
            <div>
              <dt>Head manager</dt>
              <dd>
                Everything a manager can do, plus the payment ledger, discounts,
                withdrawals and staff account management for the agency.
              </dd>
            </div>
            <div>
              <dt>Platform administrator</dt>
              <dd>
                Operates across tenants. Used by groups running several branches, and
                for creating new agencies on the platform.
              </dd>
            </div>
          </dl>

          <h2 id="workflow">The placement workflow</h2>
          <ol>
            <li>
              <strong>Intake.</strong> Create the student record with an agency ID and
              assign a tariff. Uploaded documents can have their details extracted
              automatically rather than retyped.
            </li>
            <li>
              <strong>University selection.</strong> Record the chosen university on the
              status board, which determines the document set and the deadlines that
              follow.
            </li>
            <li>
              <strong>Payments.</strong> Record payments and discounts against the
              student. The balance recalculates on every change — see
              <a href="/features/#payments">how the ledger works</a>.
            </li>
            <li>
              <strong>KDB deposit.</strong> Set the deposit date. The student enters the
              urgency queue and moves through normal, urgent and critical as the date
              approaches.
            </li>
            <li>
              <strong>Embassy and visa.</strong> Work the sponsorship document set and
              record the visa outcome. Missing documents are shown as explicit blocking
              reasons.
            </li>
          </ol>

          <h2 id="getting-started">Getting started</h2>
          <p>
            New agencies are set up as their own tenant, with a head manager account
            created first. That account then creates staff accounts, sets the agency's
            tariffs, and imports existing student data — usually from spreadsheets you
            already keep.
          </p>
          <p>
            If you are already set up, sign in at
            <a href="${esc(site.appUrl)}/login" rel="noopener">${esc(site.appUrl.replace(/^https?:\/\//, ''))}</a>.
            If you are evaluating ${esc(site.brand)}, start with the
            <a href="/features/">features overview</a> or
            <a href="/contact/">ask for a walkthrough</a>.
          </p>

          <h2 id="data">Your data</h2>
          <p>
            Each agency's records are isolated at the database query level rather than
            filtered in the interface. Significant actions — payment edits, deletions,
            withdrawals, account changes — are written to an audit log, so financial
            history can be reconstructed after the fact.
          </p>
          <p>
            Data can be exported to Excel at any time from both the student list and the
            payment ledger.
          </p>
        </div>
      </section>

      <section class="section-soft">
        <div class="wrap">
          <h2>Common questions</h2>
          <div class="faq" style="margin-top:24px">
${faqHtml}
          </div>
        </div>
      </section>

      <section>
        <div class="wrap">
          <div class="cta-band">
            <h2>Question not answered here?</h2>
            <p class="muted">Support handles setup and day-to-day questions on every plan.</p>
            <div class="hero-actions">
              <a class="btn btn-primary" href="/contact/">Contact support</a>
            </div>
          </div>
        </div>
      </section>`

  return {
    title: `${site.brand} Documentation — Roles, Workflow & Setup`,
    description: `How ${site.brand} works: manager, head manager and administrator roles, the placement workflow from intake through KDB deposit to visa, agency setup, and data export.`,
    trail: [
      { href: '/', label: 'Home' },
      { href: '/docs/', label: 'Documentation' },
    ],
    faqs,
    body,
  }
}
