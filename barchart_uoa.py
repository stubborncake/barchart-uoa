"""
Unofficial Barchart Unusual Options Activity client.

Uses Playwright headless browser to load the page and capture the internal
API response that the AngularJS frontend uses.

    pip install playwright
    python -m playwright install chromium

Source: https://www.barchart.com/options/unusual-activity/stocks
Internal API: /proxies/core-api/v1/options/get
"""
import asyncio
import csv
import json
from datetime import datetime
from playwright.async_api import async_playwright


class BarchartUOA:
    """Fetch unusual options activity data from Barchart.

    Usage:
        client = BarchartUOA()
        await client.fetch(max_pages=10)       # fetch up to 10 pages (500 records)
        await client.fetch(max_pages=None)      # fetch ALL pages (~3143 records)
        records = client.to_dicts()
        client.to_csv('output.csv')
        client.top(10)                          # top 10 by Vol/OI
        client.by_symbol('AAPL')               # filter by ticker
    """

    BASE_URL = 'https://www.barchart.com/options/unusual-activity/stocks'
    API_PATH = '/proxies/core-api/v1/options/get'

    def __init__(self, headless=True):
        self.headless = headless
        self.data = []
        self.total = 0

    # ── main fetch ──────────────────────────────────────────────────────

    async def fetch(self, max_pages=1, order_by='volumeOpenInterestRatio',
                    order_dir='desc'):
        """Fetch unusual options activity.

        Args:
            max_pages: Number of pages (50 records/page). None = all pages.
            order_by: volumeOpenInterestRatio, volume, openInterest, etc.
            order_dir: asc or desc

        Returns:
            List of raw data dicts from the API.
        """
        captured = []
        seen_symbols = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/131.0.0.0 Safari/537.36'
                )
            )
            page = await context.new_page()

            async def on_response(response):
                if self.API_PATH in response.url:
                    try:
                        body = await response.json()
                        captured.append(body)
                    except Exception:
                        pass

            page.on('response', on_response)

            # Load page 1
            url = f'{self.BASE_URL}?orderBy={order_by}&orderDir={order_dir}'
            await page.goto(url, wait_until='networkidle', timeout=90000)
            await self._wait_for(captured, 20)
            if captured:
                self._merge(captured[-1], seen_symbols)

            # Paginate through remaining pages
            total = self.total
            if total and not max_pages:
                max_pages = (total // 50) + 1

            for pg in range(2, (max_pages or 2) + 1):
                if pg > 100:
                    break  # safety limit
                print(f'  Fetching page {pg}/{max_pages}...')

                ok = await self._click_next(page)
                if not ok:
                    print(f'  (no more pages)')
                    break

                await self._wait_for_new(captured, len(captured), 15)
                if len(captured) > pg - 1:
                    self._merge(captured[-1], seen_symbols)

                if len(self.data) >= self.total:
                    break

            await browser.close()

        return self.data

    # ── helpers ─────────────────────────────────────────────────────────

    def _merge(self, response, seen):
        """Merge a page of data, deduping by symbol."""
        for item in response.get('data', []):
            sym = item.get('symbol', '')
            if sym not in seen:
                seen.add(sym)
                self.data.append(item)
        self.total = response.get('total', self.total)

    async def _wait_for(self, captured, seconds):
        for _ in range(seconds):
            if captured:
                return True
            await asyncio.sleep(0.5)
        return False

    async def _wait_for_new(self, captured, prev_count, seconds):
        for _ in range(seconds):
            if len(captured) > prev_count:
                return True
            await asyncio.sleep(0.5)
        return False

    async def _click_next(self, page):
        """Click hidden 'next page' link via JS dispatchEvent."""
        try:
            result = await page.evaluate('''() => {
                const ctrls = document.querySelector('.pagination-controls');
                if (ctrls) ctrls.classList.remove('ng-hide');
                const next = document.querySelector('.pagination-controls a.next');
                if (!next || next.classList.contains('ng-hide')) return false;
                next.style.display = 'inline-block';
                next.dispatchEvent(new MouseEvent('click', {
                    bubbles: true, cancelable: true, view: window
                }));
                return true;
            }''')
            return bool(result)
        except Exception:
            return False

    # ── data conversion ─────────────────────────────────────────────────

    def to_dicts(self):
        """Convert raw API data to list of dicts with clean types."""
        results = []
        for item in self.data:
            results.append({
                'symbol': item.get('baseSymbol', ''),
                'option_symbol': item.get('symbol', ''),
                'option_type': item.get('symbolType', ''),
                'strike': self._float(item.get('strikePrice', 0)),
                'expiration_date': self._parse_date(item.get('expirationDate', '')),
                'dte': int(item.get('daysToExpiration', 0)),
                'moneyness': item.get('moneyness', ''),
                'bid': self._float(item.get('bidPrice', 0)),
                'last': self._float(item.get('lastPrice', 0)),
                'ask': self._float(item.get('askPrice', 0)),
                'stock_price': self._float(item.get('baseLastPrice', 0)),
                'volume': self._int(item.get('volume', '0')),
                'open_interest': self._int(item.get('openInterest', '0')),
                'vol_oi_ratio': self._float(item.get('volumeOpenInterestRatio', 0)),
                'implied_volatility': item.get('weightedImpliedVolatility', ''),
                'volatility': item.get('volatility', ''),
                'delta': self._float(item.get('delta', 0)),
                'trade_time': self._parse_date(item.get('tradeTime', '')),
                'has_options': item.get('hasOptions', False),
            })
        return results

    def top(self, n=10, key='vol_oi_ratio'):
        records = self.to_dicts()
        return sorted(records, key=lambda x: x.get(key, 0) or 0, reverse=True)[:n]

    def by_symbol(self, ticker):
        records = self.to_dicts()
        return [r for r in records if r['symbol'].upper() == ticker.upper()]

    def to_csv(self, filepath=None):
        records = self.to_dicts()
        if not filepath:
            filepath = f'barchart_uoa_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        if records:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
        return filepath

    def to_json(self, filepath=None):
        records = self.to_dicts()
        if not filepath:
            filepath = f'barchart_uoa_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filepath, 'w') as f:
            json.dump(records, f, indent=2)
        return filepath

    # ── static helpers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_date(val):
        if not val or '/' not in str(val):
            return val
        try:
            parts = str(val).split('/')
            if len(parts) == 3:
                month, day, year = parts
                year = int(year)
                if year < 100:
                    year += 2000
                return f'{year:04d}-{int(month):02d}-{int(day):02d}'
        except (ValueError, TypeError):
            pass
        return val

    @staticmethod
    def _float(val):
        try:
            return float(str(val).replace(',', '').replace('%', ''))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _int(val):
        try:
            return int(str(val).replace(',', ''))
        except (ValueError, TypeError):
            return 0


# ── demo ─────────────────────────────────────────────────────────────────

async def demo():
    client = BarchartUOA()
    await client.fetch(max_pages=2)  # fetch 2 pages = 100 records

    records = client.to_dicts()
    print(f'Barchart Unusual Stock Options Activity')
    print(f'Fetched: {len(client.data)} | Total available: {client.total}')
    print()

    top20 = client.top(20)
    print(f'{"#":<3} {"Sym":<6} {"Type":<5} {"Strike":>8} {"Expiry":<12} {"DTE":>4} '
          f'{"Bid":>7} {"Ask":>7} {"Last":>7} {"Volume":>8} {"OI":>6} {"Vol/OI":>8} '
          f'{"IV":>7} {"Delta":>7}')
    print('-' * 115)
    for i, r in enumerate(top20, 1):
        print(f'{i:<3} {r["symbol"]:<6} {r["option_type"]:<5} {r["strike"]:>8.2f} '
              f'{r["expiration_date"]:<12} {r["dte"]:>4} '
              f'{r["bid"]:>7.2f} {r["ask"]:>7.2f} {r["last"]:>7.2f} '
              f'{r["volume"]:>8,} {r["open_interest"]:>6,} '
              f'{r["vol_oi_ratio"]:>8.1f} {r["implied_volatility"]:>7} '
              f'{r["delta"]:>7.4f}')

    csv_path = client.to_csv()
    print(f'\nExported to: {csv_path}')
    return records


if __name__ == '__main__':
    asyncio.run(demo())
