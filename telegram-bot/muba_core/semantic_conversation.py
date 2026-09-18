"""Zero-cost multilingual topic/question/context resolver for MUBA."""
from __future__ import annotations
import re, unicodedata
from .semantic_knowledge import TOPICS

# Each frame separates WHAT the message is about (subjects) from WHAT it asks
# (predicates). Generic manner words such as how/nasıl/كيف are never plan intent
# by themselves.
FRAMES={
"tr":{
 "origin":(("muba","proje","karakter","seni"),("doğdu","ortaya çık","başla","başlangıç","köken","nasıl ortaya","nereden","fikirden")),
 "identity":(("muba","kimlik","karakter","bu durum","bu kimlik"),("nedir","tanımla","anlat","kimlik","şekillen","etkile","nasıl bir")),
 "purpose":(("muba","proje","karakter"),("amaç","amac","amacı","niye var","neden var","hedef","ne için")),
 "difference":(("muba","karakter","meme","onu"),("fark","farklı","ayır","özgün","özel","yapan","ibaret","sadece")),
 "community":(("topluluk","insan","kullanıcı","katılımcı"),("rol","katkı","neresinde","yapabilir","merkez","paylaş","üret","ne yap")),
 "plan":(("muba","proje","topluluk"),("plan","gerçekleştir","büyü","sonra ne","gelecek","ilerle","yapacak","bundan sonra","ne olacak")),
},
"en":{
 "origin":(("muba","project","character"),("emerge","origin","begin","start","come from","born","built around","first appear")),
 "identity":(("muba","identity","character","that","this"),("what is muba","define muba","describe muba","identity","shape","affect","what muba is")),
 "purpose":(("muba","project","character"),("purpose","goal","aim","why exist","does muba exist","what for")),
 "difference":(("muba","character","meme","it"),("different","difference","unique","apart","special","only","just","another","nothing more","makes")),
 "community":(("community","people","users","participants"),("role","contribute","fit","participate","create","share","where")),
 "plan":(("muba","project","community"),("plan","grow","next","future","build","achieve","what comes next","after that")),
},
"zh":{
 "origin":(("muba","项目","角色"),("出现","诞生","起源","开始","最初","怎么来的","从何而来")),
 "identity":(("muba","身份","角色","这","这种"),("什么","介绍","定义","身份","塑造","影响","形成")),
 "purpose":(("muba","项目","角色"),("目的","目标","为什么存在","为何存在","为什么")),
 "difference":(("muba","角色","meme","它"),("不同","区别","独特","特别","只是","特点")),
 "community":(("社区","大家","人们","普通人","用户","参与者"),("角色","作用","贡献","参与","做什么","位置","如何参与")),
 "plan":(("muba","项目","社区"),("计划","发展","下一步","未来","实现","壮大","以后怎么办")),
},
"ar":{
 "origin":(("muba","المشروع","الشخصية"),("نشأ","ظهر","بدأ","بداية","أصل","انبثق","من أين")),
 "identity":(("muba","هوية","الهوية","الشخصية","ذلك","هذه"),("ما هو","عرّف","عرف","اشرح","هوية","شكل","تشكيل","أثر","يؤثر")),
 "purpose":(("muba","المشروع","الشخصية"),("هدف","غرض","لماذا يوجد","لأي غرض")),
 "difference":(("muba","الشخصية","ميم","هو"),("مختلف","فرق","يميز","مميز","فقط","مجرد")),
 "community":(("المجتمع","الناس","المستخدم","المشاركون"),("دور","مكان","يساهم","مشاركة","يفعل")),
 "plan":(("muba","المشروع","المجتمع"),("خطة","ينمو","التالي","مستقبل","يحقق","يبني","ماذا بعد")),
},
"hi":{
 "origin":(("muba","project","character"),("शुरू","जन्म","उभरा","मूल","कहां से","कैसे बना","शुरुआत")),
 "identity":(("muba","identity","पहचान","character","इससे","यह"),("क्या है","बताओ","परिभाष","पहचान","बनती","आकार","असर")),
 "purpose":(("muba","project","character"),("उद्देश्य","मकसद","क्यों मौजूद","क्यों है","लक्ष्य")),
 "difference":(("muba","character","meme","यह","इसकी"),("अलग","फर्क","खास","विशेष","सिर्फ","बनाता")),
 "community":(("community","समुदाय","लोग","users"),("भूमिका","योगदान","जगह","हिस्सा","कर सकते","भाग")),
 "plan":(("muba","project","community"),("योजना","बढ़","अगला","भविष्य","पूरा","बनाए","आगे क्या")),
}}

