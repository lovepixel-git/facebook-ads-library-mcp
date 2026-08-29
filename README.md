# Facebook Ads Library MCP

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.x-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A free, self-hosted MCP server for pulling competitor ads out of the **Facebook Ad
> Library** — both by scraping the public web UI (works for commercial ads, any country,
> no token) and through Meta's official `ads_archive` Graph API (political & issue ads
> worldwide, all ad types for the EU/UK).

Built as an open alternative to paid Ad Library scrapers (Apify actors, ScrapeCreators,
etc.). No account, no subscription — you run it locally and it drives a headless browser.

## What it actually does

| Capability | How | Needs a token? | Coverage |
|---|---|---|---|
| Keyword search of the public Ad Library | Headless-browser render of the SPA + HTML parse | No | Commercial ads, any country |
| Scrape a specific Ad Library URL you already have | Same | No | Anything the URL shows |
| `ads_archive` API search / spend / impressions / demographics | Meta Graph API | Yes (`ads_read`) | **Political & issue ads only** worldwide; all ad types only for EU/UK |

The important limitation: Meta's official API does **not** expose spend, impressions or
demographics for ordinary commercial ads outside the EU/UK. The API tools in this repo
will tell you when a result set has no such data rather than inventing zeros. If you're
researching normal brands (most people), use the scraping tools.

## Install

```bash
git clone https://github.com/RamsesAguirre777/facebook-ads-library-mcp.git
cd facebook-ads-library-mcp
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium   # crawl4ai needs a browser
```

### Optional: Facebook token (only for the `ads_archive` API tools)

1. [Graph API Explorer](https://developers.facebook.com/tools/explorer/) → generate a token with `ads_read`.
2. Put it in a `.env` file next to the script — it's auto-loaded:
   ```
   FACEBOOK_ACCESS_TOKEN=EAAB...
   ```

You can skip this entirely if you only use `search_ad_library` / `scrape_ad_library_url`.

### Register with your MCP client

Claude Code:
```bash
claude mcp add facebook-ads -- /abs/path/to/venv/bin/python /abs/path/to/facebook_ads_mcp_complete.py
```

Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "facebook-ads": {
      "command": "/abs/path/to/venv/bin/python",
      "args": ["/abs/path/to/facebook_ads_mcp_complete.py"]
    }
  }
}
```

## Tools

### Web scraping — no token, any country

- **`search_ad_library(query, country="MX", active_status="active", media_type="all", ad_type="all", advertiser_page_id="", wait_seconds=8, scroll_rounds=8)`**
  Keyword search. Renders the SPA, scrolls it `scroll_rounds` times to get past the first
  ~24 cards, and returns structured records per ad: `advertiser` + Page handle,
  `started_running`, `ads_using_creative` (how many creatives share the copy — a rough
  scale signal), `landing_url` / `landing_domain`, `cta` button label, `link_text`
  headline, full `body`, `creative_image`, `ad_details_url`. Also returns an
  `advertisers` histogram and `raw_markdown` so the model can pull anything the parser missed.

- **`scrape_ad_library_url(url, wait_seconds=8, scroll_rounds=8)`**
  Same rendering + parsing for any `facebook.com/ads/library/...` URL you already have —
  a prefilled search, a shared filter link, an advertiser's "view all ads" page.

> Facebook returns HTTP 403 to the headless browser but still serves the rendered ad
> cards, so these tools judge success by whether cards parsed, not by status code. If a
> call comes back empty, raise `wait_seconds`, or fall back to a real browser
> (see [docs/examples.md](docs/examples.md)).

### `ads_archive` Graph API — needs a token, political/EU-UK only

- **`search_facebook_ads(brand_name, country="US", ad_type="ALL", date_range=30, limit=50)`** — archive search, sorted by days active.
- **`discover_competitor_brands(industry_keywords, region="US", min_ads=5, limit=100)`** — group archive results by advertiser.
- **`analyze_ad_creative_elements(ad_snapshot_url, ...)`** — fetch a snapshot URL and run keyword/CTA/urgency regex over the text.
- **`analyze_ad_performance_metrics(brand_name, time_period=30, ...)`** — aggregate spend/impression/demographic ranges. Returns a `data_available: false` flag when the archive has no spend/impression data for the query (i.e. non-political ads).
- **`competitive_ad_analysis(brands_list, ...)`** — compare the above across several advertisers.
- **`generate_facebook_intelligence_report(brand_name, include_competitors=True, ...)`** — rolls the API tools into one report.
- **`export_facebook_ads_data(brand_name, export_format="json", ...)`** — dump to JSON / CSV / Markdown.

The keyword/CTA/urgency detection in the analysis tools is plain regex, not a model —
it's a cheap first pass, not "AI creative analysis".

### Planned (not implemented — see [ROADMAP.md](ROADMAP.md))

`find_similar_advertisers`, `analyze_ad_targeting_insights`, `monitor_brand_ad_changes`,
`track_ad_spend_estimation`, `benchmark_against_industry`, `identify_market_opportunities`,
`predict_ad_performance`.

## Example

```
"Search the Mexico Ad Library for 'automatización con inteligencia artificial',
 group by advertiser, and list the landing domains."

"Scrape https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MX&q=nike&search_type=keyword_unordered
 with scroll_rounds=15 and summarise the creative angles."
```

Full discovery → website-teardown → cadence workflow: **[docs/examples.md](docs/examples.md)**.

## How the scraper works

`crawl4ai` (`AsyncWebCrawler`) opens the Ad Library URL in headless Chromium, waits for
the React app to hydrate, runs a scroll loop to trigger lazy-loaded cards, serialises the
DOM to markdown, and a regex parser (`_parse_ad_library_markdown`) splits it on
`Library ID:` boundaries and extracts the fields above. It's best-effort: Facebook's
markup changes, and some fields (`platforms`) don't always survive the markdown
conversion. `raw_markdown` is always returned as a fallback.

## Limitations

- Scraping depends on Facebook's current DOM — expect to touch the parser periodically.
- The `advertiser_page_id` / "view all ads" path is heavier client-rendered and doesn't
  always hydrate headless; a keyword search of the advertiser name is more reliable.
- The `ads_archive` API only covers political/issue ads (worldwide) and all ad types for
  the EU/UK. There is no official API for commercial-ad spend anywhere else.
- No caching or rate-limit handling yet — be reasonable with `scroll_rounds`.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp)
- [crawl4ai](https://github.com/unclecode/crawl4ai)
- [Facebook Ad Library](https://www.facebook.com/ads/library/) & the [Ad Library API](https://www.facebook.com/ads/library/api/)
