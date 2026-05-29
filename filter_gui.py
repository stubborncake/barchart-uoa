"""
Graphical option filter — tkinter UI for OptionFilter.

Usage:
    python filter_gui.py
    python filter_gui.py data.csv
"""
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from option_filter import OptionFilter


class FilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Option Filter')
        self.root.geometry('1200x700')
        self.root.minsize(900, 500)

        self.filter = OptionFilter()
        self._results = []
        self._update_pending = False

        self._build_toolbar()
        self._build_panes()

    # ── toolbar ────────────────────────────────────────────────────────

    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=(8, 6))
        bar.pack(fill='x')

        ttk.Button(bar, text='Load CSV', command=self._load_csv).pack(side='left')
        self._file_label = ttk.Label(bar, text='No file loaded', foreground='gray')
        self._file_label.pack(side='left', padx=(12, 0))

        self._count_label = ttk.Label(bar, text='')
        self._count_label.pack(side='right')

    # ── main panes ─────────────────────────────────────────────────────

    def _build_panes(self):
        pw = ttk.PanedWindow(self.root, orient='horizontal')
        pw.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        # left panel — filters
        left = ttk.Frame(pw, width=320)
        pw.add(left, weight=0)
        self._build_filters(left)

        # right panel — table
        right = ttk.Frame(pw)
        pw.add(right, weight=1)
        self._build_table(right)

        # bottom bar
        bot = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        bot.pack(fill='x')
        ttk.Button(bot, text='Export Filtered CSV', command=self._export).pack(
            side='right')
        self._summary_label = ttk.Label(bot, text='Ready')
        self._summary_label.pack(side='left')

    # ── filter panel ───────────────────────────────────────────────────

    def _build_filters(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        frame = ttk.Frame(canvas)

        frame.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind_all('<MouseWheel>', _on_mousewheel, add='+')

        pad = {'padx': 4, 'pady': 2}
        ipad = {'ipadx': 2, 'ipady': 2}

        row = 0

        # ── DTE ──
        ttk.Label(frame, text='Days to Expiration (DTE)', font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        ttk.Label(frame, text='Min').grid(row=row, column=0, sticky='w', **pad)
        self.dte_min_var = tk.StringVar(value='0')
        self.dte_min_entry = ttk.Entry(frame, textvariable=self.dte_min_var, width=8)
        self.dte_min_entry.grid(row=row, column=1, sticky='e', **pad)
        self._trace(self.dte_min_var)
        row += 1
        ttk.Label(frame, text='Max').grid(row=row, column=0, sticky='w', **pad)
        self.dte_max_var = tk.StringVar(value='100')
        self.dte_max_entry = ttk.Entry(frame, textvariable=self.dte_max_var, width=8)
        self.dte_max_entry.grid(row=row, column=1, sticky='e', **pad)
        self._trace(self.dte_max_var)
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=6)
        row += 1

        # ── strike diff % ──
        ttk.Label(frame, text='Strike vs Stock Price', font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        ttk.Label(frame, text='Max deviation %').grid(row=row, column=0, sticky='w', **pad)
        self.strike_diff_var = tk.StringVar(value='')
        self.strike_diff_entry = ttk.Entry(frame, textvariable=self.strike_diff_var, width=8)
        self.strike_diff_entry.grid(row=row, column=1, sticky='e', **pad)
        self._trace(self.strike_diff_var)
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=6)
        row += 1

        # ── option type ──
        ttk.Label(frame, text='Option Type', font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        self.type_var = tk.StringVar(value='both')
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=row, column=0, columnspan=2, sticky='w', **pad)
        ttk.Radiobutton(type_frame, text='Both', variable=self.type_var,
                        value='both', command=self._schedule_update).pack(side='left')
        ttk.Radiobutton(type_frame, text='Call', variable=self.type_var,
                        value='call', command=self._schedule_update).pack(side='left')
        ttk.Radiobutton(type_frame, text='Put', variable=self.type_var,
                        value='put', command=self._schedule_update).pack(side='left')
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=6)
        row += 1

        # ── volume ──
        ttk.Label(frame, text='Volume', font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        ttk.Label(frame, text='Min').grid(row=row, column=0, sticky='w', **pad)
        self.vol_min_var = tk.StringVar(value='')
        ttk.Entry(frame, textvariable=self.vol_min_var, width=8).grid(
            row=row, column=1, sticky='e', **pad)
        self._trace(self.vol_min_var)
        row += 1

        # ── open interest ──
        ttk.Label(frame, text='Open Interest', font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        ttk.Label(frame, text='Min').grid(row=row, column=0, sticky='w', **pad)
        self.oi_min_var = tk.StringVar(value='')
        ttk.Entry(frame, textvariable=self.oi_min_var, width=8).grid(
            row=row, column=1, sticky='e', **pad)
        self._trace(self.oi_min_var)
        row += 1

        # ── Vol/OI ratio ──
        ttk.Label(frame, text='Vol / OI Ratio', font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        ttk.Label(frame, text='Min').grid(row=row, column=0, sticky='w', **pad)
        self.vol_oi_min_var = tk.StringVar(value='')
        ttk.Entry(frame, textvariable=self.vol_oi_min_var, width=8).grid(
            row=row, column=1, sticky='e', **pad)
        self._trace(self.vol_oi_min_var)
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=6)
        row += 1

        # ── delta ──
        ttk.Label(frame, text='Delta', font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        ttk.Label(frame, text='Min').grid(row=row, column=0, sticky='w', **pad)
        self.delta_min_var = tk.StringVar(value='')
        ttk.Entry(frame, textvariable=self.delta_min_var, width=8).grid(
            row=row, column=1, sticky='e', **pad)
        self._trace(self.delta_min_var)
        row += 1
        ttk.Label(frame, text='Max').grid(row=row, column=0, sticky='w', **pad)
        self.delta_max_var = tk.StringVar(value='')
        ttk.Entry(frame, textvariable=self.delta_max_var, width=8).grid(
            row=row, column=1, sticky='e', **pad)
        self._trace(self.delta_max_var)
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=6)
        row += 1

        # ── symbols ──
        ttk.Label(frame, text='Symbols', font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        ttk.Label(frame, text='Comma-separated (e.g. AAPL,TSLA)',
                  foreground='gray').grid(row=row, column=0, columnspan=2, sticky='w', **pad)
        row += 1
        self.symbols_var = tk.StringVar(value='')
        ttk.Entry(frame, textvariable=self.symbols_var, width=24).grid(
            row=row, column=0, columnspan=2, sticky='ew', **pad)
        self._trace(self.symbols_var)

        # spacer
        row += 1
        ttk.Label(frame, text='').grid(row=row, column=0, **pad)  # bottom spacer

    # ── table ──────────────────────────────────────────────────────────

    def _build_table(self, parent):
        columns = ('symbol', 'type', 'strike', 'price', 'strike_diff%',
                   'dte', 'expiry', 'vol', 'OI', 'vol/OI', 'delta', 'last')
        self._tree = ttk.Treeview(parent, columns=columns, show='headings',
                                  selectmode='browse')

        headers = {
            'symbol': 'Sym', 'type': 'Type', 'strike': 'Strike',
            'price': 'Price', 'strike_diff%': 'Diff%',
            'dte': 'DTE', 'expiry': 'Expiry', 'vol': 'Volume',
            'OI': 'OI', 'vol/OI': 'Vol/OI', 'delta': 'Delta',
            'last': 'Last',
        }
        widths = {
            'symbol': 70, 'type': 50, 'strike': 75, 'price': 75,
            'strike_diff%': 60, 'dte': 50, 'expiry': 90, 'vol': 70,
            'OI': 70, 'vol/OI': 60, 'delta': 60, 'last': 70,
        }

        for col in columns:
            self._tree.heading(col, text=headers.get(col, col),
                               command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=widths.get(col, 80), anchor='center',
                              minwidth=40)

        scroll_v = ttk.Scrollbar(parent, orient='vertical', command=self._tree.yview)
        scroll_h = ttk.Scrollbar(parent, orient='horizontal', command=self._tree.xview)
        self._tree.configure(yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)

        self._tree.pack(side='left', fill='both', expand=True)
        scroll_v.pack(side='right', fill='y')
        scroll_h.pack(side='bottom', fill='x')

        self._tree.tag_configure('call', foreground='#0a0')
        self._tree.tag_configure('put', foreground='#c00')

        self._sort_col = None
        self._sort_rev = False

    # ── actions ────────────────────────────────────────────────────────

    def _load_csv(self):
        path = filedialog.askopenfilename(
            title='Open CSV',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
        )
        if not path:
            return

        try:
            self.filter.load(path)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load CSV:\n{e}')
            return

        self._file_label.config(text=path, foreground='black')

        # detect max DTE and set reasonable defaults
        max_dte = max((r.get('dte', 0) for r in self.filter._records), default=0)
        self.dte_max_var.set(str(max_dte))

        self._apply_and_show()

    def _apply_and_show(self):
        self._read_params()
        self._results = self.filter.apply()
        self._refresh_table()
        self._count_label.config(
            text=f'{self.filter.count:,} / {self.filter.total:,} records')
        self._summary_label.config(text=self.filter.summary)

    def _refresh_table(self):
        tree = self._tree
        for item in tree.get_children():
            tree.delete(item)

        for r in self._results:
            sym = r.get('symbol', '')
            otype = r.get('option_type', '').lower()
            tag = 'call' if otype == 'call' else ('put' if otype == 'put' else '')
            tree.insert('', 'end', values=(
                sym,
                otype.upper(),
                f'{r.get("strike", 0):.2f}',
                f'{r.get("stock_price", 0):.2f}',
                f'{r.get("strike_diff_pct", 0):.1f}%',
                r.get('dte', ''),
                r.get('expiration_date', ''),
                f'{r.get("volume", 0):,}',
                f'{r.get("open_interest", 0):,}',
                f'{r.get("vol_oi_ratio", 0):.1f}',
                f'{r.get("delta", 0):.4f}',
                f'{r.get("last", 0):.2f}',
            ), tags=(tag,))

    def _read_params(self):
        f = self.filter
        f.dte_min = self._int_or_none(self.dte_min_var.get())
        f.dte_max = self._int_or_none(self.dte_max_var.get())
        f.strike_diff_pct_max = self._float_or_none(self.strike_diff_var.get())
        f.option_type = self.type_var.get()
        f.volume_min = self._int_or_none(self.vol_min_var.get())
        f.open_interest_min = self._int_or_none(self.oi_min_var.get())
        f.vol_oi_ratio_min = self._float_or_none(self.vol_oi_min_var.get())
        f.delta_min = self._float_or_none(self.delta_min_var.get())
        f.delta_max = self._float_or_none(self.delta_max_var.get())
        f.symbols = self.symbols_var.get().strip() or None

    def _export(self):
        if not self._results:
            messagebox.showinfo('Export', 'No data to export.')
            return
        path = filedialog.asksaveasfilename(
            title='Export CSV',
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')],
        )
        if path:
            self.filter.export(path)
            messagebox.showinfo('Export', f'Exported {len(self._results)} records to\n{path}')

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False

        key_map = {
            'symbol': 'symbol', 'type': 'option_type', 'strike': 'strike',
            'price': 'stock_price', 'strike_diff%': 'strike_diff_pct',
            'dte': 'dte', 'expiry': 'expiration_date', 'vol': 'volume',
            'OI': 'open_interest', 'vol/OI': 'vol_oi_ratio',
            'delta': 'delta', 'last': 'last',
        }
        key = key_map.get(col, col)
        self._results.sort(key=lambda r: r.get(key, 0) or 0,
                           reverse=self._sort_rev)
        self._refresh_table()

        # update sort arrow in header
        arrow = '▼' if self._sort_rev else '▲'
        for c in self._tree['columns']:
            h = self._tree.heading(c).get('text', '')
            h = h.rstrip(' ▼▲')
            if c == col:
                h += f' {arrow}'
            self._tree.heading(c, text=h)

    # ── helpers ────────────────────────────────────────────────────────

    def _trace(self, var):
        var.trace_add('write', lambda *_: self._schedule_update())

    def _schedule_update(self):
        if self._update_pending:
            return
        self._update_pending = True
        self.root.after(150, self._do_update)

    def _do_update(self):
        self._update_pending = False
        if self.filter._records:
            self._apply_and_show()

    @staticmethod
    def _int_or_none(s):
        s = s.strip()
        return int(s) if s else None

    @staticmethod
    def _float_or_none(s):
        s = s.strip()
        if s:
            return float(s.replace(',', ''))
        return None


# ── entry ──────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app = FilterApp(root)

    if len(sys.argv) > 1:
        try:
            app.filter.load(sys.argv[1])
            app._file_label.config(text=sys.argv[1], foreground='black')
            app._apply_and_show()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load:\n{e}')

    root.mainloop()


if __name__ == '__main__':
    main()
