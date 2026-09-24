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

    def test_visual_policy_uses_fresh_dev_reference(self):
        item=muba_story.draft("2099-01-01")
        prompt=item["prompts"][0].lower()
        self.assertIn("current dev reference is the only muba identity",prompt)
        self.assertIn("never a collage",prompt)
        self.assertIn("face/identity lock",prompt)
        self.assertEqual(item["rules"]["visual_style"],"daily-story-reference-first-v3")
        self.assertEqual(item["rules"]["visual_layer"],"muba_story_visual")
        self.assertEqual(item["rules"]["continuity"],"fresh-dev-reference-plus-scene-state")
        self.assertEqual(item["rules"]["character_anchor_version"],"daily-story-reference-first-v3")
        self.assertEqual(item["rules"]["character_anchor"],"dev-upload-per-production")
        self.assertEqual(item["rules"]["aspect_ratio"],"16:9")

    def test_each_prompt_has_concrete_story_state(self):
        item=muba_story.draft("2099-01-01")
        joined=" ".join(item["prompts"]).lower()
        self.assertTrue(("same box" in joined) or ("same folded paper" in joined))
        self.assertNotIn("tiny integrated story word",joined)
        self.assertEqual(item["rules"]["frame_text_max_words"],0)

    def test_legacy_story_layers_are_removed_and_v3_isolated(self):
        self.assertFalse((ROOT/"muba_story_chibi.py").exists())
        self.assertFalse((ROOT/"muba_daily_story_reference.py").exists())
        layer=(ROOT/"muba_story_visual.py").read_text(encoding="utf-8").lower()
        self.assertIn("reference-first v3",layer)
        self.assertIn("do not import any older muba drawing style",layer)

    def test_web_uses_short_summary_without_panel_numbers(self):
        web=(ROOT.parent/"index.html").read_text(encoding="utf-8")
        self.assertIn('story.summary||story.twt',web)
        self.assertNotIn('story-panel-no',web)
        self.assertNotIn('>0\'+(i+1)',web)
        self.assertIn('story-book',web)

    def test_visual_layer_requires_four_separate_images(self):
        layer=(ROOT/"muba_story_visual.py").read_text(encoding="utf-8").lower()
        self.assertIn("four separate full-bleed 16:9 images",layer)
        self.assertIn("never a collage",layer)
        self.assertIn("face/identity lock",layer)

    def test_generation_uses_kaggle_canonical_reference_for_batch(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        section=bot[bot.index("async def _story_generate_images"):bot.index("async def story_public_handler")]
        self.assertIn("muba_story_kaggle",section)
        self.assertIn("story_reference_for_day",section)
        self.assertIn("read_gallery_image",section)
        self.assertIn("checksum mismatch",section)
        self.assertNotIn("session.get(",section)
        self.assertIn("generate_batch(reference,item[\"prompts\"])",section)
        self.assertNotIn("muba_story_openai",section)
        self.assertNotIn("generate_anchor",section)

    def test_huggingface_bridge_uses_configured_credentials_and_reference(self):
        bridge=(ROOT/"muba_story_zerogpu.py").read_text(encoding="utf-8")
        self.assertIn("HF_"+"TOKEN",bridge)
        self.assertIn("HF_"+"TOKEN",bridge)
        self.assertIn("HF_"+"TOKEN",bridge)
        self.assertIn('args={"prompt":prompt,"reference":handle_file(str(ref))}',bridge)
        self.assertIn("gradio_client",bridge)
        self.assertNotIn("OPENAI_"+"API_KEY",bridge)
        self.assertNotIn("api.openai.com",bridge)

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
        muba_story.set_reference(day,"test-ref","abc","image/jpeg")
        muba_story.set_images(day,[])
        with self.assertRaises(ValueError): muba_story.publish(day)
        self.assertIsNone(muba_story.public_story(day))

    def test_unapproved_story_is_not_public(self):
        day="2099-01-02"
        muba_story.unpublish(day)
        self.assertIsNone(muba_story.public_story(day))

    def test_fresh_reference_gate_drives_story_generation(self):
        layer=(ROOT/"muba_story_visual.py").read_text(encoding="utf-8")
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn("CURRENT DEV REFERENCE IS THE ONLY MUBA IDENTITY",layer)
        self.assertIn("FOUR-IMAGE STORY CONTRACT",layer)
        self.assertIn("📷 REFERANS GÖRSEL VER",bot)
        self.assertIn('context.user_data["daily_story_waiting_reference"]=True',bot)
        self.assertIn("daily_story_reference_photo",bot)
        self.assertIn("story_reference_for_day",bot)
        self.assertIn("reply_photo",bot)

    def test_web_x_share_only_lives_in_approved_story_path(self):
        web=(ROOT.parent/"index.html").read_text(encoding="utf-8")
        self.assertIn('id="story-share-x"',web)
        self.assertIn("twitter.com/intent/tweet",web)
        self.assertIn("share.hidden=false",web)

    def test_story_uses_previous_day_and_web_summary_is_100_chars(self):
        item=muba_story.draft("2026-09-23")
        self.assertTrue(item["previous_day"])
        self.assertLessEqual(len(item["summary"]),100)
        self.assertLessEqual(len(item["summary_tr"]),100)
        self.assertTrue(all("CONTINUITY FROM YESTERDAY:" in p for p in item["prompts"]))

    def test_scheduler_is_pre_11_istanbul_and_prepare_is_protected(self):
        workflow=(ROOT.parent/".github/workflows/muba-daily-story-prepare.yml").read_text(encoding="utf-8")
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn('cron: "45 7 * * *"',workflow)
        self.assertIn("MUBA_STORY_SCHEDULER_SECRET",workflow)
        self.assertIn("story_prepare_handler",bot)
        self.assertIn('add_post("/story/prepare"',bot)
        self.assertIn("compare_digest",bot)

    def test_internal_scheduler_needs_no_external_scheduler_secret(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn("daily_story_scheduler(application)",bot)
        self.assertIn('ZoneInfo("Europe/Istanbul")',bot)
        self.assertIn("hour=10,minute=45",bot)
        self.assertIn("asyncio.create_task(daily_story_scheduler(application))",bot)
        self.assertIn("Görsel üretiminden önce referans MUBA görselini gönder",bot)

if __name__=="__main__": unittest.main()


class TestLivingStoryIsolation(unittest.TestCase):
    def test_story_is_kaggle_only_and_fails_closed(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        start=source.index("async def _story_generate_images")
        end=source.index("async def story_public_handler",start)
        story=source[start:end]
        self.assertIn("muba_story_kaggle",story)
        self.assertIn("Kaggle Daily Story bridge is not configured",story)
        self.assertIn("generated=await generate_batch",story)
        self.assertIn("for index,(body,out_type) in enumerate(generated):",story)
        self.assertNotIn("muba_story_openai",story)
        self.assertNotIn("generate_anchor",story)
