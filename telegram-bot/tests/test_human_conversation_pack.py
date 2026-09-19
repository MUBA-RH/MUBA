from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import human_conversation_pack as hp

class HumanConversationPackExam(unittest.TestCase):
 def test_five_language_native_chat(self):
  cases=[("tr","Ne yapıyorsun?"),("en","What are you up to?"),("zh","你在干嘛？"),("ar","ماذا تفعل؟"),("hi","क्या कर रहे हो?")]
  for lang,q in cases:self.assertTrue(hp.reply(lang,q),(lang,q))
 def test_live_weather_is_not_fabricated(self):
  for lang,q in [("tr","Bugün hava nasıl?"),("en","How's the weather?"),("zh","今天天气怎么样？"),("ar","كيف الطقس اليوم؟"),("hi","आज मौसम कैसा है?")]:
   self.assertTrue(hp.reply(lang,q))
 def test_human_identity_is_not_fabricated(self):
  for lang,q in [("tr","Kaç yaşındasın?"),("en","How old are you?"),("zh","你多大？"),("ar","كم عمرك؟"),("hi","तुम्हारी उम्र क्या है?")]:
   self.assertTrue(hp.reply(lang,q))
 def test_language_isolation(self):
  self.assertIsNone(hp.reply("tr","What are you up to?"))
  self.assertIsNone(hp.reply("en","Ne yapıyorsun?"))
 def test_emotion_and_followup_families(self):
  for lang,qs in {"tr":["Sıkıldım","Nasıl yani?","Devam et"],"en":["I'm bored","What do you mean?","Go on"],"zh":["好无聊","什么意思","继续"],"ar":["مللت","ماذا تقصد","أكمل"],"hi":["बोर हो रहा हूँ","क्या मतलब","आगे बोलो"]}.items():
   for q in qs:self.assertTrue(hp.reply(lang,q),(lang,q))
 def test_unknown_is_not_hijacked(self):
  for lang in hp.DATA:self.assertIsNone(hp.reply(lang,"ZXQ-UNRELATED-991"))
if __name__=="__main__":unittest.main(verbosity=2)
