"""Daily Story's one-scene publication and continuity gates."""
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import muba_story
from muba_story_visual import normalize_ready_image
from state import MemoryRepository


class DailyStoryTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryRepository()
        patch = mock.patch.object(muba_story, "STORE", self.store)
        patch.start()
        self.addCleanup(patch.stop)

    def test_each_day_is_short_connected_and_one_scene(self):
        for n in range(2):
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

    def test_new_origin_starts_without_experiments_and_next_day_requires_it(self):
        day = '2026-09-29'
        with self.assertRaisesRegex(RuntimeError, 'awaiting a new connected episode'):
            muba_story.draft(day)
        episode = {'title': 'A Name on the Street', 'title_tr': 'Sokakta Bir İsim',
                   'story': 'The young stranger unfolds the paper for the others to see. Someone sketches the little name on a window; soon the whole block begins asking where it came from.',
                   'story_tr': 'Genç, kâğıdı açıp çevresindekilere gösterir. Biri adı dükkân camına çizer; sokaktan geçenler durup bu sözcüğün nereden geldiğini birbirlerine sormaya başlar.',
                   'story_zh': '年轻人打开纸张给大家看，人群聚了过来。有人把这个名字画在商店玻璃上，路过的陌生人也停下脚步，好奇地打听它从何而来。',
                   'story_ar': 'يفتح الشاب الورقة ليراها الجميع. يرسم أحدهم الاسم على زجاج متجر، وسرعان ما يتوقف المارة ليسألوا من أين جاء هذا الاسم الغريب.',
                   'story_hi': 'युवा कागज़ खोलकर सबको दिखाता है। कोई दुकान की खिड़की पर नाम बनाता है; राहगीर रुकते हैं और पूछने लगते हैं कि यह नाम कहाँ से आया।',
                   'scene': 'city storefront window, a young person showing the paper to a curious crowd'}
        self.assertTrue(150 <= len(episode['story']) <= 170)
        self.assertTrue(150 <= len(episode['story_tr']) <= 170)
        with self.assertRaisesRegex(RuntimeError, 'preceding canonical episode'):
            muba_story.save_episode(day, episode)
        origin = {'title': 'The Paper', 'title_tr': 'Uçan Kâğıt',
                  'story': 'A paper marked “MUBA” glides above a busy city crowd. The wind drops it into a young person\'s hand; they smile, and strangers pause to look at the same name.',
                  'story_tr': 'Kalabalık caddede “MUBA” yazılı bir kâğıt başların üstünden süzülür. Rüzgâr onu bir gencin eline bırakır; genç gülümser, kalabalık ilk kez aynı söze bakar.',
                  'story_zh': episode['story_zh'], 'story_ar': episode['story_ar'], 'story_hi': episode['story_hi'],
                  'scene': 'paper flying above a human crowd on a lively city street'}
        first = muba_story.save_episode(muba_story.ORIGIN_START.isoformat(), origin)
        self.assertIsNone(first['previous_day'])
        item = muba_story.save_episode(day, episode)
        self.assertEqual(item['previous_day'], muba_story.ORIGIN_START.isoformat())
        self.assertEqual(item['story'], episode['story'])
        self.assertEqual(muba_story.draft(day)['story'], episode['story'])

    def test_approval_requires_one_image_and_binds_reference(self):
        day = '2026-09-26'
        with self.assertRaisesRegex(ValueError, 'one approved image'):
            muba_story.publish(day)
        with self.assertRaisesRegex(ValueError, 'one image'):
            muba_story.set_images(day, ['a', 'b'])
        item = muba_story.set_images(day, ['one'])
        self.assertEqual(item['images'], ['one'])
        self.assertIsNone(muba_story.public_story(day))
        with self.assertRaisesRegex(ValueError, 'DEV review'):
            muba_story.publish(day)
        muba_story.approve_today(day, today=muba_story.START)
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

    def test_tomorrow_review_is_bound_to_scene_and_reference(self):
        today = muba_story.START
        tomorrow = '2026-09-27'
        with self.assertRaisesRegex(ValueError, 'one image'):
            muba_story.approve_tomorrow(tomorrow, today=today)
        muba_story.request_preview(tomorrow)
        self.assertTrue(muba_story.preview_requested(tomorrow))
        muba_story.set_images(tomorrow, ['scene-one'])
        muba_story.approve_tomorrow(tomorrow, today=today)
        self.assertTrue(muba_story.review_approved(tomorrow))
        muba_story.set_images(tomorrow, ['scene-two'])
        self.assertFalse(muba_story.review_approved(tomorrow))
        with self.assertRaisesRegex(ValueError, "Only tomorrow"):
            muba_story.approve_tomorrow('2026-09-28', today=today)

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

    def test_dev_supplied_scene_is_landscape_and_normalized(self):
        from io import BytesIO
        from PIL import Image
        supplied=BytesIO()
        Image.new('RGB',(1536,864),'orange').save(supplied,format='PNG')
        ready=normalize_ready_image(supplied.getvalue())
        with Image.open(BytesIO(ready)) as scene:
            self.assertEqual(scene.size,(1024,576))
        near=BytesIO()
        Image.new('RGB',(1672,941),'orange').save(near,format='PNG')
        with Image.open(BytesIO(normalize_ready_image(near.getvalue()))) as scene:
            self.assertEqual(scene.size,(1024,576))
        square=BytesIO()
        Image.new('RGB',(1024,1024),'orange').save(square,format='PNG')
        with self.assertRaisesRegex(ValueError,'16:9'):
            normalize_ready_image(square.getvalue())


if __name__ == '__main__':
    unittest.main()
