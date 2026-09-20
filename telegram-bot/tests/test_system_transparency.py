import unittest
from system_transparency import TRANSPARENCY_LABELS, TRANSPARENCY_NAV, TRANSPARENCY_PAGES
from system_notes import EXTRA_TRANSPARENCY_PAGES, TRANSLATOR_NOTE_LABELS, TRANSLATOR_NOTE_TEXT

class TransparencyTests(unittest.TestCase):
 def test_all_five_languages_have_complete_pages(self):
  self.assertEqual(set(TRANSPARENCY_PAGES),{"en","tr","zh","ar","hi"})
  self.assertTrue(all(len(pages)==12 for pages in TRANSPARENCY_PAGES.values()))
  self.assertEqual(set(TRANSPARENCY_LABELS),set(TRANSPARENCY_PAGES))
  self.assertEqual(set(TRANSPARENCY_NAV),set(TRANSPARENCY_PAGES))

 def test_core_topics_exist_in_every_locale(self):
  required=("MUBA","Assistant","Guardian","CA","GitHub")
  for lang,pages in TRANSPARENCY_PAGES.items():
   joined="\n".join(pages)
   for term in required:
    self.assertIn(term,joined,(lang,term))

 def test_current_ca_boundary_is_explicit(self):
  for lang,pages in TRANSPARENCY_PAGES.items():
   self.assertIn("CA","\n".join(pages),lang)

 def test_additional_transparency_notes_cover_all_locales(self):
  self.assertEqual(set(EXTRA_TRANSPARENCY_PAGES),set(TRANSPARENCY_PAGES))
  self.assertTrue(all(len(pages)==2 for pages in EXTRA_TRANSPARENCY_PAGES.values()))
  self.assertEqual(set(TRANSLATOR_NOTE_LABELS),set(TRANSPARENCY_PAGES))
  self.assertEqual(set(TRANSLATOR_NOTE_TEXT),set(TRANSPARENCY_PAGES))
  for lang in TRANSPARENCY_PAGES:
   self.assertIn("DEV","\n".join(EXTRA_TRANSPARENCY_PAGES[lang]))
   self.assertIn("DEV",TRANSLATOR_NOTE_TEXT[lang])

if __name__=="__main__":
 unittest.main()
