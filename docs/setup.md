# Setup

## Requirements

- Python 3.10+
- An MCP client (Claude Code, Claude Desktop, …)
- ~400 MB disk for the headless Chromium that crawl4ai downloads

No Facebook account or API token is needed.

## Install

```bash
git clone https://github.com/RamsesAguirre777/facebook-ads-library-mcp.git
cd facebook-ads-library-mcp
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

Verify:

```bash
python -m pytest tests/ -q
python facebook_ads_mcp_complete.py   # prints the startup line, then waits on stdio; Ctrl-C to exit
```

## Register the server

### Claude Code

```bash
claude mcp add facebook-ads -- \
  /absolute/path/to/venv/bin/python \
  /absolute/path/to/facebook_ads_mcp_complete.py
```

### Claude Desktop

Config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "facebook-ads": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/facebook_ads_mcp_complete.py"]
    }
  }
}
```

Restart the client. You should see `search_ad_library` and `scrape_ad_library_url` in the
tool list.

## Troubleshooting

**Server won't start / `ModuleNotFoundError`** — the MCP client must run the Python from
the venv where you installed the requirements. Use the absolute path to `venv/bin/python`,
not bare `python`.

**`playwright` / browser errors** — run `python -m playwright install chromium` inside the
venv.

**`search_ad_library` returns `success: false` with no ads** — Facebook is rate-limiting
the headless browser, or there genuinely are no results. Wait a few minutes, raise
`wait_seconds`, or open the `url` from the response in a real browser to check.

**Results are thin** — raise `scroll_rounds` (each round pulls more of the infinite-scroll
feed; `15`+ for a full sweep).

See [examples.md](examples.md) for the research workflow.
