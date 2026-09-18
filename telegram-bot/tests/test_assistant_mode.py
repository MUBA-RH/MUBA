from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import muba_brain as brain
from assistant_mode import LANGS,QUESTIONS,group_event,assistant_relevant,guided_answer

class AssistantModeExam(unittest.TestCase):
 def setUp(self): brain.reset_runtime_state()
 def test_language_lock_persists(self):
  for i,lang in enumerate(LANGS):
   self.assertTrue(brain.set_assistant_language(100+i,lang)); self.assertEqual(brain.get_assistant_language(100+i),lang)
 def test_guided_questions_cover_all_core_topics(self):
  expected={'origin','identity','difference','purpose','community','plan'}
  for lang in LANGS:
   self.assertEqual(len(QUESTIONS[lang]),12)
   self.assertEqual({t for t,_ in QUESTIONS[lang]},expected)
   for i in range(12): self.assertTrue(guided_answer(lang,i))
 def test_group_is_silent_for_normal_chat(self):
  for text in ['Akşam maç kaçta?','Bitcoin ne olur?','hello guys','Bugün yemek ne yiyelim?','What is the weather?']:
   self.assertIsNone(group_event(text),text)
 def test_group_guardian_events(self):
  self.assertEqual(group_event('/ca'),'ca')
  self.assertEqual(group_event('MUBA fake CA scam'),'fake_ca')
  self.assertEqual(group_event('Who is MUBA DEV?'),'dev')
  self.assertEqual(group_event('MUBA official source?'),'official')
  self.assertEqual(group_event('What is MUBA?'),'assistant_redirect')
 def test_private_scope(self):
  self.assertTrue(assistant_relevant('MUBA nedir?'))
  self.assertTrue(assistant_relevant('Topluluğun rolü ne?'))
  self.assertFalse(assistant_relevant('Galatasaray maçı kaçta?'))

if __name__=='__main__': unittest.main(verbosity=2)
