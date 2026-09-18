import io,pathlib,sys,unittest
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import muba_studio
class StudioRuntimeExam(unittest.TestCase):
 def setUp(self):muba_studio._usage.clear()
 def test_quota(self):
  for _ in range(5):self.assertTrue(muba_studio.consume(7))
  self.assertFalse(muba_studio.consume(7))
 def test_render(self):
  im=Image.new("RGB",(300,300));b=io.BytesIO();im.save(b,"JPEG")
  out=muba_studio.render_meme(b.getvalue(),"GM MUBA","meme")
  self.assertEqual(Image.open(io.BytesIO(out)).size,(1200,675))
 def test_miniapp(self):
  h=muba_studio.studio_html("https://example.test");self.assertIn("telegram-web-app.js",h);self.assertIn("5 creations/day",h)
 def test_isolation(self):
  s=(ROOT/"muba_studio.py").read_text();self.assertNotIn("from guardian",s);self.assertNotIn("inspect_message",s)
if __name__=="__main__":unittest.main()
