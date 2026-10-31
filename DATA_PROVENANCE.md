# Data provenance and licensing

The default 105-row `data/plotly_stocks_weekly_2018_2019.csv` was exported from
`plotly.express.data.stocks()` installed in the build environment on 2026-10-31.
Source docs: https://plotly.com/python-api-reference/generated/plotly.express.data.html
and Plotly's package: https://github.com/plotly/plotly.py.

**Important:** Plotly states the sample contains **normalized weekly 2018–2019 prices for six US stocks**, not the exact tradeable share prices (and not OHLC or adjusted returns). It is historical illustrative data; no forward-looking or live trading inference is appropriate. The CSV belongs to the underlying source/rights holders. This project's MIT license governs original project code, not third-party rights.

Optional live download uses Binance's public SPOT monthly ZIP structure, but **no Binance data was downloaded as part of the offline build**: https://github.com/binance/binance-public-data. Binance's January 2025 onward SPOT kline timestamps use microseconds, earlier files milliseconds. See `quantlab/binance.py`.
