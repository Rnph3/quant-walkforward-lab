from pathlib import Path
import json, argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .data import load_prices
from .engine import walkforward
from .binance import download_month

ROOT = Path(__file__).resolve().parents[1]

def main(argv=None):
    p = argparse.ArgumentParser(description='Historical walk-forward research demonstrator; no trading')
    p.add_argument('--input', type=Path, default=ROOT/'data/plotly_stocks_weekly_2018_2019.csv')
    p.add_argument('--column', default='AAPL')
    p.add_argument('--train', type=int, default=48)
    p.add_argument('--test', type=int, default=18)
    p.add_argument('--cost-bps', type=float, default=10.0)
    p.add_argument('--periods-per-year', type=int, default=52)
    p.add_argument('--out', type=Path, default=ROOT/'artifacts')
    p.add_argument('--download-binance-month', help='Opt-in network download: YYYY-MM')
    p.add_argument('--binance-symbol', default='BTCUSDT')
    p.add_argument('--binance-interval', default='1h')
    args = p.parse_args(argv)
    if args.download_binance_month:
        report = download_month(args.binance_symbol, args.binance_interval, args.download_binance_month,
                                args.out/f'{args.binance_symbol}_{args.binance_interval}_{args.download_binance_month}.csv')
        print(json.dumps(report, indent=2))
        return
    prices = load_prices(args.input, args.column)
    stats, oos = walkforward(prices, min_train=args.train, test_size=args.test,
                             one_way_cost_bps=args.cost_bps, periods_per_year=args.periods_per_year)
    args.out.mkdir(parents=True, exist_ok=True)
    oos.to_csv(args.out/'oos_predictions_and_returns.csv', index=False, float_format='%.10f')
    (args.out/'results.json').write_text(json.dumps(stats, indent=2, ensure_ascii=False) + '\n')
    fig, ax = plt.subplots(figsize=(10.5, 4.5))
    xs = list(range(len(oos)))
    ax.plot(xs, oos['strategy_equity'], label='Walk-forward strategy (net)')
    ax.plot(xs, oos['benchmark_equity'], label='Buy/hold per fold (net)', ls='--')
    for i in range(1, len(stats['folds'])):
        ax.axvline(oos[oos['fold'] == i+1].index[0], lw=.7, alpha=.6)
    ax.set_title(f'Historical OOS equity | {prices.name} | weekly normalized example')
    ax.set_ylabel('Growth of 1.0 (fold-reset convention)')
    tick_ids = sorted({int(round(i)) for i in np.linspace(0, len(oos)-1, 7)})
    ax.set_xticks(tick_ids, [oos['date'].iloc[i] for i in tick_ids], rotation=20, ha='right')
    ax.set_xlabel('Historical OOS observation date (fold boundaries shown)')
    ax.legend()
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(args.out/'oos_equity.png', dpi=180)
    plt.close(fig)
    s=stats['oos_strategy']; b=stats['oos_buy_and_hold']
    md = f'''# Walk-forward research result — {prices.name}\n\n**HISTORICAL STUDY / NO LIVE TRADING / NOT FINANCIAL ADVICE**\n\n- Source: Plotly example normalized weekly equity prices (2018–2019).\n- Observations: {stats['n_observations']} ({stats['first_observation']} to {stats['last_observation']}).\n- Expanding train: {args.train} initial rows, OOS test window: {args.test} rows.\n- Candidate grid: {stats['candidate_grid']}. Selection uses training history only.\n- Trading assumption: signal known at t−2, rebalance at t−1 close, earn price[t−1]→price[t] return.\n- All folds separately reset flat; round trip incurs entry and exit costs when present.\n- Approximate one-way fees + slippage: {args.cost_bps:.1f} bps per unit turnover.\n\n| Metric | Strategy OOS | Buy & hold OOS (fold reset) |\n|---|---:|---:|\n| Total growth - 1 | {s['total_return']:.2%} | {b['total_return']:.2%} |\n| Max drawdown | {s['max_drawdown']:.2%} | {b['max_drawdown']:.2%} |\n| Ann. Sharpe (risk-free=0) | {s['annualized_sharpe']:.2f} | {b['annualized_sharpe']:.2f} |\n\n## Fold selection (training-only)\n\n| Fold | OOS start | OOS end | Selected fast/slow | Train Sharpe |\n|---|---|---|---|---:|\n'''
    for f in stats['folds']:
        md += f"| {f['fold']} | {f['test_start']} | {f['test_end']} | {f['selected_fast']}/{f['selected_slow']} | {f['selected_train_sharpe']:.2f} |\n"
    md += '\n## Limits\n\n' + '\n'.join('- '+x for x in stats['limitations'])
    md += '\n\n**Interpretation:** This is an educational stress test of a fixed candidate grid, not evidence of market-beating skill. Returns are from a small, old normalized equity dataset; no claim about BTC.\n'
    (args.out/'RESEARCH_NOTE.md').write_text(md)
    print(json.dumps({'repo':'quant-walkforward-lab','folds':len(stats['folds']),
                      'oos_total_return':s['total_return'], 'benchmark_total_return':b['total_return'],
                      'outputs':str(args.out)}, indent=2))

if __name__ == '__main__': main()
