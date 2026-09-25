import asyncio
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import muba_price as price


class Response:
    status = 200
    def __init__(self, data): self.data = data
    async def __aenter__(self): return self
    async def __aexit__(self, *args): return False
    async def json(self):
        if isinstance(self.data, Exception): raise self.data
        return self.data


class Session:
    def __init__(self, ticker, stats=None):
        self.ticker, self.stats = ticker, stats or {"open": "100"}
        self.urls = []
    def get(self, url, **kwargs):
        self.urls.append(url)
        return Response(self.ticker if url.endswith('/ticker') else self.stats)


class PriceTests(unittest.TestCase):
    def setUp(self):
        price._cached.clear()
        price._opening.clear()
        price._last_attempt = 0

    def test_near_live_shared_cache_and_muba_identity(self):
        stamp=1000
        session=Session({"price":"105","time":datetime.fromtimestamp(stamp,timezone.utc).isoformat()})
        first=asyncio.run(price.prices(session,lambda:stamp))
        self.assertEqual([row['symbol'] for row in first['assets']],['BTC','ETH','MUBA'])
        self.assertEqual(first['assets'][0]['change_24h_pct'],5.0)
        self.assertEqual(first['assets'][2]['status'],'IDENTITY_UNAVAILABLE')
        self.assertIsNone(first['assets'][2]['price_usd'])
        self.assertEqual(len(session.urls),4)
        asyncio.run(price.prices(session,lambda:stamp+4))
        self.assertEqual(len(session.urls),4)
        session.ticker={"price":"110","time":datetime.fromtimestamp(stamp+5,timezone.utc).isoformat()}
        second=asyncio.run(price.prices(session,lambda:stamp+5))
        self.assertEqual(second['assets'][0]['price_usd'],110)
        self.assertEqual(len(session.urls),6)  # Opening price remains cached for 60s.
        self.assertTrue(all(url.endswith(('/BTC-USD/ticker','/ETH-USD/ticker','/BTC-USD/stats','/ETH-USD/stats')) for url in session.urls))

    def test_wrong_identity_invalid_stats_and_stale_trade(self):
        for symbol,payload in [('MUBA',{'last':1,'open':1}),('BTC',{'last':0,'open':1}),
                               ('ETH',{'last':'nan','open':1}),('BTC',{'last':1})]:
            with self.assertRaises(ValueError): price.parse_stats(symbol,payload,1000)
        for payload in [{'price':'0','time':'1970-01-01T00:16:40Z'},
                        {'price':'nan','time':'1970-01-01T00:16:40Z'},
                        {'price':'1','time':'1970-01-01T00:15:00Z'}]:
            with self.assertRaises(ValueError): price.parse_ticker('BTC',payload,100,1000)

    def test_timeout_never_displays_delayed_price(self):
        good=Session({'price':'100','time':datetime.fromtimestamp(1000,timezone.utc).isoformat()},{'open':'110'})
        first=asyncio.run(price.prices(good,lambda:1000))
        self.assertEqual(first['assets'][0]['change_24h_pct'],-9.09)
        broken=Session(TimeoutError('API timeout'))
        after=asyncio.run(price.prices(broken,lambda:1010))
        self.assertEqual(after['assets'][0]['status'],'LIVE')  # Last verified trade is still 10s old.
        expired=asyncio.run(price.prices(broken,lambda:1031))
        self.assertEqual(expired['assets'][0]['status'],'UNAVAILABLE')
        self.assertIsNone(expired['assets'][0]['price_usd'])


if __name__=='__main__': unittest.main()
