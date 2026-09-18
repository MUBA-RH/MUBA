from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from human_catalog import CATALOG,match
class HumanCatalogExam(unittest.TestCase):
 def test_exactly_100_or_more_per_language(self):
  for lang in ('en','tr','zh','ar','hi'): self.assertGreaterEqual(len(CATALOG[lang]),100)
 def test_every_entry_has_answer(self):
  for lang,items in CATALOG.items():
   for q,a in items: self.assertTrue(q.strip()); self.assertTrue(a.strip())
 def test_language_locked_matching(self):
  probes={'tr':'MUBA uyur mu?','en':'Does MUBA sleep?','zh':'MUBA 会睡觉吗？','ar':'هل ينام MUBA؟','hi':'क्या MUBA सोता है?'}
  for lang,q in probes.items(): self.assertTrue(match(lang,q),(lang,q))
 def test_unrelated_question_not_matched(self):
  for lang in CATALOG: self.assertIsNone(match(lang,'987654321 completely unrelated weather football pasta'))
if __name__=='__main__': unittest.main(verbosity=2)
