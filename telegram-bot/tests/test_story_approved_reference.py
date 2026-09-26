"""Approved references and one-scene generation safety checks."""
import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import muba_story
import muba_story_visual
import muba_story_cloudflare as cloudflare_bridge


class StoryReferenceTests(unittest.TestCase):
    def test_bundled_scene_and_master_are_readable(self):
        from PIL import Image
        scene = muba_story.SCENE_REFERENCE
        master = ROOT.parent/'daily-story-worker/muba_daily_story_master_reference.png'
        with Image.open(scene) as image:
            self.assertEqual(image.size, (1536, 864))
        with Image.open(master) as image:
            self.assertEqual(image.size, (1536, 1152))
        self.assertEqual(muba_story.reference_for_day('2026-09-26')['file'], str(scene))

    def test_prompt_does_not_demand_yesterdays_picture(self):
        prompt = muba_story_visual.story_identity_prompt()
        self.assertIn('canonical MUBA identity remains authoritative', prompt)
        self.assertIn('SINGLE SCENE CONTRACT', prompt)
        self.assertIn('never condition on yesterday', prompt)

    def test_cloudflare_reference_transport_and_filter_retry(self):
        source = inspect.getsource(cloudflare_bridge._prepare_reference)
        self.assertIn('511/max_side', source)
        self.assertTrue(cloudflare_bridge._flagged(400, 'output has been flagged'))
        self.assertFalse(cloudflare_bridge._flagged(500, 'server error'))
        safe = cloudflare_bridge._safe_retry_prompt('RULES CURRENT BEAT: MUBA enters a quiet street.')
        self.assertIn('MUBA enters a quiet street', safe)
        self.assertNotIn('RULES', safe)

    def test_telegram_web_gates_remain_dev_approved(self):
        bot = (ROOT/'bot_mention.py').read_text(encoding='utf-8')
        web = (ROOT.parent/'index.html').read_text(encoding='utf-8')
        self.assertIn('callback_data="story_publish"', bot)
        self.assertIn('story_reference_for_day', bot)
        self.assertIn('if(urls.length!==1 && urls.length!==4)', web)
        self.assertIn('id="story-share-x"', web)
        self.assertIn('MUBA_STORY_SCHEDULER_SECRET', bot)


if __name__ == '__main__':
    unittest.main()
