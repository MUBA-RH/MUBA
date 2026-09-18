"""Zero-cost multilingual semantic frame resolver for MUBA conversation.

This module is intentionally isolated behind the protected deterministic brain.
It generalizes natural paraphrases into a small set of MUBA knowledge frames
without external APIs, model downloads, secrets, or runtime network calls.
"""
from __future__ import annotations
import re, unicodedata
from .semantic_knowledge import TOPICS

FRAMES={
"tr":{
 "identity":(("muba",),("nedir","ne","kim","tanımla","anlat")),
 "purpose":(("muba","proje","karakter"),("amaç","niye","neden","var","fikir","ortaya","hedef")),
 "difference":(("muba","karakter","meme","onu"),("fark","farklı","ayır","özgün","özel","yapan","ibaret","sadece")),
 "community":(("topluluk","insan","kullanıcı","katılımcı"),("rol","katkı","neresinde","yapabilir","merkez","paylaş","üret")),
 "plan":(("muba","proje","topluluk","sonra"),("plan","nasıl","gerçekleştir","büyü","sonra","gelecek","ilerle","yapacak")),
},
"en":{
 "identity":(("muba",),("what","define","describe")),
 "purpose":(("muba","project","character"),("purpose","goal","aim","exist","why","idea","created")),
 "difference":(("muba","character","meme","it"),("different","difference","unique","apart","special","only","just","makes")),
 "community":(("community","people","users","participants"),("role","contribute","fit","participate","create","share")),
 "plan":(("muba","project","community","then"),("plan","how","grow","next","then","future","build","achieve")),
},
"zh":{
 "identity":(("muba",),("什么","介绍","定义")),
 "purpose":(("muba","项目","角色"),("目的","目标","为什么","存在","理念","诞生")),
 "difference":(("muba","角色","meme","它"),("不同","区别","独特","特别","只是","特点")),
 "community":(("社区","大家","人们","用户","参与者"),("角色","作用","贡献","参与","做什么","位置")),
 "plan":(("muba","项目","社区","以后"),("计划","如何","怎么","发展","下一步","未来","实现","壮大")),
},
"ar":{
 "identity":(("muba",),("ما هو","عرّف","عرف","اشرح")),
 "purpose":(("muba","المشروع","الشخصية"),("هدف","غرض","لماذا","يوجد","فكرة","نشأ")),
 "difference":(("muba","الشخصية","ميم","هو"),("مختلف","فرق","يميز","مميز","فقط","مجرد")),
 "community":(("المجتمع","الناس","المستخدم","المشاركون"),("دور","مكان","يساهم","مشاركة","يفعل")),
 "plan":(("muba","المشروع","المجتمع","بعد"),("خطة","كيف","ينمو","التالي","مستقبل","يحقق","يبني")),
},
"hi":{
 "identity":(("muba",),("क्या है","बताओ","परिभाष")),
 "purpose":(("muba","project","character"),("उद्देश्य","मकसद","क्यों","वजूद","विचार","बना")),
 "difference":(("muba","character","meme","यह","इसकी"),("अलग","फर्क","खास","विशेष","सिर्फ","बनाता")),
 "community":(("community","समुदाय","लोग","users"),("भूमिका","योगदान","जगह","हिस्सा","कर सकते","भाग")),
 "plan":(("muba","project","community","आगे"),("योजना","कैसे","बढ़","अगला","भविष्य","पूरा","बनाए")),
}}
FOLLOW={
"tr":{"purpose":("niye","neden","fikir"),"difference":("fark","ayır","ibaret","yapan"),"community":("insan","topluluk","katkı","rol"),"plan":("nasıl","sonra","büyü","plan")},
"en":{"purpose":("why","purpose","idea"),"difference":("different","apart","only","makes"),"community":("people","community","contribute","role"),"plan":("how","then","next","grow")},
"zh":{"purpose":("为什么","目的","理念"),"difference":("不同","独特","只是"),"community":("社区","大家","贡献"),"plan":("如何","以后","下一步")},
"ar":{"purpose":("لماذا","هدف","فكرة"),"difference":("مختلف","يميز","مجرد"),"community":("المجتمع","الناس","دور"),"plan":("كيف","بعد","خطة")},
"hi":{"purpose":("क्यों","उद्देश्य","विचार"),"difference":("अलग","खास","सिर्फ"),"community":("community","लोग","भूमिका"),"plan":("कैसे","आगे","योजना")}}
def _norm(s):
 s=unicodedata.normalize("NFKC",(s or "").casefold()).replace("\u0307","")
 return re.sub(r"\s+"," ",s).strip()
def _hit(v,items): return sum(1 for x in items if x in v)
def resolve(text,language,recent):
 v=_norm(text); frames=FRAMES.get(language,FRAMES["en"]); scored={}
 for topic,(subjects,predicates) in frames.items():
  a,b=_hit(v,subjects),_hit(v,predicates)
  scored[topic]=(2 if a else 0)+(2*b)+(1 if a and b else 0)
 topic=max(scored,key=scored.get) if scored and max(scored.values())>=3 else None
 if not topic:
  for candidate,cues in FOLLOW.get(language,{}).items():
   if any(c in v for c in cues): topic=candidate; break
 if not topic and recent:
  last=next((x.get("active_topic") for x in reversed(recent) if x.get("active_topic") in TOPICS),None)
  if last and len(v.split())<=12: topic=last
 if not topic:return None
 return topic,TOPICS[topic].get(language,TOPICS[topic]["en"])
