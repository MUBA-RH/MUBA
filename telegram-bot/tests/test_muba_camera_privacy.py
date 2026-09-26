import ast,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
BOT=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
CAMERA=(ROOT/"muba_camera.py").read_text(encoding="utf-8")
STUDIO=(ROOT/"muba_studio.py").read_text(encoding="utf-8")

class CameraPrivacyTests(unittest.TestCase):
 def test_runtime_parses(self):
  ast.parse(BOT);ast.parse(CAMERA);ast.parse(STUDIO)
 def test_camera_is_telegram_mini_app_route(self):
  self.assertIn('web_app=WebAppInfo(url=EXTERNAL_URL.rstrip()+"/camera?',BOT)
  self.assertIn('app.router.add_get("/camera", camera_page_handler)',BOT)
  self.assertIn('app.router.add_post("/camera/generate", camera_generate_handler)',BOT)
  self.assertIn('capture="user"',CAMERA)
 def test_source_is_not_persisted_or_published(self):
  start=BOT.index("async def camera_generate_handler")
  end=BOT.index("async def studio_generate_handler",start)
  handler=BOT[start:end]
  for forbidden in ("archive_creation(","share_gallery_item(","_publish_studio_creation(","_STUDIO_OUTPUTS[","open(","write_bytes(","write_text("):
   self.assertNotIn(forbidden,handler)
  self.assertIn('"X-MUBA-Source-Persisted":"false"',handler)
  self.assertIn('"X-MUBA-Gallery-Published":"false"',handler)
  self.assertIn('"Cache-Control":"no-store, no-cache, must-revalidate, private"',handler)
  self.assertIn("source_bytes=None",handler)
 def test_source_is_sent_only_as_ephemeral_ai_input(self):
  start=BOT.index("async def camera_generate_handler")
  end=BOT.index("async def studio_generate_handler",start)
  handler=BOT[start:end]
  self.assertIn('form.add_field("input_image_1",source_bytes',handler)
  self.assertIn("camera_ai_prompt()",handler)
  self.assertNotIn("logger.",handler.split("except Exception:",1)[0])
 def test_daily_limit_counts_only_success(self):
  start=BOT.index("async def camera_generate_handler")
  end=BOT.index("async def studio_generate_handler",start)
  handler=BOT[start:end]
  self.assertIn("remaining(uid)<=0",handler)
  self.assertEqual(handler.count("consume(uid)"),1)
  self.assertGreater(handler.index("consume(uid)"),handler.index("AI response contained no image"))
  self.assertIn("Daily MUBA Camera allowance used — 1/1.",handler)
  self.assertIn("Başarısız işlem hakkından düşmez",CAMERA)
 def test_gallery_is_explicitly_disabled_in_test_ui(self):
  self.assertIn("Gallery: yayınlanmadı",CAMERA)
  self.assertNotIn("/studio/share",CAMERA)
  self.assertNotIn("/gallery",CAMERA)

if __name__=="__main__":unittest.main()
