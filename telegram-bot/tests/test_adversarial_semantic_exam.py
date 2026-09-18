"""Adversarial semantic generalization regression tests.

These are intentionally different phrasings from the original happy-path
conversation tests. Production baseline protections must continue to pass.
"""
from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import muba_brain as brain
CASES=[
 ("tr","MUBA niye var?","purpose"),("tr","Onu diğerlerinden ayıran şey ne?","difference"),("tr","İnsanlar bu işin neresinde?","community"),
 ("en","Why does MUBA exist?","purpose"),("en","What sets it apart from the rest?","difference"),("en","Where do the people fit into all this?","community"),
 ("zh","MUBA 为什么存在？","purpose"),("zh","它独特的地方在哪里？","difference"),("zh","大家在这里要做什么？","community"),
 ("ar","لماذا يوجد MUBA؟","purpose"),("ar","ما الذي يميزه عن البقية؟","difference"),("ar","أين مكان الناس في هذا كله؟","community"),
 ("hi","MUBA आखिर क्यों है?","purpose"),("hi","बाकियों से इसकी खास बात क्या है?","difference"),("hi","इस सब में लोगों की जगह क्या है?","community"),
]
class AdversarialSemanticExam(unittest.TestCase):
 def setUp(self): brain.reset_runtime_state()
 def test_unseen_natural_paraphrases(self):
  for lang,q,want in CASES:
   with self.subTest(q=q):
    d=brain.build_decision(q,chat_id=42,user_id=101)
    self.assertEqual(d.language,lang); self.assertIn(want,d.intents); self.assertTrue(d.response)
if __name__=="__main__": unittest.main(verbosity=2)
