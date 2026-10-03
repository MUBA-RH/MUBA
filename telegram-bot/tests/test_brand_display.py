"""Brand labels must not change the identity of existing official accounts."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from assistant_extras import GUIDE, security_check
from muba_brain import PROTECTED_OFFICIAL_SOURCES, build_reply
from muba_daily import daily_text


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}
        self.href = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            if self.href:
                self.links.setdefault(self.href, "")

    def handle_endtag(self, tag):
        if tag == "a":
            self.href = None

    def handle_data(self, text):
        if self.href:
            self.links[self.href] += text


class BrandDisplayTests(unittest.TestCase):
    def test_social_cards_keep_destinations_with_brand_labels(self):
        page = Links()
        page.feed((ROOT.parent / "index.html").read_text())
        for url in ("https://x.com/MUBA_RH", "https://t.me/MUBA_RH"):
            self.assertIn("MUBA", page.links[url])
            self.assertNotIn("MUBA_RH", page.links[url])
        self.assertIn("https://t.me/MUBA_RH_AI_Bot?start=assistant", page.links)

    def test_multilingual_responses_use_brand_without_inventing_a_handle(self):
        for lang in ("en", "tr", "zh", "ar", "hi"):
            texts = [build_reply("official sources", language=lang), " ".join(GUIDE[lang])]
            texts.extend(daily_text(lang, section) for section in ("x", "telegram"))
            for text in texts:
                self.assertIn("MUBA", text)
                self.assertNotIn("MUBA_RH", text)
                self.assertNotIn("@MUBA", text)

    def test_existing_source_identity_and_security_are_preserved(self):
        self.assertEqual(PROTECTED_OFFICIAL_SOURCES["official_x"], "@MUBA_RH")
        for url in ("https://x.com/MUBA_RH", "https://t.me/MUBA_RH"):
            self.assertIn("✅", security_check("tr", url))
        for url in ("https://x.com/MUBA", "https://t.me/MUBA"):
            self.assertIn("❌", security_check("tr", url))
