import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_updates

class AssistantUpdateFeedTests(unittest.TestCase):
    def test_history_is_append_only_data_with_unique_ids(self):
        ids=[item["id"] for item in muba_updates.UPDATES]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),6)

    def test_gallery_update_targets_web_and_telegram_studio(self):
        gallery=muba_updates.entries("tr","gallery")
        self.assertTrue(gallery)
        self.assertIn("Galeri",gallery[0]["text"])
        item=next(item for item in muba_updates.UPDATES if item["id"]=="20260921-gallery")
        for area in ("gallery","studio","web","telegram"):
            self.assertIn(area,item["areas"])

    def test_badge_is_unseen_until_latest_id_matches(self):
        latest=muba_updates.latest_id("studio")
        self.assertTrue(muba_updates.has_unseen("studio",None))
        self.assertFalse(muba_updates.has_unseen("studio",latest))

    def test_all_five_languages_have_ui_labels(self):
        self.assertEqual(set(muba_updates.UPDATE_LABELS),{"en","tr","zh","ar","hi"})
        self.assertEqual(set(muba_updates.AREA_LABELS),{"en","tr","zh","ar","hi"})

if __name__=="__main__":
    unittest.main(verbosity=2)
