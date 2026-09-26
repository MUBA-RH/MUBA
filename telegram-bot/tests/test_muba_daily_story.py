"""Daily Story's one-scene publication and continuity gates."""
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import muba_story
from state import MemoryRepository


class DailyStoryTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryRepository()
        patch = mock.patch.object(muba_story, "STORE", self.store)
        patch.start()
        self.addCleanup(patch.stop)

    def test_each_day_is_short_connected_and_one_scene(self):
        for n in range(35):
            day = (muba_story.START + __import__('datetime').timedelta(days=n)).isoformat()
            item = muba_story.draft(day)
            self.assertTrue(150 <= len(item['story']) <= 170)
            self.assertTrue(150 <= len(item['story_tr']) <= 170)
            self.assertEqual(len(item['prompts']), 1)
            self.assertEqual(item['rules']['frames'], 1)
            self.assertEqual(item['rules']['aspect_ratio'], '16:9')
            self.assertNotIn('PREVIOUS STORY STATE:', item['prompts'][0])
            self.assertIn('TODAY\'S STORY:', item['prompts'][0])
            self.assertIn('No panels', item['prompts'][0])
            if n:
                self.assertEqual(item['previous_day'],
                                 (muba_story.START + __import__('datetime').timedelta(days=n - 1)).isoformat())

    def test_approval_requires_one_image_and_binds_reference(self):
        day = '2026-09-26'
        with self.assertRaisesRegex(ValueError, 'one approved image'):
            muba_story.publish(day)
        with self.assertRaisesRegex(ValueError, 'one image'):
            muba_story.set_images(day, ['a', 'b'])
        item = muba_story.set_images(day, ['one'])
        self.assertEqual(item['images'], ['one'])
        self.assertIsNone(muba_story.public_story(day))
        muba_story.publish(day)
        self.assertEqual(muba_story.public_story(day)['images'], ['one'])
        self.assertEqual(self.store.get('story_canon', day, None)['story'], item['story'])
        with self.assertRaisesRegex(ValueError, 'Published'):
            muba_story.set_reference(day, 'another', 'hash', 'image/jpeg')

    def test_reference_change_invalidates_pending_scene(self):
        day = '2026-09-27'
        muba_story.set_images(day, ['one'])
        muba_story.set_reference(day, 'new', 'hash', 'image/jpeg')
        self.assertEqual(muba_story.image_ids(day), [])

    def test_worker_contract_is_single_scene(self):
        job = muba_story.worker_job('2026-09-26')
        self.assertEqual(job['rules']['images'], 1)
        self.assertEqual(len(job['chapters']), 1)
        self.assertFalse(job['rules']['previous_frame_conditioning'])

    def test_published_legacy_image_batch_remains_readable(self):
        day = '2026-09-25'
        self.store.set('story_image_batches', day, {'ids': ['1', '2', '3', '4']})
        self.store.set('story_publish', day, True)
        self.assertEqual(len(muba_story.public_story(day)['images']), 4)


if __name__ == '__main__':
    unittest.main()
