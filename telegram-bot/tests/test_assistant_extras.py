from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from assistant_mode import LANGS
from assistant_extras import LABELS,STORY,LAB,GUIDE,SECURITY_PROMPT,security_check

class AssistantExtrasExam(unittest.TestCase):
 def test_all_modes_cover_five_languages(self):
  for lang in LANGS:
   self.assertIn(lang,LABELS); self.assertEqual(len(STORY[lang]),5); self.assertEqual(len(GUIDE[lang]),4)
   self.assertEqual(set(LAB[lang]),{"meme","tweet","visual"}); self.assertTrue(SECURITY_PROMPT[lang])
 def test_official_sources(self):
  for lang in LANGS:
   self.assertIn("✅",security_check(lang,"https://x.com/MUBA_RH"))
   self.assertIn("✅",security_check(lang,"https://t.me/MUBA_RH"))
   self.assertIn("✅",security_check(lang,"https://muba-rh.github.io/MUBA/"))
 def test_security_rejects_impostors_and_unpublished_ca(self):
  for lang in LANGS:
   self.assertIn("❌",security_check(lang,"https://evil.example/MUBA"))
   self.assertIn("❌",security_check(lang,"https://x.com/MUBA_RH/status/1"))
   self.assertIn("⚠️",security_check(lang,"0x1111111111111111111111111111111111111111"))
 def test_no_guardian_dependency(self):
  src=(ROOT/"assistant_extras.py").read_text(encoding="utf-8")
  self.assertNotIn("from guardian",src)
  self.assertNotIn("inspect_message",src)
 def test_no_invented_official_ca(self):
  joined=" ".join(x for lang in LANGS for x in GUIDE[lang])
  self.assertTrue("official CA" in joined or "resmi CA" in joined)

if __name__=="__main__": unittest.main(verbosity=2)
