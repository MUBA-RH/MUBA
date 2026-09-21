from __future__ import annotations
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO=ROOT.parent
sys.path.insert(0,str(ROOT))

import muba_history
import muba_updates
import muba_daily

class ContinuityHistoryTests(unittest.TestCase):
    def test_canonical_history_has_unique_ids_and_five_languages(self):
        ids=[]
        for item in muba_history.UPDATES:
            self.assertNotIn(item["id"],ids)
            ids.append(item["id"])
            self.assertIn(item["type"],{"new","updated","improved","fixed"})
            for field in ("title","text"):
                self.assertEqual(set(item[field]),{"en","tr","zh","ar","hi"})

    def test_updates_and_daily_share_canonical_history(self):
        self.assertIs(muba_updates.UPDATES,muba_history.UPDATES)
        self.assertTrue(any("Continuity" in row for row in muba_daily.DEVLOG["en"]["fixed"]))
        latest=muba_updates.entries("tr")[0]
        self.assertEqual(latest["id"],muba_history.UPDATES[0]["id"])
        self.assertTrue(any(item["id"]=="20260921-continuity" for item in muba_history.UPDATES))
        self.assertTrue(latest["title_text"])

    def test_web_reads_same_history_file(self):
        html=(REPO/"index.html").read_text(encoding="utf-8")
        self.assertIn('fetch("./muba_history.json"',html)
        self.assertIn("loadDevelopmentHistory();",html)
        self.assertNotIn("const devLog = {",html)

    def test_history_policy_requires_user_facing_updates(self):
        data=json.loads((REPO/"muba_history.json").read_text(encoding="utf-8"))
        self.assertTrue(data["policy"]["append_only"])
        self.assertTrue(data["policy"]["required_for_user_facing_changes"])

if __name__=="__main__":
    unittest.main(verbosity=2)
