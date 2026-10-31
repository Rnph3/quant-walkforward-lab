"""Optional, explicitly invoked importer for Binance official PUBLIC spot monthly klines.

SPOT open_time fields change from milliseconds to microseconds starting 2025.
This code is never invoked by the bundled default example or tests.
"""
from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO, StringIO
import re
import urllib.request
import pandas as pd

FIELDS = ['open_time','open','high','low','close','volume','close_time',
          'quote_volume','trade_count','taker_buy_base_volume','taker_buy_quote_volume','ignore']


def monthly_url(symbol: str, interval: str, month: str) -> str:
    if not re.fullmatch(r'[A-Z0-9]{3,20}', symbol):
        raise ValueError('Invalid symbol')
    if interval not in {'1h','4h','1d'}:
        raise ValueError('Supported intervals: 1h, 4h, 1d')
    if not re.fullmatch(r'20\d\d-(0[1-9]|1[0-2])', month):
        raise ValueError('Month YYYY-MM required')
    return f'https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{month}.zip'


def parse_zip_bytes(raw: bytes) -> pd.DataFrame:
    if len(raw) > 25_000_000:
        raise ValueError('Archive too large')
    with ZipFile(BytesIO(raw)) as zf:
        names = [x for x in zf.namelist() if x.endswith('.csv') and '/' not in x]
        if len(names) != 1 or zf.getinfo(names[0]).file_size > 50_000_000:
            raise ValueError('Expected one non-nested CSV with constrained size')
        text = zf.read(names[0]).decode('utf-8')
    frame = pd.read_csv(StringIO(text), header=None, names=FIELDS)
    # Some archives include a header; discard it only if present.
    if len(frame) and str(frame['open_time'].iloc[0]).strip().lower() in {'open time','open_time'}:
        frame = frame.iloc[1:].copy()
    frame['open_time'] = pd.to_numeric(frame['open_time'], errors='raise').astype('int64')
    microseconds = bool((frame['open_time'] >= 10**15).all())
    milliseconds = bool((frame['open_time'] < 10**15).all())
    if not (microseconds or milliseconds):
        raise ValueError('Mixed timestamp units')
    unit = 'us' if microseconds else 'ms'
    frame['date'] = pd.to_datetime(frame['open_time'], unit=unit, utc=True)
    frame['close'] = pd.to_numeric(frame['close'], errors='raise')
    if frame['date'].duplicated().any() or not frame['date'].is_monotonic_increasing:
        raise ValueError('Duplicate or unsorted timestamps')
    return frame[['date','close']]


def download_month(symbol: str, interval: str, month: str, out: str | Path):
    url = monthly_url(symbol, interval, month)
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'QuantWalkforwardLab/0.1'}), timeout=20) as response:
        raw = response.read(25_000_001)
    frame = parse_zip_bytes(raw)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    return {'url':url, 'rows':len(frame), 'csv':str(out), 'timestamp_unit':'automatically parsed'}
