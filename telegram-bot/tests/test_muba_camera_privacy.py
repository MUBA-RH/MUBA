import ast,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
BOT=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
CAMERA=(ROOT/"muba_camera.py").read_text(encoding="utf-8")
STUDIO=(ROOT/"muba_studio.py").read_text(encoding="utf-8")

class CameraPrivacyTests(unittest.TestCase):
 def test_runtime_parses(self):
  ast.parse(BOT);ast.parse(CAMERA);ast.parse(STUDIO)
 def test_camera_button_arms_native_telegram_photo_flow(self):
  self.assertGreaterEqual(BOT.count('callback_data="camera_native"'),2)
  self.assertIn('if data=="camera_native":',BOT)
  self.assertIn('context.user_data["muba_camera_waiting_photo"]=True',BOT)
  self.assertIn('MessageHandler(filters.PHOTO, muba_camera_photo',BOT)
 def test_camera_is_telegram_mini_app_route(self):
  self.assertIn('/camera?uid=',BOT)
  self.assertIn('app.router.add_get("/camera", camera_page_handler)',BOT)
  self.assertIn('app.router.add_post("/camera/generate", camera_generate_handler)',BOT)
  self.assertIn('navigator.mediaDevices.getUserMedia',CAMERA)
  self.assertIn('facingMode:"user"',CAMERA)
  self.assertIn('id="cameraFallback" type="file" accept="image/*" capture="user"',CAMERA)
  self.assertIn('fallback.click()',CAMERA)
  self.assertIn('fallback.onchange=',CAMERA)
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
 def test_camera_shows_selected_photo_and_result(self):
  self.assertIn('id="openCamera">📷 KAMERAYI AÇ',CAMERA)
  self.assertIn('id="camera" autoplay playsinline muted',CAMERA)
  self.assertIn('id="status">Fotoğraf çekildi ✓',CAMERA)
  self.assertIn('id="preview" alt="Captured camera frame"',CAMERA)
  self.assertIn('id="resultTitle">MUBA\'N HAZIR ✓',CAMERA)
  self.assertIn('take.onclick=',CAMERA)
  self.assertIn('document.getElementById("resultTitle").style.display="block"',CAMERA)
  self.assertIn('out.style.display="block"',CAMERA)
 def test_daily_limit_counts_only_success(self):
  start=BOT.index("async def camera_generate_handler")
  end=BOT.index("async def studio_generate_handler",start)
  handler=BOT[start:end]
  self.assertIn("remaining(uid)<=0",handler)
  self.assertEqual(handler.count("consume(uid)"),1)
  self.assertGreater(handler.index("consume(uid)"),handler.index("AI response contained no image"))
  self.assertIn("Daily MUBA Camera allowance used — 1/1.",handler)
  self.assertIn("Başarısız işlem hakkından düşmez",CAMERA)
  self.assertIn('fd.append("photo",capturedBlob,"camera.jpg")',CAMERA)
 def test_gallery_is_explicitly_disabled_in_test_ui(self):
  self.assertIn("Gallery: yayınlanmadı",CAMERA)
  self.assertNotIn("/studio/share",CAMERA)
  self.assertNotIn("/gallery",CAMERA)

if __name__=="__main__":unittest.main()
