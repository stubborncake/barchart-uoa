# Barchart Unusual Options Activity · 非正常期权活动数据抓取

Unofficial Python client for [Barchart.com](https://www.barchart.com/options/unusual-activity/stocks) unusual stock options activity data.

Barchart 非正常期权活动页面的非官方 Python 客户端，抓取后可用图形化界面筛选。

---

## What This Is · 项目简介

Barchart's Unusual Options Activity page tracks options contracts where today's trading volume is significantly higher than open interest — a signal that large players may be positioning. This library scrapes that data so you can analyze it programmatically.

Barchart 的非正常期权活动页面追踪当日成交量远高于持仓量的期权合约——通常意味着有大资金在布局。本项目抓取这些数据供程序化分析。

## Installation · 安装

```bash
pip install playwright
python -m playwright install chromium
```

## Quick Start · 快速开始

### 获取数据

```bash
python barchart_uoa.py
```

Or in your own code · 或用代码调用：

```python
from barchart_uoa import BarchartUOA
import asyncio

async def main():
    client = BarchartUOA()

    # Fetch 2 pages (100 records) · 获取2页（100条）
    await client.fetch(max_pages=2)

    # Or fetch everything (~3,000+ records) · 或获取全部（~3000条）
    # await client.fetch(max_pages=None)

    # Query · 查询
    print(client.top(10))               # Top 10 by Vol/OI
    print(client.by_symbol('AAPL'))     # Filter by ticker · 按代码筛选

    # Export · 导出
    client.to_csv('output.csv')
    client.to_json('output.json')

asyncio.run(main())
```

### 图形化筛选

```bash
python filter_gui.py
```

Or open a CSV directly · 或直接加载 CSV：

```bash
python filter_gui.py data.csv
```

The GUI lets you filter by DTE, strike/price deviation %, option type, volume, open interest, Vol/OI ratio, delta, and symbols — with real-time preview and CSV export.

图形化界面支持按 DTE、行权价偏差百分比、期权类型、成交量、持仓量、Vol/OI、Delta、股票代码筛选，实时预览，支持导出。

## Parameters · 参数

### `BarchartUOA(headless=True)`

| Param | Type | Default | Description |
|---|---|---|---|
| `headless` | `bool` | `True` | Run browser in headless mode. Set `False` to show browser. · 无头模式，False 则显示浏览器 |

### `fetch()`

| Param | Type | Default | Description |
|---|---|---|---|
| `max_pages` | `int` or `None` | `1` | Pages to fetch (50 records/page). `None` = all. · 获取页数，None 为全部 |
| `order_by` | `str` | `volumeOpenInterestRatio` | Sort field · 排序字段 |
| `order_dir` | `str` | `desc` | Sort direction · 排序方向：`asc` / `desc` |

### Query Methods · 查询方法

| Method | Returns | Description |
|---|---|---|
| `client.top(n=10)` | `list[dict]` | Top N by Vol/OI (or `key='volume'` etc.) |
| `client.by_symbol('AAPL')` | `list[dict]` | Filter by ticker · 按代码筛选 |
| `client.to_dicts()` | `list[dict]` | All records with cleaned types · 全部记录 |

### Export Methods · 导出方法

| Method | Description |
|---|---|
| `client.to_csv(filepath=None)` | Export CSV (auto-names with timestamp). · 导出 CSV，不传路径则自动命名 |
| `client.to_json(filepath=None)` | Export JSON · 导出 JSON |

### Attributes · 属性

| Attr | Description |
|---|---|
| `client.total` | Total records available on Barchart. · 平台可用总记录数 |
| `client.data` | Raw API response data (list of dicts). · 原始 API 数据 |

## Filter Engine · 筛选引擎

`option_filter.py` — pure filtering logic, reusable in any context.

纯逻辑筛选引擎，可在任意场景复用。

```python
from option_filter import OptionFilter

f = OptionFilter('data.csv')
f.dte_min = 7
f.dte_max = 30
f.strike_diff_pct_max = 5    # Strike within 5% of stock price · 行权价在股价 5% 以内
f.option_type = 'call'
f.volume_min = 1000
result = f.apply()
f.export('filtered.csv')
```

### Filter Params · 筛选参数

| Param | Type | Default | Description |
|---|---|---|---|
| `dte_min` / `dte_max` | `int` | `None` | Days to expiration range · 到期天数范围 |
| `strike_diff_pct_max` | `float` | `None` | Max |strike - price| / price % · 行权价与股价偏差上限 |
| `option_type` | `str` | `both` | `'call'`, `'put'`, or `'both'` |
| `volume_min` | `int` | `None` | Min volume · 最小成交量 |
| `open_interest_min` | `int` | `None` | Min open interest · 最小持仓量 |
| `vol_oi_ratio_min` | `float` | `None` | Min Vol/OI ratio · 最小 Vol/OI 比 |
| `delta_min` / `delta_max` | `float` | `None` | Delta range · Delta 范围 |
| `symbols` | `str` | `None` | Comma-separated tickers · 逗号分隔股票代码，如 `'AAPL,TSLA'` |

## Output Fields · 输出字段

| Field | Type | Description |
|---|---|---|
| `symbol` | `str` | Ticker (e.g. `AAPL`) · 股票代码 |
| `option_symbol` | `str` | Full option contract symbol · 完整期权代码 |
| `option_type` | `str` | `Call` or `Put` |
| `strike` | `float` | Strike price · 行权价 |
| `expiration_date` | `str` | Expiry date (YYYY-MM-DD) · 到期日 |
| `dte` | `int` | Days to expiration · 距到期天数 |
| `moneyness` | `str` | Distance from strike to underlying (e.g. `-5.2%`) · 实值/虚值程度 |
| `bid` | `float` | Bid price · 买价 |
| `last` | `float` | Last traded price · 最新成交价 |
| `ask` | `float` | Ask price · 卖价 |
| `stock_price` | `float` | Underlying stock price · 正股价格 |
| `volume` | `int` | Option trading volume · 期权成交量 |
| `open_interest` | `int` | Open interest · 持仓量 |
| `vol_oi_ratio` | `float` | Volume / Open Interest ratio · 成交/持仓比 |
| `implied_volatility` | `str` | Weighted implied volatility · 加权隐含波动率 |
| `volatility` | `str` | Historical volatility · 历史波动率 |
| `delta` | `float` | Option delta |
| `trade_time` | `str` | Last trade date (YYYY-MM-DD) · 最后交易日期 |
| `has_options` | `bool` | Whether underlying has options · 正股是否有期权 |

## How It Works · 工作原理

The Barchart unusual options page is rendered client-side with AngularJS. Data is loaded via an internal JSON API (`/proxies/core-api/v1/options/get`). This library uses Playwright (headless Chromium) to:

1. Load the page and wait for AngularJS to bootstrap
2. Intercept the API response as the data grid loads
3. Click through hidden pagination links to fetch additional pages

Pure `requests`/`httpx` cannot call the API directly due to browser-level header checks.

Barchart 的非正常期权页面使用了 AngularJS 客户端渲染，数据通过内部 JSON API 加载。本项目用 Playwright（无头 Chromium）：

1. 加载页面，等待 AngularJS 启动
2. 拦截 API 响应获取数据
3. 绕过隐藏的分页按钮获取所有页面

由于需要浏览器级 header，`requests`/`httpx` 无法直接调用该 API。

## Limitations · 局限性

- **No sentiment data** — The website shows bullish/bearish labels (green/red strike prices) based on trade execution vs bid/ask, but the API does not expose this. · 网站上的看涨/看跌标签 API 不提供。
- **Delayed data** — Options prices are delayed ~25-30 minutes per Barchart. · 数据延迟约 25-30 分钟。
- **Rate limiting** — Fetching all ~3,000 records takes ~10 minutes. Aggressive scraping may trigger rate limits. · 全量获取约需 10 分钟，过于频繁可能触发限流。
- **Site changes** — If Barchart changes their frontend or API, this library may break. · 如 Barchart 调整页面或 API，本项目可能失效。

## License · 许可

[PolyForm Noncommercial 1.0.0](LICENSE) — free for personal, educational, and nonprofit use. Commercial use requires prior written permission.

个人、教育、非营利用途免费。商业用途需事先书面许可。

## Disclaimer · 免责声明

This is an **unofficial** client. Not affiliated with or endorsed by Barchart. Use at your own risk. Respect Barchart's terms of service and rate limits.

本项目为非官方客户端，与 Barchart 无关亦未获其认可。使用风险自负。请遵守 Barchart 服务条款与速率限制。
