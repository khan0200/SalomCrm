/**
 * JSON-LD builders.
 *
 * Two rules hold throughout this file:
 *
 * 1. Nothing is emitted that is not visible on the page. Structured data that
 *    contradicts the rendered content is a spam signal, not a ranking boost.
 * 2. Empty config fields are dropped rather than emitted as empty strings.
 *    `prune()` handles this recursively.
 */

import { abs } from './html.mjs'

/** Recursively drop null/undefined/'' values and the empty objects they leave. */
export function prune(value) {
  if (Array.isArray(value)) {
    const out = value.map(prune).filter((v) => v !== undefined)
    return out.length ? out : undefined
  }
  if (value && typeof value === 'object') {
    const out = {}
    for (const [k, v] of Object.entries(value)) {
      const pruned = prune(v)
      if (pruned !== undefined) out[k] = pruned
    }
    // An object holding only its @type carries no information.
    return Object.keys(out).some((k) => !k.startsWith('@')) ? out : undefined
  }
  if (value === null || value === undefined || value === '') return undefined
  return value
}

/** Stable @id anchors so the graph nodes can reference each other. */
export const ids = {
  organization: (site) => `${site.url}/#organization`,
  website: (site) => `${site.url}/#website`,
  software: (site) => `${site.url}/#software`,
  page: (site, path) => `${abs(site.url, path)}#webpage`,
}

/**
 * Organization — the node that anchors the brand entity. Emitted once, on the
 * home page, and referenced by @id from every other page.
 */
export function organization(site) {
  const a = site.contact.address
  return prune({
    '@type': 'Organization',
    '@id': ids.organization(site),
    name: site.brand,
    legalName: site.legalName,
    alternateName: site.alternateNames,
    url: `${site.url}/`,
    logo: {
      '@type': 'ImageObject',
      '@id': `${site.url}/#logo`,
      url: abs(site.url, '/assets/salomcrm-logo-512.png'),
      contentUrl: abs(site.url, '/assets/salomcrm-logo-512.png'),
      width: 512,
      height: 512,
      caption: site.brand,
    },
    image: { '@id': `${site.url}/#logo` },
    description: site.description,
    email: site.contact.email || undefined,
    telephone: site.contact.phone || undefined,
    address: {
      '@type': 'PostalAddress',
      streetAddress: a.street,
      addressLocality: a.city,
      addressRegion: a.region,
      postalCode: a.postalCode,
      addressCountry: a.country,
    },
    areaServed: { '@type': 'Country', name: a.countryName },
    sameAs: site.sameAs,
    contactPoint: site.contact.email || site.contact.phone
      ? {
          '@type': 'ContactPoint',
          contactType: 'customer support',
          email: site.contact.email || undefined,
          telephone: site.contact.phone || undefined,
          areaServed: a.country,
          availableLanguage: ['en', 'uz', 'ru'],
        }
      : undefined,
  })
}

/**
 * WebSite — tells Google the domain is one coherent site under one name.
 * No `potentialAction`/SearchAction: the site has no search endpoint, and
 * claiming one that does not exist is a false signal.
 */
export function website(site) {
  return prune({
    '@type': 'WebSite',
    '@id': ids.website(site),
    url: `${site.url}/`,
    name: site.brand,
    alternateName: site.alternateNames,
    description: site.description,
    inLanguage: site.locale,
    publisher: { '@id': ids.organization(site) },
  })
}

/**
 * SoftwareApplication — describes the product itself.
 *
 * `offers` is emitted only when a real price exists in the config. A price of
 * 0 or a placeholder would make the product eligible for price-bearing rich
 * results with a figure nobody can actually pay.
 */
export function softwareApplication(site) {
  const priced = site.plans.filter((p) => typeof p.amount === 'number' && p.amount > 0)
  return prune({
    '@type': 'SoftwareApplication',
    '@id': ids.software(site),
    name: site.brand,
    applicationCategory: 'BusinessApplication',
    applicationSubCategory: 'Customer Relationship Management',
    operatingSystem: 'Web browser',
    url: `${site.url}/`,
    description: site.description,
    softwareHelp: abs(site.url, '/docs/'),
    featureList: [
      'Student records and application pipeline',
      'Payment ledger with tariffs, discounts and balances',
      'KDB deposit tracking with urgency states',
      'Visa and embassy document checklists',
      'Multi-tenant data isolation',
      'Role-based staff access',
      'Excel export',
      'Audit log',
    ],
    publisher: { '@id': ids.organization(site) },
    offers: priced.length
      ? priced.map((p) => ({
          '@type': 'Offer',
          name: p.name,
          price: String(p.amount),
          priceCurrency: site.currency,
          url: abs(site.url, '/pricing/'),
        }))
      : undefined,
  })
}

/**
 * BreadcrumbList mirroring the visible breadcrumb trail. Emitted on every page
 * except the home page, where a one-item trail carries no information.
 */
export function breadcrumbs(site, trail) {
  if (!trail || trail.length < 2) return undefined
  return {
    '@type': 'BreadcrumbList',
    '@id': `${abs(site.url, trail[trail.length - 1].href)}#breadcrumb`,
    itemListElement: trail.map((crumb, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: crumb.label,
      item: abs(site.url, crumb.href),
    })),
  }
}

/** WebPage node linking the page to the site and its breadcrumb trail. */
export function webPage(site, { path, title, description, trail }) {
  return prune({
    '@type': 'WebPage',
    '@id': ids.page(site, path),
    url: abs(site.url, path),
    name: title,
    description,
    isPartOf: { '@id': ids.website(site) },
    about: { '@id': ids.organization(site) },
    inLanguage: site.locale,
    breadcrumb: trail && trail.length > 1
      ? { '@id': `${abs(site.url, path)}#breadcrumb` }
      : undefined,
  })
}

/**
 * FAQPage — only ever built from questions that are genuinely rendered as
 * visible Q&A on the same page. Callers pass the same array they render.
 */
export function faqPage(site, path, faqs) {
  if (!faqs || !faqs.length) return undefined
  return {
    '@type': 'FAQPage',
    '@id': `${abs(site.url, path)}#faq`,
    mainEntity: faqs.map((f) => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  }
}

/**
 * Assemble the page's @graph. A single graph per page lets the nodes reference
 * each other by @id instead of repeating the Organization on every page.
 */
export function graph(site, page) {
  const nodes = [
    website(site),
    organization(site),
    webPage(site, page),
    breadcrumbs(site, page.trail),
    page.software ? softwareApplication(site) : undefined,
    page.faqs ? faqPage(site, page.path, page.faqs) : undefined,
  ].filter(Boolean)

  return { '@context': 'https://schema.org', '@graph': nodes }
}
