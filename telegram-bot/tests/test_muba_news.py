import asyncio
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import muba_news as news


class NewsTests(unittest.TestCase):
    def row(self,**overrides):
        row={"id":"old","title":"SEC Approves Bitcoin ETF Launch","summary":"Official ETF approval announced.",
             "category":"ETF","source_name":"SEC","source_url":"https://www.sec.gov/newsroom/press-releases/123",
             "published_at":datetime.now(timezone.utc).isoformat(),"duplicate_hash":"h",
             "verification_status":"VERIFIED","status":"ACTIVE"}
        row.update(overrides)
        return row

    def test_source_and_timestamp_fail_closed(self):
        self.assertIsNone(news.canonical_url("https://sec.gov.evil.org/fake","www.sec.gov"))
        self.assertIsNone(news.canonical_url("http://www.sec.gov/news","www.sec.gov"))
        self.assertIsNone(news.parsed_time("invalid"))
        self.assertEqual(news.verified_row(self.row(source_url=None),b"SEC Approves Bitcoin ETF Launch"),"PENDING")
        self.assertEqual(news.verified_row(self.row(),None),"PENDING")
        self.assertEqual(news.verified_row(self.row(title="Rumor: Bitcoin ETF Launch"),b"Rumor Bitcoin ETF Launch"),"REJECTED")
        self.assertEqual(news.verified_row(self.row(),b"<h1>SEC Approves Bitcoin ETF Launch</h1>"),"VERIFIED")

    def test_duplicate_and_correction_preserve_original(self):
        original=self.row()
        pool=[original]
        self.assertFalse(news.merge(pool,self.row(id="same")))
        update=self.row(id="new",summary="Official ETF approval and new detail announced.")
        self.assertTrue(news.merge(pool,update))
        self.assertEqual(len(pool),2)
        self.assertEqual(pool[0]["status"],"ARCHIVED")
        self.assertEqual(pool[1]["status"],"UPDATED")
        self.assertEqual(pool[1]["correction_of"],"old")
        self.assertFalse(news.merge(pool,self.row(id="repeat",summary=update["summary"])))

    def test_rss_rejects_external_and_invalid_items(self):
        xml=b'<rss><channel><item><title>SEC Approves Bitcoin ETF Launch</title><link>https://sec.gov.evil.org/x</link><pubDate>bad</pubDate></item></channel></rss>'
        row=news.parse_feed(xml,news.SOURCES[0])[0]
        self.assertIsNone(row["source_url"])
        self.assertIsNone(row["published_at"])
        with self.assertRaises(ValueError): news.parse_feed(b'<!DOCTYPE foo>',news.SOURCES[0])

    def test_translation_isolation_and_no_unverified_delivery(self):
        row=self.row()
        session=object()
        with patch.object(news,"translate",new=AsyncMock(side_effect=lambda text,lang,session: "TR:"+text if lang=="tr" else None)):
            tr=asyncio.run(news.telegram_news(row,"tr",session))
            self.assertIn("TR:SEC Approves",tr)
            for lang in ("zh","ar","hi"):
                self.assertIsNone(asyncio.run(news.telegram_news(row,lang,session)))
        self.assertIsNone(asyncio.run(news.telegram_news(self.row(verification_status="PENDING"),"en",session)))

    def test_five_language_delivery_uses_local_labels(self):
        session=object()
        for lang in news.LABELS:
            with self.subTest(lang=lang), patch.object(news,"translate",new=AsyncMock(side_effect=lambda text,locale,session: locale+":"+text)):
                result=asyncio.run(news.telegram_news(self.row(status="UPDATED"),lang,session))
                verified,source,time_label,update,_=news.TELEGRAM_FIELDS[lang]
                self.assertIn(lang+":SEC Approves",result)
                self.assertIn(lang+":Official ETF",result)
                self.assertIn(verified,result)
                self.assertIn(source+": SEC",result)
                self.assertIn(time_label+":",result)
                self.assertIn(update,result)

    def test_official_crypto_update_is_important(self):
        row=self.row(title="CFTC Updates Crypto Asset FAQs",summary="Official staff guidance on blockchain activities.",category="REGULATION")
        self.assertTrue(news.important(row))
        self.assertEqual(news.verified_row(row,b"<h1>CFTC Updates Crypto Asset FAQs</h1>"),"VERIFIED")
        self.assertFalse(news.important(self.row(title="CFTC Updates FAQ",summary="Generic filing note.")))


if __name__=="__main__": unittest.main()
