import os
import pathlib
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
import muba_gallery

class GalleryArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old=os.environ.get("MUBA_GALLERY_DIR")
        os.environ["MUBA_GALLERY_DIR"]=self.tmp.name

    def tearDown(self):
        if self.old is None:
            os.environ.pop("MUBA_GALLERY_DIR",None)
        else:
            os.environ["MUBA_GALLERY_DIR"]=self.old
        self.tmp.cleanup()

    def test_archives_without_personal_data(self):
        item=muba_gallery.archive_creation(b"fake-png","image/png","MUBA denizde olsun","image","web")
        self.assertEqual(item["label"],"MUBA at the Beach")
        self.assertEqual(item["kind"],"image")
        self.assertEqual(item["source"],"web")
        self.assertNotIn("user_id",item)
        self.assertNotIn("username",item)
        self.assertNotIn("prompt",item)
        rows=muba_gallery.list_gallery()
        self.assertEqual(rows[0]["id"],item["id"])
        data,content_type=muba_gallery.read_gallery_image(item["id"])
        self.assertEqual(data,b"fake-png")
        self.assertEqual(content_type,"image/png")

    def test_all_studio_formats_supported(self):
        for kind in ("meme","image","sticker","emoji","reaction"):
            item=muba_gallery.archive_creation((kind+"x").encode(),"image/png",kind,kind,"telegram")
            expected="emoji" if kind=="reaction" else kind
            self.assertEqual(item["kind"],expected)
        self.assertEqual(len(muba_gallery.list_gallery()),5)

    def test_storage_reports_configured_persistence(self):
        state=muba_gallery.storage_status()
        self.assertTrue(state["persistent"])
        self.assertTrue(state["writable"])

if __name__=="__main__":
    unittest.main(verbosity=2)
