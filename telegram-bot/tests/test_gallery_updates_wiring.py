import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
BOT=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
INDEX=(ROOT.parent/"index.html").read_text(encoding="utf-8")

class GalleryAndUpdatesWiringTests(unittest.TestCase):
    def test_gallery_routes_and_both_studio_sources_are_wired(self):
        self.assertIn('app.router.add_get("/gallery", gallery_list_handler)',BOT)
        self.assertIn('app.router.add_get("/gallery/image/{item_id}", gallery_image_handler)',BOT)
        self.assertIn('app.router.add_post("/studio/share", studio_share_handler)',BOT)
        self.assertIn('list_gallery(limit=limit,kind=kind,shared_only=True)',BOT)
        self.assertNotIn('_archive_studio_output(body,out_type,prompt,kind,"web")',BOT)
        self.assertNotIn('_archive_studio_output(body,out_type,prompt,kind,"telegram")',BOT)

    def test_public_gallery_metadata_excludes_user_identity(self):
        handler=BOT[BOT.index("async def gallery_list_handler"):BOT.index("async def studio_share_handler")]
        self.assertNotIn('"user_id"',handler)
        self.assertNotIn('"username"',handler)
        self.assertNotIn('"prompt"',handler)
        for key in ('"label"','"kind"','"source"','"created_at"','"image_url"'):
            self.assertIn(key,handler)

    def test_assistant_has_update_center_and_area_badges(self):
        self.assertIn('callback_data="updates_center"',BOT)
        self.assertIn('data.startswith("updates_area:")',BOT)
        self.assertIn('_update_badge(lang,user_id,"studio")',BOT)
        self.assertIn('_update_badge(lang,user_id,"gallery")',BOT)
        self.assertIn('_update_badge(lang,user_id,"web")',BOT)
        self.assertIn('_update_badge(lang,user_id,"telegram")',BOT)

    def test_web_gallery_is_manual_horizontal_scroll_without_pager(self):
        self.assertIn('id="gallery-strip"',INDEX)
        self.assertIn('overflow-x: auto',INDEX)
        self.assertIn('scroll-snap-type: x proximity',INDEX)
        self.assertNotIn('id="gallery-prev"',INDEX)
        self.assertNotIn('id="gallery-next"',INDEX)
        self.assertIn('loadGallery();',INDEX)

if __name__=="__main__":
    unittest.main(verbosity=2)
