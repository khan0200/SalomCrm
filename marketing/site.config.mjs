/**
 * SalomCRM marketing site — single source of truth for all business facts.
 *
 * Everything search engines assert about the company comes from this file:
 * Organization schema, contact page, footer, sitemap host, canonical URLs.
 *
 * ⚠ Fields marked TODO are intentionally empty. The generator OMITS empty
 * fields rather than inventing values — an unset phone number renders nothing
 * and is left out of the structured data. Never place a placeholder value here;
 * a wrong phone number in Google's knowledge panel is worse than no phone
 * number at all.
 */

export const site = {
  // ── Canonical identity ────────────────────────────────────────────────────
  // The root domain is the canonical home of the brand. The app lives on the
  // `crm.` subdomain and is deliberately excluded from search indexes.
  url: 'https://salomkorea.uz',
  appUrl: 'https://crm.salomkorea.uz',

  // Brand name, used verbatim everywhere. Consistency is the single strongest
  // signal for branded search. Do not vary casing or spacing between pages.
  brand: 'SalomCRM',
  legalName: 'Salom Korea',
  // Alternate spellings people actually type. Used only in Organization
  // `alternateName` — never sprinkled into body copy.
  alternateNames: ['Salom CRM', 'Salom Korea CRM'],

  tagline: 'Student recruitment CRM for education agencies',
  description:
    'Student recruitment CRM for education agencies. Track applications, payments, KDB deposits and visa documents for Korean university placements.',

  locale: 'en',
  localeTag: 'en_US',

  // ── Contact & location ────────────────────────────────────────────────────
  // Leave a field as '' to omit it from the site and from structured data.
  contact: {
    email: '', // TODO: e.g. 'info@salomkorea.uz'
    phone: '', // TODO: E.164 format, e.g. '+998901234567'
    telegram: '', // TODO: e.g. 'https://t.me/salomkorea'
    address: {
      street: '', // TODO
      city: 'Tashkent',
      region: '', // TODO: e.g. 'Toshkent shahri'
      postalCode: '', // TODO
      country: 'UZ',
      countryName: 'Uzbekistan',
    },
    // Shown on the contact page. Omitted entirely when empty.
    hours: '', // TODO: e.g. 'Mon–Fri, 09:00–18:00 (UTC+5)'
  },

  // ── Official profiles (Organization.sameAs) ───────────────────────────────
  // Only list profiles that genuinely exist and are controlled by the company.
  // Google uses these to consolidate brand entities; a dead or wrong link
  // weakens the association instead of strengthening it.
  sameAs: [
    // TODO: 'https://t.me/salomkorea',
    // TODO: 'https://www.instagram.com/salomkorea',
    // TODO: 'https://www.facebook.com/salomkorea',
    // TODO: 'https://www.linkedin.com/company/salomkorea',
  ].filter(Boolean),

  // ── Pricing ───────────────────────────────────────────────────────────────
  // When `amount` is null the plan renders a "Request a quote" call to action
  // and no `offers` price is emitted in structured data. Fill in real figures
  // before advertising a price.
  currency: 'UZS',
  plans: [
    {
      id: 'starter',
      name: 'Starter',
      amount: null, // TODO: monthly price in UZS, e.g. 1200000
      period: 'month',
      summary: 'For a single agency office getting its first intake organised.',
      seats: 'Up to 5 staff accounts',
      features: [
        'Student records and application pipeline',
        'Payment ledger with tariffs and discounts',
        'Visa and embassy document checklists',
        'Excel export',
        'Email support',
      ],
    },
    {
      id: 'agency',
      name: 'Agency',
      amount: null, // TODO
      period: 'month',
      summary: 'For growing agencies running several intakes at once.',
      seats: 'Up to 25 staff accounts',
      featured: true,
      features: [
        'Everything in Starter',
        'KDB deposit status board with urgency tracking',
        'Role-based access for head managers and managers',
        'Telegram notifications',
        'Document data extraction',
        'Priority support',
      ],
    },
    {
      id: 'network',
      name: 'Network',
      amount: null, // TODO
      period: 'month',
      summary: 'For multi-branch operators who need isolated tenant data.',
      seats: 'Unlimited staff accounts',
      features: [
        'Everything in Agency',
        'Multiple tenants with strict data isolation',
        'Cross-tenant administration',
        'Full audit log',
        'Onboarding and data migration',
      ],
    },
  ],

  // ── Search engine verification tokens ─────────────────────────────────────
  // Paste the token value only (not the whole meta tag). Empty tokens are
  // omitted, so an unverified property never ships a broken meta tag.
  verification: {
    google: '', // TODO: Search Console → HTML tag → content="..."
    bing: '', // TODO: Bing Webmaster Tools → HTML Meta Tag
    yandex: '', // TODO: Yandex Webmaster → Meta tag
  },

  // ── IndexNow (Bing, Yandex, Seznam, Naver) ────────────────────────────────
  // A UUID-style key. The generator writes `<key>.txt` containing the key to
  // the site root, which is how IndexNow verifies ownership.
  indexNowKey: 'a7f3c9e21b4d48f6ae05c8317d92b6e4',
}

/**
 * Every indexable page on the marketing site.
 *
 * `path` must start and end with `/` (except the root). This is the single
 * place URLs are declared — the sitemap, the navigation, the breadcrumbs and
 * the internal link checker all read from here, so a page cannot become
 * orphaned or fall out of the sitemap by accident.
 *
 * priority/changefreq are advisory hints; Google ignores them but Bing and
 * Yandex still read them.
 */
export const pages = [
  { path: '/', module: 'home', nav: 'Home', priority: '1.0', changefreq: 'weekly' },
  { path: '/features/', module: 'features', nav: 'Features', priority: '0.9', changefreq: 'monthly' },
  { path: '/pricing/', module: 'pricing', nav: 'Pricing', priority: '0.9', changefreq: 'monthly' },
  { path: '/docs/', module: 'docs', nav: 'Documentation', priority: '0.8', changefreq: 'monthly' },
  { path: '/about/', module: 'about', nav: 'About', priority: '0.7', changefreq: 'yearly' },
  { path: '/contact/', module: 'contact', nav: 'Contact', priority: '0.7', changefreq: 'yearly' },
]

/**
 * Primary navigation — the ordering Google is most likely to mirror when it
 * generates organic sitelinks. Keep it short, stable and identical on every
 * page. `Log in` points at the app subdomain and is excluded from the sitemap.
 */
export const primaryNav = pages.map((p) => ({ href: p.path, label: p.nav }))

export default site
