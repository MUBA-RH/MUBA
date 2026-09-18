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


def assistant_relevant(text):
 v=(text or "").casefold()
 terms=("muba","community","topluluk","toplulu","kimlik","identity","meme","karakter","character","amaç","purpose","plan","gelecek","future","köken","origin","fark","different","社区","身份","角色","المجتمع","هوية","الشخصية","community","पहचान","character")
 return any(x in v for x in terms)

# Expanded guided catalogue. Answers stay deterministic and language-locked.
EXTRA={
"en":[("identity","Is MUBA a coin or a character?","MUBA is first an original meme character and community identity. Official token details are only stated when they are confirmed."),("identity","Is MUBA an AI?","No. MUBA is the character and culture; MUBA Assistant is the bot helping people understand it."),("difference","Is MUBA another dog or cat meme?","No. That is rather the point: MUBA has its own face, character and identity."),("purpose","Does MUBA promise revolutionary technology?","No grand technological promise is part of MUBA's identity. The focus is character, culture, community, creativity and consistency."),("community","Who owns MUBA's story?","There is no prewritten legend to obey. The community helps the story develop through participation and creation."),("community","Can I create MUBA content?","Yes. Participation and original community creativity are part of MUBA culture."),("plan","When will everything happen?","Confirmed developments are announced when they are ready. MUBA does not invent dates just to fill a roadmap."),("plan","Wen moon?","The moon has terrible customer support. MUBA sticks to confirmed developments."),("difference","Is MUBA just a meme?","MUBA is a meme character, but the identity also lives through its community, culture and participation."),("identity","Who is behind MUBA?","Developer or team identities are not publicly disclosed. MUBA does not invent names."),("purpose","Will MUBA make me rich?","MUBA Assistant does not promise profits or predict prices. It explains MUBA; your financial decisions remain yours."),("identity","Are you alive?","Alive enough to answer MUBA questions. For biology, I have disappointing news.")],
"tr":[("identity","MUBA coin mi yoksa karakter mi?","MUBA öncelikle özgün bir meme karakteri ve topluluk kimliğidir. Token ile ilgili resmi detaylar yalnızca doğrulandığında paylaşılır."),("identity","MUBA bir yapay zekâ mı?","Hayır. MUBA karakter ve kültürdür; MUBA Assistant ise onu anlamana yardımcı olan bottur."),("difference","MUBA yine bir köpek veya kedi meme'i mi?","Hayır. Zaten mesele de bu: MUBA'nın kendi yüzü, karakteri ve kimliği var."),("purpose","MUBA devrimsel teknoloji vaat ediyor mu?","Hayır. MUBA'nın kimliği büyük teknolojik vaatlere dayanmıyor. Odak; karakter, kültür, topluluk, yaratıcılık ve istikrar."),("community","MUBA'nın hikâyesinin sahibi kim?","Uyulması gereken önceden yazılmış bir efsane yok. Topluluk, katılım ve üretimle hikâyenin gelişmesine katkı sağlar."),("community","Ben de MUBA içeriği üretebilir miyim?","Evet. Katılım ve özgün topluluk üretimi MUBA kültürünün parçasıdır."),("plan","Her şey ne zaman olacak?","Doğrulanmış gelişmeler hazır olduğunda duyurulur. MUBA sırf roadmap dolsun diye tarih uydurmaz."),("plan","Wen moon?","Ayın müşteri hizmetleri biraz yavaş. MUBA doğrulanmış gelişmelerle ilerler."),("difference","MUBA sadece bir meme mi?","MUBA bir meme karakteridir; fakat kimliği topluluğu, kültürü ve katılımla birlikte yaşar."),("identity","MUBA'nın arkasında kim var?","Geliştirici veya ekip kimlikleri kamuya açıklanmış değildir. MUBA isim uydurmaz."),("purpose","MUBA beni zengin eder mi?","MUBA Assistant kazanç vaat etmez ve fiyat tahmini yapmaz. MUBA'yı anlatır; finansal kararlar sana aittir."),("identity","Sen canlı mısın?","MUBA sorularına cevap verecek kadar. Biyoloji kısmında haberler pek iyi değil.")],
"zh":[("identity","MUBA 是币还是角色？","MUBA 首先是一个原创 meme 角色和社区身份。Token 的官方信息只会在确认后公布。"),("identity","MUBA 是人工智能吗？","不是。MUBA 是角色和文化；MUBA Assistant 是帮助你了解它的机器人。"),("difference","MUBA 又是狗或猫 meme 吗？","不是。这正是重点：MUBA 有自己的面孔、角色和身份。"),("purpose","MUBA 承诺革命性技术吗？","不。MUBA 的身份不建立在宏大的技术承诺上，而是角色、文化、社区、创造力和持续建设。"),("community","谁拥有 MUBA 的故事？","没有必须遵循的预写传奇。社区通过参与和创作帮助故事自然发展。"),("community","我可以创作 MUBA 内容吗？","可以。参与和原创社区创作是 MUBA 文化的一部分。"),("plan","所有事情什么时候发生？","确认后的进展会在准备好时公布。MUBA 不会为了填满路线图而编造日期。"),("plan","Wen moon?","月球客服回复得有点慢。MUBA 只按已确认的进展前进。"),("difference","MUBA 只是一个 meme 吗？","MUBA 是 meme 角色，但它的身份也通过社区、文化和参与而存在。"),("identity","MUBA 背后是谁？","开发者或团队身份没有公开披露。MUBA 不会编造名字。"),("purpose","MUBA 能让我发财吗？","MUBA Assistant 不承诺收益，也不预测价格。它负责解释 MUBA；财务决定由你自己做。"),("identity","你活着吗？","回答 MUBA 问题算是挺有活力。至于生物学，情况不太乐观。")],
"ar":[("identity","هل MUBA عملة أم شخصية؟","MUBA أولاً شخصية ميم أصلية وهوية مجتمع. تفاصيل التوكن الرسمية لا تُذكر إلا بعد تأكيدها."),("identity","هل MUBA ذكاء اصطناعي؟","لا. MUBA هو الشخصية والثقافة، أما MUBA Assistant فهو البوت الذي يساعدك على فهمه."),("difference","هل MUBA مجرد ميم كلب أو قطة آخر؟","لا. وهذه هي الفكرة: لـ MUBA وجهه وشخصيته وهويته الخاصة."),("purpose","هل يعد MUBA بتكنولوجيا ثورية؟","لا. هوية MUBA لا تقوم على وعود تقنية ضخمة؛ التركيز على الشخصية والثقافة والمجتمع والإبداع والاستمرارية."),("community","من يملك قصة MUBA؟","لا توجد أسطورة مكتوبة مسبقاً يجب اتباعها. المجتمع يساعد القصة على التطور بالمشاركة والإبداع."),("community","هل يمكنني صنع محتوى MUBA؟","نعم. المشاركة والإبداع الأصلي من المجتمع جزء من ثقافة MUBA."),("plan","متى سيحدث كل شيء؟","تُعلن التطورات المؤكدة عندما تصبح جاهزة. MUBA لا يخترع مواعيد فقط لملء خارطة طريق."),("plan","Wen moon?","خدمة عملاء القمر بطيئة قليلاً. MUBA يلتزم بالتطورات المؤكدة."),("difference","هل MUBA مجرد ميم؟","MUBA شخصية ميم، لكن هويته تعيش أيضاً من خلال المجتمع والثقافة والمشاركة."),("identity","من يقف خلف MUBA؟","هويات المطور أو الفريق غير معلنة للعامة. MUBA لا يخترع أسماء."),("purpose","هل سيجعلني MUBA غنياً؟","MUBA Assistant لا يعد بالأرباح ولا يتنبأ بالأسعار. هو يشرح MUBA، والقرارات المالية لك."),("identity","هل أنت حي؟","حي بما يكفي للإجابة عن أسئلة MUBA. أما من ناحية علم الأحياء فالأخبار أقل حماساً.")],
"hi":[("identity","MUBA coin है या character?","MUBA सबसे पहले एक original meme character और community identity है। Token की official details केवल confirm होने पर बताई जाती हैं।"),("identity","क्या MUBA AI है?","नहीं। MUBA character और culture है; MUBA Assistant उसे समझने में मदद करने वाला bot है।"),("difference","क्या MUBA फिर कोई dog या cat meme है?","नहीं। यही बात खास है: MUBA का अपना चेहरा, character और identity है।"),("purpose","क्या MUBA revolutionary technology का वादा करता है?","नहीं। MUBA की identity बड़े technological promises पर नहीं, बल्कि character, culture, community, creativity और consistency पर केंद्रित है।"),("community","MUBA की कहानी किसकी है?","कोई पहले से लिखी legend नहीं है जिसे मानना जरूरी हो। Community participation और creation से कहानी को आगे बढ़ाती है।"),("community","क्या मैं MUBA content बना सकता हूँ?","हाँ। Participation और original community creativity MUBA culture का हिस्सा हैं।"),("plan","सब कुछ कब होगा?","Confirmed developments तैयार होने पर announce किए जाते हैं। MUBA roadmap भरने के लिए dates नहीं बनाता।"),("plan","Wen moon?","Moon की customer service थोड़ी slow है। MUBA confirmed developments पर चलता है।"),("difference","क्या MUBA सिर्फ meme है?","MUBA meme character है, लेकिन उसकी identity community, culture और participation के साथ जीती है।"),("identity","MUBA के पीछे कौन है?","Developer या team identities publicly disclosed नहीं हैं। MUBA नाम नहीं बनाता।"),("purpose","क्या MUBA मुझे अमीर बनाएगा?","MUBA Assistant profit का वादा या price prediction नहीं करता। यह MUBA को समझाता है; financial decisions आपके हैं।"),("identity","क्या तुम जिंदा हो?","MUBA के सवालों का जवाब देने जितना। Biology के हिसाब से खबर थोड़ी कमजोर है।")]}
for _lang,_items in EXTRA.items():
 for _topic,_q,_a in _items: QUESTIONS[_lang].append((_topic,_q))

def answer_for_question(lang,index):
 base=12
 if index<base: return guided_answer(lang,index)
 return EXTRA[lang][index-base][2]

def match_catalog(lang,text):
 import difflib
 v=_norm_match(text)
 best=(0.0,None)
 for i,(_,q) in enumerate(QUESTIONS[lang]):
  score=difflib.SequenceMatcher(None,v,_norm_match(q)).ratio()
  if score>best[0]: best=(score,i)
 return best[1] if best[0]>=0.72 else None

def _norm_match(s):
 return re.sub(r"[^\w\s]"," ",(s or "").casefold()).strip()
