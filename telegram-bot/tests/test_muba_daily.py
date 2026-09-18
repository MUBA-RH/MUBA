from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from muba_daily import DAILY,DAILY_LABELS,daily_text
from assistant_mode import LANGS

class MubaDailyExam(unittest.TestCase):
 def test_all_languages_have_daily_sections(self):
  for lang in LANGS:
   self.assertIn(lang,DAILY_LABELS)
   for section in ("x","web","telegram","updates"):
    self.assertTrue(daily_text(lang,section))
 def test_sources_are_official_user_facing(self):
  for lang in LANGS:
   joined=" ".join(DAILY[lang].values())
   self.assertIn("@MUBA_RH",joined)
   self.assertIn("muba-rh.github.io/MUBA/",joined)
 def test_internal_github_details_not_exposed(self):
  forbidden=("commit sha","pull request","branch feature/","github.com/MUBA-RH/MUBA/commit")
  for lang in LANGS:
   joined=" ".join(DAILY[lang].values()).casefold()
   for term in forbidden: self.assertNotIn(term.casefold(),joined)

if __name__=="__main__": unittest.main(verbosity=2)
