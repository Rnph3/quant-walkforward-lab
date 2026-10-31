# Quant Walk-Forward Lab | historical research / no live trading

**Claim:** This is a reproducible **historical** walk-forward evaluation harness, not a validated alpha strategy, broker implementation, or live BTC backtest.

## Why it exists

A backtest showing profit can be misleading when its parameters were selected using future observations. This repository demonstrates explicit chronological training-only tuning; non-overlapping out-of-sample (OOS) windows; one-bar-delayed execution signal; simplified turnover costs; and independently reset fold reporting.

## Demonstration data

Bundled: 105 weekly normalized *equity* price observations for AAPL, GOOG, AMZN, FB, NFLX, MSFT (2018–2019), from `plotly.express.data.stocks()`. This is not crypto or OHLCV data, so no claim about crypto trading performance is warranted. See `DATA_PROVENANCE.md`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m quantlab.run
python -m pytest -q
```

Outputs: `artifacts/results.json`, `artifacts/RESEARCH_NOTE.md`, `artifacts/oos_predictions_and_returns.csv`, `artifacts/oos_equity.png`.

## Experiment definition

- Four moving-average candidates: fast/slow 3/8, 4/12, 6/18, 8/24 (observation units = weeks for supplied data).
- At each fold, tune exclusively on data before the OOS test. Use net in-sample Sharpe as the selection score.
- Signal computed with closing-price data at `t-2`; exposure to return from `t-1` to `t`. This imposes an extra delay and an idealized trade at `t-1` close.
- Long/flat only; costs deducted on absolute position changes at 10 bps per side by default; benchmark also pays an entry cost on each independent fold.
- Fold partitions: 48 expanding training observations, 18 OOS observations, three disjoint folds. Each fold starts flat. Combining fold returns is an **evaluation convention**, not a continuous historical account statement.
- The strategy is *not* funded or deployed. No margin, order-book impact, short, funding, volatility-targeting, taxes, dividends, corporate actions, or broker execution are modeled.

## Changing data / costs

```bash
python -m quantlab.run --column MSFT --cost-bps 25
python -m quantlab.run --input data/your_closes.csv --column close --train 400 --test 150 --periods-per-year 8760
```

Input CSV: `date,close` with strictly increasing UTC-parseable times and positive prices. The example candidate grid is NOT optimized for hourly BTC; changing time frequency demands separately justified lookback choices.

### Optional public Binance SPOT importer

```bash
python -m quantlab.run --download-binance-month 2025-01 --binance-symbol BTCUSDT --binance-interval 1h
```

This invokes network access **only on explicit request** and writes `artifacts/BTCUSDT_1h_2025-01.csv`. A single-month download is *not sufficient for robust strategy inference*; accumulate many months and redesign train/test and candidate grid. Real downloader was **not** exercised in this sandbox (no internet access). Timestamp microseconds are supported. Spot data should never be represented as perpetual funding or futures execution data.

## What was tested

See `tests/test_engine.py` for lag, train-only selection under future modification, fold uniqueness, costs, sample source, errors, and Binance microsecond parsing. These tests demonstrate code behavior, **not alpha validity**.

## Learning and presentation

- `docs/KO_BEGINNER_TO_INTERVIEW.md` — Korean beginner-to-interview handbook.
- `publishing/MEDIUM_EN.md`, `publishing/X_POST_EN.md` — factual post drafts with result numbers from artifacts (review before posting).
- `artifacts/RESEARCH_NOTE.md` — generated output.

## References

- Plotly sample prices: https://plotly.com/python-api-reference/generated/plotly.express.data.html
- Binance public data documentation: https://github.com/binance/binance-public-data
- General methodological caution: OOS performance cannot erase strategy-selection bias, unrealistic execution or small sample effects.

## License

MIT for original code; third-party sample data rights remain with original sources. Copyright notice in LICENSE should be reviewed by the repository owner before publishing.
