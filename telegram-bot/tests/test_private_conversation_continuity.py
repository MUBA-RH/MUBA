from __future__ import annotations
import pathlib,sys,time,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import conversation_continuity as cc

class ConversationContinuityExam(unittest.TestCase):
 def setUp(self): cc._STATE.clear()
 def test_wellbeing_followup_five_languages(self):
  cases={
   "tr":("İyi gidiyor. Senin keyfin nasıl?","Keyfim yerinde sağ ol"),
   "en":("I'm good. How are you?","I'm good, thanks"),
   "zh":("我很好。你好吗？","我很好，谢谢"),
   "ar":("أنا بخير. كيف حالك؟","أنا بخير، شكراً"),
   "hi":("मैं ठीक हूँ। आप कैसे हैं?","मैं ठीक हूँ, धन्यवाद"),
  }
  for i,(lang,(assistant,user)) in enumerate(cases.items(),1):
   cc.remember_assistant_turn(i,lang,assistant)
   self.assertTrue(cc.reply(i,lang,user),(lang,user))
 def test_short_positive_reply(self):
  cc.remember_assistant_turn(1,"tr","İyi gidiyor. Senin keyfin nasıl?")
  self.assertIn("enerji",cc.reply(1,"tr","İyi").casefold())
 def test_verified_muba_routing_five_languages(self):
  cases=[("tr","MUBA kim?"),("en","Who is MUBA?"),("zh","MUBA 是什么？"),("ar","ما هو MUBA؟"),("hi","MUBA क्या है?")]
  for i,(lang,text) in enumerate(cases,20):
   cc.remember_assistant_turn(i,lang,"x")
   answer=cc.reply(i,lang,text)
   self.assertTrue(answer)
   self.assertIn("muba",answer.casefold())
 def test_language_isolation(self):
  cc.remember_assistant_turn(1,"tr","İyi gidiyor. Senin keyfin nasıl?")
  self.assertIsNone(cc.reply(1,"en","I'm good, thanks"))
 def test_expired_context_is_ignored(self):
  cc.remember_assistant_turn(1,"tr","İyi gidiyor. Senin keyfin nasıl?")
  cc._STATE[1]["at"]=time.monotonic()-cc._TTL-1
  self.assertIsNone(cc.reply(1,"tr","Keyfim yerinde sağ ol"))
 def test_unrelated_message_is_not_hijacked(self):
  cc.remember_assistant_turn(1,"tr","İyi gidiyor. Senin keyfin nasıl?")
  self.assertIn("muba",cc.reply(1,"tr","MUBA nedir?").casefold())
if __name__=="__main__": unittest.main(verbosity=2)
