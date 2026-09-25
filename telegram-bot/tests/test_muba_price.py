import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import muba_price as price


class Response:
    status = 200

    def __init__(self, data):
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self):
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


class Session:
    def __init__(self, data):
        self.data = data
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        return Response(self.data)


class PriceTests(unittest.TestCase):
    def setUp(self):
        price._cached.clear()
        price._last_attempt = 0

    def test_btc_eth_cache_and_unidentified_muba(self):
        session = Session({"last": "105", "open": "100"})
        first = asyncio.run(price.prices(session, lambda: 1000))
        self.assertEqual([asset["symbol"] for asset in first["assets"]], ["BTC", "ETH", "MUBA"])
        self.assertEqual(first["assets"][0]["change_24h_pct"], 5.0)
        self.assertEqual(first["assets"][1]["price_usd"], 105)
        self.assertEqual(first["assets"][2]["status"], "IDENTITY_UNAVAILABLE")
        self.assertIsNone(first["assets"][2]["price_usd"])
        self.assertEqual(len(session.urls), 2)
        self.assertEqual(asyncio.run(price.prices(session, lambda: 1030))["assets"][0]["status"], "LIVE")
        self.assertEqual(len(session.urls), 2)
        self.assertTrue(all(url.endswith(("BTC-USD/stats", "ETH-USD/stats")) for url in session.urls))

    def test_bad_price_identity_and_numbers(self):
        for symbol, data in (("MUBA", {"last": 1, "open": 1}),
                             ("BTC", {"last": 0, "open": 1}),
                             ("ETH", {"last": "nan", "open": 1}),
                             ("BTC", {"last": 1}),
                             ("BTC", {"last": 1, "open": 0})):
            with self.assertRaises(ValueError):
                price.parse_stats(symbol, data, 1000)

    def test_timeout_and_bounded_stale_cache(self):
        good = Session({"last": 100, "open": 110})
        first = asyncio.run(price.prices(good, lambda: 1000))
        self.assertEqual(first["assets"][0]["change_24h_pct"], -9.09)
        broken = Session(TimeoutError("API timeout"))
        stale = asyncio.run(price.prices(broken, lambda: 1100))
        self.assertEqual(stale["assets"][0]["status"], "STALE")
        self.assertEqual(stale["assets"][0]["price_usd"], 100)
        self.assertEqual(asyncio.run(price.prices(broken, lambda: 1701))["assets"][0]["status"], "UNAVAILABLE")
        self.assertIsNone(asyncio.run(price.prices(broken, lambda: 1701))["assets"][0]["price_usd"])


if __name__ == "__main__":
    unittest.main()
