# data_sources.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import pandas as pd
import yfinance as yf

# Simple in-memory cache (per-process)
_CACHE: Dict[str, Dict[str, Any]] = {}
_TTL = timedelta(minutes=10)

def _is_stale(ts: datetime) -> bool:
    return datetime.utcnow() - ts > _TTL

def _compute_1y_return(hist: pd.DataFrame) -> Optional[float]:
    if hist is None or hist.empty or "Close" not in hist or len(hist["Close"]) < 2:
        return None
    start = float(hist["Close"].iloc[0])
    end   = float(hist["Close"].iloc[-1])
    if start == 0:
        return None
    return (end / start - 1.0) * 100.0

def _compute_div_yield(dividends: pd.Series, last_price: Optional[float]) -> Optional[float]:
    if last_price is None or last_price == 0:
        return None
    if dividends is None or dividends.empty:
        return 0.0
    cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=365)
    last_12m = dividends[dividends.index >= cutoff]
    ttm = float(last_12m.sum()) if len(last_12m) else 0.0
    return (ttm / last_price) * 100.0

def get_quote_snapshot(symbol: str) -> Dict[str, Optional[float]]:
    """
    Returns: {"price": float|None, "ret_1y_pct": float|None, "div_yield_pct": float|None}
    Cached for ~10 minutes per symbol.
    """
    sym = symbol.upper()

    if sym in _CACHE and not _is_stale(_CACHE[sym]["ts"]):
        return _CACHE[sym]["data"]

    tkr = yf.Ticker(sym)

    # History for price & 1y return
    try:
        hist = tkr.history(period="1y", interval="1d", auto_adjust=False)
    except Exception:
        hist = pd.DataFrame()

    price = float(hist["Close"].iloc[-1]) if not hist.empty else None
    ret_1y = _compute_1y_return(hist) if not hist.empty else None

    # Dividends → trailing 12m yield
    try:
        dividends = tkr.dividends
    except Exception:
        dividends = pd.Series(dtype=float)

    div_yield = _compute_div_yield(dividends, price) if price is not None else None

    data = {"price": price, "ret_1y_pct": ret_1y, "div_yield_pct": div_yield}
    _CACHE[sym] = {"data": data, "ts": datetime.utcnow()}
    return data
