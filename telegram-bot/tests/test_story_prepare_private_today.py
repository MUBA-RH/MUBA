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
