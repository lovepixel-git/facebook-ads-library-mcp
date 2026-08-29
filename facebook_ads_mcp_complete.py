"""Facebook Ad Library MCP — a free, self-hosted scraper for the public Ad Library.

Meta's official ads_archive API only returns political & issue ads worldwide (all ad
types only for the EU/UK), so it is useless for researching ordinary commercial
advertisers. This server skips the API entirely: it renders the public Ad Library web
app in headless Chromium (via crawl4ai), scrolls it, and parses the ad cards into
structured records. No token, no account, any country.

Tools:
  - search_ad_library(query, country, ...)   keyword search
  - scrape_ad_library_url(url, ...)           scrape a specific Ad Library URL
"""
import asyncio
import re
from typing import List
from urllib.parse import quote, urlparse, parse_qs, unquote

from fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler

mcp = FastMCP(
    name="Facebook Ad Library",
    instructions="""
    Scrapes the public Facebook Ad Library (no API, no token) for competitive ad research.
    Works for commercial ads in any country. Returns structured ad cards: advertiser,
    run date, creative count, landing domain, CTA, headline and body copy.
    """,
)

AD_LIBRARY_BASE = "https://www.facebook.com/ads/library/"


async def _render_ad_library(url: str, wait_seconds: int = 8, scroll_rounds: int = 8) -> dict:
    """Render the Ad Library SPA and return its markdown.

    Facebook flags the headless browser and answers HTTP 403, but still serves the
    rendered ad cards, so callers judge success by parsed content, not status code.

    The Ad Library is an infinite-scroll SPA — the first paint only holds ~20-26 cards.
    ``scroll_rounds`` drives that many extra scroll-to-bottom + wait cycles so lazy-loaded
    cards are in the DOM before it is serialised. 0 = first render only (fast).
    """
    from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode

    bc = BrowserConfig(headless=True, browser_type="chromium",
                       viewport_width=1400, viewport_height=1600)
    hydrate_ms = max(3, wait_seconds) * 1000
    rounds = max(0, int(scroll_rounds))
    js = (
        f"await new Promise(r=>setTimeout(r,{hydrate_ms}));"
        + "".join(
            "window.scrollTo(0, document.body.scrollHeight);"
            "await new Promise(r=>setTimeout(r,2500));"
            for _ in range(rounds)
        )
        + "window.scrollTo(0, document.body.scrollHeight);"
    )
    cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        delay_before_return_html=max(3, wait_seconds),
        page_timeout=max(90000, 20000 + rounds * 3000),
        js_code=[js],
    )
    async with AsyncWebCrawler(config=bc) as crawler:
        r = await crawler.arun(url=url, config=cfg)
        md = r.markdown.raw_markdown if hasattr(r.markdown, "raw_markdown") else str(r.markdown)
        return {"markdown": md or "", "status_code": r.status_code}


def _decode_landing_url(fb_link: str) -> str:
    """Turn an l.facebook.com/l.php?u=... redirect into the real destination URL."""
    try:
        qs = parse_qs(urlparse(fb_link).query)
        if "u" in qs:
            return unquote(qs["u"][0])
    except Exception:
        pass
    return fb_link


# CTA button label sits as plain text immediately before the landing redirect link, e.g.
#   ... Learn more ](https://l.facebook.com/l.php?u=...)
# Match against Facebook's fixed set of button labels so we don't grab trailing caption words.
_CTA_LABELS = (
    "Learn more", "Sign up", "Shop now", "Book now", "Send message",
    "Send WhatsApp message", "Contact us", "Subscribe", "Get offer", "Get quote",
    "Apply now", "Download", "Watch more", "See menu", "Order now", "Donate now",
    "Play game", "Listen now", "Get showtimes", "Save", "Open link", "Message page",
    "Call now", "Get directions", "Follow page", "Use app", "Install now",
    "Buy tickets", "Request time", "Try in camera",
)
_CTA_RE = re.compile(
    r'\s(' + '|'.join(re.escape(c) for c in _CTA_LABELS) +
    r')\s+\]\(https://l\.facebook\.com/l\.php', re.IGNORECASE)


