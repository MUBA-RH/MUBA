"""Read-only Coinbase Exchange USD price service; unrelated to MUBA news."""
from __future__ import annotations

import asyncio
import math
import time
from datetime import datetime, timezone

ASSETS={"BTC":{"symbol":"BTC","type":"crypto","product":"BTC-USD"},
        "ETH":{"symbol":"ETH","type":"crypto","product":"ETH-USD"},
        "MUBA":{"symbol":"MUBA","type":"crypto","contract_address":None,"chain":None}}
API="https://api.exchange.coinbase.com/products/{product}/stats"
TTL=60
STALE_LIMIT=600
_cached={}
_last_attempt=0.0
_lock=asyncio.Lock()


def parse_stats(symbol,data,stamp):
    if symbol not in ("BTC","ETH") or not isinstance(data,dict): raise ValueError("Unknown price identity")
    try:
        last=float(data["last"])
        opening=float(data["open"])
    except (KeyError,TypeError,ValueError) as exc: raise ValueError("Invalid price payload") from exc
    if not math.isfinite(last) or not math.isfinite(opening) or last<=0 or opening<=0:
        raise ValueError("Price and 24h opening must be positive finite numbers")
    return {"symbol":symbol,"price_usd":last,"change_24h_pct":round((last-opening)/opening*100,2),
            "updated_at":datetime.fromtimestamp(stamp,timezone.utc).isoformat(timespec="seconds"),
            "source":"Coinbase Exchange","status":"LIVE"}


def _display(symbol,now):
    row=_cached.get(symbol)
    if not row: return {"symbol":symbol,"price_usd":None,"change_24h_pct":None,"status":"UNAVAILABLE"}
    age=now-row["fetched_at"]
    if age>STALE_LIMIT: return {"symbol":symbol,"price_usd":None,"change_24h_pct":None,"status":"UNAVAILABLE"}
    return row["data"]|{"status":"LIVE" if age<=TTL else "STALE"}


async def prices(session,clock=time.time):
    """One shared in-process fetch per minute, including a cooldown on failures."""
    global _last_attempt
    async with _lock:
        now=clock()
        if now-_last_attempt>=TTL:
            _last_attempt=now
            for symbol in ("BTC","ETH"):
                try:
                    url=API.format(product=ASSETS[symbol]["product"])
                    async with session.get(url,timeout=8,allow_redirects=False) as response:
                        if response.status!=200: raise ValueError("Price API unavailable")
                        payload=await response.json()
                    row=parse_stats(symbol,payload,now)
                    _cached[symbol]={"data":row,"fetched_at":now}
                except Exception:
                    # Keep the previous verified value only during the bounded stale window.
                    pass
        return {"assets":[_display("BTC",now),_display("ETH",now),
                          {"symbol":"MUBA","price_usd":None,"change_24h_pct":None,
                           "status":"IDENTITY_UNAVAILABLE","label":"PRICE NOT AVAILABLE"}],
                "source":"Coinbase Exchange","cache_seconds":TTL}