# Explicit follow-up question targets. These are semantic nouns/actions, not
# generic question words. Previous context is only used when the new message
# does not clearly name a target.
FOLLOW={
"tr":{"identity":("kimlik","kimliğini","kimliği"),"community":("topluluk","insan","katkı","rol"),"plan":("bundan sonra","sonra ne","ne olacak","plan"),"origin":("köken","başlangıç","nasıl doğ","nasıl ortaya"),"difference":("fark","ayır","ibaret")},
"en":{"identity":("identity","what muba is","shape what"),"community":("community","people","contribute","role","fit into"),"plan":("what comes next","next step","after that","plan"),"origin":("origin","how did it start","where did it come"),"difference":("different","apart","only","makes")},
"zh":{"identity":("身份","塑造","影响"),"community":("社区","大家","贡献","参与"),"plan":("下一步","未来","以后怎么办"),"origin":("起源","开始","诞生"),"difference":("不同","独特","只是")},
"ar":{"identity":("هوية","الهوية","تشكيل","يؤثر"),"community":("المجتمع","الناس","دور"),"plan":("ماذا بعد","الخطوة التالية","خطة"),"origin":("أصل","بداية","نشأ"),"difference":("مختلف","يميز","مجرد")},
"hi":{"identity":("identity","पहचान","बनती"),"community":("community","समुदाय","लोग","भूमिका"),"plan":("आगे क्या","अगला","योजना"),"origin":("शुरुआत","मूल","शुरू"),"difference":("अलग","खास","सिर्फ")}}

def _norm(s):
 s=unicodedata.normalize("NFKC",(s or "").casefold()).replace("\u0307","")
 return re.sub(r"\s+"," ",s).strip()
def _hit(v,items): return sum(1 for x in items if x in v)

def resolve(text,language,recent):
 v=_norm(text); frames=FRAMES.get(language,FRAMES["en"])
 # 1) NE HAKKINDA + 2) NE SORUYOR?
 scored={}
 for topic,(subjects,predicates) in frames.items():
  a,b=_hit(v,subjects),_hit(v,predicates)
  scored[topic]=(2*a)+(4*b)+(2 if a and b else 0)
 # Explicit target terms beat generic manner/question wording.
 explicit=[]
 for topic,cues in FOLLOW.get(language,{}).items():
  hits=_hit(v,cues)
  if hits: explicit.append((hits,topic))
 if explicit:
  ranked=[]
  for hits,target in explicit:
   subjects,_=frames[target]
   # Prefer the actor/topic named in the question. Community is the actor in
   # "how does the community shape this identity"; identity is the object.
   subject_hits=_hit(v,subjects)
   actor_bonus=3 if target=="community" and subject_hits else 0
   ranked.append((subject_hits+actor_bonus,hits,target))
  _,_,target=max(ranked)
  # Question intent overrides actor nouns: future/next-step questions are plan.
  plan_pred_hits=_hit(v,frames["plan"][1])
  if plan_pred_hits:
   target="plan"
  # Explicit actor/topic wins over incidental object mentions.
  scored[target]=max(scored.values() or [0])+12
 has_subject=any(_hit(v,subjects) for subjects,_ in frames.values())
 topic=max(scored,key=scored.get) if has_subject and scored and max(scored.values())>=4 else None
 # Origin wording is more specific than generic why/purpose wording.
 if "origin" in scored and scored["origin"]>=6:
  origin_preds=frames["origin"][1]
  if _hit(v,origin_preds): topic="origin"

 # 3) ÖNCEKİ BAĞLAM: only resolve genuinely elliptical follow-ups.
 if not topic and recent:
  last=next((x.get("active_topic") for x in reversed(recent) if x.get("active_topic") in TOPICS),None)
  if last:
   for candidate,cues in FOLLOW.get(language,{}).items():
    if any(c in v for c in cues): topic=candidate; break
   if not topic and len(v.split())<=8 and any(x in v for x in ("peki","yani","so ","and ","then","那么","那","وكيف","وما","तो ","और ")):
    topic=last
 if not topic:return None
 return topic,TOPICS[topic].get(language,TOPICS[topic]["en"])
