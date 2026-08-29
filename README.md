# Facebook Ad Library MCP

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.x-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A small MCP server that scrapes the **public Facebook Ad Library** for competitive ad
research — from your MCP client, with no Facebook account and no API token.

It exists because the paid Ad Library scrapers (Apify actors, ScrapeCreators, and friends)
charge for something that is publicly visible in a browser. This just drives a headless
browser instead.

## Why not the official API?

Meta's `ads_archive` API only returns **political & issue ads** worldwide (and all ad
types only for the EU/UK). For an ordinary commercial advertiser in most of the world it
returns nothing useful — no ads, no spend, no impressions. So this server doesn't use it
at all. It renders the same Ad Library web page you'd open yourself and parses the cards.

## What you get

Two tools:

- **`search_ad_library(query, country="MX", ...)`** — keyword search.
- **`scrape_ad_library_url(url, ...)`** — scrape any Ad Library URL you already have.

Both return structured records per ad:

| field | meaning |
|---|---|
| `advertiser`, `advertiser_handle` | Page name and its `facebook.com/<handle>` |
| `started_running` | first-seen date |
| `ads_using_creative` | how many creatives share this copy — a rough scale signal |
| `landing_url`, `landing_domain` | destination, unwrapped from the `l.facebook.com` redirect |
| `cta` | the button label (`Learn more`, `Sign up`, `Send message`, …) |
| `link_text` | the headline strip under the creative |
| `body` | full ad copy |
| `creative_image` | thumbnail URL |
| `ad_details_url` | deep link to that ad's detail view |

Plus an `advertisers` histogram and the `raw_markdown` of the page so the model can pull
anything the parser missed.

## Install

```bash
git clone https://github.com/RamsesAguirre777/facebook-ads-library-mcp.git
cd facebook-ads-library-mcp
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium   # crawl4ai needs a browser
```

### Register with your MCP client

Claude Code:
```bash
claude mcp add facebook-ads -- /abs/path/venv/bin/python /abs/path/facebook_ads_mcp_complete.py
```

Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "facebook-ads": {
      "command": "/abs/path/venv/bin/python",
      "args": ["/abs/path/facebook_ads_mcp_complete.py"]
    }
  }
}
```

Restart the client.

## Usage

```
"Search the Mexico Ad Library for 'automatización con inteligencia artificial',
 group by advertiser, and list the landing domains."

"Scrape https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MX&q=nike&search_type=keyword_unordered
 with scroll_rounds=15 and summarise the creative angles."
```

Full discovery → website-teardown workflow: **[docs/examples.md](docs/examples.md)**.

### Parameters worth knowing

- **`scroll_rounds`** (default 8) — the Ad Library is infinite-scroll; the first paint is
  only ~20–26 cards. Each round is a scroll-to-bottom + 2.5s wait. `0` = first render only
  (fast); `15+` for a deep historical sweep. It trades time for completeness.
- **`wait_seconds`** (default 8) — SPA hydration wait before scraping. Raise it if results
  come back empty.
- **`country`** — ISO code the ads were delivered in (`MX`, `US`, `ES`, …).
- **`advertiser_page_id`** — target one Page's "all ads" view. This view is heavier
  client-rendered and doesn't always hydrate headless; a keyword search of the advertiser
  name is more reliable.

## How it works

`crawl4ai` (`AsyncWebCrawler`) opens the Ad Library URL in headless Chromium, waits for
the React app to hydrate, runs a scroll loop to trigger lazy-loaded cards, serialises the
DOM to markdown, and a regex parser (`_parse_ad_library_markdown`) splits it on
`Library ID:` boundaries and pulls the fields above.

Facebook answers the headless browser with **HTTP 403** but still serves the rendered
cards, so the tools judge success by whether cards parsed, not by status code.

## Limitations

- It parses the public SPA markup, so a Facebook layout change can break field
  extraction. `raw_markdown` is always returned as a fallback.
- `platforms` often comes back empty — the FB/IG/Messenger markers render as icons, not
  text, so they only survive when the page includes their labels.
- No caching or rate-limit handling. If you hammer it you'll get empty results for a
  while; back off and raise `wait_seconds`.
- Spend and impression numbers are **not available** — Meta only publishes those for
  political ads, and only through the API. This tool gives you creative, cadence and
  landing-page intelligence, not budget figures.

## Tests

```bash
python -m pytest tests/ -q
```

Offline — they exercise the markdown parser against a fixture.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp)
- [crawl4ai](https://github.com/unclecode/crawl4ai)
- [Facebook Ad Library](https://www.facebook.com/ads/library/)
