from __future__ import annotations
import os
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_gallery

class GalleryModerationTests(unittest.TestCase):
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

    def test_new_item_is_public_and_can_be_hidden_or_rejected(self):
        item=muba_gallery.archive_creation(b"image","image/png","MUBA sahilde","image","web")
        self.assertEqual(item["visibility"],"public")
        self.assertEqual(len(muba_gallery.list_gallery()),1)
        hidden=muba_gallery.set_gallery_visibility(item["id"],"hidden")
        self.assertEqual(hidden["visibility"],"hidden")
        self.assertEqual(muba_gallery.list_gallery(),[])
        self.assertIsNone(muba_gallery.read_gallery_image(item["id"]))
        body,content_type=muba_gallery.read_gallery_image(item["id"],include_nonpublic=True)
        self.assertEqual(body,b"image")
        self.assertEqual(content_type,"image/png")
        rejected=muba_gallery.set_gallery_visibility(item["id"],"rejected")
        self.assertEqual(rejected["visibility"],"rejected")
        self.assertEqual(muba_gallery.list_gallery(visibility=None)[0]["visibility"],"rejected")

    def test_invalid_visibility_is_rejected(self):
        item=muba_gallery.archive_creation(b"image","image/png","MUBA","image","telegram")
        with self.assertRaises(ValueError):
            muba_gallery.set_gallery_visibility(item["id"],"deleted")

if __name__=="__main__":
    unittest.main(verbosity=2)
