# Barchart Unusual Options Activity

Unofficial Python client for [Barchart.com](https://www.barchart.com/options/unusual-activity/stocks) unusual stock options activity data.

[中文版](README_CN.md)

---

## What This Is

Barchart's Unusual Options Activity page tracks options contracts where today's trading volume is significantly higher than open interest — a signal that large players may be positioning. This library scrapes that data so you can analyze it programmatically.

## One-Minute Quickstart

Get from zero to filtered results in three commands.

```bash
# 1. Install
pip install playwright
python -m playwright install chromium

# 2. Fetch data
python barchart_uoa.py
# → generates barchart_uoa_20260529_xxxxxx.csv

# 3. Open the filter GUI
python filter_gui.py
# → Load CSV → adjust filters → Export
```

No code needed after step 1. Filter by DTE, strike/price deviation, option type, volume, open interest, delta, and more — all in the GUI.

## Quick Start

### Fetch Data

```bash
python barchart_uoa.py
```

Or in your own code:

```python
from barchart_uoa import BarchartUOA
import asyncio

async def main():
    client = BarchartUOA()

    # Fetch 2 pages (100 records)
    await client.fetch(max_pages=2)

    # Or fetch everything (~3,000+ records)
    # await client.fetch(max_pages=None)

    # Query
    print(client.top(10))               # Top 10 by Vol/OI
    print(client.by_symbol('AAPL'))     # Filter by ticker

    # Export
    client.to_csv('output.csv')
    client.to_json('output.json')

asyncio.run(main())
```

### Filter GUI

```bash
python filter_gui.py
```

Or open a CSV directly:

```bash
python filter_gui.py data.csv
```

The GUI lets you filter by DTE, strike/price deviation %, option type, volume, open interest, Vol/OI ratio, delta, and symbols — with real-time preview and CSV export.

## Parameters

### `BarchartUOA(headless=True)`

| Param | Type | Default | Description |
|---|---|---|---|
| `headless` | `bool` | `True` | Run browser in headless mode. Set `False` to see the browser window. |

### `fetch()`

| Param | Type | Default | Description |
|---|---|---|---|
| `max_pages` | `int` or `None` | `1` | Pages to fetch (50 records/page). `None` = fetch all. |
| `order_by` | `str` | `volumeOpenInterestRatio` | Sort field: `volume`, `openInterest`, `strikePrice`, etc. |
| `order_dir` | `str` | `desc` | Sort direction: `asc` or `desc`. |

### Query Methods

| Method | Returns | Description |
|---|---|---|
| `client.top(n=10)` | `list[dict]` | Top N by Vol/OI (or `key='volume'` etc.) |
| `client.by_symbol('AAPL')` | `list[dict]` | Filter by ticker |
| `client.to_dicts()` | `list[dict]` | All records with cleaned types |

### Export Methods

| Method | Description |
|---|---|
| `client.to_csv(filepath=None)` | Export CSV (auto-names with timestamp if no path given) |
| `client.to_json(filepath=None)` | Export JSON |

### Attributes

| Attr | Description |
|---|---|
| `client.total` | Total records available on Barchart for current filters |
| `client.data` | Raw API response data (list of dicts) |

## Filter Engine

`option_filter.py` — pure filtering logic, reusable in any context.

```python
from option_filter import OptionFilter

f = OptionFilter('data.csv')
f.dte_min = 7
f.dte_max = 30
f.strike_diff_pct_max = 5    # Strike within 5% of stock price
f.option_type = 'call'
f.volume_min = 1000
result = f.apply()
f.export('filtered.csv')
```

### Filter Params

| Param | Type | Default | Description |
|---|---|---|---|
| `dte_min` / `dte_max` | `int` | `None` | Days to expiration range |
| `strike_diff_pct_max` | `float` | `None` | Max \|strike - price\| / price % |
| `option_type` | `str` | `both` | `'call'`, `'put'`, or `'both'` |
| `volume_min` | `int` | `None` | Min volume |
| `open_interest_min` | `int` | `None` | Min open interest |
| `vol_oi_ratio_min` | `float` | `None` | Min Vol/OI ratio |
| `delta_min` / `delta_max` | `float` | `None` | Delta range |
| `symbols` | `str` | `None` | Comma-separated tickers, e.g. `'AAPL,TSLA'` |

## Output Fields

| Field | Type | Description |
|---|---|---|
| `symbol` | `str` | Ticker (e.g. `AAPL`) |
| `option_symbol` | `str` | Full option contract symbol |
| `option_type` | `str` | `Call` or `Put` |
| `strike` | `float` | Strike price |
| `expiration_date` | `str` | Expiry date (YYYY-MM-DD) |
| `dte` | `int` | Days to expiration |
| `moneyness` | `str` | Distance from strike to underlying (e.g. `-5.2%`) |
| `bid` | `float` | Bid price |
| `last` | `float` | Last traded price |
| `ask` | `float` | Ask price |
| `stock_price` | `float` | Underlying stock price |
| `volume` | `int` | Option trading volume |
| `open_interest` | `int` | Open interest |
| `vol_oi_ratio` | `float` | Volume / Open Interest ratio |
| `implied_volatility` | `str` | Weighted implied volatility |
| `volatility` | `str` | Historical volatility |
| `delta` | `float` | Option delta |
| `trade_time` | `str` | Last trade date (YYYY-MM-DD) |
| `has_options` | `bool` | Whether underlying has options |

## How It Works

The Barchart unusual options page is rendered client-side with AngularJS. Data is loaded via an internal JSON API (`/proxies/core-api/v1/options/get`). This library uses Playwright (headless Chromium) to:

1. Load the page and wait for AngularJS to bootstrap
2. Intercept the API response as the data grid loads
3. Click through hidden pagination links to fetch additional pages

Pure `requests`/`httpx` cannot call the API directly due to browser-level header checks.

## Limitations

- **No sentiment data** — The website shows bullish/bearish labels (green/red strike prices) based on trade execution vs bid/ask, but the API does not expose this.
- **Delayed data** — Options prices are delayed ~25-30 minutes per Barchart.
- **Rate limiting** — Fetching all ~3,000 records takes ~10 minutes. Aggressive scraping may trigger rate limits.
- **Site changes** — If Barchart changes their frontend or API, this library may break.

## License

[PolyForm Noncommercial 1.0.0](LICENSE) — free for personal, educational, and nonprofit use. Commercial use requires prior written permission.

## Disclaimer

This is an **unofficial** client. Not affiliated with or endorsed by Barchart. Use at your own risk. Respect Barchart's terms of service and rate limits.
