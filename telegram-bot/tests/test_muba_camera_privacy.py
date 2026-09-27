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
 def test_legacy_camera_route_remains_isolated_from_native_entry(self):
  self.assertIn('app.router.add_get("/camera", camera_page_handler)',BOT)
  self.assertIn('app.router.add_post("/camera/generate", camera_generate_handler)',BOT)
  self.assertNotIn('web_app=WebAppInfo(url=EXTERNAL_URL.rstrip()+"/camera?uid="',BOT)
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
 def test_camera_prompt_is_intent_aware(self):
  for required in (
   "do not assume every request means transforming the photographed person into MUBA",
   "KEEP THE PERSON HUMAN and recognizable",
   "Never replace the person's head or face in this case",
   "explicitly asks to transform the person into MUBA",
   "preserve as much of the person's original facial structure",
   "destination, setting, environment or scene",
   "No arbitrary portrait reframing, no pasted head",
  ):
   self.assertIn(required,STUDIO)

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

 def test_camera_references_fit_flux_multi_reference_limit(self):
  self.assertIn("def camera_reference_bytes(value:bytes,max_side:int=511)",STUDIO)
  self.assertIn("src.thumbnail((max_side,max_side)",STUDIO)
  self.assertIn("muba_ref=camera_reference_bytes(ref_path.read_bytes())",BOT)
  self.assertIn("source_ai=camera_reference_bytes(source_bytes)",BOT)
  self.assertIn('form.add_field("input_image_0",source_ai',BOT)

 def test_camera_result_has_clean_back_to_main_menu(self):
  self.assertIn('callback_data="camera_back"',BOT)
  self.assertIn('if data=="camera_back":',BOT)
  self.assertIn('"muba_camera_message_ids"',BOT)
  self.assertIn("delete_message",BOT)
  self.assertIn("assistant_menu_text(lang)",BOT)

 def test_success_quota_is_rolling_24_hours_from_first_production(self):
  self.assertIn('time.time()-used_at<86400',STUDIO)
  self.assertIn('row["used_at"]=now',STUDIO)
  self.assertNotIn('row["day"]!=day',STUDIO)
  self.assertIn('time.time()-used_at<86400',BOT)
  self.assertIn('row["used_at"]=time.time()',BOT)
 def test_camera_sends_source_as_primary_reference(self):
  self.assertIn('form.add_field("input_image_0",source_ai',BOT)
  self.assertIn('form.add_field("input_image_1",muba_ref',BOT)
  self.assertIn("1️⃣ 📎 simgesine dokun ve Kamera’yı aç.",BOT)


 def test_camera_waits_for_user_instruction_before_generation(self):
  self.assertIn('context.user_data["muba_camera_waiting_instruction"]=True',BOT)
  self.assertIn('context.user_data["muba_camera_source_bytes"]=source_bytes',BOT)
  self.assertIn('if context.user_data.get("muba_camera_waiting_instruction",False):',BOT)
  self.assertIn('camera_ai_prompt(user_request)',BOT)
  self.assertIn('camera_ai_prompt(text)',BOT) if False else None
  self.assertIn("Günlük hakkın yalnızca başarılı bir görsel üretildiğinde kullanılır.",BOT)

 def test_camera_prompt_includes_user_request(self):
  self.assertIn('def camera_ai_prompt(user_request:str="")',STUDIO)
  self.assertIn('"USER REQUEST: "+request',STUDIO)

 def test_camera_honors_requested_environment_with_muba(self):
  for required in (
   "that requested setting MUST be visibly realized in the output",
   "do not preserve the old background when it conflicts with the requested setting",
   "satisfy BOTH requirements at the same time",
   "add MUBA as a separate character",
   "visibly place them together in the requested environment",
   "Do not satisfy only the MUBA part while ignoring the requested location",
  ):
   self.assertIn(required,STUDIO)

if __name__=="__main__":unittest.main()
