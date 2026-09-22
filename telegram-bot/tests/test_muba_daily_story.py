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

    def test_visual_policy_uses_reusable_chibi_character_anchor(self):
        item=muba_story.draft("2099-01-01")
        prompt=item["prompts"][0].lower()
        self.assertIn("recurring character dna",prompt)
        self.assertIn("strict 2d japanese chibi",prompt)
        self.assertIn("identity anchor only",prompt)
        self.assertEqual(item["rules"]["visual_style"],"living-story-chibi-hf-ipadapter-v3")
        self.assertEqual(item["rules"]["visual_layer"],"muba_story_chibi")
        self.assertEqual(item["rules"]["continuity"],"canonical-reference-plus-story-state")
        self.assertEqual(item["rules"]["character_anchor_version"],"hf-sdxl-ipadapter-v3")
        self.assertIn("purple neon",prompt)

    def test_web_uses_short_summary_without_panel_numbers(self):
        web=(ROOT.parent/"index.html").read_text(encoding="utf-8")
        self.assertIn('story.summary||story.twt',web)
        self.assertNotIn('story-panel-no',web)
        self.assertNotIn('>0\'+(i+1)',web)
        self.assertIn('story-book',web)

    def test_chibi_layer_has_character_sheet_anchor(self):
        layer=(ROOT/"muba_story_chibi.py").read_text(encoding="utf-8").lower()
        self.assertIn("character_dna",layer)
        self.assertIn("character sheet anchor",layer)
        self.assertIn("2-head-tall",layer)
        self.assertIn("no 3d",layer)
        self.assertIn("no panel number",layer)
        self.assertIn("20-45 percent",layer)

    def test_generation_uses_hf_ipadapter_canonical_reference_for_all_panels(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        section=bot[bot.index("async def _story_generate_images"):bot.index("async def story_public_handler")]
        self.assertIn("muba_story_hf",section)
        self.assertIn("hf_story_generate(session,prompt,REFERENCE_URL)",section)
        self.assertNotIn("previous_frame",section)
        self.assertNotIn("character_anchor,_=await render",section)

    def test_hf_bridge_is_real_sdxl_ipadapter_and_token_gated(self):
        bridge=(ROOT/"muba_story_hf.py").read_text(encoding="utf-8")
        self.assertIn('stabilityai/SDXL-Base-1.0',bridge)
        self.assertIn('"injector_type":"ipadapter"',bridge)
        self.assertIn('"preset":IP_PRESET',bridge)
        self.assertIn('HF_TOKEN',bridge)
        self.assertIn('/gradio_api/call/',bridge)
        self.assertNotIn('CLOUDFLARE_API_TOKEN',bridge)

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
