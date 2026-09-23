"""Offline behavior tests; no Telegram messages or billable image requests."""
import ast
import hashlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PIL import Image
import muba_daily_story_reference as reference
import muba_story
import muba_story_cloudflare as bridge
from state import MemoryRepository


class ApprovedReferenceTests(unittest.TestCase):
    def test_asset_is_exact_unmodified_approved_upload_and_correct_mime(self):
        body,mime=reference.load_reference()
        self.assertEqual(hashlib.sha256(body).hexdigest(),
                         "175a87e2331228d079487b7e0a1119c7a182649a72f877e3069407f16a8b88a0")
        self.assertEqual(mime,"image/jpeg")
        with Image.open(io.BytesIO(body)) as image:
            self.assertEqual(image.format,"JPEG")
            self.assertEqual(image.size,(1536,1536))
            image.verify()

    def test_missing_or_changed_asset_never_falls_back(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"reference.jpg"
            with mock.patch.object(reference,"REFERENCE_PATH",path):
                with self.assertRaisesRegex(RuntimeError,"unavailable"):
                    reference.load_reference()
                path.write_bytes(b"substitute-image")
                with self.assertRaisesRegex(RuntimeError,"checksum mismatch"):
                    reference.load_reference()

    def test_path_is_absolute_and_not_a_mutable_social_profile_url(self):
        self.assertTrue(reference.REFERENCE_PATH.is_absolute())
        source=(ROOT/"muba_daily_story_reference.py").read_text()
        self.assertNotIn("pbs.twimg.com",source)
        self.assertNotIn("from muba_face_architecture import",source)

    def test_all_prompts_use_new_identity_style_without_frozen_scenery(self):
        with mock.patch.object(muba_story,"STORE",MemoryRepository()):
            item=muba_story.draft("2099-03-08")
        for prompt in item["prompts"]:
            self.assertIn("DEV-APPROVED MUBA 2D CHIBI REFERENCE",prompt)
            self.assertIn("pink cheek patches",prompt)
            self.assertIn("identity AND drawing style",prompt)
            self.assertIn("EXAMPLE SCENERY, not required content",prompt)
            self.assertIn("Expressions, gaze, mouth movement and poses follow the action",prompt)
            self.assertIn("NO visible text except the existing MUBA lettering on the cap",prompt)
            self.assertNotIn("reject large round ears",prompt)
            self.assertNotIn("Viewer-left eye sits higher",prompt)
            self.assertNotIn("black $MUBA hoodie",prompt)
            self.assertIn("CURRENT BEAT:",prompt)


class ReferenceBatchTests(unittest.TestCase):
    def setUp(self):
        self.store=MemoryRepository()
        self.patch=mock.patch.object(muba_story,"STORE",self.store)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.day="2099-03-08"
        self.old=["old-1","old-2","old-3","old-4"]
        self.new=["new-1","new-2","new-3","new-4"]

    def test_unapproved_legacy_batch_is_not_reused_or_published(self):
        self.store.set("story_images",self.day,self.old)
        self.assertEqual(muba_story.draft(self.day)["images"],[])
        with self.assertRaises(ValueError):
            muba_story.publish(self.day)
        self.assertEqual(self.store.get("story_images",self.day),self.old)

    def test_published_legacy_images_are_preserved(self):
        self.store.set("story_images",self.day,self.old)
        self.store.set("story_publish",self.day,True)
        item=muba_story.public_story(self.day)
        self.assertEqual(item["images"],self.old)
        self.assertIsNone(item["image_reference"])
        with self.assertRaisesRegex(ValueError,"cannot be replaced"):
            muba_story.set_images(self.day,self.new)
        self.assertEqual(muba_story.image_ids(self.day),self.old)

    def test_new_batch_is_bound_to_reference_but_still_needs_approval(self):
        item=muba_story.set_images(self.day,self.new)
        self.assertEqual(item["images"],self.new)
        self.assertEqual(item["image_reference"],reference.reference_metadata())
        self.assertIsNone(muba_story.public_story(self.day))
        self.assertEqual(muba_story.publish(self.day)["images"],self.new)

    def test_stale_reference_version_or_checksum_cannot_publish(self):
        for key in ("version","sha256"):
            metadata=reference.reference_metadata()
            metadata[key]="old-value"
            self.store.set("story_image_batches",self.day,{"ids":self.old,"reference":metadata})
            self.assertEqual(muba_story.image_ids(self.day),[])
            with self.assertRaises(ValueError):
                muba_story.publish(self.day)

    def test_partial_batch_cannot_publish(self):
        muba_story.set_images(self.day,self.new[:3])
        with self.assertRaises(ValueError):
            muba_story.publish(self.day)

    def test_reference_and_images_are_saved_in_one_state_write(self):
        with mock.patch.object(self.store,"set",wraps=self.store.set) as save:
            muba_story.set_images(self.day,self.new)
        batch_writes=[call for call in save.call_args_list if call.args[0].startswith("story_image")]
        self.assertEqual(len(batch_writes),1)
        self.assertEqual(batch_writes[0].args[2],{"ids":self.new,"reference":reference.reference_metadata()})


class StoryGenerationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Execute the actual production function without booting the bot or
        # requiring production credentials. No copied implementation is tested.
        tree=ast.parse((ROOT/"bot_mention.py").read_text())
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=="_story_generate_images")
        self.archive=mock.Mock(side_effect=[{"id":str(i)} for i in range(4)])
        self.save=mock.Mock(return_value={"images":[str(i) for i in range(4)]})
        namespace={"_archive_studio_output":self.archive,"set_story_images":self.save}
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(ROOT/"bot_mention.py"),"exec"),namespace)
        self.generate=namespace["_story_generate_images"]
        self.item={"day":"2099-03-08","status":"draft","prompts":[f"panel {i}" for i in range(4)]}
        self.session=mock.MagicMock()
        self.session.__aenter__.return_value=self.session
        self.backend=mock.AsyncMock(return_value=(b"generated-test-image","image/png"))
        for patch in (mock.patch("aiohttp.ClientSession",return_value=self.session),
                      mock.patch.object(bridge,"configured",return_value=True),
                      mock.patch.object(bridge,"generate",self.backend)):
            patch.start()
            self.addCleanup(patch.stop)

    async def test_exact_same_approved_image_is_forwarded_to_all_four_calls(self):
        body,mime=reference.load_reference()
        await self.generate(self.item)
        self.assertEqual(self.backend.await_count,4)
        for index,call in enumerate(self.backend.call_args_list):
            self.assertEqual(call.args,(self.session,self.item["prompts"][index],body))
            self.assertEqual(call.kwargs,{"reference_type":mime})
        self.session.get.assert_not_called()
        self.assertEqual(self.archive.call_count,4)
        self.save.assert_called_once_with(self.item["day"],[str(i) for i in range(4)])

    async def test_fourth_generation_failure_archives_and_publishes_nothing(self):
        self.backend.side_effect=[(b"image","image/png")]*3+[RuntimeError("generation failed")]
        with self.assertRaises(RuntimeError):
            await self.generate(self.item)
        self.archive.assert_not_called()
        self.save.assert_not_called()

    async def test_bad_reference_stops_before_any_generation(self):
        with mock.patch.object(reference,"load_reference",side_effect=RuntimeError("checksum mismatch")):
            with self.assertRaisesRegex(RuntimeError,"checksum mismatch"):
                await self.generate(self.item)
        self.backend.assert_not_awaited()
        self.archive.assert_not_called()
        self.save.assert_not_called()

    async def test_invalid_panel_count_stops_before_any_generation(self):
        self.item["prompts"].pop()
        with self.assertRaises(ValueError):
            await self.generate(self.item)
        self.backend.assert_not_awaited()
        self.save.assert_not_called()

    async def test_published_story_is_not_regenerated(self):
        self.item["status"]="published"
        self.assertIs(await self.generate(self.item),self.item)
        self.backend.assert_not_awaited()
        self.archive.assert_not_called()
        self.save.assert_not_called()

    async def test_archive_failure_does_not_replace_story_batch(self):
        self.archive.side_effect=[{"id":"first"},None]
        with self.assertRaisesRegex(RuntimeError,"archive failed"):
            await self.generate(self.item)
        self.save.assert_not_called()


class StoryBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_multipart_forwards_correct_image_bytes_mime_and_dimensions(self):
        body,mime=reference.load_reference()
        response=mock.MagicMock()
        response.__aenter__.return_value=response
        response.status=200
        response.headers={"Content-Type":"image/png"}
        response.read=mock.AsyncMock(return_value=b"test-image")
        session=mock.Mock()
        session.post.return_value=response
        with mock.patch.dict(os.environ,{"CLOUDFLARE_ACCOUNT_ID":"test-account","CLOUDFLARE_API_TOKEN":"test-token"}), \
             mock.patch.multiple(bridge,WIDTH=1024,HEIGHT=576), mock.patch("aiohttp.FormData") as form_type:
            self.assertEqual(await bridge.generate(session,"test prompt",body,reference_type=mime),(b"test-image","image/png"))
        form_type.return_value.add_field.assert_any_call("width","1024")
        form_type.return_value.add_field.assert_any_call("height","576")
        form_type.return_value.add_field.assert_any_call("input_image_0",body,filename="muba-reference.jpg",content_type="image/jpeg")
        session.post.assert_called_once()

    async def test_square_override_fails_before_request(self):
        session=mock.Mock()
        with mock.patch.object(bridge,"configured",return_value=True), mock.patch.multiple(bridge,WIDTH=1024,HEIGHT=1024):
            with self.assertRaisesRegex(RuntimeError,"16:9"):
                await bridge.generate(session,"prompt",b"image")
        session.post.assert_not_called()


if __name__=="__main__":
    unittest.main()
