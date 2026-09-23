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
import muba_story_cloudflare as bridge
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
        self.assertEqual(item["rules"]["visual_style"],"daily-story-reference-first-v3")

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
        self.assertIn("ONLY MUBA IDENTITY AND VISUAL-STYLE SOURCE",prompt)
        self.assertIn("four separate full-bleed 16:9 images",prompt)
        self.assertIn("never a collage",prompt)
        self.assertIn("FACE/IDENTITY LOCK",prompt)


class CloudflareReferenceInputTests(unittest.TestCase):
    def test_reference_preparation_contract_is_present(self):
        source=inspect.getsource(bridge._prepare_reference)
        self.assertIn("511/max_side",source)
        self.assertIn('format="JPEG"',source)
        self.assertIn('"image/jpeg"',source)


class CloudflareRetryTests(unittest.TestCase):
    def test_only_provider_flag_retries(self):
        self.assertTrue(bridge._flagged(400,'AIError: output has been flagged. prompt input image combination'))
        self.assertFalse(bridge._flagged(500,'server error'))
        safe=bridge._safe_retry_prompt('IDENTITY RULES CURRENT BEAT: MUBA walks into a quiet street.')
        self.assertIn('friendly fictional illustrated scene',safe)
        self.assertIn('MUBA walks into a quiet street',safe)
        self.assertNotIn('IDENTITY RULES',safe)


class SequentialIdentityEngineTests(unittest.TestCase):
    def test_cloudflare_uses_9b_multi_reference_contract(self):
        source=inspect.getsource(bridge)
        self.assertIn("flux-2-klein-9b",source)
        self.assertIn('input_image_1',source)
        self.assertIn('guidance","5.0',source)
        self.assertIn("exactly ONE full-bleed cinematic 16:9 image",source)
        self.assertIn("immutable MUBA identity/style reference",source)

    def test_story_generation_chains_previous_frame(self):
        source=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn("continuity_bytes=previous_body",source)
        self.assertIn("previous_body,previous_type=body,out_type",source)


class CloudflareFilterIsolationTests(unittest.TestCase):
    def test_filter_diagnostic_is_text_only_and_discarded(self):
        source=inspect.getsource(bridge.generate)
        self.assertIn("diagnostic=text-only-ok",source)
        self.assertIn("reference-combination-flagged",source)
        self.assertIn("A simple friendly fictional character standing in a quiet room.",source)


class ProductionFunctionTests(unittest.IsolatedAsyncioTestCase):
    async def test_generation_reads_fresh_gallery_reference_and_forwards_same_bytes_four_times(self):
        tree=ast.parse((ROOT/"bot_mention.py").read_text())
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=="_story_generate_images")
        body=b"fresh-dev-reference"; digest=hashlib.sha256(body).hexdigest()
        backend=mock.AsyncMock(return_value=(b"generated","image/png"))
        archive=mock.Mock(side_effect=[{"id":str(i)} for i in range(4)])
        save=mock.Mock(return_value={"images":[str(i) for i in range(4)]})
        namespace={
            "_archive_studio_output":archive,"set_story_images":save,
            "story_reference_for_day":mock.Mock(return_value={"gallery_id":"ref","sha256":digest}),
            "read_gallery_image":mock.Mock(return_value=(body,"image/jpeg")),
            "hashlib":hashlib,
        }
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(ROOT/"bot_mention.py"),"exec"),namespace)
        session=mock.MagicMock(); session.__aenter__.return_value=session
        with mock.patch("aiohttp.ClientSession",return_value=session), \
             mock.patch.object(bridge,"configured",return_value=True), \
             mock.patch.object(bridge,"generate",backend):
            await namespace["_story_generate_images"]({"day":"2099-03-08","status":"draft","prompts":["a","b","c","d"]})
        self.assertEqual(backend.await_count,4)
        for call in backend.call_args_list:
            self.assertEqual(call.args[2],body)
            self.assertEqual(call.kwargs["reference_type"],"image/jpeg")
        save.assert_called_once_with("2099-03-08",["0","1","2","3"])


if __name__=="__main__":
    unittest.main()
