from __future__ import annotations

import json
import os
import pathlib
import sys
import unittest
from unittest import mock
from urllib.parse import urlparse

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_gallery


class _FakeResponse:
    def __init__(self,status_code=200,content=b""):
        self.status_code=status_code
        self.content=content


class GalleryR2Tests(unittest.TestCase):
    def setUp(self):
        self.saved={key:os.environ.get(key) for key in (
            "MUBA_R2_ACCOUNT_ID",
            "MUBA_R2_ACCESS_KEY_ID",
            "MUBA_R2_SECRET_ACCESS_KEY",
            "MUBA_R2_BUCKET",
            "CLOUDFLARE_ACCOUNT_ID",
        )}
        os.environ["MUBA_R2_ACCOUNT_ID"]="acct123"
        os.environ["MUBA_R2_ACCESS_KEY_ID"]="access123"
        os.environ["MUBA_R2_SECRET_ACCESS_KEY"]="secret123"
        os.environ["MUBA_R2_BUCKET"]="muba-gallery"
        self.objects={}

        def fake_request(method,url,content=b"",headers=None,timeout=None):
            parsed=urlparse(url)
            prefix="/muba-gallery/"
            self.assertTrue(parsed.path.startswith(prefix))
            key=parsed.path[len(prefix):]
            if method=="PUT":
                self.objects[key]=bytes(content)
                return _FakeResponse(200,b"")
            if method=="GET":
                if key not in self.objects:
                    return _FakeResponse(404,b"")
                return _FakeResponse(200,self.objects[key])
            return _FakeResponse(405,b"")

        self.patch=mock.patch.object(muba_gallery.httpx,"request",side_effect=fake_request)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        for key,value in self.saved.items():
            if value is None:
                os.environ.pop(key,None)
            else:
                os.environ[key]=value

    def test_r2_archive_survives_without_local_filesystem(self):
        item=muba_gallery.archive_creation(
            b"persistent-image",
            "image/png",
            "MUBA denizde olsun",
            "image",
            "web",
        )
        self.assertEqual(item["label"],"MUBA at the Beach")
        self.assertTrue(item["file"].startswith("images/"))
        self.assertIn("gallery/index.json",self.objects)
        self.assertIn(item["file"],self.objects)

        rows=muba_gallery.list_gallery()
        self.assertEqual([row["id"] for row in rows],[item["id"]])

        body,content_type=muba_gallery.read_gallery_image(item["id"])
        self.assertEqual(body,b"persistent-image")
        self.assertEqual(content_type,"image/png")

        state=muba_gallery.storage_status()
        self.assertEqual(state["backend"],"r2")
        self.assertTrue(state["persistent"])
        self.assertTrue(state["writable"])

    def test_r2_moderation_updates_persistent_index(self):
        item=muba_gallery.archive_creation(
            b"image",
            "image/png",
            "MUBA",
            "meme",
            "telegram",
        )
        hidden=muba_gallery.set_gallery_visibility(item["id"],"hidden")
        self.assertEqual(hidden["visibility"],"hidden")
        self.assertEqual(muba_gallery.list_gallery(),[])
        self.assertIsNone(muba_gallery.read_gallery_image(item["id"]))

        body,content_type=muba_gallery.read_gallery_image(item["id"],include_nonpublic=True)
        self.assertEqual(body,b"image")
        self.assertEqual(content_type,"image/png")

        persisted=json.loads(self.objects["gallery/index.json"].decode("utf-8"))
        self.assertEqual(persisted[0]["visibility"],"hidden")

    def test_incomplete_r2_configuration_fails_closed(self):
        os.environ.pop("MUBA_R2_SECRET_ACCESS_KEY",None)
        with self.assertRaises(muba_gallery.GalleryStorageError):
            muba_gallery.storage_status()


if __name__=="__main__":
    unittest.main(verbosity=2)
