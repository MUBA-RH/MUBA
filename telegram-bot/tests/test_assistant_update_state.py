import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_brain

class AssistantUpdateStateTests(unittest.TestCase):
    def setUp(self):
        muba_brain.reset_runtime_state()

    def test_seen_state_is_per_user_and_area(self):
        self.assertIsNone(muba_brain.get_assistant_update_seen(1,"studio"))
        muba_brain.mark_assistant_update_seen(1,"studio","u1")
        self.assertEqual(muba_brain.get_assistant_update_seen(1,"studio"),"u1")
        self.assertIsNone(muba_brain.get_assistant_update_seen(1,"gallery"))
        self.assertIsNone(muba_brain.get_assistant_update_seen(2,"studio"))

if __name__=="__main__":
    unittest.main(verbosity=2)
