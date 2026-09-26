"""Only real Studio generations enter the public Gallery; Story and DEV stay separate."""
import asyncio
import os
import pathlib
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_gallery


class _Request:
    def __init__(self,data,origin=""):
        self.data=data
        self.headers={"Origin":origin}

    async def json(self):
        return self.data


class GalleryShareFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=mock.patch.dict(os.environ,{"MUBA_GALLERY_DIR":self.tmp.name,"TELEGRAM_BOT_TOKEN":"123456:gallery-test","RENDER_EXTERNAL_URL":"https://example.org"})
        self.env.start()
        from system_transparency import TRANSPARENCY_PAGES
        page_lengths={language:len(pages) for language,pages in TRANSPARENCY_PAGES.items()}
        import bot_mention
        # Importing the bot extends this global catalog; keep unrelated tests isolated.
        for language,pages in TRANSPARENCY_PAGES.items():
            del pages[page_lengths[language]:]
        self.bot=bot_mention
        self.bot._STUDIO_OUTPUTS.clear()

    def tearDown(self):
        self.bot._STUDIO_OUTPUTS.clear()
        self.env.stop()
        self.tmp.cleanup()

    def _output(self,key,source,owner):
        self.bot._STUDIO_OUTPUTS[key]={"body":b"studio-image","content_type":"image/png","created":time.time(),"prompt":"Community MUBA","kind":"meme","source":source,"owner":owner}

    def _share(self,key,origin="",**auth):
        return asyncio.run(self.bot.studio_share_handler(_Request({"key":key,**auth},origin)))

    def test_story_archive_stays_out_of_gallery_while_user_creation_is_published(self):
        story=muba_gallery.archive_creation(b"frame","image/png","Story frame","image","telegram")
        self.assertEqual(muba_gallery.list_gallery(shared_only=True),[])
        self.assertEqual(muba_gallery.read_gallery_image(story["id"])[0],b"frame")
        item=self.bot._publish_studio_creation(b"studio-image","image/png","Community MUBA","meme","web")
        self.assertEqual(item["source"],"web")
        self.assertEqual([row["id"] for row in muba_gallery.list_gallery(shared_only=True)],[item["id"]])

    def test_legacy_explicit_share_endpoint_remains_compatible(self):
        self._output("visitor","web","visitor")
        result=self._share("visitor",origin="https://muba-rh.github.io")
        self.assertEqual(result.status,200)
        self.assertEqual(len(muba_gallery.list_gallery(shared_only=True)),1)
        self.assertEqual(self._share("visitor",origin="https://muba-rh.github.io").status,200)
        self.assertEqual(len(muba_gallery.list_gallery(shared_only=True)),1)

    def test_untrusted_origin_and_dev_previews_cannot_share(self):
        self._output("visitor","web","visitor")
        self.assertEqual(self._share("visitor",origin="https://untrusted.example").status,403)
        self.bot._STUDIO_OUTPUTS["visitor"]["preview_only"]=True
        self.assertEqual(self._share("visitor",origin="https://muba-rh.github.io").status,403)
        self._output("developer","telegram",934598759)
        token=self.bot.studio_token(934598759,self.bot.TOKEN)
        self.assertEqual(self._share("developer",uid=934598759,studioToken=token).status,403)
        self.assertEqual(muba_gallery.list_gallery(shared_only=True),[])

    def test_telegram_owner_can_share_but_other_users_cannot(self):
        self._output("creator","telegram",921)
        wrong=self.bot.studio_token(922,self.bot.TOKEN)
        self.assertEqual(self._share("creator",uid=922,studioToken=wrong).status,403)
        correct=self.bot.studio_token(921,self.bot.TOKEN)
        self.assertEqual(self._share("creator",uid=921,studioToken=correct).status,200)
        self.assertEqual(len(muba_gallery.list_gallery(shared_only=True)),1)
