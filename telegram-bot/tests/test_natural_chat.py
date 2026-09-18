from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from natural_chat import DATA,count,match

class NaturalAssistantChatExam(unittest.TestCase):
 def test_200_phrasings_per_language(self):
  for lang in ("tr","en","zh","ar","hi"):
   self.assertGreaterEqual(count(lang),200,lang)
 def test_three_answers_per_intent(self):
  for lang,intents in DATA.items():
   for intent,phrases,replies in intents:
    self.assertGreaterEqual(len(phrases),5,(lang,intent))
    self.assertGreaterEqual(len(replies),3,(lang,intent))
 def test_no_muba_prefix_required(self):
  probes={"tr":"nasılsın","en":"how are you","zh":"你好吗","ar":"كيف حالك","hi":"कैसे हो"}
  for lang,q in probes.items(): self.assertTrue(match(lang,q),(lang,q))
 def test_everyday_states(self):
  probes={"tr":["açım","uykum var","hava nasıl","yoruldum","iyi akşamlar"],"en":["I'm hungry","I'm sleepy","how's the weather","I'm tired","good evening"],"zh":["我饿了","我困了","天气怎么样","我累了","晚上好"],"ar":["أنا جائع","أنا نعسان","كيف الطقس","أنا متعب","مساء الخير"],"hi":["मुझे भूख लगी है","नींद आ रही है","मौसम कैसा है","मैं थक गया हूँ","शुभ संध्या"]}
  for lang,qs in probes.items():
   for q in qs: self.assertTrue(match(lang,q),(lang,q))
 def test_language_is_locked(self):
  self.assertIsNone(match("en","nasılsın"))
  self.assertIsNone(match("tr","how are you"))
 def test_colloquial_everyday_forms(self):
  probes={"tr":["iyim","napiyon","acıktım","pilim bitti","dışardayım"],"en":["doing great","wyd","getting hungry"],"zh":["我挺好","干嘛呢","有点饿"],"ar":["أنا تمام","شو عم تعمل","جعت"],"hi":["मैं बढ़िया हूँ","क्या सीन है","भूख लग रही"]}
  for lang,qs in probes.items():
   for q in qs: self.assertTrue(match(lang,q),(lang,q))
 def test_unrelated_does_not_false_match(self):
  for lang in DATA:
   self.assertIsNone(match(lang,"zxqv 92817"))

if __name__=="__main__": unittest.main(verbosity=2)
