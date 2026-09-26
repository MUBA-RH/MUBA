"""Restart durability and scope for private Daily Story state."""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from state import MemoryRepository
from muba_story_state import StoryState


class StoryStateTests(unittest.TestCase):
    def test_approved_story_survives_new_process(self):
        objects = {}

        def request(method, path, **kwargs):
            if method == 'PUT':
                objects[path] = kwargs['body']
                return mock.Mock()
            if path not in objects:
                return None
            return mock.Mock(content=objects[path])

        with mock.patch('muba_story_state._r2_enabled', return_value=True), mock.patch(
            'muba_story_state._r2_request', side_effect=request
        ):
            first = StoryState(MemoryRepository())
            first.set('story_review_approved', '2026-09-27', {'image': 'scene-one'})
            second = StoryState(MemoryRepository())
            self.assertEqual(second.get('story_review_approved', '2026-09-27'), {'image': 'scene-one'})
            self.assertEqual(json.loads(objects['daily-story/state/story_review_approved/2026-09-27.json'])['value']['image'], 'scene-one')
            with self.assertRaisesRegex(ValueError, 'another namespace'):
                second.set('studio_tokens', '2026-09-27', {})


if __name__ == '__main__':
    unittest.main()
