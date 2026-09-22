import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_story

class DailyStoryTests(unittest.TestCase):
    def test_daily_story_has_four_connected_scenes(self):
        item=muba_story.draft("2099-01-01")
        self.assertEqual(len(item["scenes"]),4)
        self.assertEqual(len(item["prompts"]),4)
        self.assertTrue(item["rules"]["human_approval_required"])
        self.assertFalse(item["rules"]["auto_publish"])

    def test_visual_policy_preserves_muba_without_anime_or_comic_style(self):
        prompt=muba_story.draft("2099-01-01")["prompts"][0].lower()
        self.assertIn("do not redesign the face",prompt)
        self.assertIn("no anime",prompt)
        self.assertIn("no comic-book",prompt)
        self.assertIn("no hard glossy cgi",prompt)

    def test_dev_menu_exposes_story_director(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn('InlineKeyboardButton("🎬 MUBA Daily Story",callback_data="story_director")',bot)
        self.assertIn('if is_dev(user_id):',bot)

    def test_story_callback_chain_exists(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn('if data=="story_director":',bot)
        self.assertIn('if data=="story_publish":',bot)
        self.assertIn('callback_data="story_publish"',bot)
        self.assertIn('callback_data="menu"',bot)
        self.assertIn('MUBA GÜNLÜK HİKÂYE',bot)\n        self.assertEqual(bot.count('if data=="story_director":'),1)\n        self.assertEqual(bot.count('if data=="story_publish":'),1)

    def test_today_change_has_turkish_runtime_fields(self):\n        item=muba_story.draft("2026-09-22")\n        self.assertTrue(item["theme_tr"])\n        self.assertTrue(item["source_truth_tr"])\n\n    def test_unapproved_story_is_not_public(self):
        day="2099-01-02"
        muba_story.unpublish(day)
        self.assertIsNone(muba_story.public_story(day))

if __name__=="__main__": unittest.main()
