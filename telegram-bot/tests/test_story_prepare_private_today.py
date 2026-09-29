"""DEV's prepare button builds only the current day's verified private draft."""
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
        self.assertEqual(markup.inline_keyboard[0][0].callback_data, "story_test")
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

    def test_private_prepare_wakes_chatgpt_and_reads_verified_draft(self):
        record = {"draft": None}
        async def tick(seconds):
            record["draft"] = ({"status": "draft"}, b"new-image")
        with mock.patch.object(bot, "_story_today", return_value=date(2026, 9, 29)), \
             mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", side_effect=lambda day: record["draft"]), \
             mock.patch.object(archive, "request_chatgpt_day", return_value="queued") as wake, \
             mock.patch.object(bot.asyncio, "sleep", side_effect=tick), \
             mock.patch.object(bot, "_story_github_draft", return_value={"day": "2026-09-29"}) as read:
            self.assertEqual(asyncio.run(bot._story_prepare_private_today("2026-09-29")),
                             {"day": "2026-09-29"})
            wake.assert_called_once_with("2026-09-29")
            read.assert_awaited_once()
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                asyncio.run(bot._story_prepare_private_today("2026-09-30"))

    def test_current_day_error_names_request_stage(self):
        with mock.patch.object(bot, "_story_today", return_value=date(2026, 9, 29)), \
             mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "request_chatgpt_day", side_effect=RuntimeError("403")):
            with self.assertRaisesRegex(bot.StoryPreparationError, "ChatGPT isteği oluşturulamadı"):
                asyncio.run(bot._story_prepare_private_today("2026-09-29"))

    def test_request_is_private_and_idempotent(self):
        calls = []
        def api(path, method="GET", body=None):
            calls.append((path, method))
            if path.startswith("/pulls?state=all"):
                return [{"title": "Daily Story Request: 2026-09-29", "state": "open"}]
            return None
        with mock.patch.object(archive, "_private"), \
             mock.patch.object(archive, "read_day", return_value=None), \
             mock.patch.object(archive, "_settings", return_value=("MUBA-RH/MUBA-DAILY-STORY", "private-token", "main")), \
             mock.patch.object(archive, "_api", side_effect=api):
            self.assertEqual(archive.request_chatgpt_day("2026-09-29"), "queued")
        self.assertFalse(any(method == "POST" for _, method in calls))

    def test_missing_day_opens_one_dated_request_pr(self):
        calls = []
        def api(path, method="GET", body=None):
            calls.append((path, method, body))
            if path.startswith("/pulls?state=all"):
                return []
            if path == "/git/ref/heads/main":
                return {"object": {"sha": "base-sha"}}
            return None
        with mock.patch.object(archive, "_private") as private, \
             mock.patch.object(archive, "read_day", return_value=None), \
             mock.patch.object(archive, "_settings", return_value=("MUBA-RH/MUBA-DAILY-STORY", "private-token", "main")), \
             mock.patch.object(archive, "_api", side_effect=api):
            self.assertEqual(archive.request_chatgpt_day("2026-09-29"), "queued")
        private.assert_called_once()
        posts = [(path, body) for path, method, body in calls if method == "POST"]
        self.assertEqual([path for path, _ in posts], ["/git/refs", "/pulls"])
        self.assertEqual(posts[-1][0], "/pulls")
        import json
        self.assertEqual(json.loads(posts[-1][1])["title"], "Daily Story Request: 2026-09-29")
        self.assertTrue(any(path == "/contents/daily-story/requests/2026-09-29.json" and method == "PUT"
                            for path, method, _ in calls))

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
