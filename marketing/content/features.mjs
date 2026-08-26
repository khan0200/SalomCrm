import { esc } from '../lib/html.mjs'

/**
 * Features page.
 *
 * Section ids are stable and linked to from the home page and the docs, which
 * gives Google in-page anchors it can surface. Each section is a real module
 * of the product.
 */
export default function features(site) {
  const body = `
      <section class="hero" style="padding-bottom:40px">
        <div class="wrap">
          <h1>Everything a placement needs, in one record</h1>
          <p class="lead">
            ${esc(site.brand)} covers the full lifecycle of a student placement: intake,
            money, deadlines, documents and visa outcome. Each area below is a module
            inside the product.
          </p>
        </div>
      </section>

      <section id="students">
        <div class="wrap">
          <h2>Student records and pipeline</h2>
          <div class="grid grid-2" style="margin-top:24px">
            <div>
              <p>
                Students are the spine of the system. Each one carries an agency ID,
                contact details, chosen university, tariff, document set and current
                stage. Records sort by agency ID the way people actually read them —
                <code>UB1</code>, <code>UB2</code>, <code>UB10</code> — rather than as
                raw text, so a list of two hundred students stays navigable.
              </p>
              <p>
                Students can be grouped into folders for an intake or a university
                batch, and exported to Excel with the columns you choose.
              </p>
            </div>
            <ul class="check">
              <li>Agency IDs that sort naturally</li>
              <li>Folders for intakes and batches</li>
              <li>Configurable Excel export</li>
              <li>Archive without deleting history</li>
              <li>Document data extraction on upload</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="payments" class="section-soft">
        <div class="wrap">
          <h2>Payment ledger</h2>
          <div class="grid grid-2" style="margin-top:24px">
            <div>
              <p>
                A student's balance is calculated, never entered:
                <strong>payments plus discounts, minus the tariff price</strong>. Because
                the figure is derived, it cannot be edited into agreement with a number
                somebody wants to see.
              </p>
              <p>
                Tariffs price themselves from the student's situation — an E-VISA
                placement with a language certificate is priced differently from one
                without. Editing a payment, deleting it, or withdrawing funds triggers
                an atomic recalculation and rolls the ledger forward correctly.
              </p>
            </div>
            <ul class="check">
              <li>Derived balances that cannot drift</li>
              <li>Dynamic tariff pricing</li>
              <li>Discounts recorded separately from payments</li>
              <li>Fund withdrawals with rollback</li>
              <li>Full payment history per student</li>
              <li>Excel export of the ledger</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="status">
        <div class="wrap">
          <h2>Status board and KDB deposit tracking</h2>
          <div class="grid grid-2" style="margin-top:24px">
            <div>
              <p>
                The status board turns deadlines into a shared, sorted queue. KDB
                deposit dates drive an urgency state on every student —
                <strong>overdue</strong>, <strong>critical</strong>,
                <strong>urgent</strong> or <strong>normal</strong> — recalculated
                continuously rather than reviewed weekly.
              </p>
              <p>
                A separate embassy view tracks sponsorship documents through their own
                sequence, so the two workstreams do not obscure each other.
              </p>
            </div>
            <ul class="check">
              <li>Live KDB deposit countdowns</li>
              <li>Four-level urgency classification</li>
              <li>General and KDB-specific views</li>
              <li>Embassy sponsorship tracking</li>
              <li>University selection per student</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="documents" class="section-soft">
        <div class="wrap">
          <h2>Documents and visa checks</h2>
          <div class="grid grid-2" style="margin-top:24px">
            <div>
              <p>
                Every placement carries a required document set — certificates,
                apostilles, sponsorship paperwork — tracked as a checklist rather than
                a folder. The system records which documents are expected, which have
                arrived, and which are blocking the next step.
              </p>
              <p>
                Uploaded documents can have their data extracted automatically, so
                details are read off the document instead of retyped from it.
              </p>
            </div>
            <ul class="check">
              <li>Per-student document checklists</li>
              <li>Apostille and certificate states</li>
              <li>Automatic data extraction from uploads</li>
              <li>Visa check workflow</li>
              <li>Clear blocking reasons</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="teams">
        <div class="wrap">
          <h2>Staff roles and multi-tenancy</h2>
          <div class="grid grid-2" style="margin-top:24px">
            <div>
              <p>
                Access is enforced on the server, not merely hidden in the interface.
                Each agency is a <strong>tenant</strong>, and every query is scoped to
                the signed-in user's tenant — one agency cannot read or write another's
                records under any circumstances.
              </p>
              <p>
                Within an agency, head managers see the full financial picture and
                manage staff; managers work their own placements. Platform
                administrators can operate across tenants where a group runs several
                branches.
              </p>
            </div>
            <ul class="check">
              <li>Server-enforced tenant isolation</li>
              <li>Head manager, manager and admin roles</li>
              <li>Staff account management</li>
              <li>Cross-tenant administration for groups</li>
              <li>Audit log of significant actions</li>
              <li>Telegram notifications for key events</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="section-soft">
        <div class="wrap">
          <div class="cta-band">
            <h2>Want to see it against your own process?</h2>
            <p class="muted">
              Read the <a href="/docs/">documentation</a>, check
              <a href="/pricing/">pricing</a>, or <a href="/contact/">book a walkthrough</a>.
            </p>
          </div>
        </div>
      </section>`

  return {
    title: `${site.brand} Features — Students, Payments, Visa & KDB Tracking`,
    description:
      `Inside ${site.brand}: student records, a self-balancing payment ledger, KDB deposit urgency tracking, visa document checklists and multi-tenant staff access.`,
    trail: [
      { href: '/', label: 'Home' },
      { href: '/features/', label: 'Features' },
    ],
    software: true,
    body,
  }
}
