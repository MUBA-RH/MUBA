"""DEV's prepare button must build only tomorrow's verified private draft."""
import asyncio
import io
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from state import MemoryRepository
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

    def test_unprepared_next_day_offers_a_dev_trigger(self):
        text, markup = bot._story_unprepared_panel("2026-09-29")
        self.assertIn("2026-09-29", text)
        self.assertEqual(markup.inline_keyboard[0][0].callback_data, "story_prepare_tomorrow")
        self.assertFalse(any(button.callback_data == "story_publish"
                             for row in markup.inline_keyboard for button in row))

    def test_private_prepare_reuses_canon_and_verifies_saved_image(self):
        picture = io.BytesIO()
        Image.new("RGB", (1024, 576), "gold").save(picture, "PNG")
        previous = {"episode": {"story": "Yesterday's city scene", "title": "Origin"}}
        record = {}

        def read_day(day):
            if day == "2026-09-28":
                return previous, picture.getvalue()
            return (record["manifest"], picture.getvalue()) if record else None

        def write_day(day, episode, image):
            self.assertEqual(day, "2026-09-29")
            self.assertEqual(image, picture.getvalue())
            self.assertEqual(episode["story"], "New episode")
            record["manifest"] = {"status": "draft", "episode": episode}

        async def text_generator(day):
            self.assertEqual(day, "2026-09-29")
            self.assertEqual(muba_story.STORE.get("story_text", "2026-09-28", None)["story"],
                             "Yesterday's city scene")
            return {"day": day, "images": [], "status": "draft"}

        async def image_generator(item):
            return {**item, "images": ["private-gallery-id"]}

        with mock.patch.object(muba_story, "STORE", MemoryRepository()), \
             mock.patch.object(bot, "_story_today", return_value=date(2026, 9, 28)), \
             mock.patch.object(archive, "configured", return_value=True), \
             mock.patch.object(archive, "read_day", side_effect=read_day), \
             mock.patch.object(archive, "write_day", side_effect=write_day) as writer, \
             mock.patch.object(bot, "prepare_story_text", side_effect=text_generator) as text_call, \
             mock.patch.object(bot, "_story_generate_images", side_effect=image_generator) as image_call, \
             mock.patch.object(bot, "read_gallery_image", return_value=(picture.getvalue(), "image/png")), \
             mock.patch.object(bot, "_story_github_draft", return_value={"day": "2026-09-29"}):
            muba_story.STORE.set("story_text", "2026-09-29", {"story": "New episode"})
            first = asyncio.run(bot._story_prepare_private_tomorrow("2026-09-29"))
            second = asyncio.run(bot._story_prepare_private_tomorrow("2026-09-29"))
            self.assertEqual(first, second)
            writer.assert_called_once()
            text_call.assert_awaited_once()
            image_call.assert_awaited_once()
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                asyncio.run(bot._story_prepare_private_tomorrow("2026-09-30"))


if __name__ == "__main__":
    unittest.main()
