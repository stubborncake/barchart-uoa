"""
Option filter engine — pure logic, no UI dependency.

Usage:
    f = OptionFilter('data.csv')
    f.dte_min = 7
    f.dte_max = 30
    f.strike_diff_pct_max = 5
    result = f.apply()
    f.export('filtered.csv')
"""
import csv


class OptionFilter:
    """Filter unusual options data by multiple criteria."""

    def __init__(self, csv_path=None):
        self._records = []
        self._filtered = []

        # All filter params with defaults (None = no filter)
        self.dte_min = None
        self.dte_max = None
        self.strike_diff_pct_max = None  # |strike - price| / price * 100
        self.option_type = 'both'        # 'call', 'put', 'both'
        self.volume_min = None
        self.open_interest_min = None
        self.vol_oi_ratio_min = None
        self.delta_min = None
        self.delta_max = None
        self.symbols = None              # comma-separated string, e.g. 'AAPL,TSLA'

        if csv_path:
            self.load(csv_path)

    # ── load / export ──────────────────────────────────────────────────

    def load(self, csv_path):
        self._records = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                # convert numeric fields from strings
                row['dte'] = self._int(row.get('dte'))
                row['strike'] = self._float(row.get('strike'))
                row['stock_price'] = self._float(row.get('stock_price'))
                row['volume'] = self._int(row.get('volume'))
                row['open_interest'] = self._int(row.get('open_interest'))
                row['vol_oi_ratio'] = self._float(row.get('vol_oi_ratio'))
                row['delta'] = self._float(row.get('delta'))
                row['bid'] = self._float(row.get('bid'))
                row['ask'] = self._float(row.get('ask'))
                row['last'] = self._float(row.get('last'))

                # compute derived field
                price = row['stock_price']
                row['strike_diff_pct'] = self._calc_diff_pct(
                    row['strike'], price
                )

                self._records.append(row)
        self._filtered = list(self._records)
        return self

    def export(self, filepath=None):
        if not filepath:
            filepath = 'filtered_options.csv'
        out = self._filtered
        fields = [k for k in out[0].keys() if k != 'strike_diff_pct'] if out else []
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(out)
        return filepath

    # ── apply filters ──────────────────────────────────────────────────

    def apply(self):
        result = list(self._records)

        result = [r for r in result if self._check_type(r)]
        result = [r for r in result if self._check_dte(r)]
        result = [r for r in result if self._check_strike_diff(r)]
        result = [r for r in result if self._check_volume(r)]
        result = [r for r in result if self._check_oi(r)]
        result = [r for r in result if self._check_vol_oi(r)]
        result = [r for r in result if self._check_delta(r)]
        result = [r for r in result if self._check_symbols(r)]

        self._filtered = result
        return result

    # ── individual checks ──────────────────────────────────────────────

    def _check_type(self, r):
        if self.option_type == 'both':
            return True
        return r.get('option_type', '').lower() == self.option_type.lower()

    def _check_dte(self, r):
        dte = r.get('dte')
        if dte is None:
            return True
        if self.dte_min is not None and dte < self.dte_min:
            return False
        if self.dte_max is not None and dte > self.dte_max:
            return False
        return True

    def _check_strike_diff(self, r):
        if self.strike_diff_pct_max is None:
            return True
        return r.get('strike_diff_pct', 999) <= self.strike_diff_pct_max

    def _check_volume(self, r):
        if self.volume_min is None:
            return True
        return r.get('volume', 0) >= self.volume_min

    def _check_oi(self, r):
        if self.open_interest_min is None:
            return True
        return r.get('open_interest', 0) >= self.open_interest_min

    def _check_vol_oi(self, r):
        if self.vol_oi_ratio_min is None:
            return True
        return r.get('vol_oi_ratio', 0) >= self.vol_oi_ratio_min

    def _check_delta(self, r):
        d = r.get('delta')
        if d is None:
            return True
        if self.delta_min is not None and d < self.delta_min:
            return False
        if self.delta_max is not None and d > self.delta_max:
            return False
        return True

    def _check_symbols(self, r):
        if not self.symbols:
            return True
        wanted = {s.strip().upper() for s in self.symbols.split(',') if s.strip()}
        return r.get('symbol', '').upper() in wanted

    # ── stats ──────────────────────────────────────────────────────────

    @property
    def count(self):
        return len(self._filtered)

    @property
    def total(self):
        return len(self._records)

    @property
    def summary(self):
        return (
            f'Filtered {self.count} / {self.total} records'
            f' ({self.count / self.total * 100:.1f}%)'
            if self.total else 'No data loaded'
        )

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _calc_diff_pct(strike, price):
        if not price or price == 0:
            return 999
        return abs(strike - price) / price * 100

    @staticmethod
    def _int(val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _float(val):
        try:
            return float(str(val).replace(',', '').replace('%', ''))
        except (ValueError, TypeError):
            return 0.0
