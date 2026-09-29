"""Telegram previews only the verified private draft; production is scheduled."""
import asyncio
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import muba_story
import muba_story_github as archive

class PrivatePrepareTests(unittest.TestCase):
    def test_story_gallery_cache_is_hidden_at_creation(self):
        with mock.patch.object(bot, "archive_creation", return_value={"id": "hidden-frame"}) as save, \
             mock.patch.object(bot, "set_story_images", return_value={"images": ["hidden-frame"]}):
            bot._story_archive_preview({"day": "2026-09-29", "prompts": ["city scene"]},
                                       b"scene", "image/png", "github-daily-story")
        self.assertEqual(save.call_args.kwargs["visibility"], "hidden")

    @classmethod
    def setUpClass(cls):
        global bot
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "1:dummy",
                                           "RENDER_EXTERNAL_URL": "https://muba.test"}):
            import bot_mention as bot

    def test_unprepared_current_day_offers_isolated_test_only(self):
        text, markup = bot._story_unprepared_panel("2026-09-29")
        self.assertIn("2026-09-29", text)
        self.assertEqual(markup.inline_keyboard[0][0].callback_data, "story_director")
        self.assertEqual(markup.inline_keyboard[1][0].callback_data, "story_test")
        self.assertIn("kilitli", text)
        self.assertFalse(any(button.callback_data == "story_prepare_today"
                             for row in markup.inline_keyboard for button in row))
        self.assertFalse(any(button.callback_data == "story_publish"
                             for row in markup.inline_keyboard for button in row))

    def test_missing_current_day_is_unprepared_without_implicit_generation(self):
        with mock.patch.object(bot, "_story_today", return_value=date(2026, 9, 29)), \
             mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", return_value=None), \
             mock.patch.object(muba_story, "is_published", return_value=False):
            self.assertIsNone(asyncio.run(bot._story_github_draft("2026-09-29")))
            with self.assertRaisesRegex(RuntimeError, "not ready"):
                asyncio.run(bot._story_github_draft("2026-09-28"))

    def test_current_day_requires_private_archive(self):
        with mock.patch.object(archive, "configured", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "not configured"):
                asyncio.run(bot._story_github_draft("2026-09-29"))

    def test_telegram_has_no_production_request_writer(self):
        self.assertFalse(hasattr(archive, "request_chatgpt_day"))
        self.assertFalse(hasattr(bot, "_story_prepare_private_today"))

    def test_web_button_is_below_approved_current_day_photo_only(self):
        item = {"day": "2026-09-29", "status": "draft", "images": ["approved-scene"]}
        with mock.patch.object(bot, "_story_today", return_value=date(2026, 9, 29)), \
             mock.patch.object(bot, "_story_production_enabled", return_value=True), \
             mock.patch.object(bot, "story_review_approved", return_value=False):
            actions = bot._story_photo_actions(item)
            self.assertEqual(actions.inline_keyboard[0][0].callback_data, "story_approve_today:2026-09-29")
        with mock.patch.object(bot, "_story_today", return_value=date(2026, 9, 29)), \
             mock.patch.object(bot, "_story_production_enabled", return_value=True), \
             mock.patch.object(bot, "story_review_approved", return_value=True):
            actions = bot._story_photo_actions(item)
            self.assertEqual(actions.inline_keyboard[0][0].callback_data, "story_publish:2026-09-29")
            self.assertIsNone(bot._story_photo_actions({**item, "day": "2026-09-28"}))
            self.assertIsNone(bot._story_photo_actions({**item, "status": "published"}))
            self.assertIsNone(bot._story_photo_actions({**item, "images": []}))
        with mock.patch.object(bot, "_story_production_enabled", return_value=False):
            self.assertIsNone(bot._story_photo_actions(item))

    def test_telegram_photo_carries_the_action_under_its_caption(self):
        item = {"day": "2026-09-29", "status": "draft", "images": ["approved-scene"],
                "story": "English preview", "story_tr": "Türkçe önizleme"}
        message = mock.Mock()
        message.reply_photo = mock.AsyncMock()
        with mock.patch.object(bot, "_story_today", return_value=date(2026, 9, 29)), \
             mock.patch.object(bot, "_story_production_enabled", return_value=True), \
             mock.patch.object(bot, "story_review_approved", return_value=True), \
             mock.patch.object(bot, "read_gallery_image", return_value=(b"scene", "image/png")):
            asyncio.run(bot._story_send_preview(message, item, "tr"))
        fields = message.reply_photo.await_args.kwargs
        self.assertEqual(fields["caption"], "Türkçe önizleme")
        self.assertEqual(fields["reply_markup"].inline_keyboard[0][0].callback_data,
                         "story_publish:2026-09-29")

    def test_isolated_test_photo_approval_and_signed_web_preview(self):
        from types import SimpleNamespace
        from urllib.parse import parse_qs, urlparse
        from state import MemoryRepository
        day="2026-09-29"
        record=({"version":1,"day":day,"test_id":day+"-01","status":"test",
                 "episode":{"title":"Street meeting","story":"Private test text"},
                 "image_sha256":"test-image"},b"private-png")
        fingerprint=bot._story_test_fingerprint(record)
        with mock.patch.object(bot,"STORY_STORE",MemoryRepository()), \
             mock.patch.object(bot,"TOKEN","1:dummy"), \
             mock.patch.object(bot,"EXTERNAL_URL","https://muba.test"), \
             mock.patch.object(archive,"read_test_day",return_value=record):
            self.assertEqual(bot._story_test_photo_actions(record,day).inline_keyboard[0][0].callback_data,
                             "story_test_approve:"+day)
            bot.STORY_STORE.set("story_test_approved",day,fingerprint)
            self.assertEqual(bot._story_test_photo_actions(record,day).inline_keyboard[0][0].callback_data,
                             "story_test_web:"+day)
            url=bot._story_test_web_url(day)
            query={key:values[0] for key,values in parse_qs(urlparse(url).query).items()}
            request=SimpleNamespace(query=query)
            self.assertEqual(asyncio.run(bot.story_test_web_handler(request)).status,403)
            bot.STORY_STORE.set("story_test_web",day,fingerprint)
            response=asyncio.run(bot.story_test_web_handler(request))
            self.assertEqual(response.status,200)
            self.assertIn("Private test text",response.text)
            self.assertIn("NOT PUBLISHED",response.text)
            self.assertEqual(response.headers["Cache-Control"],"no-store")
            self.assertEqual(asyncio.run(bot.story_test_web_handler(
                SimpleNamespace(query={**query,"signature":"0"*64}))).status,403)

    def test_web_approval_rechecks_private_text_and_exact_image(self):
        day = "2026-09-29"
        episode = {key: key + " text" for key in
                   ("story", "story_tr", "story_zh", "story_ar", "story_hi")}
        item = {"day": day, "status": "draft", "images": ["private-frame"], **episode}
        record = ({"status": "draft", "episode": episode}, b"approved-png")
        with mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", return_value=record), \
             mock.patch.object(bot, "read_gallery_image", return_value=(b"approved-png", "image/png")):
            asyncio.run(bot._story_verify_private_publication(day, item))
        with mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", return_value=record), \
             mock.patch.object(bot, "read_gallery_image", return_value=(b"other-png", "image/png")):
            with self.assertRaisesRegex(ValueError, "image changed"):
                asyncio.run(bot._story_verify_private_publication(day, item))
        with mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", return_value=({"status": "test", "episode": episode}, b"approved-png")):
            with self.assertRaisesRegex(ValueError, "draft is unavailable"):
                asyncio.run(bot._story_verify_private_publication(day, item))
        with mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", return_value=record):
            with self.assertRaisesRegex(ValueError, "draft and one image"):
                asyncio.run(bot._story_verify_private_publication("2026-09-30", item))

    def test_live_test_uses_separate_path_and_request(self):
        calls=[]
        def api(path, method="GET", body=None):
            calls.append((path,method,body))
            return None
        with mock.patch.object(archive,"_private"), \
             mock.patch.object(archive,"read_test_day",return_value=None), \
             mock.patch.object(archive,"_settings",return_value=("MUBA-RH/MUBA-DAILY-STORY","token","main")), \
             mock.patch.object(archive,"_api",side_effect=api):
            self.assertEqual(archive.request_chatgpt_test("2026-09-28"),"queued")
        self.assertTrue(any(path == "/contents/daily-story/requests/test-2026-09-28-01.json" and method == "PUT"
                            for path,method,_ in calls))
        import base64, json
        payload=json.loads(calls[-1][2])
        self.assertEqual(payload["branch"],"daily-story-test-queue")
        self.assertEqual(json.loads(base64.b64decode(payload["content"]))["source"],"telegram-dev-test")
        self.assertFalse(any(path.startswith("/pulls") or path.startswith("/git/ref") for path,_,_ in calls))
        self.assertIn("/daily-story/tests/2026-09-28-01/scene.png",archive._path("2026-09-28","scene.png",test=True))


if __name__ == "__main__":
    unittest.main()
