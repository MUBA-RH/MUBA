import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_master_identity as identity
import muba_master_visual as visual

class MasterIdentityV6Tests(unittest.TestCase):
    def test_embedded_visual_checksum(self):
        self.assertGreater(len(visual.bytes_value()),1000)
        self.assertEqual(visual.BOARD_SHA256,"f3e84997b86b084b8dacfb650aec795f8f87626c61cfba0c0a96fcf619526e7b")
    def test_body_lock(self):
        p=identity.profile()
        self.assertTrue(p["body_master"]["full_body_required"])
        self.assertEqual(p["body_master"]["feet"],"bare, no shoes")
        self.assertIn("tan/brown",p["body_master"]["fur"])
    def test_cloudflare_transport_preserves_aspect_and_body_prompt(self):
        source=(ROOT/"muba_story_cloudflare.py").read_text(encoding="utf-8")
        self.assertIn("scale=511/max_side",source)
        self.assertIn("preserve full frame/aspect ratio",source)
        self.assertIn("fully visible from cap to bare feet",source)
        self.assertIn("never add shoes",source)

if __name__=="__main__":
    unittest.main()
