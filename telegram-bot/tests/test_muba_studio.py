from __future__ import annotations
import io,pathlib,sys,unittest
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import muba_studio

class StudioExam(unittest.TestCase):
 def setUp(self): muba_studio._usage.clear()
 def test_prompt_is_bounded(self):
  self.assertLessEqual(len(muba_studio.clean_prompt("x"*500)),120)
 def test_daily_limit_is_five(self):
  uid=424242
  self.assertEqual(muba_studio.remaining(uid),5)
  for _ in range(5): self.assertTrue(muba_studio.consume(uid))
  self.assertFalse(muba_studio.consume(uid)); self.assertEqual(muba_studio.remaining(uid),0)
 def test_render_uses_reference_without_external_ai(self):
  src=Image.new("RGB",(300,300),(120,80,50)); b=io.BytesIO(); src.save(b,"JPEG")
  out=muba_studio.render_meme(b.getvalue(),"WE LIVE HERE NOW","meme")
  im=Image.open(io.BytesIO(out)); self.assertEqual(im.size,(1200,675)); self.assertEqual(im.format,"JPEG")
 def test_sticker_canvas(self):
  src=Image.new("RGB",(300,300)); b=io.BytesIO(); src.save(b,"PNG")
  im=Image.open(io.BytesIO(muba_studio.render_meme(b.getvalue(),"GM MUBA","sticker")))
  self.assertEqual(im.size,(512,512))
 def test_miniapp_has_free_prompt_and_telegram_sdk(self):
  html=muba_studio.studio_html("https://example.test")
  self.assertIn("telegram-web-app.js",html); self.assertIn("textarea",html); self.assertIn("Daily limit: 5",html)
 def test_no_guardian_dependency(self):
  src=(ROOT/"muba_studio.py").read_text(encoding="utf-8")
  self.assertNotIn("from guardian",src); self.assertNotIn("inspect_message",src)
 def test_reference_is_canonical_public_muba_asset(self):
  self.assertIn("pbs.twimg.com/profile_images/",muba_studio.REFERENCE_URL)

if __name__=="__main__": unittest.main(verbosity=2)
