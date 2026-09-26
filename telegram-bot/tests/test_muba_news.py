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

    def test_web_news_script_parses_for_price_and_feed(self):
        page=(Path(__file__).resolve().parents[2]/"index.html").read_text()
        self.assertIn('let newsRows=[], newsCategory="ALL", newsVisible=10;',page)
        self.assertIn('if(list.scrollTop+list.clientHeight>=list.scrollHeight-120)',page)
        self.assertIn('const filtered=newsRows.filter(row=>newsCategory==="ALL"||newsBucket(row)===newsCategory);\n      const items=',page)
        self.assertNotIn('===newsCategory);\\n      const items=',page)
        self.assertIn('loadPrices();setInterval(loadPrices,5000);',page)

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
                self.assertNotIn(self.row()["published_at"][10:],result)
                self.assertIn(update,result)

    def test_official_crypto_update_is_important(self):
        row=self.row(title="CFTC Updates Crypto Asset FAQs",summary="Official staff guidance on blockchain activities.",category="REGULATION")
        self.assertTrue(news.important(row))
        self.assertEqual(news.verified_row(row,b"<h1>CFTC Updates Crypto Asset FAQs</h1>"),"VERIFIED")
        self.assertFalse(news.important(self.row(title="CFTC Updates FAQ",summary="Generic filing note.")))

    def test_media_needs_independent_evidence_and_cross_source_dedup(self):
        first=self.row(source_name="CoinDesk",source_url="https://www.coindesk.com/news/bitcoin-etf-approval-2026",
                       title="Bitcoin ETF Approval Announced by Commission")
        second=self.row(source_name="The Block",source_url="https://www.theblock.co/news/bitcoin-etf-approval-2026",
                        title="Commission Announces Bitcoin ETF Approval Today")
        third=self.row(source_name="Cointelegraph",source_url="https://cointelegraph.com/news/unrelated-exchange-hack",
                       title="Exchange Hack Leaves Crypto Users Waiting",category="SECURITY")
        self.assertTrue(news.corroborates(first,second))
        self.assertFalse(news.corroborates(first,third))
        self.assertEqual(news.primary_links(b'<a href="https://www.sec.gov/newsroom/press-releases/valid">source</a> '
                                            b'<a href="https://sec.gov.evil.org/fake">fake</a>'),
                         ['https://www.sec.gov/newsroom/press-releases/valid'])
        first['duplicate_hash']=news.duplicate_hash(first)
        second['duplicate_hash']=news.duplicate_hash(second)
        pool=[first]
        self.assertFalse(news.merge(pool,second))
        self.assertEqual(len(pool),1)

    def test_trusted_media_article_is_checked_against_its_publisher_page(self):
        row=self.row(source_name="CoinDesk",source_url="https://www.coindesk.com/news/bitcoin-etf-approval-2026")
        self.assertFalse(news.primary_links(b'<h1>SEC Approves Bitcoin ETF Launch</h1>'))
        self.assertTrue(news.relevant(row))
        self.assertEqual(news.verified_row(row,b'<h1>SEC Approves Bitcoin ETF Launch</h1>'),"VERIFIED")
        self.assertEqual(news.verified_row(row,b'<h1>Unrelated publisher page</h1>'),"PENDING")
        self.assertIsNone(news.canonical_url("https://www.coindesk.com.evil.org/fake","www.coindesk.com"))

    def test_official_and_media_reports_share_one_public_event(self):
        official=self.row(title="Federal Reserve Board requests public comment on payment stablecoin issuers under GENIUS Act",
                          summary="Federal Reserve Board requests public comment on payment stablecoin issuers under GENIUS Act",
                          category="STABLECOIN",source_name="Federal Reserve",
                          duplicate_hash="official-hash",
                          source_url="https://www.federalreserve.gov/newsevents/pressreleases/bcreg20260924a.htm")
        media=self.row(id="media",title="Fed proposes new capital redemption rules for stablecoin issuers",
                       summary="The Fed proposal sets capital requirements as regulators implement the GENIUS Act.",
                       category="STABLECOIN",source_name="Cointelegraph",
                       duplicate_hash="media-hash",
                       source_url="https://cointelegraph.com/news/fed-stablecoins")
        self.assertTrue(news.event_match(official,media))
        with patch.object(news,"load_pool",return_value=[official,media]):
            self.assertEqual([row["id"] for row in news.public_news()],[official["id"]])
        unrelated=self.row(id="other",title="Stablecoin issuer announces new exchange listing",
                           summary="A separate crypto exchange listing today.",category="STABLECOIN",
                           source_name="Cointelegraph",source_url="https://cointelegraph.com/news/separate",
                           duplicate_hash="other-hash")
        self.assertFalse(news.event_match(official,unrelated))

    def test_security_headline_variants_stay_in_one_category_and_deduplicate(self):
        coinbase_news=news.category_for("Crypto exchange Bitget says $352 million affected in a hack, claims breach resolved","")
        decrypt_news=news.category_for("Bitget Hacked as $350 Million Vanishes From Crypto Exchange Wallets","")
        self.assertEqual(coinbase_news,"SECURITY")
        self.assertEqual(decrypt_news,"SECURITY")
        first=self.row(source_name="CoinDesk",title="Crypto exchange Bitget says $352 million affected in a hack, claims breach resolved",category=coinbase_news,duplicate_hash="bitget-a")
        second=self.row(source_name="Decrypt",title="Bitget Hacked as $350 Million Vanishes From Crypto Exchange Wallets",category=decrypt_news,duplicate_hash="bitget-b")
        self.assertTrue(news.event_match(first,second))


if __name__=="__main__": unittest.main()
