import numpy as np
import pandas as pd
import pytest
from quantlab.data import load_prices
from quantlab.engine import Candidate, signals, interval_results, folds, performance, walkforward
from quantlab.binance import monthly_url, parse_zip_bytes
from zipfile import ZipFile
from io import BytesIO


def series(n=105):
    return pd.Series(np.linspace(100, 210, n), index=pd.date_range('2018-01-01',periods=n,freq='W',tz='UTC'), name='AAPL')

def test_candidate_guard():
    with pytest.raises(ValueError): Candidate(10, 5)

def test_two_index_signal_lag():
    s = series(50)
    p = signals(s, Candidate(2, 4))
    # Modifying the immediately preceding close cannot affect current trade exposure.
    altered = s.copy(); altered.iloc[30] = 0.1
    pp = signals(altered, Candidate(2, 4))
    assert p.iloc[31] == pp.iloc[31]
    assert p.iloc[32] != pp.iloc[32]

def test_fees_on_entry_and_exit():
    s=series(10); pos=pd.Series([0.,0.,1.,1.,0.,0.,0.,0.,0.,0.],index=s.index)
    frame=interval_results(s,pos,2,5,100)
    assert np.allclose(frame['turnover'],[1.,0.,1.])
    assert np.isclose(frame['net_return'].iloc[-1],-.01)

def test_lookahead_train_only_on_future_mutation():
    s=series()
    baseline,_=walkforward(s)
    tampered=s.copy(); tampered.iloc[84:] *= 100
    later,_=walkforward(tampered)
    assert baseline['folds'][0]['selected_fast']==later['folds'][0]['selected_fast']
    assert baseline['folds'][1]['selected_fast']==later['folds'][1]['selected_fast']

def test_non_overlapping_oos_and_flat_reset():
    summary,frame=walkforward(series())
    assert frame['date'].is_unique
    assert len(frame)==54 and len(summary['folds'])==3
    for f in summary['folds']:
        fold = frame[frame['fold']==f['fold']]
        assert fold['turnover'].iloc[0] == abs(fold['position'].iloc[0])

def test_constrained_bad_series():
    s=series(4);p=s.copy()
    with pytest.raises(ValueError): interval_results(s,p,0,2,10)

def test_performance_drawdown():
    p = performance(pd.Series([.1, -.5, .1]),52)
    assert p['max_drawdown'] == pytest.approx(-.5)

def test_folds_guard():
    with pytest.raises(ValueError): folds(20,48,18)

def test_binance_urls_no_injection():
    with pytest.raises(ValueError): monthly_url('../secret','1h','2025-01')

def test_binance_microsecond_zip_parse():
    text='1735689600000000,4,5,3,4.5,20,1735693199999999,1,2,3,4,0\n1735693200000000,4,5,3,4.7,20,1735696799999999,1,2,3,4,0\n'
    mem=BytesIO()
    with ZipFile(mem,'w') as f:f.writestr('BTCUSDT-1h-2025-01.csv',text)
    data=parse_zip_bytes(mem.getvalue())
    assert data['date'].iloc[0].year==2025
    assert data['close'].iloc[1]==4.7

def test_real_bundled_prices():
    from pathlib import Path
    path=Path(__file__).parents[1]/'data/plotly_stocks_weekly_2018_2019.csv'
    x=load_prices(path)
    assert x.index[0].year == 2018 and x.index[-1].year == 2019
    assert len(x)==105
