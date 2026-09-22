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

    def test_visual_policy_is_isolated_chibi_episode(self):
        item=muba_story.draft("2099-01-01")
        prompt=item["prompts"][0].lower()
        self.assertIn("preserve muba's original facial identity",prompt)
        self.assertIn("chibi / super-deformed",prompt)
        self.assertIn("one chibi mini-story",prompt)
        self.assertIn("continuity:",prompt)
        self.assertEqual(item["rules"]["visual_style"],"living-story-chibi-only")
        self.assertEqual(item["rules"]["visual_layer"],"muba_story_chibi")
        self.assertEqual(item["rules"]["continuity"],"previous-frame-image")
        self.assertEqual(item["rules"]["frame_text_max_words"],3)
        self.assertEqual(len(item["frame_labels"]),4)
        self.assertGreater(len(item["story"].split()),70)
        self.assertLess(len(item["summary"].split()),40)
        self.assertIn("purple neon",item["prompts"][0].lower())
        self.assertIn("must not appear",item["prompts"][0].lower())

    def test_web_uses_short_summary_without_panel_numbers(self):
        web=(ROOT.parent/"index.html").read_text(encoding="utf-8")
        self.assertIn('story.summary||story.twt',web)
        self.assertNotIn('story-panel-no',web)
        self.assertNotIn('>0\'+(i+1)',web)
        self.assertIn('story-book',web)

    def test_chibi_layer_is_dedicated_to_living_story(self):
        layer=(ROOT/"muba_story_chibi.py").read_text(encoding="utf-8").lower()
        self.assertIn("living story chibi only",layer)
        self.assertIn("2-to-2.5-head-tall",layer)
        self.assertIn("not 3d",layer)
        self.assertIn("no panel number",layer)
        self.assertIn("upside-down",layer)

    def test_generation_chains_previous_frame_as_visual_reference(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn('input_image_1',bot)
        self.assertIn('previous_frame=body',bot)

    def test_technical_change_is_not_literal_story_title(self):
        item=muba_story.draft("2026-09-22")
        self.assertNotIn("four-image production connected",item["theme"].lower())
        self.assertNotIn("four-image production connected",item["story"].lower())

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
        self.assertIn('MUBA GÜNLÜK HİKÂYE',bot)
        self.assertIn('if data==\"story_generate\":',bot)
        self.assertIn('callback_data=\"story_generate\"',bot)
        self.assertIn('_story_generate_images',bot)
        self.assertEqual(bot.count('if data=="story_director":'),1)
        self.assertEqual(bot.count('if data=="story_publish":'),1)

    def test_today_change_has_turkish_runtime_fields(self):
        item=muba_story.draft("2026-09-22")
        self.assertTrue(item["theme_tr"])
        self.assertTrue(item["source_truth_tr"])

    def test_story_cannot_publish_without_four_images(self):
        day="2099-01-03"
        muba_story.unpublish(day)
        muba_story.set_images(day,[])
        with self.assertRaises(ValueError): muba_story.publish(day)
        self.assertIsNone(muba_story.public_story(day))

    def test_unapproved_story_is_not_public(self):
        day="2099-01-02"
        muba_story.unpublish(day)
        self.assertIsNone(muba_story.public_story(day))

if __name__=="__main__": unittest.main()
