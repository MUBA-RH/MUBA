        self.assertIn("20-35 percent",layer)

    def test_generation_uses_hf_ipadapter_canonical_reference_for_all_panels(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        section=bot[bot.index("async def _story_generate_images"):bot.index("async def story_public_handler")]
        self.assertIn("muba_story_hf",section)
        self.assertIn("generate_anchor(session,character_anchor_prompt(),REFERENCE_URL)",section)
        self.assertIn("hf_story_generate(session,prompt,anchor_path",section)
        self.assertNotIn("previous_frame",section)
        self.assertNotIn("character_anchor,_=await render",section)

    def test_hf_bridge_is_real_flux_ipadapter_and_token_gated(self):
        bridge=(ROOT/"muba_story_hf.py").read_text(encoding="utf-8")
        self.assertIn('InstantX/flux-IP-adapter',bridge)
        self.assertIn('API_CANDIDATES=("process_image","predict")',bridge)
        self.assertIn('HF_TOKEN',bridge)
        self.assertIn('MAX_ATTEMPTS',bridge)
        self.assertIn('asyncio.wait_for',bridge)
        self.assertIn('from gradio_client import Client, handle_file',bridge)
        self.assertIn('Client(SPACE_ID,token=token,verbose=False)',bridge)
        self.assertIn('view_api(return_format="dict",print_info=False)',bridge)
        self.assertIn('handle_file(reference)',bridge)
        self.assertIn('PANEL_IP_WEIGHT',bridge)
        self.assertIn('ANCHOR_IP_WEIGHT',bridge)
        self.assertIn('"0.82"',bridge)
        self.assertIn('"0.78"',bridge)
        self.assertNotIn('RioShiina/ImageGen',bridge)
        self.assertNotIn('run_imagegen',bridge)
        self.assertNotIn('CLOUDFLARE_API_TOKEN',bridge)

    def test_technical_change_is_not_literal_story_title(self):
        item=muba_story.draft("2026-09-22")
        self.assertNotIn("four-image production connected",item["theme"].lower())
        self.assertNotIn("four-image production connected",item["story"].lower())

    def test_dev_menu_exposes_story_director(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn('InlineKeyboardButton("🎬 MUBA Daily Story",callback_data="story_director")',bot)
        self.assertIn('if is_dev(user_id):',bot)

    def test_story_callback_chain_exists(self):
        bot=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
        self.assertIn('if data=="story_director":',bot)
        self.assertIn('if data=="story_publish":',bot)
        self.assertIn('callback_data="story_publish"',bot)
        self.assertIn('callback_data="menu"',bot)