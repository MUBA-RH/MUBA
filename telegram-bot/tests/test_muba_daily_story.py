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
        self.assertIn("canonical muba face architecture",prompt)
        self.assertIn("true hand-drawn 2d japanese chibi",prompt)
        self.assertIn("identity",prompt)
        self.assertEqual(item["rules"]["visual_style"],"living-story-true-2d-chibi-hf-flux-ipadapter-v6")
        self.assertEqual(item["rules"]["visual_layer"],"muba_story_chibi")
        self.assertEqual(item["rules"]["continuity"],"canonical-face-architecture-plus-clean-chibi-anchor-plus-scene-state")
        self.assertEqual(item["rules"]["character_anchor_version"],"muba-face-architecture-v1")
        self.assertIn("no purple neon ring",prompt)
        self.assertIn("no visible text",prompt)

    def test_each_prompt_has_concrete_story_state(self):
        item=muba_story.draft("2099-01-01")
        joined=" ".join(item["prompts"]).lower()
        self.assertTrue(("same box" in joined) or ("same folded paper" in joined))
        self.assertNotIn("tiny integrated story word",joined)
        self.assertEqual(item["rules"]["frame_text_max_words"],0)

    def test_canonical_face_architecture_is_hard_identity_constraint(self):
        face=(ROOT/"muba_face_architecture.py").read_text(encoding="utf-8").lower()
        layer=(ROOT/"muba_story_chibi.py").read_text(encoding="utf-8").lower()
        self.assertIn("giant asymmetric bulging eyes",face)
        self.assertIn("tiny dark nose",face)
        self.assertIn("hanging pink tongue",face)
        self.assertIn("reject hamster",face)
        self.assertIn("identity_prompt",layer)

    def test_web_uses_short_summary_without_panel_numbers(self):
        web=(ROOT.parent/"index.html").read_text(encoding="utf-8")
        self.assertIn('story.summary||story.twt',web)
        self.assertNotIn('story-panel-no',web)
        self.assertNotIn('>0\'+(i+1)',web)
        self.assertIn('story-book',web)

    def test_chibi_layer_has_character_sheet_anchor(self):
        layer=(ROOT/"muba_story_chibi.py").read_text(encoding="utf-8").lower()
        self.assertIn("character_dna",layer)
        self.assertIn("clean reusable 2d chibi character reference",layer)
        self.assertIn("2 heads tall",layer)
        self.assertIn("no 3d",layer)
        self.assertIn("no visible text",layer)
        self.assertIn("20-35 percent",layer)

    def test_generation_uses_hf_ipadapter_canonical_reference_for_all_panels(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        section=bot[bot.index("async def _story_generate_images"):bot.index("async def story_public_handler")]
        self.assertIn("muba_story_hf",section)
        self.assertIn("generate_anchor(session,character_anchor_prompt(),REFERENCE_URL)",section)
        self.assertIn("hf_story_generate(session,prompt,anchor_path",section)
        self.assertNotIn("previous_frame",section)
        self.assertNotIn("character_anchor,_=await render",section)

    def test_hf_bridge_is_real_flux_ipadapter_and_token_gated(self):
        bridge=(ROOT/"muba_story_hf.py").read_text(encoding="utf-8")
        self.assertIn('InstantX/flux-IP-adapter',bridge)
        self.assertIn('API_CANDIDATES=("process_image","predict")',bridge)
        self.assertIn('HF_TOKEN',bridge)
        self.assertIn('MAX_ATTEMPTS',bridge)
        self.assertIn('asyncio.wait_for',bridge)
        self.assertIn('from gradio_client import Client, handle_file',bridge)
        self.assertIn('Client(SPACE_ID,token=token,verbose=False)',bridge)
        self.assertIn('view_api(return_format="dict",print_info=False)',bridge)
        self.assertIn('handle_file(reference_url)',bridge)
        self.assertIn('PANEL_IP_WEIGHT',bridge)
        self.assertIn('ANCHOR_IP_WEIGHT',bridge)
        self.assertIn('"0.82"',bridge)
        self.assertIn('"0.78"',bridge)
        self.assertNotIn('RioShiina/ImageGen',bridge)
        self.assertNotIn('run_imagegen',bridge)
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


class TestLivingStoryIsolation(unittest.TestCase):
    def test_story_is_hf_only_and_fails_closed(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        start=source.index("async def _story_generate_images")
        end=source.index("async def story_public_handler",start)
        story=source[start:end]
        self.assertIn("generate_anchor(session,character_anchor_prompt(),REFERENCE_URL)",story)
        self.assertIn("hf_story_generate(session,prompt,anchor_path",story)
        self.assertIn("generated=[]",story)
        self.assertLess(story.index("generated.append"),story.index("_archive_studio_output"))
        self.assertIn("Living Story HF engine is not configured",story)
        self.assertNotIn("cloudflare_story_generate",story)
        self.assertNotIn("ai_endpoint()",story)
        self.assertNotIn("CLOUDFLARE_API_TOKEN",story)
        self.assertNotIn("ai_payload(",story)