def _parse_ad_library_markdown(md: str) -> List[dict]:
    """Best-effort structured extraction of ad cards from rendered Ad Library markdown."""
    ads = []
    seen = set()
    # Each card starts at a "Library ID: <digits>" line
    chunks = re.split(r'\nLibrary ID:\s*', md)
    for chunk in chunks[1:]:
        lib_id = re.match(r'(\d+)', chunk)
        if not lib_id:
            continue
        lid = lib_id.group(1)
        if lid in seen:  # infinite scroll can re-render the same card
            continue
        seen.add(lid)
        ad = {
            "library_id": lid,
            "ad_details_url": f"https://www.facebook.com/ads/library/?id={lid}",
        }

        m = re.search(r'Started running on ([A-Za-z]{3} \d{1,2}, \d{4})', chunk)
        ad["started_running"] = m.group(1) if m else None

        m = re.search(r'\*\*(\d+)\s+ads?\*\*\s+use this creative', chunk)
        ad["ads_using_creative"] = int(m.group(1)) if m else 1

        # advertiser: first [Name](facebook.com/<handle>/) link in the block
        m = re.search(r'\[([^\]]+)\]\(https://www\.facebook\.com/([^/)]+)/?\)', chunk)
        if m:
            ad["advertiser"] = m.group(1)
            ad["advertiser_handle"] = m.group(2)

        # landing domain from the first l.facebook.com redirect
        m = re.search(r'\(https://l\.facebook\.com/l\.php\?u=([^)&]+)', chunk)
        if m:
            real = _decode_landing_url("https://l.facebook.com/l.php?u=" + m.group(1))
            ad["landing_url"] = real
            ad["landing_domain"] = urlparse(real).netloc

        # call-to-action button label (Learn more / Sign up / Send message / Shop now ...)
        m = _CTA_RE.search(chunk)
        ad["cta"] = m.group(1).strip() if m else None

        # creative thumbnail + the headline/caption strip shown under it
        m = re.search(r'\((https://scontent[^)]+?\.(?:jpe?g|png|webp)[^)]*)\)', chunk)
        ad["creative_image"] = m.group(1) if m else None
        if ad["cta"]:
            # the creative card is [![<alt>](<img>) <headline/caption> <CTA> ](<l.facebook link>)
            m = re.search(
                r'\[!\[[^\]]*\]\(https?://scontent[^)]+\)\s+(.+?)\s+' + re.escape(ad["cta"]) +
                r'\s+\]\(https://l\.facebook\.com', chunk, re.DOTALL)
            if m:
                link_text = re.sub(r'\s+', ' ', m.group(1)).strip()
                # drop a leading shouted domain token ("FB.ME", "GLYVER.NET")
                link_text = re.sub(r'^[A-Z0-9][A-Z0-9.\-]{2,}\s+', '', link_text)
                ad["link_text"] = link_text[:400]

        # body copy: text between "Sponsored" and the next structural marker
        body = re.search(r'\*\*Sponsored\*\*\s*\n(.+?)(?:\n\[!\[|\nActive\n|\nInactive\n|$)',
                         chunk, re.DOTALL)
        if body:
            txt = re.sub(r'\s+\n', '\n', body.group(1)).strip()
            # collapse "[visible text](l.facebook redirect)" links down to the visible text
            txt = re.sub(r'\[([^\]]+)\]\(https?://l\.facebook\.com[^)]*\)', r'\1', txt)
            # drop a trailing half-captured markdown link ("... offer: [https://x](https://l.fac")
            txt = re.sub(r'\s*\[[^\]]*\]\([^)]*$', '', txt).strip()
            ad["body"] = txt[:2000]

        ad["platforms"] = [p for p in ("Facebook", "Instagram", "Audience Network", "Messenger")
                           if p in chunk]
        ads.append(ad)
    return ads


@mcp.tool(description="Search the public Facebook Ad Library for a keyword in a given country "
                      "(works for commercial ads, any country — no token). Renders the SPA "
                      "with a headless browser, scrolls past the first page, and returns "
                      "structured ad cards: advertiser, run date, creative count, landing "
                      "domain, CTA button, headline and body copy. Pass advertiser_page_id "
                      "to pull every ad from one Page.")
