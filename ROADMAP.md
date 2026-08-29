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
