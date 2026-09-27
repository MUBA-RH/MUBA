"""The private GitHub handoff must fail closed and verify the complete dated pair."""
import base64
import asyncio
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import muba_story
import muba_story_github as archive


class PrivateArchiveTests(unittest.TestCase):
    def setUp(self):
        env = mock.patch.dict(os.environ, {
            "MUBA_STORY_GITHUB_REPO": "MUBA-RH/muba-daily-story-private",
            "MUBA_STORY_GITHUB_TOKEN": "test-token",
        })
        env.start()
        self.addCleanup(env.stop)
        self.files = {}

        def api(path, method="GET", body=None):
            if path == "":
                return {"private": True}
            key = path.split("?", 1)[0]
            if method == "GET":
                return ({"content": base64.b64encode(self.files[key]).decode("ascii"),
                         "sha": "version"} if key in self.files else None)
            payload = json.loads(body)
            self.files[key] = base64.b64decode(payload["content"])
            return {"content": {"sha": "new-version"}}

        patch = mock.patch.object(archive, "_api", side_effect=api)
        patch.start()
        self.addCleanup(patch.stop)

    def test_private_record_is_read_with_same_day_and_image_checksum(self):
        beat = muba_story.BEATS[0]
        episode = {"title": beat[0], "title_tr": beat[1], "story": beat[2],
                   "story_tr": beat[3], "scene": beat[4]}
        picture = io.BytesIO()
        Image.new("RGB", (1024, 576), "peachpuff").save(picture, "PNG")
        manifest = archive.write_day("2026-09-26", episode, picture.getvalue())
        stored, image = archive.read_day("2026-09-26")
        self.assertEqual(stored, manifest)
        self.assertEqual(image, self.files[archive._path("2026-09-26", "scene.png")])
        self.files[archive._path("2026-09-26", "scene.png")] += b"changed"
        with self.assertRaisesRegex(RuntimeError, "changed"):
            archive.read_day("2026-09-26")

    def test_large_github_scene_is_read_from_git_blob(self):
        picture = b"scene" * 225000  # exceeds GitHub Contents API's 1 MB inline limit
        blob_sha = "a" * 40
        def api(path, method="GET", body=None):
            if path.startswith("/contents/"):
                return {"sha": blob_sha, "encoding": "none", "content": "", "size": len(picture)}
            if path == "/git/blobs/" + blob_sha:
                return {"sha": blob_sha, "encoding": "base64",
                        "content": base64.b64encode(picture).decode("ascii")}
            raise AssertionError(path)
        with mock.patch.object(archive, "_api", side_effect=api):
            self.assertEqual(archive._get("2026-09-27", "scene.png"), (picture, blob_sha))

    def test_public_repository_is_rejected_before_upload(self):
        with mock.patch.dict(os.environ, {"MUBA_STORY_GITHUB_REPO": "MUBA-RH/MUBA"}):
            with self.assertRaisesRegex(RuntimeError, "public MUBA"):
                archive.read_day("2026-09-26")
        with mock.patch.object(archive, "_api", return_value={"private": False}):
            with self.assertRaisesRegex(RuntimeError, "private repository"):
                archive.read_day("2026-09-26")

    def test_missing_image_never_returns_a_story(self):
        path = archive._path("2026-09-26", "story.json")
        self.files[path] = json.dumps({"version": 1, "day": "2026-09-26",
                                       "image_sha256": "missing"}).encode()
        with self.assertRaisesRegex(RuntimeError, "missing"):
            archive.read_day("2026-09-26")

    def test_next_day_needs_the_preceding_github_episode(self):
        beat = muba_story.BEATS[1]
        episode = {"title": beat[0], "title_tr": beat[1], "story": beat[2],
                   "story_tr": beat[3], "scene": beat[4]}
        with self.assertRaisesRegex(RuntimeError, "Previous Daily Story"):
            archive.write_day("2026-09-27", episode, b"not-an-image")

    def test_telegram_reader_uses_the_dated_record_without_generating(self):
        from state import MemoryRepository
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "1:dummy",
                                           "RENDER_EXTERNAL_URL": "https://muba.test"}):
            import bot_mention
        beat = muba_story.BEATS[0]
        manifest = {"version": 1, "day": "2026-09-26", "episode": {
            "title": beat[0], "title_tr": beat[1], "story": beat[2],
            "story_tr": beat[3], "scene": beat[4]}}
        with mock.patch.object(muba_story, "STORE", MemoryRepository()), \
             mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", return_value=(manifest, b"private image")), \
             mock.patch.object(bot_mention, "_story_archive_preview",
                               side_effect=lambda item, *_: muba_story.set_images(item["day"], ["image-id"])) as saved:
            first = asyncio.run(bot_mention._story_github_draft("2026-09-26"))
            second = asyncio.run(bot_mention._story_github_draft("2026-09-26"))
            self.assertEqual(first["story_tr"], beat[3])
            self.assertEqual(second["images"], ["image-id"])
            saved.assert_called_once()

    def test_new_origin_reads_private_draft_and_dev_selected_language(self):
        from state import MemoryRepository
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "1:dummy",
                                           "RENDER_EXTERNAL_URL": "https://muba.test"}):
            import bot_mention
        episode = {"title": "The Paper", "title_tr": "Uçan Kâğıt",
                   "story": "A paper marked MUBA glides above a busy city crowd. The wind drops it into a young person's hand; they smile, and strangers pause to look at the same new name.",
                   "story_tr": "Kalabalık caddede MUBA yazılı bir kâğıt başların üstünden süzülür. Rüzgâr onu bir gencin eline bırakır; genç gülümser, kalabalık ilk kez aynı söze bakar.",
                   "story_zh": "写着MUBA的纸飞过城市人群，落在一个年轻人的手中；陌生人们微笑着围了过来。",
                   "story_ar": "تحلّق ورقة تحمل اسم MUBA فوق الحشد وتهبط في يد شاب؛ يبتسم الناس ويتجمعون لرؤيتها.",
                   "story_hi": "MUBA लिखा कागज़ शहर की भीड़ के ऊपर उड़ता है और एक युवा के हाथ में आ गिरता है; लोग मुस्कुराकर उसे देखने रुकते हैं।",
                   "scene": "paper flying over a human crowd on a bright city street"}
        manifest = {"version": 1, "day": "2026-09-28", "episode": episode}
        with mock.patch.object(muba_story, "STORE", MemoryRepository()), \
             mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", return_value=(manifest, b"private image")), \
             mock.patch.object(bot_mention, "_story_archive_preview",
                               side_effect=lambda item, *_: muba_story.set_images(item["day"], ["image-id"])):
            item = asyncio.run(bot_mention._story_github_draft("2026-09-28"))
            self.assertIsNone(item["previous_day"])
            self.assertEqual(bot_mention._story_display_text(item, "zh"), episode["story_zh"])
            self.assertEqual(bot_mention._story_display_text(item, "en"), episode["story"])
            self.assertEqual(item["images"], ["image-id"])


if __name__ == "__main__":
    unittest.main()
