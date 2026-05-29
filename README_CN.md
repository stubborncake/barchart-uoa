# Barchart 非正常期权活动数据抓取

[Barchart.com](https://www.barchart.com/options/unusual-activity/stocks) 非正常期权活动页面的非官方 Python 客户端。抓取数据后可搭配图形化界面筛选。

[English](README.md)

---

## 项目简介

Barchart 的非正常期权活动页面追踪当日成交量远高于持仓量的期权合约——通常意味着有大资金在布局。本项目抓取这些数据供程序化分析。

## 一分钟跑起来

从零到筛选结果，三条命令。

```bash
# 1. 安装
pip install playwright
python -m playwright install chromium

# 2. 抓数据
python barchart_uoa.py
# → 生成 barchart_uoa_20260529_xxxxxx.csv

# 3. 打开筛选器
python filter_gui.py
# → 点 Load CSV 选刚生成的文件 → 调参数 → Export 导出
```

后续全部在图形界面里操作，不用写代码。支持按 DTE、行权价偏差、期权类型、成交量、持仓量、Delta 等条件筛选。

## 快速开始

### 获取数据

```bash
python barchart_uoa.py
```

或用代码调用：

```python
from barchart_uoa import BarchartUOA
import asyncio

async def main():
    client = BarchartUOA()

    # 获取2页（100条）
    await client.fetch(max_pages=2)

    # 或获取全部（~3000条）
    # await client.fetch(max_pages=None)

    # 查询
    print(client.top(10))               # 按 Vol/OI 排序前10
    print(client.by_symbol('AAPL'))     # 按股票代码筛选

    # 导出
    client.to_csv('output.csv')
    client.to_json('output.json')

asyncio.run(main())
```

### 图形化筛选

```bash
python filter_gui.py
```

或直接加载 CSV：

```bash
python filter_gui.py data.csv
```

图形化界面支持按 DTE、行权价偏差百分比、期权类型、成交量、持仓量、Vol/OI、Delta、股票代码筛选，实时预览，支持导出 CSV。

## 参数

### `BarchartUOA(headless=True)`

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `headless` | `bool` | `True` | 无头模式，设为 `False` 可显示浏览器窗口 |

### `fetch()`

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `max_pages` | `int` 或 `None` | `1` | 获取页数（每页50条），`None` 为全部 |
| `order_by` | `str` | `volumeOpenInterestRatio` | 排序字段：`volume`、`openInterest`、`strikePrice` 等 |
| `order_dir` | `str` | `desc` | 排序方向：`asc` / `desc` |

### 查询方法

| 方法 | 返回值 | 说明 |
|---|---|---|
| `client.top(n=10)` | `list[dict]` | 按 Vol/OI 排序的前 N 条（可指定 `key='volume'`） |
| `client.by_symbol('AAPL')` | `list[dict]` | 按股票代码筛选 |
| `client.to_dicts()` | `list[dict]` | 全部记录（类型已清洗） |

### 导出方法

| 方法 | 说明 |
|---|---|
| `client.to_csv(filepath=None)` | 导出 CSV，不传路径则自动以时间戳命名 |
| `client.to_json(filepath=None)` | 导出 JSON |

### 属性

| 属性 | 说明 |
|---|---|
| `client.total` | 平台当前可用总记录数 |
| `client.data` | 原始 API 返回数据（list[dict]） |

## 筛选引擎

`option_filter.py` — 纯逻辑筛选引擎，可在任意场景复用。

```python
from option_filter import OptionFilter

f = OptionFilter('data.csv')
f.dte_min = 7
f.dte_max = 30
f.strike_diff_pct_max = 5    # 行权价在股价 5% 以内
f.option_type = 'call'
f.volume_min = 1000
result = f.apply()
f.export('filtered.csv')
```

### 筛选参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `dte_min` / `dte_max` | `int` | `None` | 到期天数范围 |
| `strike_diff_pct_max` | `float` | `None` | 行权价与股价最大偏差百分比 |
| `option_type` | `str` | `both` | `'call'`、`'put'` 或 `'both'` |
| `volume_min` | `int` | `None` | 最小成交量 |
| `open_interest_min` | `int` | `None` | 最小持仓量 |
| `vol_oi_ratio_min` | `float` | `None` | 最小 Vol/OI 比 |
| `delta_min` / `delta_max` | `float` | `None` | Delta 范围 |
| `symbols` | `str` | `None` | 逗号分隔股票代码，如 `'AAPL,TSLA'` |

## 输出字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `symbol` | `str` | 股票代码（如 `AAPL`） |
| `option_symbol` | `str` | 完整期权代码 |
| `option_type` | `str` | `Call` 或 `Put` |
| `strike` | `float` | 行权价 |
| `expiration_date` | `str` | 到期日（YYYY-MM-DD） |
| `dte` | `int` | 距到期天数 |
| `moneyness` | `str` | 实值/虚值程度（如 `-5.2%`） |
| `bid` | `float` | 买价 |
| `last` | `float` | 最新成交价 |
| `ask` | `float` | 卖价 |
| `stock_price` | `float` | 正股价格 |
| `volume` | `int` | 期权成交量 |
| `open_interest` | `int` | 持仓量 |
| `vol_oi_ratio` | `float` | 成交/持仓比 |
| `implied_volatility` | `str` | 加权隐含波动率 |
| `volatility` | `str` | 历史波动率 |
| `delta` | `float` | 期权 Delta |
| `trade_time` | `str` | 最后交易日期（YYYY-MM-DD） |
| `has_options` | `bool` | 正股是否有期权 |

## 工作原理

Barchart 的非正常期权页面使用 AngularJS 客户端渲染，数据通过内部 JSON API（`/proxies/core-api/v1/options/get`）加载。本项目用 Playwright（无头 Chromium）：

1. 加载页面，等待 AngularJS 启动
2. 拦截 API 响应获取数据
3. 绕过隐藏的分页按钮获取所有页面

由于需要浏览器级 header 检查，`requests`/`httpx` 无法直接调用该 API。

## 局限性

- **无情绪标签** — 网站上的看涨/看跌颜色标记（绿色/红色行权价）API 不提供。
- **数据延迟** — 期权价格延迟约 25-30 分钟。
- **速率限制** — 全量获取约需 10 分钟，过于频繁请求可能触发限流。
- **页面变更** — 如 Barchart 调整前端或 API，本项目可能失效。

## 许可协议

[PolyForm Noncommercial 1.0.0](LICENSE) — 个人、教育、非营利用途免费。商业用途需事先书面许可。

## 免责声明

本项目为非官方客户端，与 Barchart 无关亦未获其认可。使用风险自负。请遵守 Barchart 服务条款与速率限制。