def search_ad_library(
    query: str = "",
    country: str = "MX",
    active_status: str = "active",
    media_type: str = "all",
    ad_type: str = "all",
    advertiser_page_id: str = "",
    wait_seconds: int = 8,
    scroll_rounds: int = 8,
) -> dict:
    """
    Args:
        query: keyword(s) to search (advertiser name, product, angle...). Optional if
               advertiser_page_id is given.
        country: ISO country code the ads were delivered in (MX, US, ES, ...)
        active_status: active | inactive | all
        ad_type: all | political_and_issue_ads | employment_ads | housing_ads | financial_products_and_services_ads
        media_type: all | image | meme | video | none
        advertiser_page_id: if set, target that Page's "all ads" view instead of a keyword
               search. This view is heavier client-rendered and does not always hydrate
               headless — a keyword search of the advertiser's name is the more reliable path.
        wait_seconds: how long to let the SPA hydrate before scraping (raise if results are empty)
        scroll_rounds: infinite-scroll cycles to load more ads past the first ~24
               (0 = first render only, fast; 8 default; 15+ for a deep sweep)
    """
    if not query and not advertiser_page_id:
        return {"success": False, "error": "Pass either query or advertiser_page_id."}

    params = {
        "active_status": active_status,
        "ad_type": ad_type,
        "country": country,
        "media_type": media_type,
    }
    if advertiser_page_id:
        params["view_all_page_id"] = advertiser_page_id
        params["search_type"] = "page"
        if query:
            params["q"] = query
    else:
        params["search_type"] = "keyword_unordered"
        params["q"] = query
    url = AD_LIBRARY_BASE + "?" + "&".join(f"{k}={quote(str(v))}" for k, v in params.items())

    try:
        rendered = asyncio.run(_render_ad_library(url, wait_seconds, scroll_rounds))
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}

    md = rendered["markdown"]
    ads = _parse_ad_library_markdown(md)
    if not ads:
        return {
            "success": False,
            "url": url,
            "note": "No ad cards parsed. The page may be rate-limiting the headless browser "
                    "or there are genuinely no results. Retry with a higher wait_seconds, or "
                    "fall back to a real browser as documented in docs/examples.md.",
            "status_code": rendered["status_code"],
            "markdown_preview": md[:1500],
        }

    advertisers = {}
    for a in ads:
        name = a.get("advertiser", "unknown")
        advertisers[name] = advertisers.get(name, 0) + 1

    return {
        "success": True,
        "query": query or f"page_id:{advertiser_page_id}",
        "country": country,
        "url": url,
        "scroll_rounds": max(0, int(scroll_rounds)),
        "total_ads_parsed": len(ads),
        "total_advertisers": len(advertisers),
        "advertisers": dict(sorted(advertisers.items(), key=lambda x: -x[1])),
        "ads": ads,
        "raw_markdown": md[:16000],
    }


@mcp.tool(description="Scrape any Facebook Ad Library URL you already have (a prefilled search, "
                      "an advertiser's 'view all ads' page, a shared filter link) and return "
                      "structured ad cards plus the raw rendered text.")
def scrape_ad_library_url(url: str, wait_seconds: int = 8, scroll_rounds: int = 8) -> dict:
    """
    Args:
        url: a facebook.com/ads/library/... URL
        wait_seconds: SPA hydration wait before scraping
        scroll_rounds: infinite-scroll cycles to load more cards (0 = first render only)
    """
    if "facebook.com/ads/library" not in url:
        return {"success": False, "error": "URL must be a facebook.com/ads/library/... link"}
    try:
        rendered = asyncio.run(_render_ad_library(url, wait_seconds, scroll_rounds))
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}
    md = rendered["markdown"]
    ads = _parse_ad_library_markdown(md)
    return {
        "success": bool(ads),
        "url": url,
        "scroll_rounds": max(0, int(scroll_rounds)),
        "total_ads_parsed": len(ads),
        "ads": ads,
        "raw_markdown": md[:16000],
        "status_code": rendered["status_code"],
    }


if __name__ == "__main__":
    print("Facebook Ad Library MCP — scraping tools: search_ad_library, scrape_ad_library_url")
    mcp.run(transport="stdio")
