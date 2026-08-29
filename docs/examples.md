# Examples — real-world workflow

The README shows one-liners ("analyze Nike"). This page is the **repeatable procedure** the
server was actually built for: map who advertises in a niche, read their copy, see which
creatives scale, then jump to their websites to understand *how they close and what backend
they run*. No login, no token — the two tools scrape the public Ad Library web app, so they
work for **commercial ads in any country**. (Meta's official `ads_archive` API only returns
political/issue ads worldwide plus all ad types for the EU/UK, which is why this server
doesn't use it.)

| Tool | What it does |
|---|---|
| `search_ad_library` | keyword search of the Ad Library for a country |
| `scrape_ad_library_url` | scrape a specific Ad Library URL you already have |

Both render the SPA with crawl4ai + headless Chromium and parse the ad cards.

---

## Phase 1 — Discovery (`search_ad_library`)

### 1. Pick 3–5 queries
The terms a prospect would actually search, or that a competitor would put in their own copy.
Example, "AI automation consulting" in Mexico:

```
"implementación de IA en tu negocio"
"automatización con inteligencia artificial"
"IA para empresas"
"consultoría inteligencia artificial"
```

### 2. Run each query

```
search_ad_library(
    query="implementación de IA en tu negocio",
    country="MX",
    active_status="active",
    wait_seconds=12,      # raise if results come back empty — the SPA is slow to hydrate
    scroll_rounds=8,      # infinite-scroll cycles; 0 = first page only, 15+ = deep sweep
)
```

### 3. What you get back, per ad

| field | meaning |
|---|---|
| `advertiser`, `advertiser_handle` | name + numeric Page id (feed the id back in as `advertiser_page_id`) |
| `library_id`, `ad_details_url` | stable id + deep link to the ad's detail view |
| `started_running` | first seen date — **months old = validated copy, not an experiment** |
| `ads_using_creative` | how many active ads share this exact text — **proxy for budget/scale** |
| `landing_url`, `landing_domain` | where the click goes |
| `cta` | the button label (`Learn more`, `Sign up`, `Send message`, `Shop now`, ...) |
| `link_text` | the headline/caption strip under the creative |
| `body` | full ad copy |

### 4. Read the results

- **Group by `advertiser`**, sort by frequency → who dominates the niche.
- **High `ads_using_creative`** → that advertiser is scaling; their copy is the benchmark.
- **`landing_domain`**:
  - `fb.me` / `api.whatsapp.com` / `wa.me` → funnel goes straight to a DM, **no website**.
    Usually a solo operator or a CRM reseller. Nothing is measured or pre-qualified.
  - a real domain → they run a landing page; worth the Phase 2 teardown.
- **Read the `body`**: does it sell the tool or the outcome? Generic ("automate your
  processes") or a concrete pain ("double data entry between your ERP and CRM")? One vertical
  or "companies with 30–50 employees" in general?

### Pull every ad from one advertiser

Once you have a Page id, drop the keyword and target their "all ads" view:

```
search_ad_library(advertiser_page_id="100094954977054", country="MX", scroll_rounds=12)
```

> The Page view is more heavily client-rendered and does not always hydrate under the
> headless browser. If it comes back empty, fall back to a keyword search of the
> advertiser's name — that path is reliable.

---

## Phase 2 — Website teardown (outside this MCP)

For each competitor that has its own domain:

### 1. Resolve the real domain
The ad's `landing_url` is often a useless `fb.me` redirect. Open their Facebook Page
(`facebook.com/<advertiser_handle>`) and read the "About" link, or try candidate domains.

### 2. Fingerprint the stack with `curl`

```bash
curl -sI -L -A "Mozilla/5.0" https://DOMAIN/          # server, x-powered-by, CDN, security headers

curl -s  -L -A "Mozilla/5.0" https://DOMAIN/ | grep -oiE \
  "wp-content|/_next/|__NEXT_DATA__|framer|webflow|lovable|_l5e|leadconnector|msgsndr|\
   gohighlevel|calendly|cal\.com|hubspot|hsforms|typeform|tally\.so|supabase|\
   G-[A-Z0-9]{9,11}|GTM-[A-Z0-9]{6,8}|AW-[0-9]{9,}|fbq\('init'|wa\.me/[0-9]+" | sort -u
```

| marker | means |
|---|---|
| `leadconnector` / `msgsndr` | **GoHighLevel** — all-in-one CRM + booking + funnel + SMS |
| `hubspot` / `hsforms` | HubSpot CRM |
| `cal.com` / `calendly` | dedicated scheduling |
| `lovable` / `_l5e` / `lovable-uploads` | built on Lovable (no-code); pair with `supabase` for its backend |
| `supabase` | Supabase backend (forms, auth, DB) |
| `wp-content` | WordPress · `/_next/` | Next.js · `framer` / `webflow` | site builder |
| `AW-` | they also run **Google Ads**, not just Meta |
| `G-...` / `GTM-...` | GA4 / Google Tag Manager |

### 3. Read the funnel with a fetch/summary tool
Hero copy, the offer, **where the CTA goes** (form / WhatsApp / calendar), stated
implementation time, pricing, and the *type* of social proof (concrete numbers vs. vague
vs. placeholder logos).

### 4. Open the conversion page separately
`/demo`, `/book`, `/prueba`, `/getdemo` — this is where you see whether booking is a native
calendar, a form to a CRM, or just a WhatsApp link.

### 5. SPA gotcha
Sites that are 100% client-rendered (Vite/React with no SSR) return almost nothing to
`curl`. Use a real browser automation tool and read the **network requests** — that reveals
embedded booking widgets, chat widgets, which pixels fire, and form endpoints (e.g. a
`supabase.co` XHR tells you the backend without any server-rendered HTML).

---

## Phase 3 — Output & cadence

- Keep a running doc of advertisers, their angle, and who is scaling creatives.
- Keep a teardown table: stack / funnel / close, one row per competitor.
- Re-run Phase 1 every **2–4 weeks** and diff advertisers / copy / `ads_using_creative`.

---

## Notes & limits

- **403 is expected.** Facebook flags the headless browser and returns HTTP 403, but usually
  still serves the rendered ad cards — the tools judge success by parsed content, not status
  code. If a call comes back with `success: false` and no ads, you are likely being
  rate-limited: wait a few minutes, raise `wait_seconds`, or fall back to a real browser.
- **`scroll_rounds` trades time for completeness.** Each round is a scroll-to-bottom plus a
  2.5s wait. `0` returns just the first paint (~20–26 cards, fast); `8` (default) is a good
  balance; `15+` for a full historical sweep of a busy query.
- The scraper parses the public SPA markup, so a Facebook layout change can break field
  extraction. `raw_markdown` is always returned so you can re-parse by hand if needed.
- No spend or impression numbers — Meta only publishes those for political ads. This is
  creative / cadence / landing-page intelligence, not a budget estimator.
