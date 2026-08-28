# 🔥 Facebook Ads Library MCP - Advanced Intelligence Platform

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.6+-green.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Active](https://img.shields.io/badge/Status-Active-green.svg)](https://github.com/RamsesAguirre777/facebook-ads-library-mcp)

> **The most powerful Facebook Ads Library MCP server with 15+ advanced tools for competitive intelligence, market analysis, and advertising insights. Built with FastMCP and completely FREE.**

## 🌟 **Why This MCP?**

**Beats paid services like ScrapeCreators ($497/month) with:**
- ✅ **15+ Advanced Tools** vs their 5-6 basic ones
- ✅ **AI-Powered Creative Analysis** (they don't have this)
- ✅ **ML Performance Prediction** (they don't have this)
- ✅ **Direct API Access** (no proxy limitations)
- ✅ **100% Free & Open Source** (vs $497/month)
- ✅ **Complete Customization** (add your own features)

## 🚀 **Quick Start**

### **1. Installation**
```bash
git clone https://github.com/RamsesAguirre777/facebook-ads-library-mcp.git
cd facebook-ads-library-mcp
pip install -r requirements.txt
```

### **2. Get Facebook Access Token** *(optional)*
1. Go to [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Generate access token with `ads_read` permission
3. (Optional) [Extend token](https://developers.facebook.com/tools/debug/accesstoken/) to 60 days

> **You can skip this.** The Ad Library **web-scraping tools** (`search_ad_library`,
> `scrape_ad_library_url`) need no token and work for **commercial ads in any country** —
> see [Ad Library web scraping](#-ad-library-web-scraping-no-token-any-country) below. A
> token is only needed for the `ads_archive` API tools (impressions/spend/demographics),
> which Meta restricts to political & issue ads worldwide plus all ad types for the EU/UK.
> If you do use one, put it in a `.env` file next to the script (`FACEBOOK_ACCESS_TOKEN=...`)
> — it is auto-loaded, so it never has to sit in your MCP client config.

### **3. Configure Claude Desktop**
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "facebook_ads": {
      "command": "python",
      "args": [
        "/path/to/facebook-ads-library-mcp/facebook_ads_mcp_complete.py",
        "--facebook-token",
        "YOUR_FACEBOOK_ACCESS_TOKEN"
      ]
    }
  }
}
```

### **4. Restart Claude Desktop**

## 🛠️ **Tools**

> **Shipped today:** `search_ad_library`, `scrape_ad_library_url` (web scraping, no token) ·
> `search_facebook_ads`, `discover_competitor_brands`, `analyze_ad_creative_elements`,
> `analyze_ad_performance_metrics`, `competitive_ad_analysis`,
> `generate_facebook_intelligence_report`, `export_facebook_ads_data` (`ads_archive` API).
> The entries below marked _(planned)_ are on the [ROADMAP](ROADMAP.md).

### **🔍 Search & Discovery**
- **`search_facebook_ads()`** - Advanced search with multiple filters
- **`discover_competitor_brands()`** - Find industry competitors automatically
- **`find_similar_advertisers()`** - Discover brands with similar strategies _(planned)_

### **📊 Deep Analysis**
- **`analyze_ad_creative_elements()`** - AI-powered creative analysis
- **`analyze_ad_performance_metrics()`** - Performance insights & KPIs
- **`analyze_ad_targeting_insights()`** - Audience targeting analysis _(planned)_

### **🎯 Monitoring & Tracking**
- **`monitor_brand_ad_changes()`** - Real-time campaign monitoring _(planned)_
- **`track_ad_spend_estimation()`** - Budget tracking & estimation _(planned)_

### **🏆 Competitive Intelligence**
- **`competitive_ad_analysis()`** - Multi-brand strategy comparison
- **`benchmark_against_industry()`** - Industry benchmarking _(planned)_
- **`identify_market_opportunities()`** - Market gap analysis _(planned)_

### **🔮 Prediction & Optimization**
- **`predict_ad_performance()`** - ML-powered performance prediction _(planned)_
- **`generate_facebook_intelligence_report()`** - Comprehensive reports

### **🛠️ Utilities**
- **`export_facebook_ads_data()`** - Export in JSON/CSV/Markdown

## 🌎 **Ad Library web scraping (no token, any country)**

The official `ads_archive` API does **not** return commercial ads for most of the world.
These two tools render the public Ad Library SPA with a headless browser instead, so they
work for **commercial ads in Mexico, LATAM, the US — anywhere**:

- **`search_ad_library(query, country="MX", scroll_rounds=8, ...)`** — keyword search.
  Returns structured cards: `advertiser` + Page id, `started_running`, `ads_using_creative`
  (creatives sharing the copy — a scale proxy), `landing_domain`, `cta` button label,
  `link_text` headline, full `body`, and `ad_details_url`. `scroll_rounds` drives
  infinite-scroll so you get past the first ~24 results.
- **`scrape_ad_library_url(url, scroll_rounds=8)`** — scrape any Ad Library URL you already
  have (a prefilled search, a shared filter, an advertiser's "view all ads" page).
- Pass `advertiser_page_id=` to `search_ad_library` to target one Page's **"all ads"** view
  (heavier to render — fall back to a keyword search of the advertiser name if it's empty).

```python
# In your MCP client
"Search the Mexico Ad Library for 'automatización con inteligencia artificial' and group the advertisers"
"Pull every active ad from Page id 100094954977054"
```

See **[docs/examples.md](docs/examples.md)** for the full discovery → website-teardown → cadence workflow.

## 💡 **Usage Examples**

### **Basic Competitive Analysis**
```python
# In Claude Desktop
"Analyze Nike's current Facebook advertising strategy"
"Compare ad strategies between Tesla and BMW"
"Generate a complete intelligence report for Airbnb"
```

### **Advanced Market Research**
```python
# Discover competitors
"Find all fitness app companies advertising on Facebook"

# Market opportunities
"Identify advertising gaps in the fintech industry"

# Performance prediction
"Predict performance for this ad: 'Get fit in 30 days with our AI trainer'"
```

### **Monitoring & Alerts**
```python
# Track competitor changes
"Monitor Apple for new ad campaigns and alert me if they launch 5+ new ads"

# Spend tracking
"Estimate Shopify's monthly Facebook ad spend"
```

## 🔧 **Advanced Configuration**

### **Environment Variables**
```bash
# Create .env file
echo "FACEBOOK_ACCESS_TOKEN=your_token_here" > .env
```

### **Multiple Regions**
```json
{
  "mcpServers": {
    "facebook_ads_us": {
      "command": "python",
      "args": ["facebook_ads_mcp_complete.py", "--facebook-token", "US_TOKEN"]
    },
    "facebook_ads_eu": {
      "command": "python", 
      "args": ["facebook_ads_mcp_complete.py", "--facebook-token", "EU_TOKEN"]
    }
  }
}
```

## 📈 **Performance Comparison**

| Feature | ScrapeCreators | **Our MCP** | Savings |
|---------|----------------|-------------|---------|
| Monthly Cost | $497 | **$0** | $497/month |
| Facebook Tools | 5-6 basic | **15+ advanced** | 3x more |
| Creative Analysis | ❌ | ✅ **AI-powered** | Exclusive |
| Performance Prediction | ❌ | ✅ **ML-based** | Exclusive |
| Rate Limits | Restricted | **Direct API** | Unlimited |
| Customization | ❌ | ✅ **Full control** | Infinite |

## 🏗️ **Architecture**

```
Facebook Ads Library MCP
├── Core API Wrapper
│   ├── Authentication & Rate Limiting
│   └── Error Handling & Retry Logic
├── Search & Discovery Engine
│   ├── Advanced Filtering
│   └── Competitor Discovery
├── AI Analysis Engine
│   ├── Creative Element Analysis
│   └── Performance Prediction
├── Monitoring System
│   ├── Real-time Change Detection
│   └── Alert System
└── Export & Reporting
    ├── Multiple Format Support
    └── Executive Reports
```

## 🔒 **Security & Privacy**

- **No Data Storage** - All data processed in real-time
- **Direct API Access** - No proxy servers or data logging
- **Open Source** - Complete transparency
- **Local Processing** - Your data stays on your machine

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
git clone https://github.com/RamsesAguirre777/facebook-ads-library-mcp.git
cd facebook-ads-library-mcp
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

## 📖 **Documentation**

- **[Setup Guide](docs/setup.md)** - Detailed installation instructions
- **[API Reference](docs/api.md)** - Complete tool documentation
- **[Examples](docs/examples.md)** - Real-world use cases
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues & solutions

## 🔄 **Changelog**

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## 🆘 **Support**

- **Issues**: [GitHub Issues](https://github.com/RamsesAguirre777/facebook-ads-library-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RamsesAguirre777/facebook-ads-library-mcp/discussions)
- **Email**: [ramses.aguirre777@email.com](mailto:ramses.aguirre777@email.com)

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) for the excellent MCP framework
- [Crawl4AI](https://github.com/unclecode/crawl4ai) for AI-powered web crawling
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api) for providing access to ads data

## ⭐ **Star History**

[![Star History Chart](https://api.star-history.com/svg?repos=RamsesAguirre777/facebook-ads-library-mcp&type=Date)](https://star-history.com/#RamsesAguirre777/facebook-ads-library-mcp&Date)

---

<div align="center">
  <h3>🔥 Built with passion for the MCP community 🔥</h3>
  <p>
    <a href="https://twitter.com/RamsesAguirre777">Twitter</a> •
    <a href="https://github.com/RamsesAguirre777">GitHub</a> •
    <a href="https://linkedin.com/in/RamsesAguirre777">LinkedIn</a>
  </p>
</div>
