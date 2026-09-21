from __future__ import annotations

import pathlib
import sys
import unittest

REPO=pathlib.Path(__file__).resolve().parents[2]
BOT=(REPO/"telegram-bot"/"bot_mention.py").read_text(encoding="utf-8")
DAILY=(REPO/"telegram-bot"/"muba_daily.py").read_text(encoding="utf-8")
sys.path.insert(0,str(REPO/"telegram-bot"))

import muba_history
import muba_updates


class CentralUpdatesHubTests(unittest.TestCase):
    def test_canonical_history_contains_centralization_record(self):
        item=next(item for item in muba_history.UPDATES if item["id"]=="20260922-central-updates")
        self.assertEqual(
            set(item["areas"]),
            {"assistant","daily","telegram"},
        )

    def test_global_feed_uses_all_canonical_entries_once(self):
        rows=muba_updates.entries("en")
        ids=[item["id"] for item in rows]
        self.assertEqual(ids,[item["id"] for item in muba_history.UPDATES])
        self.assertEqual(len(ids),len(set(ids)))

    def test_assistant_has_global_pager_and_area_jump(self):
        self.assertIn('callback_data=f"updates_global:{index-1}"',BOT)
        self.assertIn('callback_data=f"updates_global:{index+1}"',BOT)
        self.assertIn('callback_data="updates_area:gallery:0"',BOT)
        self.assertIn('if data.startswith("updates_area:")',BOT)
        self.assertIn('UPDATE_LABELS[lang]["related"]',BOT)

    def test_daily_routes_updates_to_central_feed(self):
        self.assertIn('callback_data="updates_center"',BOT)
        self.assertIn('if section=="updates":',BOT)
        self.assertNotIn('from muba_history import entries as _history_entries',DAILY)

    def test_unit_update_views_are_area_scoped(self):
        self.assertIn('rows=update_entries(lang,area)',BOT)
        self.assertIn('callback_data=f"updates_area:{area}:{index-1}"',BOT)
        self.assertIn('callback_data=f"updates_area:{area}:{index+1}"',BOT)

    def test_seen_state_is_advanced_only_by_central_updates(self):
        self.assertEqual(BOT.count("mark_assistant_update_seen("),1)
        self.assertIn("def _mark_central_update_seen",BOT)


if __name__=="__main__":
    unittest.main(verbosity=2)
