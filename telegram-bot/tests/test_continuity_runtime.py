from __future__ import annotations
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
BOT=(ROOT/"bot_mention.py").read_text(encoding="utf-8")

class ContinuityRuntimeWiringTests(unittest.TestCase):
    def test_gallery_moderation_is_dev_gated(self):
        self.assertIn('callback_data="gallery_admin"',BOT)
        self.assertIn('if data=="gallery_admin":\n        if not is_dev(user_id): return',BOT)
        self.assertIn('if data.startswith("gallery_set:"):\n        if not is_dev(user_id): return',BOT)
        self.assertIn("set_gallery_visibility",BOT)

    def test_state_health_route_exists(self):
        self.assertIn('"/health/state"',BOT)
        self.assertIn("state_storage_status()",BOT)

    def test_update_detail_includes_title_and_text(self):
        self.assertIn('item["title_text"]',BOT)
        self.assertIn('item["text"]',BOT)

if __name__=="__main__":
    unittest.main(verbosity=2)
