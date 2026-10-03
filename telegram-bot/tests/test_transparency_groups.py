import os
import unittest
from unittest import mock

from transparency_groups import GROUP_PAGES, GROUP_LABELS, GROUP_NAV, page_group


class TransparencyGroupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "1:dummy", "RENDER_EXTERNAL_URL": "https://muba.test"}):
            import bot_mention
        cls.bot = bot_mention

    def setUp(self):
        # Gallery tests restore the shared base-page registry after importing
        # the bot. Rebuild the production composition without mutating it.
        from system_transparency import TRANSPARENCY_PAGES
        from system_notes import EXTRA_TRANSPARENCY_PAGES
        from ecosystem_expansion import TRANSPARENCY_RECORDS
        pages = {lang: TRANSPARENCY_PAGES[lang][:12] + EXTRA_TRANSPARENCY_PAGES[lang]
                 + [title + "\n\n" + body for _, title, body in TRANSPARENCY_RECORDS[lang]]
                 for lang in GROUP_LABELS}
        patch = mock.patch.object(self.bot, "TRANSPARENCY_PAGES", pages)
        patch.start()
        self.addCleanup(patch.stop)

    def test_every_page_has_exactly_one_parent_in_every_language(self):
        flat = [page for pages in GROUP_PAGES for page in pages]
        self.assertEqual(len(flat), len(set(flat)))
        self.assertEqual(len(GROUP_PAGES), 5)
        for lang in GROUP_LABELS:
            self.assertEqual(sorted(flat), list(range(len(self.bot.TRANSPARENCY_PAGES[lang]))))
            self.assertTrue(all(1 <= len(pages) <= 5 for pages in GROUP_PAGES))
            self.assertEqual(len(GROUP_LABELS[lang]), 5)
            self.assertEqual(len(GROUP_NAV[lang]), 5)

    def test_leaf_returns_to_its_parent_and_neighbors_stay_in_group(self):
        for lang in GROUP_LABELS:
            root = self.bot.transparency_index_keyboard(lang)
            self.assertEqual(sum(button.callback_data.startswith("transparency_group:")
                                 for row in root.inline_keyboard for button in row), 5)
            for group, pages in enumerate(GROUP_PAGES):
                submenu = self.bot.transparency_group_keyboard(lang, group)
                self.assertEqual([row[0].callback_data for row in submenu.inline_keyboard[:-1]],
                                 [f"transparency:{page}" for page in pages])
                for page in pages:
                    leaf = self.bot.transparency_keyboard(lang, page)
                    callbacks = [button.callback_data for row in leaf.inline_keyboard for button in row]
                    self.assertIn(f"transparency_group:{group}", callbacks)
                    self.assertIn("transparency_menu", callbacks)
                    self.assertNotIn("menu", callbacks)
                    for value in callbacks:
                        if value.startswith("transparency:"):
                            self.assertEqual(page_group(int(value.split(":")[1])), group)
                    self.assertIn(self.bot.TRANSPARENCY_PAGES[lang][page],
                                  self.bot.transparency_text(lang, page))



if __name__ == "__main__":
    unittest.main()
