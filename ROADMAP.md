# Roadmap

This is a small tool with a narrow job: scrape the public Facebook Ad Library well.
The roadmap is about doing that job more reliably, not adding surface area.

## Near term

- **Parser robustness** — `platforms` extraction, CTA edge cases, and resilience to
  Facebook markup changes. Add more fixtures to `tests/`.
- **`advertiser_page_id` / "view all ads"** — this view frequently fails to hydrate under
  headless Chromium. Investigate a longer wait / different `search_type` / a click on
  "See ad details".
- **Pagination sanity** — confirm `scroll_rounds` actually keeps pulling new cards on
  large result sets rather than re-rendering the same ones.
- **Optional pass-through of the ad detail page** — `ad_details_url` sometimes exposes an
  EU spend range and audience size; add a tool to fetch and parse one ad's detail view.

## Maybe

- A thin cache (per-URL, short TTL) so repeated calls during one research session don't
  re-render.
- CSV / markdown export of a result set.
- Screenshot capture per ad (crawl4ai supports it) for a visual teardown.

## Explicitly not planned

Spend/impression estimation, "ML performance prediction", cross-platform (TikTok/YouTube/
LinkedIn) scraping, a web dashboard. If you want budget numbers, that data only exists for
political ads and only through Meta's API.

## Removed in the rewrite

Earlier versions shipped `ads_archive` API tools (`search_facebook_ads`,
`analyze_ad_performance_metrics`, `generate_facebook_intelligence_report`, …). They
depended on data Meta only returns for political ads, so for commercial research they
returned empty or misleading results. They were removed — this server is now scraping-only.

---

# OWT fork — `lovepixel-git/facebook-ads-library-mcp`

Forked 2026-09-20 from `RamsesAguirre777/facebook-ads-library-mcp` (MIT). Upstream is a
good, honestly-scoped tool; this fork exists to harden the one field we actually rank on.

## Landed

- **The duplication signal was silently dead.** Upstream matched `**N ads** use this
  creative` and defaulted a miss to `1`. Meta no longer renders that string in the grid
  (0 occurrences across 35 live Nio Teas ads on 2026-09-20; `This ad has multiple
  versions` appeared instead). So every ad read as un-duplicated. On Jade Leaf the true
  figure is **59 of 70 multi-version** — the original output inverted the strategic
  conclusion. Now: `has_multiple_versions` boolean, and `ads_using_creative` is `None`
  when duplication is known but the count is hidden, never a fabricated `1`.
- **`days_running`** computed from `started_running`; `None`, never `0`, on a parse miss,
  so a broken date cannot sort as a brand-new ad.
- **Regression tests** for both, including the negative case.

## Tested and dead — do not retry

**Upgrading the creative image past 60x60 by rewriting the URL.** `stp=dst-jpg_s60x60_tt6`
is inside the CDN signature. Dropping `stp`, swapping to `s600x600` or `p600x600`, and
reducing to `dst-jpg` all return HTTP 403 against live URLs. The full creative is only on
the per-ad detail page. A rewrite helper shipped here briefly and produced a field that
403'd every time while looking perfectly valid.

## Next

- Fetch the per-ad detail page for real creative + the count behind "See summary details".
- `rank_creatives`: sort by `days_running` x `has_multiple_versions` — the actual
  "what is working" proxy, since the Ad Library publishes no spend, CTR or ROAS.
- Surface crawl4ai's anti-bot 403 instead of returning partial results as success. One
  pull logged `Blocked by anti-bot protection: HTTP 403` and still returned 35 ads.
