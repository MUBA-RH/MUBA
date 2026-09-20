import unittest
from system_transparency import TRANSPARENCY_LABELS, TRANSPARENCY_NAV, TRANSPARENCY_PAGES

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

if __name__=="__main__":
 unittest.main()
