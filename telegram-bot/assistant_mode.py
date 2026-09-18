"""MUBA private-assistant UI and group-guardian policy."""
from __future__ import annotations
import re
from muba_core.semantic_knowledge import TOPICS

LANGS={"en":"🇬🇧 English","tr":"🇹🇷 Türkçe","zh":"🇨🇳 中文","ar":"🇸🇦 العربية","hi":"🇮🇳 हिन्दी"}
TOPIC_LABELS={
"en":{"origin":"🌱 Origin","identity":"👤 Identity","difference":"✨ Difference","purpose":"🎯 Purpose","community":"👥 Community","plan":"🧭 Future"},
"tr":{"origin":"🌱 Köken","identity":"👤 Kimlik","difference":"✨ Farkı","purpose":"🎯 Amaç","community":"👥 Topluluk","plan":"🧭 Gelecek"},
"zh":{"origin":"🌱 起源","identity":"👤 身份","difference":"✨ 独特之处","purpose":"🎯 目标","community":"👥 社区","plan":"🧭 未来"},
"ar":{"origin":"🌱 النشأة","identity":"👤 الهوية","difference":"✨ الاختلاف","purpose":"🎯 الهدف","community":"👥 المجتمع","plan":"🧭 المستقبل"},
"hi":{"origin":"🌱 शुरुआत","identity":"👤 पहचान","difference":"✨ अंतर","purpose":"🎯 उद्देश्य","community":"👥 समुदाय","plan":"🧭 भविष्य"}}
QUESTIONS={
"en":[("origin","How did MUBA emerge?"),("origin","Was MUBA built from a prewritten story?"),("identity","What is MUBA?"),("identity","How would MUBA describe itself?"),("difference","What makes MUBA different?"),("difference","Is MUBA a copy of another meme character?"),("purpose","Why does MUBA exist?"),("purpose","What is MUBA trying to build?"),("community","What role does the community play?"),("community","How can people participate?"),("plan","What comes next for MUBA?"),("plan","How does MUBA plan to grow?")],
"tr":[("origin","MUBA nasıl ortaya çıktı?"),("origin","MUBA önceden yazılmış bir hikâyeden mi doğdu?"),("identity","MUBA nedir?"),("identity","MUBA kendini nasıl tanımlar?"),("difference","MUBA'yı farklı yapan nedir?"),("difference","MUBA başka bir meme karakterinin kopyası mı?"),("purpose","MUBA neden var?"),("purpose","MUBA ne inşa etmeye çalışıyor?"),("community","Topluluğun rolü nedir?"),("community","İnsanlar nasıl katılabilir?"),("plan","MUBA için sırada ne var?"),("plan","MUBA nasıl büyümeyi planlıyor?")],
"zh":[("origin","MUBA 是如何出现的？"),("origin","MUBA 来自预先写好的故事吗？"),("identity","MUBA 是什么？"),("identity","MUBA 如何定义自己？"),("difference","MUBA 有什么不同？"),("difference","MUBA 是其他 meme 角色的复制品吗？"),("purpose","MUBA 为什么存在？"),("purpose","MUBA 想建立什么？"),("community","社区扮演什么角色？"),("community","人们如何参与？"),("plan","MUBA 接下来会做什么？"),("plan","MUBA 如何计划发展？")],
"ar":[("origin","كيف ظهر MUBA؟"),("origin","هل بدأ MUBA من قصة مكتوبة مسبقاً؟"),("identity","ما هو MUBA؟"),("identity","كيف يعرّف MUBA نفسه؟"),("difference","ما الذي يجعل MUBA مختلفاً؟"),("difference","هل MUBA نسخة من شخصية ميم أخرى؟"),("purpose","لماذا يوجد MUBA؟"),("purpose","ماذا يحاول MUBA أن يبني؟"),("community","ما دور المجتمع؟"),("community","كيف يمكن للناس المشاركة؟"),("plan","ما الخطوة التالية لـ MUBA؟"),("plan","كيف يخطط MUBA للنمو؟")],
"hi":[("origin","MUBA कैसे शुरू हुआ?"),("origin","क्या MUBA पहले से लिखी कहानी से बना?"),("identity","MUBA क्या है?"),("identity","MUBA खुद को कैसे परिभाषित करता है?"),("difference","MUBA को अलग क्या बनाता है?"),("difference","क्या MUBA किसी दूसरे meme character की copy है?"),("purpose","MUBA क्यों है?"),("purpose","MUBA क्या बनाना चाहता है?"),("community","Community की क्या भूमिका है?"),("community","लोग कैसे भाग ले सकते हैं?"),("plan","MUBA के लिए आगे क्या है?"),("plan","MUBA कैसे बढ़ने की योजना बनाता है?")]}
TEXT={
"en":{"choose":"Welcome to MUBA Assistant. Choose your language:","menu":"MUBA Assistant — choose a topic or ask your own MUBA question.","back":"⬅️ Back","language":"🌐 Change Language","outside":"I’m the MUBA Assistant. I focus on MUBA, its identity, culture, community and official information."},
"tr":{"choose":"MUBA Assistant'a hoş geldin. Dilini seç:","menu":"MUBA Assistant — bir konu seç veya MUBA hakkında kendi sorunu yaz.","back":"⬅️ Geri","language":"🌐 Dili Değiştir","outside":"Ben MUBA Assistant'ım. MUBA'nın kimliği, kültürü, topluluğu ve resmi bilgileri üzerine çalışıyorum."},
"zh":{"choose":"欢迎使用 MUBA Assistant。请选择语言：","menu":"MUBA Assistant — 选择一个主题，或直接询问有关 MUBA 的问题。","back":"⬅️ 返回","language":"🌐 更改语言","outside":"我是 MUBA Assistant，只专注于 MUBA 的身份、文化、社区和官方信息。"},
"ar":{"choose":"مرحباً بك في MUBA Assistant. اختر لغتك:","menu":"MUBA Assistant — اختر موضوعاً أو اسأل سؤالك عن MUBA.","back":"⬅️ رجوع","language":"🌐 تغيير اللغة","outside":"أنا MUBA Assistant. أركز على MUBA وهويته وثقافته ومجتمعه ومعلوماته الرسمية."},
"hi":{"choose":"MUBA Assistant में आपका स्वागत है। अपनी भाषा चुनें:","menu":"MUBA Assistant — कोई विषय चुनें या MUBA के बारे में अपना सवाल पूछें।","back":"⬅️ वापस","language":"🌐 भाषा बदलें","outside":"मैं MUBA Assistant हूँ। मैं MUBA की identity, culture, community और official information पर केंद्रित हूँ।”"}}

def guided_answer(lang,index):
 topic,_=QUESTIONS[lang][index]
 return TOPICS[topic].get(lang,TOPICS[topic]["en"])

def looks_like_muba_question(text):
 v=(text or "").casefold()
 return "muba" in v and ("?" in v or "？" in v or any(x in v for x in ("what","why","how","nedir","neden","nasıl","kim","什么","为什么","如何","ما","لماذا","كيف","क्या","क्यों","कैसे")))

def group_event(text):
 v=(text or "").casefold().strip()
 if v in {"/ca","ca","ca?","ca ?","contract address","contract address?"}: return "ca"
 if re.search(r"0x[a-f0-9]{20,}|[1-9a-hj-np-z]{32,44}",v) and ("ca" in v or "muba" in v): return "fake_ca"
 if any(x in v for x in ("fake ca","sahte ca","scam ca","sahte contract")): return "fake_ca"
 if any(x in v for x in ("muba dev","developer","geliştirici","team","ekip")): return "dev"
 if any(x in v for x in ("official source","resmi kaynak","official link","resmi link")): return "official"
 if any(x in v for x in ("scam","phishing","impersonat","taklit","dolandır")) and "muba" in v: return "security"
 if looks_like_muba_question(text): return "assistant_redirect"
 return None
