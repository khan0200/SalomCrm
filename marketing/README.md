# SalomCRM marketing site

The public website for SalomCRM, at **https://salomkorea.uz**.

This is a static site generator with no runtime dependencies — plain Node, no
framework, no npm install. Every page is rendered to complete HTML at build
time, so search engines and visitors see identical content and the site works
with JavaScript disabled.

The application at `crm.salomkorea.uz` is a separate property and is
deliberately excluded from every search index. See `nginx-salomcrm.conf`.

---

## Commands

```bash
npm run site:build      # build to marketing/dist, fail on any SEO defect
npm run site:preview    # build and serve on http://localhost:4321
npm run site:audit      # rendered checks in a real browser (needs the preview running)
npm run site:assets     # regenerate images from logo.png (needs the Python venv)
npm run site:indexnow   # notify Bing/Yandex of changes (dry run without --submit)
```

`site:build` is the one that matters in CI — it exits non-zero on duplicate
titles or descriptions, broken internal links, orphaned pages, a missing or
wrong canonical, an accidental `noindex`, invalid JSON-LD, an image without
`alt`, a malformed sitemap, or a robots.txt that would deindex the site.

---

## Layout

```
marketing/
├── site.config.mjs      ← all business facts live here, and nowhere else
├── build.mjs            ← generator + SEO validator
├── assets/styles.css    ← inlined into every page at build time
├── content/*.mjs        ← one module per page
├── lib/
│   ├── layout.mjs       ← the HTML shell: head, nav, breadcrumbs, footer
│   ├── schema.mjs       ← JSON-LD builders
│   └── html.mjs         ← escaping helpers
├── public/              ← copied to the site root verbatim
└── tools/
    ├── build_assets.py  ← image pipeline
    ├── preview.mjs      ← local server that mirrors the nginx rules
    ├── audit.mjs        ← CDP-driven rendered audit
    └── indexnow.mjs     ← IndexNow submission
```

### Adding a page

1. Write `content/<name>.mjs` exporting a function `(site) => ({ title,
   description, trail, body })`.
2. Add an entry to `pages` in `site.config.mjs`.
3. Link to it from at least one other page — the build fails on orphans.

The sitemap, the navigation and the breadcrumbs all derive from `pages`, so a
page cannot fall out of the sitemap or lose its navigation by accident.

---

## Before launch — required

These cannot be done from the codebase. The site is complete without them, but
its search presence is not.

### 1. Fill in `site.config.mjs`

Fields marked `TODO` are empty on purpose. **The generator omits empty fields
rather than inventing values**, so nothing false is ever published — but the
gaps are real gaps:

| Field | Why it matters |
|---|---|
| `contact.email` / `phone` / `telegram` | The contact page currently has no direct channel. The build warns about this on every run. |
| `contact.address.street` / `region` / `postalCode` | Completes the `PostalAddress` in Organization schema — needed for local/regional search. |
| `sameAs` | Official profiles. This is how Google links the website to the brand's other properties and consolidates the entity. Only list profiles that genuinely exist. |
| `plans[].amount` | Until set, all three plans show "Request a quote" and no price appears in structured data. That is a legitimate B2B pattern — set them only when you want to advertise figures publicly. |
| `verification.*` | See below. |

### 2. DNS

Point the apex and `www` at the server:

```
salomkorea.uz.       A      178.238.231.210
www.salomkorea.uz.   A      178.238.231.210
crm.salomkorea.uz.   A      178.238.231.210
```

### 3. TLS — currently missing entirely

Neither host serves HTTPS today; nginx listens on port 80 only. Every engine
treats HTTPS as a ranking signal, browsers mark HTTP pages "Not secure", and
Search Console will not verify cleanly.

```bash
certbot --nginx -d salomkorea.uz -d www.salomkorea.uz
certbot --nginx -d crm.salomkorea.uz
```

The nginx configs already assume the certbot paths. Once HTTPS is stable on
both hosts, raise `Strict-Transport-Security` from `max-age=86400` to
`max-age=31536000` in both files.

### 4. Deploy

```bash
npm run site:build
rsync -a --delete marketing/dist/ root@178.238.231.210:/var/www/salomkorea/

# on the server, first time only
cp nginx-salomkorea.conf /etc/nginx/sites-available/salomkorea.uz
cp nginx-salomcrm.conf   /etc/nginx/sites-available/crm.salomkorea.uz
ln -sf /etc/nginx/sites-available/salomkorea.uz     /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/crm.salomkorea.uz /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 5. Search engine verification

Each console gives a token. Paste **only the token value** into
`site.config.mjs → verification`, rebuild, redeploy, then click Verify.

| Console | Where | Config field |
|---|---|---|
| [Google Search Console](https://search.google.com/search-console) | Add property → URL prefix → `https://salomkorea.uz` → HTML tag | `verification.google` |
| [Bing Webmaster Tools](https://www.bing.com/webmasters) | Add site → HTML Meta Tag. Or import the property straight from Search Console. | `verification.bing` |
| [Yandex Webmaster](https://webmaster.yandex.com) | Add site → Meta tag | `verification.yandex` |

A DNS TXT record works equally well for all three and survives redeploys —
worth preferring if you control DNS.

After verification, in each console:

- Submit `https://salomkorea.uz/sitemap.xml`.
- **Add `crm.salomkorea.uz` as a separate property too.** You want to see if
  anything from the application ever gets indexed, and to request removal if
  it does.
- In Search Console, check Settings → Crawl stats and the Page indexing report
  a week after launch.

### 6. IndexNow

The key file ships with every build at `/{indexNowKey}.txt`. Once the site is
live and that URL returns the key as plain text:

```bash
npm run site:indexnow            # dry run, prints what it would send
node marketing/tools/indexnow.mjs --submit
```

Bing, Yandex, Seznam and Naver consume IndexNow. Google does not participate
and reads the sitemap instead. Re-run `--submit` after any content change.

---

## Deliberate decisions

**English only, no hreflang.** The target market is Uzbekistan, where searches
happen in Uzbek and Russian too. Uzbek and Russian versions are the single
highest-value next step — but machine-translated marketing copy on a brand's
own site does more harm than the traffic is worth, so they are left for
human-written translations. `hreflang` is correctly absent until there is more
than one locale; adding it for a single language is meaningless.

**No blog.** Google rewards a small site of substantial pages over a large one
of thin ones. An empty or sparse `/blog/` would dilute the site rather than
help it. Add one when there is genuinely something to publish, then link it
from the footer and add it to `pages`.

**No SearchAction in the WebSite schema.** The site has no search endpoint;
claiming one that does not exist is a false signal.

**Trailing slashes everywhere.** `/features/` is canonical and `/features`
301-redirects to it. One URL per page, no duplicate-content ambiguity.

**Sitelinks cannot be forced.** Google generates them algorithmically. What
this site does is give it everything it uses to decide: a shallow flat
hierarchy, stable and consistent navigation in the same order on every page,
descriptive anchor text, breadcrumbs backed by `BreadcrumbList`, unique
titles that lead with the brand, and no duplicate pages competing for the same
intent. Sitelinks typically appear only once a site has accumulated brand
search volume and links, so expect months, not weeks.
