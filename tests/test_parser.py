"""Offline tests for the Ad Library markdown parser and tool wiring.

Run:  python -m pytest tests/ -q
These do not hit the network — they exercise _parse_ad_library_markdown against a
fixture that mirrors the markdown crawl4ai produces for a rendered Ad Library page.
"""
import facebook_ads_mcp_complete as m

FIXTURE = """
Some header junk

Library ID: 111111111111111
Started running on Jan 5, 2026
**3 ads** use this creative
[Glyver](https://www.facebook.com/glyver/)
**Sponsored**
Automatiza tu operacion con IA. Agenda tu diagnostico gratis: [https://glyver.net](https://l.facebook.com/l.php?u=https%3A%2F%2Fglyver.net%2F&h=AbC)
[![creative](https://scontent.xx.fbcdn.net/v/photo.jpg) GLYVER.NET Agenda tu diagnostico Learn more ](https://l.facebook.com/l.php?u=https%3A%2F%2Fglyver.net%2F&h=AbC)
Facebook Instagram

Library ID: 222222222222222
Started running on Feb 16, 2026
[Otra Marca](https://www.facebook.com/otramarca/)
**Sponsored**
Prueba nuestro producto hoy.
[![creative](https://scontent.xx.fbcdn.net/v/photo2.jpg) OTRA Compra ahora Shop now ](https://l.facebook.com/l.php?u=https%3A%2F%2Fotramarca.com%2Fpromo)

Library ID: 111111111111111
(duplicate card re-rendered by infinite scroll — should be ignored)
[Glyver](https://www.facebook.com/glyver/)
"""


def _parsed():
    return m._parse_ad_library_markdown(FIXTURE)


def test_card_count_and_dedupe():
    ads = _parsed()
    assert len(ads) == 2
    assert [a["library_id"] for a in ads] == ["111111111111111", "222222222222222"]


def test_advertiser_and_dates():
    a = _parsed()[0]
    assert a["advertiser"] == "Glyver"
    assert a["advertiser_handle"] == "glyver"
    assert a["started_running"] == "Jan 5, 2026"
    assert a["ads_using_creative"] == 3


def test_landing_url_decoded():
    a = _parsed()[0]
    assert a["landing_url"] == "https://glyver.net/"
    assert a["landing_domain"] == "glyver.net"


def test_cta_and_link_text():
    a, b = _parsed()
    assert a["cta"] == "Learn more"
    assert a["link_text"] == "Agenda tu diagnostico"   # leading shouted domain dropped
    assert b["cta"] == "Shop now"


def test_body_strips_redirect_links():
    a = _parsed()[0]
    assert "l.facebook.com" not in a["body"]
    assert a["body"].startswith("Automatiza tu operacion con IA")


def test_ad_details_url():
    a = _parsed()[0]
    assert a["ad_details_url"] == "https://www.facebook.com/ads/library/?id=111111111111111"


def test_empty_input():
    assert m._parse_ad_library_markdown("") == []


def test_only_scraping_tools_are_registered():
    # The server is a pure Ad Library scraper — no ads_archive API tools.
    assert hasattr(m, "search_ad_library")
    assert hasattr(m, "scrape_ad_library_url")
    for gone in ("search_facebook_ads", "analyze_ad_performance_metrics",
                 "generate_facebook_intelligence_report", "fb_api"):
        assert not hasattr(m, gone), f"{gone} should have been removed"


# --- OWT fork -----------------------------------------------------------------
# Regression cover for the duplication signal. The upstream regex looked for
# "**N ads** use this creative", which Meta no longer renders in the grid, and it
# defaulted a miss to 1 - so a dead regex read as "nobody duplicates anything".
# Live check 2026-09-20: 59 of 70 Jade Leaf ads are multi-version.

_MULTI = """
Library ID: 111
Started running on Jun 24, 2026
Platforms
This ad has multiple versions
Open Dropdown
See ad details
"""

_SINGLE = """
Library ID: 222
Started running on Jun 24, 2026
Platforms
See ad details
"""


def test_multiple_versions_is_not_reported_as_one():
    ad = m._parse_ad_library_markdown(_MULTI)[0]
    assert ad["has_multiple_versions"] is True
    # None, never 1 - a known-duplicated ad whose count Meta hides must not be
    # indistinguishable from a genuinely single one.
    assert ad["ads_using_creative"] is None


def test_genuine_single_still_reports_one():
    ad = m._parse_ad_library_markdown(_SINGLE)[0]
    assert ad["has_multiple_versions"] is False
    assert ad["ads_using_creative"] == 1


def test_days_running_distinguishes_unparseable_from_today():
    assert m._days_running("Jun 24, 2026") > 0
    assert m._days_running(None) is None
    assert m._days_running("not a date") is None


# --- funnel inference ---------------------------------------------------------
# Cases are real creatives pulled 2026-09-20, not invented ones.

def test_replenishment_copy_is_bof():
    r = m._infer_funnel_stage({"body": "Running low? Check if it's time to top up.",
                               "landing_url": "", "cta": "Shop Now"})
    assert r["stage"] == "BOF"


def test_generic_shop_now_does_not_drown_a_real_signal():
    # "Shop Now" is 95% of this vertical's ads (measured). Weighted like a real BOF
    # signal it dragged consideration creative into BOF; this is that regression.
    r = m._infer_funnel_stage({"body": "Find Your Favourite Matcha 5 Star Reviews",
                               "landing_url": "", "cta": "Shop Now"})
    assert r["stage"] == "MOF"


def test_unreadable_ad_returns_no_stage_rather_than_a_default():
    r = m._infer_funnel_stage({"body": "", "landing_url": "", "cta": ""})
    assert r["stage"] is None and r["confidence"] == 0.0


def test_every_label_carries_its_evidence():
    r = m._infer_funnel_stage({"body": "meet the farmers",
                               "landing_url": "https://x.com/pages/about",
                               "cta": "Learn More"})
    assert r["stage"] == "TOF" and r["signals"]
