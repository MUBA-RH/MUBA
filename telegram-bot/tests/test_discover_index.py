import unittest

from assistant_mode import QUESTIONS
from assistant_extras import TOPIC_PROGRESS
from discover_index import SECTIONS, LABELS, entries
from ecosystem_expansion import ASK_RECORDS, COMMUNITY_RECORDS, TRANSPARENCY_RECORDS
from system_transparency import TRANSPARENCY_PAGES
from system_notes import EXTRA_TRANSPARENCY_PAGES


class DiscoverIndexTests(unittest.TestCase):
    def test_every_existing_knowledge_record_has_a_discover_path_in_each_language(self):
        for lang in LABELS:
            pages = {lang: TRANSPARENCY_PAGES[lang] + EXTRA_TRANSPARENCY_PAGES[lang]
                     + [title + "\n\n" + body for _, title, body in TRANSPARENCY_RECORDS[lang]]}
            all_entries = [entry for section in SECTIONS for entry in entries(lang, section, pages)]
            expected = (len(QUESTIONS[lang])
                        + sum(len(items) for items in TOPIC_PROGRESS[lang].values())
                        + len(ASK_RECORDS[lang]) + len(COMMUNITY_RECORDS[lang])
                        + len(pages[lang]))
            self.assertEqual(len(all_entries), expected, lang)
            self.assertTrue(all(title and body for title, body in all_entries), lang)
            self.assertTrue(all(len(body) < 3900 for _, body in all_entries), lang)


if __name__ == "__main__":
    unittest.main()
