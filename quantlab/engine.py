"""Long/flat moving-average strategy with two-index signal-to-return lag.

All candidate tuning is on the historical training prefix. OOS folds are
non-overlapping and scored with a fresh flat portfolio each fold. No claim of
live tradability or positive expected performance is made.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class Candidate:
    fast: int
    slow: int

    def __post_init__(self):
        if self.fast <= 0 or self.slow <= 0 or self.fast >= self.slow:
            raise ValueError('Require 0 < fast < slow')

DEFAULT_CANDIDATES = [Candidate(3, 8), Candidate(4, 12), Candidate(6, 18), Candidate(8, 24)]


def signals(prices: pd.Series, c: Candidate) -> pd.Series:
    fast = prices.rolling(c.fast, min_periods=c.fast).mean()
    slow = prices.rolling(c.slow, min_periods=c.slow).mean()
    raw = (fast > slow).astype(float)
    raw.loc[slow.isna()] = 0.0
    # Signal at price index t-2 affects price-index t return.
    # The signal is known a full observation before the assumed trade time.
    return raw.shift(2).fillna(0.0)


def performance(returns: pd.Series, periods_per_year: int) -> dict:
    if len(returns) == 0:
        raise ValueError('empty returns')
    arr = returns.to_numpy(dtype=float)
    if not np.isfinite(arr).all() or np.any(arr <= -1):
        raise ValueError('invalid net returns')
    wealth = np.cumprod(1 + arr)
    highwater = np.maximum.accumulate(np.r_[1.0, wealth])[1:]
    dd = wealth / highwater - 1
    std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    sharpe = float((np.mean(arr) / std) * np.sqrt(periods_per_year)) if std > 1e-12 else 0.0
    return {
        'total_return': float(wealth[-1] - 1),
        'max_drawdown': float(dd.min()),
        'annualized_sharpe': sharpe,
        'positive_period_fraction': float((arr > 0).mean()),
        'n_periods': len(arr),
    }


def interval_results(prices: pd.Series, pos: pd.Series, start: int, end: int,
                     one_way_cost_bps: float, buy_hold: bool = False) -> pd.DataFrame:
    """Score [start, end); periods are indexed by right-hand price observation.

    Portfolio starts flat at EACH fold boundary. Trading costs = abs(delta pos)
    times one-way cost; no borrow, cash interest, spread dynamics, or funding.
    """
    if not (1 <= start < end <= len(prices)) or one_way_cost_bps < 0:
        raise ValueError('invalid interval or cost')
    idx = prices.index[start:end]
    asset_returns = prices.pct_change().iloc[start:end]
    position = pd.Series(1.0, index=idx) if buy_hold else pos.iloc[start:end]
    change = position.diff().abs()
    change.iloc[0] = float(abs(position.iloc[0]))
    net = position * asset_returns - (one_way_cost_bps / 10_000) * change
    return pd.DataFrame({
        'asset_return': asset_returns,
        'position': position,
        'turnover': change,
        'net_return': net,
        'equity': (1.0 + net).cumprod(),
    })


def folds(n: int, min_train: int, test_size: int) -> list[tuple[int, int]]:
    if min_train < 26 or test_size < 3 or n < min_train + test_size:
        raise ValueError('insufficient data for expanding walk-forward')
    return [(a, min(a + test_size, n)) for a in range(min_train, n - 2, test_size)
            if min(a + test_size, n) - a >= test_size]


def walkforward(prices: pd.Series, candidates: list[Candidate] | None = None,
                min_train: int = 48, test_size: int = 18,
                one_way_cost_bps: float = 10.0, periods_per_year: int = 52) -> tuple[dict, pd.DataFrame]:
    candidates = candidates or DEFAULT_CANDIDATES
    if not candidates or periods_per_year <= 0 or one_way_cost_bps < 0:
        raise ValueError('bad experiment arguments')
    fs = folds(len(prices), min_train, test_size)
    rows, returns = [], []
    cached = {c: signals(prices, c) for c in candidates}
    for fold_index, (start, end) in enumerate(fs, start=1):
        # Only train on index positions < start. Critically, no test data is used
        # for candidate selection, even when calculating leading rolling signals.
        train_scores = {}
        for c in candidates:
            train = interval_results(prices, cached[c], 1, start, one_way_cost_bps)
            train_scores[c] = performance(train['net_return'], periods_per_year)['annualized_sharpe']
        chosen = max(candidates, key=lambda c: (train_scores[c], -c.fast, -c.slow))
        strategy = interval_results(prices, cached[chosen], start, end, one_way_cost_bps)
        benchmark = interval_results(prices, cached[chosen], start, end, one_way_cost_bps, buy_hold=True)
        frame = pd.DataFrame({
            'date': prices.index[start:end].date.astype(str),
            'fold': fold_index,
            'asset_return': strategy['asset_return'].to_numpy(),
            'position': strategy['position'].to_numpy(),
            'turnover': strategy['turnover'].to_numpy(),
            'strategy_net_return': strategy['net_return'].to_numpy(),
            'benchmark_net_return': benchmark['net_return'].to_numpy(),
            'selected_fast': chosen.fast,
            'selected_slow': chosen.slow,
        })
        rows.append({
            'fold': fold_index,
            'train_end_exclusive': str(prices.index[start].date()),
            'test_start': str(prices.index[start].date()),
            'test_end': str(prices.index[end-1].date()),
            'selected_fast': chosen.fast,
            'selected_slow': chosen.slow,
            'selected_train_sharpe': float(train_scores[chosen]),
            'oos_strategy': performance(strategy['net_return'], periods_per_year),
            'oos_buy_and_hold': performance(benchmark['net_return'], periods_per_year),
        })
        returns.append(frame)
    oos = pd.concat(returns, ignore_index=True)
    oos['strategy_equity'] = (1 + oos['strategy_net_return']).cumprod()
    oos['benchmark_equity'] = (1 + oos['benchmark_net_return']).cumprod()
    headline = {
        'data_series': prices.name,
        'first_observation': str(prices.index[0].date()),
        'last_observation': str(prices.index[-1].date()),
        'n_observations': len(prices),
        'source_type': 'historical_normalized_weekly_equity_prices',
        'cost_bps_per_one_way_turnover': one_way_cost_bps,
        'periods_per_year': periods_per_year,
        'fold_reset_policy': 'flat at every test fold start; folds independently scored',
        'execution_policy': 'signal uses price[t-2]; applied to close-to-close return[t]',
        'selection_policy': 'maximize expanding in-sample net Sharpe; test untouched',
        'candidate_grid': [asdict(c) for c in candidates],
        'folds': rows,
        'oos_strategy': performance(oos['strategy_net_return'], periods_per_year),
        'oos_buy_and_hold': performance(oos['benchmark_net_return'], periods_per_year),
        'oos_total_turnover': float(oos['turnover'].sum()),
        'oos_exposure_fraction': float(oos['position'].mean()),
        'limitations': [
            'Sample data covers 2018-2019 weekly, normalized equity prices, not BTC futures',
            'Point-in-time OHLCV, corporate actions, bid-ask spread and volume not modeled',
            'Historical example and small grid, not a tradable or statistically validated alpha',
            'Sharpe ignores risk-free rate; cost is simplified one-way turnover approximation',
            'Each OOS fold starts flat and benchmark also pays an entry cost per fold',
        ]
    }
    return headline, oos
