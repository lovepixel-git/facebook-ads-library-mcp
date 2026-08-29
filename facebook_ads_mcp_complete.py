# facebook_ads_mcp_complete.py
from fastmcp import FastMCP
import requests
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import re
from urllib.parse import urlencode
import time
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load .env sitting next to this script so the token never has to live in MCP config
load_dotenv(Path(__file__).resolve().parent / ".env")
from crawl4ai import AsyncWebCrawler
import asyncio

class FacebookAdsLibraryAPI:
    """Complete Facebook Ads Library API wrapper with advanced features"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v19.0/ads_archive"

    def _make_request(self, params: dict) -> dict:
        """Make API request with error handling"""
        params['access_token'] = self.access_token
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}

    def _extract_ad_id_from_url(self, snapshot_url: str) -> str:
        """Extract ad ID from snapshot URL"""
        match = re.search(r'id=(\d+)', snapshot_url)
        return match.group(1) if match else None

    def _analyze_ad_creative(self, snapshot_url: str) -> dict:
        """Analyze ad creative using web scraping"""
        async def crawl_page():
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=snapshot_url)
                return {
                    "text_content": result.cleaned_html,
                    "extracted_text": result.extracted_content,
                    "success": True
                }

        try:
            return asyncio.run(crawl_page())
        except Exception as e:
            return {"error": str(e), "success": False}

# Initialize MCP Server
mcp = FastMCP(
    name="Facebook Ads Library Complete",
    instructions="""
    Complete Facebook Ads Library MCP with 15+ advanced tools for comprehensive ad intelligence.
    Provides deep insights into competitor advertising strategies, creative analysis, and market intelligence.
    """
)

# Initialize API client
def get_facebook_token():
    """Get Facebook access token from command line arguments"""
    if "--facebook-token" in sys.argv:
        token_index = sys.argv.index("--facebook-token") + 1
        if token_index < len(sys.argv):
            return sys.argv[token_index]
    return os.getenv("FACEBOOK_ACCESS_TOKEN")

fb_api = FacebookAdsLibraryAPI(get_facebook_token())

# ===== BÚSQUEDA Y DESCUBRIMIENTO =====

@mcp.tool(description="Search Facebook Ads Library with advanced filters")
def search_facebook_ads(
    brand_name: str,
    country: str = "US",
    ad_type: str = "ALL",
    date_range: int = 30,
    limit: int = 50
) -> dict:
    """
    Search Facebook Ads Library with comprehensive filters
    
    Args:
        brand_name: Brand or company name to search
        country: Target country code (US, GB, CA, etc.)
        ad_type: Type of ads (ALL, POLITICAL_AND_ISSUE_ADS, etc.)
        date_range: Days to look back (default: 30)
        limit: Maximum number of ads to return
    """
    params = {
        'search_terms': brand_name,
        'ad_reached_countries': [country],
        'fields': 'id,ad_creation_time,ad_delivery_start_time,ad_delivery_stop_time,ad_creative_bodies,ad_creative_link_captions,ad_creative_link_descriptions,ad_creative_link_titles,ad_snapshot_url,currency,demographic_distribution,delivery_by_region,impressions,page_id,page_name,publisher_platforms,spend',
        'limit': limit,
        'ad_active_status': 'ALL'
    }

    if ad_type != "ALL":
        params['ad_type'] = ad_type

    result = fb_api._make_request(params)

    if result.get("success") is False:
        return result

    ads = result.get("data", [])
    for ad in ads:
        start = ad.get("ad_delivery_start_time")
        if start:
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                stop = ad.get("ad_delivery_stop_time")
                end_dt = datetime.fromisoformat(stop.replace("Z", "+00:00")) if stop else datetime.now(start_dt.tzinfo)
                ad["days_active"] = (end_dt - start_dt).days
            except (ValueError, TypeError):
                ad["days_active"] = None
        else:
            ad["days_active"] = None

    ads.sort(key=lambda a: (a.get("days_active") is None, -(a.get("days_active") or 0)))

    return {
        "brand": brand_name,
        "total_ads": len(ads),
        "ads": ads,
        "search_params": params,
        "success": True
    }

@mcp.tool(description="Discover competitor brands in an industry")
def discover_competitor_brands(
    industry_keywords: str,
    region: str = "US",
    min_ads: int = 5,
    limit: int = 100
) -> dict:
    """
    Discover competitor brands by industry keywords
    
    Args:
        industry_keywords: Industry-related keywords (e.g., "fitness app", "food delivery")
        region: Target region
        min_ads: Minimum number of ads to qualify as active advertiser
        limit: Maximum brands to return
    """
    params = {
        'search_terms': industry_keywords,
        'ad_reached_countries': [region],
        'fields': 'page_name,page_id,ad_creation_time',
        'limit': limit * 3,  # Get more to filter
        'ad_active_status': 'ACTIVE'
    }
    
    result = fb_api._make_request(params)
    
    if result.get("success") is False:
        return result
    
    # Count ads per brand
    brand_counts = {}
    for ad in result.get("data", []):
        page_name = ad.get("page_name", "")
        if page_name:
            brand_counts[page_name] = brand_counts.get(page_name, 0) + 1
    
    # Filter brands with minimum ads
    qualified_brands = {
        brand: count for brand, count in brand_counts.items() 
        if count >= min_ads
    }
    
    # Sort by ad count
    sorted_brands = sorted(qualified_brands.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "industry": industry_keywords,
        "region": region,
        "discovered_brands": sorted_brands[:limit],
        "total_qualified_brands": len(qualified_brands),
        "success": True
    }

@mcp.tool(description="Analyze ad creative elements in detail")
def analyze_ad_creative_elements(
    ad_snapshot_url: str,
    extract_text: bool = True,
    analyze_images: bool = True,
    detect_cta: bool = True
) -> dict:
    """
    Deep analysis of ad creative elements
    
    Args:
        ad_snapshot_url: URL to Facebook ad snapshot
        extract_text: Extract all text content
        analyze_images: Analyze image elements
        detect_cta: Detect call-to-action elements
    """
    creative_analysis = fb_api._analyze_ad_creative(ad_snapshot_url)
    
    if not creative_analysis.get("success"):
        return creative_analysis
    
    analysis_result = {
        "ad_url": ad_snapshot_url,
        "ad_id": fb_api._extract_ad_id_from_url(ad_snapshot_url),
        "analysis": {}
    }
    
    if extract_text:
        text_content = creative_analysis.get("extracted_text", "")
        analysis_result["analysis"]["text_analysis"] = {
            "word_count": len(text_content.split()),
            "character_count": len(text_content),
            "sentiment_keywords": re.findall(r'\b(?:amazing|best|free|save|new|limited|exclusive|now)\b', text_content.lower()),
            "full_text": text_content
        }
    
    if detect_cta:
        text_content = creative_analysis.get("extracted_text", "")
        cta_patterns = [
            r'\b(?:shop now|buy now|learn more|sign up|download|get started|try free|claim offer)\b',
            r'\b(?:click here|tap here|swipe up|see more|order now|book now)\b'
        ]
        
        detected_ctas = []
        for pattern in cta_patterns:
            matches = re.findall(pattern, text_content.lower())
            detected_ctas.extend(matches)
        
        analysis_result["analysis"]["cta_analysis"] = {
            "detected_ctas": detected_ctas,
            "cta_count": len(detected_ctas),
            "urgency_words": re.findall(r'\b(?:now|today|limited|hurry|urgent|expires|deadline)\b', text_content.lower())
        }
    
    analysis_result["success"] = True
    return analysis_result

@mcp.tool(description="Analyze ad performance metrics and insights")
def analyze_ad_performance_metrics(
    brand_name: str,
    time_period: int = 30,
    performance_metrics: List[str] = None
) -> dict:
    """
    Analyze ad performance metrics for a brand
    
    Args:
        brand_name: Brand name to analyze
        time_period: Analysis period in days
        performance_metrics: Specific metrics to analyze
    """
    if performance_metrics is None:
        performance_metrics = ["impressions", "spend", "reach", "demographic_distribution"]
    
    params = {
        'search_terms': brand_name,
        'ad_reached_countries': ["US"],
        'fields': 'id,ad_creation_time,impressions,spend,reach,demographic_distribution,delivery_by_region,publisher_platforms',
        'limit': 100,
        'ad_active_status': 'ALL'
    }
    
    result = fb_api._make_request(params)
    
    if result.get("success") is False:
        return result
    
    ads = result.get("data", [])

    # Aggregate metrics
    total_impressions = 0
    total_spend = 0
    platform_distribution = {}
    demographic_summary = {}
    # Meta only returns spend/impressions/demographics for political & issue ads.
    # Track how many ads actually carried that data so we can be honest about it.
    ads_with_spend_or_impressions = 0

    for ad in ads:
        if ad.get("impressions") or ad.get("spend") or ad.get("demographic_distribution"):
            ads_with_spend_or_impressions += 1
        # Impressions
        if "impressions" in ad:
            if ad["impressions"] != "≤1,000":
                try:
                    impressions = int(ad["impressions"].replace(",", ""))
                    total_impressions += impressions
                except:
                    pass
        
        # Spend
        if "spend" in ad:
            spend_range = ad["spend"]
            if spend_range and spend_range != "≤$100":
                # Extract average from range
                numbers = re.findall(r'\d+', spend_range)
                if numbers:
                    avg_spend = sum(int(n) for n in numbers) / len(numbers)
                    total_spend += avg_spend
        
        # Platform distribution
        if "publisher_platforms" in ad:
            for platform in ad["publisher_platforms"]:
                platform_distribution[platform] = platform_distribution.get(platform, 0) + 1
        
        # Demographics
        if "demographic_distribution" in ad:
            for demo in ad["demographic_distribution"]:
                age_gender = f"{demo.get('age', 'unknown')}_{demo.get('gender', 'unknown')}"
                demographic_summary[age_gender] = demographic_summary.get(age_gender, 0) + 1
    
    data_available = ads_with_spend_or_impressions > 0
    response = {
        "brand": brand_name,
        "analysis_period": f"{time_period} days",
        "total_ads_analyzed": len(ads),
        "data_available": data_available,
        "ads_with_reported_metrics": ads_with_spend_or_impressions,
        "performance_summary": {
            "total_impressions": total_impressions,
            "estimated_total_spend": total_spend,
            "platform_distribution": platform_distribution,
            "demographic_distribution": demographic_summary,
            "avg_impressions_per_ad": total_impressions / len(ads) if ads else 0,
            "avg_spend_per_ad": total_spend / len(ads) if ads else 0
        },
        "success": True
    }
    if not data_available:
        response["note"] = (
            "Meta's ads_archive API only reports spend, impressions and demographics for "
            "political & issue ads. None of the ads matched here carried that data, so the "
            "numeric totals above are 0 by absence, not by measurement. For commercial "
            "brands use the search_ad_library scraping tool instead."
        )
    return response

@mcp.tool(description="Comprehensive competitive ad analysis")
def competitive_ad_analysis(
    brands_list: List[str],
    metrics_comparison: List[str] = None,
    analysis_depth: str = "standard"
) -> dict:
    """
    Compare ad strategies across multiple competitor brands
    
    Args:
        brands_list: List of brand names to compare
        metrics_comparison: Specific metrics to compare
        analysis_depth: Depth of analysis (standard, deep)
    """
    if metrics_comparison is None:
        metrics_comparison = ["ad_count", "spend_estimation", "creative_themes", "targeting"]
    
    comparison_results = {}
    
    for brand in brands_list:
        brand_data = search_facebook_ads(brand, limit=50)
        
        if brand_data.get("success"):
            ads = brand_data.get("ads", [])
            
            # Basic metrics
            brand_analysis = {
                "total_ads": len(ads),
                "active_ads": len([ad for ad in ads if "ad_creation_time" in ad]),
                "platforms": set(),
                "estimated_spend": 0,
                "creative_themes": [],
                "targeting_insights": {}
            }
            
            # Analyze each ad
            for ad in ads:
                # Platform distribution
                if "publisher_platforms" in ad:
                    brand_analysis["platforms"].update(ad["publisher_platforms"])
                
                # Spend estimation
                if "spend" in ad and ad["spend"]:
                    spend_range = ad["spend"]
                    if spend_range != "≤$100":
                        numbers = re.findall(r'\d+', spend_range.replace(',', ''))
                        if numbers:
                            avg_spend = sum(int(n) for n in numbers) / len(numbers)
                            brand_analysis["estimated_spend"] += avg_spend
                
                # Creative themes
                for body in ad.get("ad_creative_bodies", []):
                    words = body.lower().split()
                    # Extract key themes (simple keyword analysis)
                    themes = [word for word in words if len(word) > 5 and word.isalpha()]
                    brand_analysis["creative_themes"].extend(themes[:3])
            
            # Convert sets to lists for JSON serialization
            brand_analysis["platforms"] = list(brand_analysis["platforms"])
            brand_analysis["creative_themes"] = list(set(brand_analysis["creative_themes"]))[:10]
            
            comparison_results[brand] = brand_analysis
    
    # Generate competitive insights
    insights = {
        "market_leader": max(comparison_results.items(), key=lambda x: x[1]["total_ads"])[0] if comparison_results else None,
        "highest_spender": max(comparison_results.items(), key=lambda x: x[1]["estimated_spend"])[0] if comparison_results else None,
        "platform_trends": {},
        "common_themes": []
    }
    
    # Analyze platform trends
    all_platforms = {}
    for brand, data in comparison_results.items():
        for platform in data["platforms"]:
            all_platforms[platform] = all_platforms.get(platform, 0) + 1
    
    insights["platform_trends"] = dict(sorted(all_platforms.items(), key=lambda x: x[1], reverse=True))
    
    # Find common themes
    all_themes = []
    for brand, data in comparison_results.items():
        all_themes.extend(data["creative_themes"])
    
    theme_counts = {}
    for theme in all_themes:
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
    
    insights["common_themes"] = [theme for theme, count in theme_counts.items() if count > 1][:10]
    
    return {
        "brands_analyzed": brands_list,
        "comparison_results": comparison_results,
        "competitive_insights": insights,
        "analysis_timestamp": datetime.now().isoformat(),
        "success": True
    }

@mcp.tool(description="Generate comprehensive Facebook ads intelligence report")
def generate_facebook_intelligence_report(
    brand_name: str,
    include_competitors: bool = True,
    report_depth: str = "comprehensive"
) -> dict:
    """
    Generate complete intelligence report for a brand's Facebook advertising
    
    Args:
        brand_name: Primary brand to analyze
        include_competitors: Include competitor analysis
        report_depth: Depth of report (basic, standard, comprehensive)
    """
    report = {
        "brand": brand_name,
        "report_timestamp": datetime.now().isoformat(),
        "analysis_summary": {},
        "detailed_findings": {},
        "recommendations": [],
        "success": True
    }
    
    try:
        # 1. Basic ad search
        basic_ads = search_facebook_ads(brand_name, limit=100)
        report["analysis_summary"]["total_ads"] = basic_ads.get("total_ads", 0)
        
        # 2. Performance analysis
        performance = analyze_ad_performance_metrics(brand_name)
        report["detailed_findings"]["performance_metrics"] = performance.get("performance_summary", {})
        report["detailed_findings"]["performance_data_available"] = performance.get("data_available", False)
        if not performance.get("data_available", False):
            report["detailed_findings"]["performance_note"] = performance.get("note")
        
        # 3. Recent activity analysis
        recent_ads = [ad for ad in basic_ads.get("ads", []) if ad.get("ad_creation_time")]
        report["detailed_findings"]["recent_activity"] = {
            "total_recent_ads": len(recent_ads),
            "avg_ads_per_week": len(recent_ads) / 4 if recent_ads else 0
        }
        
        # 4. Platform analysis
        platforms = {}
        for ad in basic_ads.get("ads", []):
            for platform in ad.get("publisher_platforms", []):
                platforms[platform] = platforms.get(platform, 0) + 1
        
        report["detailed_findings"]["platform_distribution"] = platforms
        
        # 5. Competitor analysis (if requested)
        if include_competitors:
            competitors = discover_competitor_brands(brand_name)
            top_competitors = [brand for brand, count in competitors.get("discovered_brands", [])[:5]]
            
            if top_competitors:
                competitive_analysis = competitive_ad_analysis([brand_name] + top_competitors)
                report["detailed_findings"]["competitive_landscape"] = competitive_analysis.get("competitive_insights", {})
        
        # Generate recommendations
        recommendations = []
        
        if report["analysis_summary"]["total_ads"] < 10:
            recommendations.append("Consider increasing ad volume for better market presence")
        
        if "instagram" not in platforms and "facebook" in platforms:
            recommendations.append("Expand to Instagram for broader reach")
        
        if len(recent_ads) < 5:
            recommendations.append("Increase creative refresh rate for better performance")
        
        report["recommendations"] = recommendations
        
        # Executive summary
        report["analysis_summary"].update({
            "ad_activity_level": "High" if len(recent_ads) > 10 else "Medium" if len(recent_ads) > 5 else "Low",
            "platform_diversity": len(platforms),
            "primary_platform": max(platforms.items(), key=lambda x: x[1])[0] if platforms else "Unknown",
            "competitive_position": "Analysis included" if include_competitors else "Not analyzed"
        })
        
    except Exception as e:
        report["success"] = False
        report["error"] = str(e)
    
    return report

@mcp.tool(description="Export Facebook ads data to various formats")
def export_facebook_ads_data(
    brand_name: str,
    export_format: str = "json",
    include_creatives: bool = False,
    limit: int = 100
) -> dict:
    """
    Export Facebook ads data in various formats
    
    Args:
        brand_name: Brand to export data for
        export_format: Format for export (json, csv, markdown)
        include_creatives: Include creative analysis
        limit: Maximum number of ads to export
    """
    # Get ads data
    ads_data = search_facebook_ads(brand_name, limit=limit)
    
    if not ads_data.get("success"):
        return ads_data
    
    ads = ads_data.get("ads", [])
    
    # Prepare export data
    export_data = []
    
    for ad in ads:
        ad_record = {
            "ad_id": ad.get("id"),
            "page_name": ad.get("page_name"),
            "creation_time": ad.get("ad_creation_time"),
            "impressions": ad.get("impressions"),
            "spend": ad.get("spend"),
            "currency": ad.get("currency"),
            "creative_bodies": ad.get("ad_creative_bodies", []),
            "platforms": ad.get("publisher_platforms", []),
            "snapshot_url": ad.get("ad_snapshot_url")
        }
        
        if include_creatives and ad.get("ad_snapshot_url"):
            creative_analysis = analyze_ad_creative_elements(ad["ad_snapshot_url"])
            ad_record["creative_analysis"] = creative_analysis.get("analysis", {})
        
        export_data.append(ad_record)
    
    # Format based on export type
    if export_format == "json":
        formatted_data = json.dumps(export_data, indent=2, default=str)
    elif export_format == "csv":
        # Simple CSV formatting
        csv_lines = ["id,page_name,creation_time,impressions,spend,platforms"]
        for record in export_data:
            csv_lines.append(f"{record['ad_id']},{record['page_name']},{record['creation_time']},{record['impressions']},{record['spend']},{';'.join(record['platforms'])}")
        formatted_data = "\n".join(csv_lines)
    elif export_format == "markdown":
        # Markdown table format
        md_lines = ["# Facebook Ads Export", f"## Brand: {brand_name}", "", "| Ad ID | Page Name | Creation Time | Impressions | Spend | Platforms |", "|-------|-----------|---------------|-------------|-------|-----------|"]
        for record in export_data:
            md_lines.append(f"| {record['ad_id']} | {record['page_name']} | {record['creation_time']} | {record['impressions']} | {record['spend']} | {', '.join(record['platforms'])} |")
        formatted_data = "\n".join(md_lines)
    else:
        formatted_data = export_data
    
    return {
        "brand": brand_name,
        "export_format": export_format,
        "total_records": len(export_data),
        "export_data": formatted_data,
        "export_timestamp": datetime.now().isoformat(),
        "success": True
    }

# ===== SCRAPING DEL AD LIBRARY WEB (no API — funciona para MX y cualquier país) =====
# La Ad Library API oficial solo cubre anuncios políticos (mundial) y todo tipo en UE/UK.
# Para anuncios comerciales de México se renderiza la SPA pública del Ad Library con crawl4ai.

from urllib.parse import quote, urlparse, parse_qs, unquote

AD_LIBRARY_BASE = "https://www.facebook.com/ads/library/"


async def _render_ad_library(url: str, wait_seconds: int = 8, scroll_rounds: int = 8) -> dict:
    """Render the Ad Library SPA and return its markdown. FB flags headless as 403 but
    still serves the rendered ad cards, so success is judged by content, not status.

    The Ad Library is an infinite-scroll SPA: the first paint only holds ~20-26 cards.
    ``scroll_rounds`` drives that many extra scroll-to-bottom + wait cycles so lazy-loaded
    cards (older ads, more advertisers) are in the DOM before it is serialised. Set it to 0
    to keep just the first render (fast), or higher for a fuller sweep."""
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
            # deep link to this specific ad's detail view (creative, spend range, EU targeting)
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


@mcp.tool(description="Search the public Facebook Ad Library web (no API) for a keyword in a "
                      "given country — works for Mexico and commercial ads. Renders the SPA "
                      "with a headless browser, scrolls it to pull past the first page, and "
                      "returns structured ad cards (advertiser, run date, creative count, "
                      "landing domain, CTA button, headline, body). Pass advertiser_page_id "
                      "with an empty query to pull every active ad from one Page.")
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
        advertiser_page_id: if set, target that Page's "all ads" view (its numeric
               advertiser_handle from a previous result) instead of a keyword search.
               Note: this view is heavier client-rendered and does not always hydrate
               under the headless browser — a keyword search of the advertiser's name is
               the more reliable path.
        wait_seconds: how long to let the SPA hydrate before scraping (raise if results are empty)
        scroll_rounds: infinite-scroll cycles to load older/more ads past the first ~24
               (0 = first render only, fast; 8 default; 15+ for a deep sweep)
    """
    if not query and not advertiser_page_id:
        return {"success": False,
                "error": "Pass either query or advertiser_page_id."}

    params = {
        "active_status": active_status,
        "ad_type": ad_type,
        "country": country,
        "media_type": media_type,
    }
    if advertiser_page_id:
        # the "all ads from this Page" view needs search_type=page, not a keyword search
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
    # The scraping tools (search_ad_library, scrape_ad_library_url) work with no token.
    # Only the ads_archive API tools need one — warn but don't hard-exit.
    token = get_facebook_token()
    if not token:
        print("⚠️  No Facebook token found — the ads_archive API tools will fail, but the "
              "Ad Library scraping tools still work.")

    print("✅ Facebook Ads Library MCP Server starting...")
    print("🔧 Tools: 8 ads_archive API tools + 2 Ad Library web-scraping tools (MX-capable)")
    mcp.run(transport="stdio")
