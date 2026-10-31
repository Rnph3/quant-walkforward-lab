from pathlib import Path
import numpy as np
import pandas as pd


def load_prices(path: str | Path, column: str = 'AAPL') -> pd.Series:
    frame = pd.read_csv(path)
    if 'date' not in frame or column not in frame:
        raise ValueError(f"CSV must contain date and {column!r} columns")
    dates = pd.to_datetime(frame['date'], utc=True, errors='raise')
    if dates.isna().any() or dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise ValueError('dates must be unique and increasing')
    vals = pd.to_numeric(frame[column], errors='raise').to_numpy(dtype=float)
    if len(vals) < 35 or not np.isfinite(vals).all() or np.any(vals <= 0):
        raise ValueError('need 35+ strictly positive, finite observations')
    return pd.Series(vals, index=pd.DatetimeIndex(dates), name=column)
