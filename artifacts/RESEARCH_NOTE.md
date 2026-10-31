# Walk-forward research result — AAPL

**HISTORICAL STUDY / NO LIVE TRADING / NOT FINANCIAL ADVICE**

- Source: Plotly example normalized weekly equity prices (2018–2019).
- Observations: 105 (2018-01-01 to 2019-12-30).
- Expanding train: 48 initial rows, OOS test window: 18 rows.
- Candidate grid: [{'fast': 3, 'slow': 8}, {'fast': 4, 'slow': 12}, {'fast': 6, 'slow': 18}, {'fast': 8, 'slow': 24}]. Selection uses training history only.
- Trading assumption: signal known at t−2, rebalance at t−1 close, earn price[t−1]→price[t] return.
- All folds separately reset flat; round trip incurs entry and exit costs when present.
- Approximate one-way fees + slippage: 10.0 bps per unit turnover.

| Metric | Strategy OOS | Buy & hold OOS (fold reset) |
|---|---:|---:|
| Total growth - 1 | 49.58% | 53.61% |
| Max drawdown | -17.32% | -17.32% |
| Ann. Sharpe (risk-free=0) | 2.14 | 1.84 |

## Fold selection (training-only)

| Fold | OOS start | OOS end | Selected fast/slow | Train Sharpe |
|---|---|---|---|---:|
| 1 | 2018-12-03 | 2019-04-01 | 4/12 | 1.00 |
| 2 | 2019-04-08 | 2019-08-05 | 4/12 | 1.51 |
| 3 | 2019-08-12 | 2019-12-09 | 4/12 | 0.86 |

## Limits

- Sample data covers 2018-2019 weekly, normalized equity prices, not BTC futures
- Point-in-time OHLCV, corporate actions, bid-ask spread and volume not modeled
- Historical example and small grid, not a tradable or statistically validated alpha
- Sharpe ignores risk-free rate; cost is simplified one-way turnover approximation
- Each OOS fold starts flat and benchmark also pays an entry cost per fold

**Interpretation:** This is an educational stress test of a fixed candidate grid, not evidence of market-beating skill. Returns are from a small, old normalized equity dataset; no claim about BTC.
