"""Topic-question-context regression exam for five supported languages."""
from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import muba_brain as brain

CHAINS=[
("tr",[("MUBA neden klasik bir meme projesi gibi ortaya çıkmadı?","origin"),("Peki bu durum MUBA'nın kimliğini nasıl etkiliyor?","identity"),("Bu kimliğin gelişmesinde topluluk ne yapıyor?","community")]),
("en",[("Why wasn't MUBA built around a typical project story?","origin"),("So how does that shape what MUBA is today?","identity"),("And where does the community fit into that identity?","community")]),
("zh",[("为什么 MUBA 没有按照传统 meme 项目的方式出现？","origin"),("那么这对 MUBA 今天的身份有什么影响？","identity"),("社区又是如何参与塑造这种身份的？","community")]),
("ar",[("لماذا لم يظهر MUBA كمشروع ميم تقليدي؟","origin"),("وكيف أثّر ذلك على هوية MUBA اليوم؟","identity"),("وما دور المجتمع في تشكيل هذه الهوية؟","community")]),
("hi",[("MUBA एक आम meme project की तरह क्यों शुरू नहीं हुआ?","origin"),("तो इससे आज MUBA की पहचान कैसे बनती है?","identity"),("और इस पहचान को बनाने में community की क्या भूमिका है?","community")]),
]
NEGATIVE=[
"Bugün kuşlar neden güneye uçuyor?",
"What is the weather like on Mars?",
"普通的鸟为什么会迁徙？",
"ما سبب دوران الأرض حول الشمس؟",
"आज आसमान नीला क्यों है?",
]
class TopicQuestionContextExam(unittest.TestCase):
 def setUp(self): brain.reset_runtime_state()
 def test_linked_chains(self):
  failures=[]
  for n,(lang,chain) in enumerate(CHAINS):
   brain.reset_runtime_state()
   for q,want in chain:
    d=brain.build_decision(q,chat_id=700+n,user_id=101)
    if d.language!=lang or want not in d.intents:
     failures.append((lang,q,want,d.language,d.intents,d.trace.winning_rule))
  self.assertFalse(failures,"\n".join(map(str,failures)))
 def test_unrelated_questions_do_not_enter_semantic_topics(self):
  semantic={"origin","identity","purpose","difference","community","plan"}
  for i,q in enumerate(NEGATIVE):
   brain.reset_runtime_state(); d=brain.build_decision(q,chat_id=800+i,user_id=101)
   self.assertTrue(semantic.isdisjoint(d.intents),(q,d.intents,d.trace.winning_rule))
 def test_how_alone_is_not_plan(self):
  for q in ["Bu kimliği nasıl etkiliyor?","So how does that shape the identity?","那么这如何影响身份？","وكيف يؤثر ذلك على الهوية؟","तो इससे पहचान कैसे बनती है?"]:
   brain.reset_runtime_state(); d=brain.build_decision(q,chat_id=900,user_id=101)
   self.assertNotIn("plan",d.intents,(q,d.intents,d.trace.winning_rule))
if __name__=="__main__": unittest.main(verbosity=2)
