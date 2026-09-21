import pathlib,sys,unittest,os
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import muba_studio
class StudioAI(unittest.TestCase):
 def setUp(self):muba_studio._usage.clear()
 def test_dev_is_unlimited(self):
  for _ in range(20):self.assertTrue(muba_studio.consume(muba_studio.DEV_USER_ID))
  self.assertEqual(muba_studio.remaining(muba_studio.DEV_USER_ID),999)
 def test_regular_user_three(self):
  for _ in range(3):self.assertTrue(muba_studio.consume(123456))
  self.assertFalse(muba_studio.consume(123456))
 def test_ai_requires_explicit_credentials(self):
  old1=os.environ.pop("CLOUDFLARE_ACCOUNT_ID",None);old2=os.environ.pop("CLOUDFLARE_API_TOKEN",None)
  try:self.assertFalse(muba_studio.ai_configured())
  finally:
   if old1:os.environ["CLOUDFLARE_ACCOUNT_ID"]=old1
   if old2:os.environ["CLOUDFLARE_API_TOKEN"]=old2
 def test_payload_preserves_muba_identity(self):
  p=muba_studio.ai_payload("on the moon","sticker","data:image/jpeg;base64,abc")
  self.assertIn("MUBA identity guidance",p["prompt"]);self.assertIn("core facial identity",p["prompt"]);self.assertIn("Do not force a large centered MUBA portrait",p["prompt"]);self.assertIn("concept should lead the composition",p["prompt"]);self.assertIn("input_image",p)
 def test_all_four_formats_are_textless_by_default(self):
  self.assertFalse(muba_studio.wants_visible_text("MUBA denizde olsun"))
  for kind in ("meme","image","sticker","emoji"):
   p=muba_studio.ai_payload("MUBA denizde olsun",kind,"data:image/jpeg;base64,abc")
   self.assertIn("ABSOLUTELY NO visible words",p["prompt"])
   self.assertIn("Do not write MUBA on a cap",p["prompt"])
   self.assertNotIn("leave clean space for a short caption",p["prompt"])
 def test_explicit_visible_text_request_is_allowed(self):
  samples=(
   "MUBA denizde olsun, üstüne 'WE LIVE HERE NOW' yaz",
   "Write HELLO on the image",
   "加上文字 MUBA",
   "اكتب MUBA على الصورة",
   "चित्र पर MUBA लिखो",
  )
  for prompt in samples:
   self.assertTrue(muba_studio.wants_visible_text(prompt),prompt)
   payload=muba_studio.ai_payload(prompt,"image","data:image/jpeg;base64,abc")
   self.assertIn("user explicitly requested visible writing",payload["prompt"])
   self.assertIn("Do not invent extra captions",payload["prompt"])
 def test_plain_identity_words_do_not_enable_text(self):
  for prompt in ("MUBA at the beach","MUBA wearing a black cap","MUBA in a cinematic city"):
   self.assertFalse(muba_studio.wants_visible_text(prompt),prompt)
 def test_workers_ai_transport_is_multipart(self):
  src=(ROOT/"bot_mention.py").read_text()
  self.assertIn('aiohttp.FormData()',src)
  self.assertIn('"input_image_0"',src)
  self.assertIn('data=form',src)
  self.assertNotIn('json=ai_payload(prompt,kind,image_data)',src)
 def test_no_guardian_dependency(self):
  self.assertNotIn("guardian",(ROOT/"muba_studio.py").read_text().lower())
if __name__=="__main__":unittest.main()
