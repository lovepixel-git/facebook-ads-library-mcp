# How the scraper works

This describes what the code in `facebook_ads_mcp_complete.py` actually does. It's a
deliberately simple pipeline: render the page, dump it to markdown, regex the fields out.

## 1. Build the URL

`search_ad_library` assembles a `https://www.facebook.com/ads/library/?...` URL from the
tool arguments (`q`, `country`, `active_status`, `ad_type`, `media_type`,
`search_type=keyword_unordered`). `scrape_ad_library_url` skips this and takes a URL you
already have.

## 2. Render it — `_render_ad_library()`

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode

bc = BrowserConfig(headless=True, browser_type="chromium",
                   viewport_width=1400, viewport_height=1600)

# js_code: wait for hydration, then scroll to the bottom `scroll_rounds` times
js = (f"await new Promise(r=>setTimeout(r,{hydrate_ms}));"
      + "window.scrollTo(0,document.body.scrollHeight);"
        "await new Promise(r=>setTimeout(r,2500));" * rounds)

cfg = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    delay_before_return_html=max(3, wait_seconds),
    page_timeout=max(90000, 20000 + rounds * 3000),
    js_code=[js],
)

async with AsyncWebCrawler(config=bc) as crawler:
    r = await crawler.arun(url=url, config=cfg)
    md = r.markdown.raw_markdown
```

The Ad Library is an infinite-scroll React app — the first paint holds ~20–26 cards. The
scroll loop is what pulls the rest. `scroll_rounds` trades wall-clock time for coverage.

Facebook answers the headless browser with **HTTP 403** but still returns the rendered
HTML with the cards in it, so the code ignores `status_code` and judges success by whether
the parser found any ads.

No proxies, no user-agent rotation, no persistent profile, no login. If you get
rate-limited, wait and retry with a higher `wait_seconds`.

## 3. Parse the markdown — `_parse_ad_library_markdown()`

Split on `\nLibrary ID:\s*` — each chunk is one ad card. Per chunk, regex out:

| field | pattern, roughly |
|---|---|
| `library_id` | leading digits of the chunk |
| `started_running` | `Started running on <Mon DD, YYYY>` |
| `ads_using_creative` | `**N ads** use this creative` |
| `advertiser` / `advertiser_handle` | first `[Name](https://www.facebook.com/<handle>/)` |
| `landing_url` / `landing_domain` | first `l.facebook.com/l.php?u=` redirect, URL-decoded |
| `cta` | one of Facebook's fixed button labels, immediately before the redirect link |
| `link_text` | the caption strip between the creative image and the CTA |
| `body` | text between `**Sponsored**` and the next structural marker; redirect links collapsed to their visible text |
| `platforms` | which of `Facebook` / `Instagram` / `Audience Network` / `Messenger` appear as text |

Duplicate `library_id`s (the scroll re-renders cards) are dropped.

## 4. Return

Structured `ads` list + an `advertisers` histogram + the first 16k chars of `raw_markdown`
so the calling model can recover anything the regexes missed.

## Known weak spots

- `platforms` is usually empty — those markers render as icons, not text.
- The `advertiser_page_id` "view all ads" URL is more heavily client-rendered and often
  doesn't hydrate under headless Chromium.
- Any Facebook markup change can break a field. The tests in `tests/test_parser.py` run
  the parser against a fixture so regressions show up there first.
