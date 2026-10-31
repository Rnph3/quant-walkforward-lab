# A Walk-Forward Backtest That Didn't Beat Its Benchmark — and Why I Still Built It

*Reproducibility, chronological parameter selection, execution delays, and cost assumptions in a small historical Python research kit.*

A profitable-looking backtest does not necessarily demonstrate trading skill. A parameter can look excellent because it was selected with information that would not have been known at the time.

I built **Quant Walk-Forward Lab** to make this problem concrete. The project evaluates a long/flat moving-average rule with four predefined parameter pairs and a simple expanding walk-forward selection protocol. The objective is not to sell a signal. It is to make evaluation assumptions inspectable.

## What I implemented

The code separates price validation, moving-average signals, an execution delay, turnover costs, chronological parameter selection, and disjoint out-of-sample (OOS) scoring. It generates a machine-readable results file, per-observation returns, a research note, and an OOS equity chart.

I deliberately require the strategy exposure applied to return `t` to come from the signal computed at `t−2`. That extra lag avoids treating the same bar's closing price as both an input and an instantaneously executable decision. Execution at the next bar's close remains a simplification.

A one-way 10-basis-point fee/slippage assumption is applied when the position changes. Each test fold begins flat; the comparison portfolio also pays entry costs at the start of each fold.

## Demonstration — a historical equity example, not crypto

The bundled data are Plotly's 105 weekly normalized technology-stock price observations from 2018–2019. For the default AAPL series, there are 48 initial training observations and three nonoverlapping 18-week OOS windows. Parameter choice is made using only the preceding training data.

The example OOS evaluation returned **+49.58% for the strategy** and **+53.61% for the fold-reset buy-and-hold comparison**. The strategy's measured annualized Sharpe was 2.14 and the benchmark's was 1.84 (zero risk-free rate assumption).

Those numbers are **not** live returns, not BTC perpetual futures results, and not proof of statistically significant alpha. Indeed, the strategy failed to outperform the chosen comparison on aggregate return. The sample is small, normalized and stale; slippage, corporate actions, funding, market impact, and broker fills are not modeled.

## What matters more than the headline return

The design makes future-data contamination harder: training stops before every test window, OOS windows do not overlap, and unit tests perturb future observations to check earlier selection remains unchanged. It also records the actual parameter pair chosen at each fold.

There is still selection bias from picking the original parameter grid. A stronger follow-up would include multiple datasets and regimes, research logs for discarded hypotheses, realistic timestamped exchange data, funding and maker/taker fees, and uncertainty intervals.

I see this as a research harness, not a portfolio claim: a small piece of code that makes it easier to reject weak strategies before risking capital.

**Code, data provenance, tests and methodology:** [GITHUB_URL]

**Chart:** insert `artifacts/oos_equity.png` (caption: "Historical normalized weekly equity sample, OOS fold-reset convention; not a live trading account")

*Data source: Plotly `plotly.express.data.stocks()` (2018–2019 normalized weekly example). Optional official Binance SPOT importer is implemented but was not exercised in this build. Code and draft were prepared with AI assistance and require final author verification.*
