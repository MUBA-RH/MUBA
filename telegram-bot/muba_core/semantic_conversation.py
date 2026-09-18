"""Lightweight multilingual semantic/conversation resolver.

Runs locally with zero API cost. It complements—not replaces—the protected
deterministic layers.
"""
from __future__ import annotations
import re
from .semantic_knowledge import TOPICS

CUES={
"purpose":("purpose","main purpose","goal","aim","amac","amacı","amaç","目的","目标","هدف","الغرض","उद्देश्य","मकसद"),
"difference":("different","difference","unique","fark","farklı","区别","不同","مختلف","الفرق","अलग","different"),
"community":("community role","role of the community","topluluğun rol","toplumun rol","社区","扮演什么角色","دور المجتمع","community की","समुदाय की"),
"plan":("plan","how will","how does it plan","nasıl gerçekleşt","nasıl yap","planlıyor","计划","كيف سي","الخطة","कैसे","योजना"),
"identity":("what is muba","muba nedir","muba 是什么","ما هو muba","muba क्या"),
}
FOLLOWUP={
"en":{"difference":("what makes it different","why is it different"),"purpose":("what is its main purpose","its purpose"),"plan":("how will it do that","how does it plan"),"community":("community","role")},
"tr":{"plan":("peki bunu nasıl","bunu nasıl gerçekleşt","nasıl yapacak"),"community":("bu planda topluluğun rol","topluluğun rol"),"difference":("onu farklı","farkı ne"),"purpose":("amacı ne","amaç ne")},
"zh":{"difference":("它和其他","有什么不同"),"community":("社区","扮演什么角色"),"plan":("如何实现","怎么实现"),"purpose":("主要目的","目标是什么")},
"ar":{"difference":("ما الذي يجعله مختلف","ما الفرق"),"community":("دور المجتمع","المجتمع في ذلك"),"plan":("كيف سيحقق","كيف يخطط"),"purpose":("هدفه","الغرض")},
"hi":{"difference":("अलग क्यों","क्या अलग"),"community":("community की क्या भूमिका","समुदाय की क्या भूमिका"),"plan":("कैसे करेगा","कैसे पूरा"),"purpose":("उद्देश्य","मकसद")},
}
def _norm(s): return re.sub(r"\s+"," ",(s or "").casefold()).strip()
def resolve(text,language,recent):
 v=_norm(text)
 scores={k:sum(1 for cue in cues if cue in v) for k,cues in CUES.items()}
 topic=max(scores,key=scores.get) if max(scores.values(),default=0)>0 else None
 if not topic:
  for candidate,cues in FOLLOWUP.get(language,{}).items():
   if any(c in v for c in cues): topic=candidate; break
 if not topic and recent:
  last=next((x.get("active_topic") for x in reversed(recent) if x.get("active_topic") in TOPICS),None)
  if last and len(v.split())<=10 and any(x in v for x in ("why","how","what about","peki","neden","nasıl","那么","为什么","وما","كيف","तो","क्यों","कैसे")):
   topic=last
 if not topic: return None
 return topic,TOPICS[topic].get(language,TOPICS[topic]["en"])
