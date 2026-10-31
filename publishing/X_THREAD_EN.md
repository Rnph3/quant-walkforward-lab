# X thread draft — Quant Walk-Forward Lab

1/3 A profitable backtest isn't proof of alpha. I built a small Python walk-forward lab to keep parameter selection chronological and test results genuinely out of sample.

2/3 Historical **equity** example (not BTC): 3 OOS folds, explicit signal lag, 10bps one-way cost assumption. Strategy +49.6%, fold-reset benchmark +53.6%. Not a trading system or live performance.

3/3 Code + reproducible artifacts + tests: [GITHUB_URL]
Chart: `artifacts/oos_equity.png`
Key limit: small 2018–2019 normalized stock sample; no real execution or funding.
