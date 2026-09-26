"""Validated, shared, near-real-time USD prices; MUBA requires official identity."""
from __future__ import annotations

import asyncio
import math
import time
from datetime import datetime, timezone

ASSETS={"BTC":{"symbol":"BTC","type":"crypto","product":"BTC-USD"},
        "ETH":{"symbol":"ETH","type":"crypto","product":"ETH-USD"},
        "MUBA":{"symbol":"MUBA","type":"crypto","contract_address":None,"chain":None}}
API="https://api.exchange.coinbase.com/products/{product}/{kind}"
TTL=5
STATS_TTL=60
FRESH_LIMIT=30
_cached={}
_opening={}
_last_attempt=0.0
_lock=asyncio.Lock()


def positive(value):
    try: number=float(value)
    except (ValueError,TypeError) as exc: raise ValueError("Invalid price") from exc
    if not math.isfinite(number) or number<=0: raise ValueError("Non-positive or non-finite price")
    return number


def parse_stats(symbol,data,stamp):
    if symbol not in ("BTC","ETH") or not isinstance(data,dict): raise ValueError("Unknown price identity")
    last=positive(data.get("last"))
    opening=positive(data.get("open"))
    return {"symbol":symbol,"price_usd":last,"change_24h_pct":round((last-opening)/opening*100,2),
            "updated_at":datetime.fromtimestamp(stamp,timezone.utc).isoformat(timespec="seconds"),
            "status":"LIVE"}


def parse_ticker(symbol,data,opening,now):
    if symbol not in ("BTC","ETH") or not isinstance(data,dict): raise ValueError("Unknown price identity")
    last=positive(data.get("price"))
    try: stamp=datetime.fromisoformat(data["time"].replace("Z","+00:00"))
    except (KeyError,ValueError,TypeError,AttributeError) as exc: raise ValueError("Invalid trade time") from exc
    if stamp.tzinfo is None or not -5<=now-stamp.timestamp()<=FRESH_LIMIT:
        raise ValueError("Stale or future trade")
    return {"symbol":symbol,"price_usd":last,
            "change_24h_pct":round((last-opening)/opening*100,2),
            "updated_at":stamp.astimezone(timezone.utc).isoformat(timespec="seconds"),"status":"LIVE"}


async def _get(session,product,kind):
    async with session.get(API.format(product=product,kind=kind),timeout=8,allow_redirects=True) as response:
        if response.status!=200: raise ValueError("Price API unavailable")
        return await response.json()


def _display(symbol,now):
    row=_cached.get(symbol)
    if row and now-row["fetched_at"]<=FRESH_LIMIT:
        return row["data"]
    return {"symbol":symbol,"price_usd":None,"change_24h_pct":None,"status":"UNAVAILABLE"}


async def prices(session,clock=time.time):
    """One shared fetch every five seconds; no old price is presented as current."""
    global _last_attempt
    async with _lock:
        now=clock()
        if now-_last_attempt>=TTL:
            _last_attempt=now
            for symbol in ("BTC","ETH"):
                product=ASSETS[symbol]["product"]
                try:
                    opening=_opening.get(symbol)
                    if not opening or now-opening["fetched_at"]>=STATS_TTL:
                        stats=await _get(session,product,"stats")
                        opening={"value":positive(stats.get("open")),"fetched_at":now}
                        _opening[symbol]=opening
                    ticker=await _get(session,product,"ticker")
                    row=parse_ticker(symbol,ticker,opening["value"],now)
                    _cached[symbol]={"data":row,"fetched_at":now}
                except Exception:
                    # Expired prices never appear as live; no invented zero or stale value.
                    pass
        return {"assets":[_display("BTC",now),_display("ETH",now),
                          {"symbol":"MUBA","price_usd":None,"change_24h_pct":None,
                           "status":"IDENTITY_UNAVAILABLE","label":"PRICE NOT AVAILABLE"}],
                "cache_seconds":TTL}
