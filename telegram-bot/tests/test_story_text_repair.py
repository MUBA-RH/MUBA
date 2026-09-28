"""The next-day producer repairs invalid languages without approving partial stories."""
import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import muba_story_text as story_text


class StoryTextRepairTest(unittest.TestCase):
    def setUp(self):
        self.episode = {
            "title": "A New Moment", "title_tr": "Yeni Bir An",
            "story": "E" * 160, "story_tr": "T" * 160,
            "story_zh": "中" * 60, "story_ar": "ع" * 160,
            "story_hi": "ह" * 80, "scene": "One new scene on a city street.",
        }

    def test_retries_only_invalid_languages_then_saves_complete_episode(self):
        answers = [json.dumps(self.episode), "中" * 158, "ह" * 159]
        with mock.patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "account", "CLOUDFLARE_API_TOKEN": "token"}), \
             mock.patch.object(story_text, "draft", side_effect=RuntimeError("awaiting a new connected episode")), \
             mock.patch.object(story_text, "_previous_state", return_value={"day": "2026-09-28", "story": "prior"}), \
             mock.patch.object(story_text, "_ask", new_callable=mock.AsyncMock, side_effect=answers) as ask, \
             mock.patch.object(story_text, "save_episode", return_value={"ready": True}) as save:
            result = asyncio.run(story_text.prepare("2026-09-29"))
        self.assertEqual(result, {"ready": True})
        self.assertEqual(ask.await_count, 3)
        saved = save.call_args.args[1]
        self.assertEqual(saved["story_zh"], "中" * 158)
        self.assertEqual(saved["story_hi"], "ह" * 159)
        self.assertEqual(saved["story_tr"], "T" * 160)

    def test_never_saves_if_translation_stays_invalid(self):
        answers = [json.dumps(self.episode)] + ["中" * 60] * 5
        with mock.patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "account", "CLOUDFLARE_API_TOKEN": "token"}), \
             mock.patch.object(story_text, "draft", side_effect=RuntimeError("awaiting a new connected episode")), \
             mock.patch.object(story_text, "_previous_state", return_value={"day": "2026-09-28", "story": "prior"}), \
             mock.patch.object(story_text, "_ask", new_callable=mock.AsyncMock, side_effect=answers), \
             mock.patch.object(story_text, "save_episode") as save:
            with self.assertRaisesRegex(RuntimeError, "story_zh"):
                asyncio.run(story_text.prepare("2026-09-29"))
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
