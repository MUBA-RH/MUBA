import inspect
"""Daily Story V3 reference-first regression tests."""
import ast
import hashlib
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_story
import muba_story_visual
import muba_story_cloudflare as cloudflare_bridge
from state import MemoryRepository


class ReferenceFirstStateTests(unittest.TestCase):
    def setUp(self):
        self.store=MemoryRepository()
        self.patch=mock.patch.object(muba_story,"STORE",self.store)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.day="2099-03-08"

    def test_new_system_starts_with_muba_origin_and_no_reference(self):
        item=muba_story.draft(self.day)
        self.assertEqual(item["theme"],"I'm MUBA")
        self.assertIsNone(muba_story.reference_for_day(self.day))
        self.assertEqual(item["rules"]["visual_layer"],"muba_story_visual")
        self.assertEqual(item["rules"]["visual_style"],"daily-story-master-identity-v9")

    def test_fresh_reference_is_required_before_image_batch(self):
        with self.assertRaisesRegex(ValueError,"Fresh DEV reference required"):
            muba_story.set_images(self.day,["1","2","3","4"])
        meta=muba_story.set_reference(self.day,"gallery-ref","abc123","image/jpeg")
        self.assertEqual(meta["gallery_id"],"gallery-ref")
        item=muba_story.set_images(self.day,["1","2","3","4"])
        self.assertEqual(item["images"],["1","2","3","4"])
        self.assertEqual(item["image_reference"],meta)

    def test_new_reference_invalidates_unpublished_old_batch(self):
        muba_story.set_reference(self.day,"ref-a","aaa","image/jpeg")
        muba_story.set_images(self.day,["1","2","3","4"])
        muba_story.set_reference(self.day,"ref-b","bbb","image/jpeg")
        self.assertEqual(muba_story.image_ids(self.day),[])

    def test_visual_contract_is_four_separate_images_and_reference_only(self):
        prompt=muba_story_visual.story_identity_prompt()
        self.assertIn("canonical MUBA identity remains authoritative",prompt)
        self.assertIn("four separate full-bleed 16:9 images",prompt)
        self.assertIn("never a collage",prompt)
        self.assertIn("FACE/BODY IDENTITY LOCK",prompt)


class CloudflareReferenceInputTests(unittest.TestCase):
    def test_reference_preparation_contract_is_present(self):
        source=inspect.getsource(cloudflare_bridge._prepare_reference)
        self.assertIn("511/max_side",source)
        self.assertIn('format="JPEG"',source)
        self.assertIn('"image/jpeg"',source)


class CloudflareRetryTests(unittest.TestCase):
    def test_only_provider_flag_retries(self):
        self.assertTrue(cloudflare_bridge._flagged(400,'AIError: output has been flagged. prompt input image combination'))
        self.assertFalse(cloudflare_bridge._flagged(500,'server error'))
        safe=cloudflare_bridge._safe_retry_prompt('IDENTITY RULES CURRENT BEAT: MUBA walks into a quiet street.')
        self.assertIn('friendly fictional illustrated scene',safe)
        self.assertIn('MUBA walks into a quiet street',safe)
        self.assertNotIn('IDENTITY RULES',safe)


class CloudflareStoryEngineTests(unittest.TestCase):
    def test_daily_story_runtime_uses_cloudflare_engine(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn("from muba_story_cloudflare import configured as story_image_configured, generate",source)
        self.assertNotIn("from muba_story_kaggle import configured as story_image_configured",source)

    def test_cloudflare_engine_uses_reference_and_sequential_continuity(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertNotIn("previous=None",source)
        self.assertIn("reference_type=reference_type",source)
        self.assertNotIn("continuity_bytes=previous",source)
        self.assertNotIn("previous,previous_type=body,out_type",source)

class TelegramInboxOutboxTests(unittest.TestCase):
    def test_reference_upload_auto_generates_and_previews(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn("DAILY STORY INBOX",source)
        self.assertIn("item=await _story_generate_images(item)",source)
        self.assertIn("DAILY STORY OUTBOX",source)
        self.assertIn('callback_data="story_publish"',source)
        self.assertIn('callback_data="story_generate"',source)

class ActiveStoryFlowTests(unittest.TestCase):
    def test_manual_package_entry_point_is_retired(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertNotIn("daily_story_waiting_package",source)
        self.assertNotIn('callback_data="story_package"',source)
        self.assertIn('callback_data="story_generate"',source)


class SequentialIdentityEngineTests(unittest.TestCase):
    def test_cloudflare_uses_9b_multi_reference_contract(self):
        source=inspect.getsource(cloudflare_bridge)
        self.assertIn("flux-2-klein-9b",source)
        self.assertIn('input_image_1',source)
        self.assertIn('guidance","5.0',source)
        self.assertIn("exactly ONE full-bleed cinematic 16:9 image",source)
        self.assertIn("immutable MUBA identity/style reference",source)

    def test_story_generation_chains_previous_frame(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertNotIn("continuity_bytes=previous",source)
        self.assertIn("telegram-story-engine",source)


class CloudflareFilterIsolationTests(unittest.TestCase):
    def test_filter_diagnostic_is_text_only_and_discarded(self):
        source=inspect.getsource(cloudflare_bridge.generate)
        self.assertIn("diagnostic=text-only-ok",source)
        self.assertIn("reference-combination-flagged",source)
        self.assertIn("A simple friendly fictional character standing in a quiet room.",source)


class ProductionFunctionTests(unittest.TestCase):
    def test_generation_reads_fresh_gallery_reference_and_chains_frames(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        start=source.index("async def _story_generate_images")
        end=source.index("async def _prepare_daily_story",start)
        section=source[start:end]
        self.assertIn("story_reference_for_day",section)
        self.assertIn("read_gallery_image",section)
        self.assertIn("checksum mismatch",section)
        self.assertIn("for prompt in item[\"prompts\"]",section)
        self.assertNotIn("continuity_bytes=previous",section)
        self.assertNotIn("previous,previous_type=body,out_type",section)
        self.assertIn("set_story_images",section)


if __name__=="__main__":
    unittest.main()
