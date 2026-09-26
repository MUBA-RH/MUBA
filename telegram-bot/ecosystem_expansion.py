"""Append-only public knowledge for MUBA Community, ASK and Transparency.
Stable IDs are never deleted or reused. New verified knowledge is appended to its single owning domain.
MUBA Updates remains the chronological append-only change history.
"""
ARCHIVE_POLICY={"append_only":True,"delete_records":False,"deduplicate_by_id":True,"domains":("community","updates","transparency","ask")}

COMMUNITY_RECORDS={
"en":[
("newcomer","🧭 New Here?","New members can learn MUBA, verify official channels, follow the story and updates, then move into creation or games."),
("culture","🎭 Community Culture","The culture grows through original participation, recognizable MUBA identity, humor and shared creation rather than manufactured mythology."),
("creation","🎨 Community Creation","Community creation moves from an idea into MUBA creation tools and, when appropriate, into sharing and public visibility."),
("story","🎬 Story Participation","The community can follow the continuing MUBA story while verified project history remains a separate factual record."),
("games","🎮 Game Participation","Games add an interactive way to experience MUBA beyond reading, watching or creating."),
("memory","📚 Community Memory","Published developments, stories and recorded ecosystem changes build a growing memory. New records extend that history rather than erase it.")],
"tr":[
("newcomer","🧭 Yeni misin?","Yeni üyeler MUBA'yı tanıyabilir, resmî kanalları doğrulayabilir, hikâye ve yenilikleri takip edip ardından üretim veya oyunlara geçebilir."),
("culture","🎭 Topluluk Kültürü","Kültür; üretilmiş mitoloji yerine özgün katılım, tanınabilir MUBA kimliği, mizah ve ortak üretimle büyür."),
("creation","🎨 Topluluk Üretimi","Topluluk üretimi fikirden MUBA üretim araçlarına, uygun olduğunda paylaşım ve kamusal görünürlüğe ilerler."),
("story","🎬 Hikâyeye Katılım","Topluluk devam eden MUBA hikâyesini takip edebilir; doğrulanmış proje geçmişi ayrı bir gerçek kayıt olarak kalır."),
("games","🎮 Oyunlara Katılım","Oyunlar MUBA'yı okumak, izlemek veya üretmek dışında etkileşimli olarak deneyimlemenin yeni yoludur."),
("memory","📚 Topluluk Hafızası","Yayınlanan gelişmeler, hikâyeler ve kayıtlı ekosistem değişiklikleri büyüyen bir hafıza oluşturur. Yeni kayıtlar geçmişi silmez, genişletir.")],
"zh":[
("newcomer","🧭 新成员","新成员可以先了解 MUBA、确认官方渠道、关注故事和更新，再进入创作或游戏。"),
("culture","🎭 社区文化","文化通过原创参与、清晰的 MUBA 身份、幽默和共同创作成长，而不是制造神话。"),
("creation","🎨 社区创作","社区创作从想法进入 MUBA 创作工具，并在合适时进入分享和公开展示。"),
("story","🎬 故事参与","社区可以跟随持续发展的 MUBA 故事，同时已验证的项目历史保持为独立事实记录。"),
("games","🎮 游戏参与","游戏让社区除了阅读、观看和创作之外，还能以互动方式体验 MUBA。"),
("memory","📚 社区记忆","已发布的发展、故事和生态变化记录形成持续增长的记忆。新记录扩展历史，而不是删除历史。")],
"ar":[
("newcomer","🧭 جديد هنا؟","يمكن للعضو الجديد التعرف على MUBA والتحقق من القنوات الرسمية ومتابعة القصة والتحديثات ثم الانتقال للإبداع أو الألعاب."),
("culture","🎭 ثقافة المجتمع","تنمو الثقافة بالمشاركة الأصلية وهوية MUBA الواضحة والفكاهة والإبداع المشترك بدلاً من الأساطير المصطنعة."),
("creation","🎨 إبداع المجتمع","ينتقل إبداع المجتمع من الفكرة إلى أدوات MUBA ثم، عند الملاءمة، إلى المشاركة والظهور العام."),
("story","🎬 المشاركة في القصة","يمكن للمجتمع متابعة قصة MUBA المستمرة بينما يبقى تاريخ المشروع الموثق سجلاً واقعياً منفصلاً."),
("games","🎮 المشاركة في الألعاب","تضيف الألعاب طريقة تفاعلية لتجربة MUBA إلى جانب القراءة والمشاهدة والإبداع."),
("memory","📚 ذاكرة المجتمع","تبني التطورات والقصص وتغييرات المنظومة المسجلة ذاكرة متنامية. السجلات الجديدة توسع التاريخ ولا تمحوه.")],
"hi":[
("newcomer","🧭 नए हैं?","नए सदस्य MUBA को जान सकते हैं, official channels verify कर सकते हैं, story और updates follow करके creation या games में जा सकते हैं।"),
("culture","🎭 समुदाय संस्कृति","Culture manufactured mythology के बजाय original participation, स्पष्ट MUBA identity, humor और shared creation से बढ़ता है।"),
("creation","🎨 समुदाय निर्माण","Community creation idea से MUBA creation tools तक और उचित होने पर sharing व public visibility तक जाता है।"),
("story","🎬 कहानी भागीदारी","Community लगातार MUBA story को follow कर सकती है, जबकि verified project history अलग factual record रहती है।"),
("games","🎮 गेम भागीदारी","Games पढ़ने, देखने या बनाने के अलावा MUBA को interactively अनुभव करने का तरीका जोड़ते हैं।"),
("memory","📚 समुदाय स्मृति","Published developments, stories और recorded ecosystem changes बढ़ती memory बनाते हैं। नए records history को बढ़ाते हैं, मिटाते नहीं।")]}

ASK_RECORDS={
"en":[
("character","👤 Character","What defines MUBA as a character?","MUBA begins with a consistent original character identity. Tools and stories grow around it rather than replacing it."),
("visual","🎨 Visual Identity","Why does visual consistency matter?","Recognizable face, clothing language and recurring character cues keep MUBA identifiable across formats."),
("voice","💬 Voice & Humor","How does MUBA communicate?","MUBA can be concise, playful and meme-native while confirmed information stays separate from jokes or invented claims."),
("culture","🌍 Culture","What is MUBA culture?","MUBA culture is created through memes, participation, recurring character language, community behavior and original work."),
("principles","🧭 Principles","What stays constant as MUBA grows?","Original identity, participation, creativity, factual clarity and consistent building remain stable beneath changing tools."),
("ecosystem","🧠 Ecosystem","What makes MUBA an ecosystem?","Knowledge, community, security, creation, story, web and games share one identity while keeping separate responsibilities."),
("facts","📖 Facts & Story","How are facts separated from story?","Verified development is factual history; creative story material remains narrative and is not presented as a literal project event."),
("evolution","🚀 Evolution","How can MUBA grow without losing itself?","New verified knowledge, tools and experiences can be added around the same identity without rewriting MUBA's origin.")],
"tr":[
("character","👤 Karakter","MUBA'yı karakter olarak ne tanımlar?","MUBA tutarlı ve özgün karakter kimliğiyle başlar. Araçlar ve hikâyeler bu kimliğin çevresinde büyür, onun yerine geçmez."),
("visual","🎨 Görsel Kimlik","Görsel tutarlılık neden önemli?","Tanınabilir yüz, giyim dili ve tekrar eden karakter işaretleri MUBA'yı farklı formatlarda ayırt edilebilir tutar."),
("voice","💬 Dil ve Mizah","MUBA nasıl iletişim kurar?","MUBA kısa, oyunbaz ve meme kültürüne doğal olabilir; doğrulanmış bilgi şaka veya uydurma iddialardan ayrı kalır."),
("culture","🌍 Kültür","MUBA kültürü nedir?","MUBA kültürü; memeler, katılım, tekrar eden karakter dili, topluluk davranışı ve özgün üretimle oluşur."),
("principles","🧭 İlkeler","MUBA büyürken ne değişmeden kalır?","Özgün kimlik, katılım, yaratıcılık, bilgi doğruluğu ve istikrarlı geliştirme değişen araçların altında sabit kalır."),
("ecosystem","🧠 Ekosistem","MUBA'yı ekosistem yapan nedir?","Bilgi, topluluk, güvenlik, üretim, hikâye, web ve oyunlar aynı kimliği paylaşırken görevlerini ayrı tutar."),
("facts","📖 Gerçek ve Hikâye","Gerçek bilgi ile hikâye nasıl ayrılır?","Doğrulanmış gelişim gerçek geçmiş olarak tutulur; yaratıcı hikâye anlatı olarak kalır ve gerçek proje olayı gibi sunulmaz."),
("evolution","🚀 Gelişim","MUBA kendini kaybetmeden nasıl büyüyebilir?","Aynı kimliğin çevresine yeni doğrulanmış bilgi, araç ve deneyimler eklenebilir; MUBA'nın kökeni yeniden yazılmaz.")],
"zh":[
("character","👤 角色","什么定义了 MUBA 这个角色？","MUBA 从一致的原创角色身份开始。工具和故事围绕这一身份成长，而不是取代它。"),
("visual","🎨 视觉身份","为什么视觉一致性重要？","可识别的面孔、服装语言和重复的角色特征让 MUBA 在不同格式中保持可识别。"),
("voice","💬 语言与幽默","MUBA 如何交流？","MUBA 可以简洁、活泼并具有 meme 感，同时确认的信息与玩笑或虚构说法保持分离。"),
("culture","🌍 文化","什么是 MUBA 文化？","MUBA 文化由 meme、参与、持续的角色语言、社区行为和原创作品共同形成。"),
("principles","🧭 原则","MUBA 成长时什么保持不变？","原创身份、参与、创造力、事实清晰和持续建设在工具变化时仍保持稳定。"),
("ecosystem","🧠 生态系统","什么让 MUBA 成为生态系统？","知识、社区、安全、创作、故事、网页和游戏共享一个身份，同时保持不同职责。"),
("facts","📖 事实与故事","事实和故事如何区分？","已验证的发展属于事实历史；创意故事保持为叙事，不作为真实项目事件呈现。"),
("evolution","🚀 发展","MUBA 如何在不失去自己的情况下成长？","可以围绕同一身份加入新的已验证知识、工具和体验，而无需重写 MUBA 的起源。")],
"ar":[
("character","👤 الشخصية","ما الذي يعرّف MUBA كشخصية؟","يبدأ MUBA بهوية شخصية أصلية ومتسقة. تنمو الأدوات والقصص حولها ولا تستبدلها."),
("visual","🎨 الهوية البصرية","لماذا الاتساق البصري مهم؟","الوجه المميز ولغة الملابس وعلامات الشخصية المتكررة تحافظ على وضوح هوية MUBA عبر الصيغ المختلفة."),
("voice","💬 اللغة والفكاهة","كيف يتواصل MUBA؟","يمكن أن يكون MUBA مختصراً ومرحاً وطبيعياً في ثقافة الميم مع فصل المعلومات المؤكدة عن النكات والادعاءات المختلقة."),
("culture","🌍 الثقافة","ما ثقافة MUBA؟","تتكون ثقافة MUBA من الميم والمشاركة ولغة الشخصية المتكررة وسلوك المجتمع والإبداع الأصلي."),
("principles","🧭 المبادئ","ما الذي يبقى ثابتاً مع نمو MUBA؟","تبقى الهوية الأصلية والمشاركة والإبداع ووضوح الحقائق والبناء المستمر ثابتة تحت الأدوات المتغيرة."),
("ecosystem","🧠 المنظومة","ما الذي يجعل MUBA منظومة؟","تشارك المعرفة والمجتمع والأمان والإبداع والقصة والويب والألعاب هوية واحدة مع بقاء المسؤوليات منفصلة."),
("facts","📖 الحقائق والقصة","كيف تنفصل الحقائق عن القصة؟","التطور الموثق تاريخ واقعي؛ أما مادة القصة الإبداعية فتبقى سرداً ولا تقدم كحدث حقيقي للمشروع."),
("evolution","🚀 التطور","كيف ينمو MUBA دون فقدان هويته؟","يمكن إضافة معرفة موثقة وأدوات وتجارب جديدة حول الهوية نفسها دون إعادة كتابة أصل MUBA.")],
"hi":[
("character","👤 चरित्र","MUBA को चरित्र के रूप में क्या परिभाषित करता है?","MUBA एक consistent original character identity से शुरू होता है। Tools और stories उसके आसपास बढ़ते हैं, उसे replace नहीं करते।"),
("visual","🎨 दृश्य पहचान","Visual consistency क्यों महत्वपूर्ण है?","पहचाने जाने वाला face, clothing language और recurring cues MUBA को अलग formats में पहचान योग्य रखते हैं।"),
("voice","💬 भाषा और हास्य","MUBA कैसे communicate करता है?","MUBA concise, playful और meme-native हो सकता है, जबकि confirmed information jokes या invented claims से अलग रहती है।"),
("culture","🌍 संस्कृति","MUBA culture क्या है?","MUBA culture memes, participation, recurring character language, community behavior और original work से बनती है।"),
("principles","🧭 सिद्धांत","MUBA के बढ़ने पर क्या स्थिर रहता है?","Original identity, participation, creativity, factual clarity और consistent building बदलते tools के नीचे स्थिर रहते हैं।"),
("ecosystem","🧠 इकोसिस्टम","MUBA को ecosystem क्या बनाता है?","Knowledge, community, security, creation, story, web और games एक identity साझा करते हैं लेकिन जिम्मेदारियाँ अलग रखते हैं।"),
("facts","📖 तथ्य और कहानी","Facts और story कैसे अलग हैं?","Verified development factual history है; creative story narrative रहती है और literal project event के रूप में प्रस्तुत नहीं होती।"),
("evolution","🚀 विकास","MUBA खुद को खोए बिना कैसे बढ़ सकता है?","उसी identity के आसपास नई verified knowledge, tools और experiences जोड़े जा सकते हैं, बिना MUBA origin को दोबारा लिखे।")]}

TRANSPARENCY_RECORDS={
"en":[
("map","ECOSYSTEM MAP","MUBA separates knowledge, community navigation, updates, security, creation, story, web access and games so each function has a clear responsibility."),
("lifecycle","CONTENT LIFECYCLE","Public content can move through creation, review or verification, publication and later historical reference. Not every content type uses every stage."),
("control","AUTOMATION & HUMAN CONTROL","Routine work can be automated while authority-sensitive actions and defined approvals remain under human control."),
("integrity","KNOWLEDGE INTEGRITY","Verified information, creative narrative and humor are different information classes and should not silently become one another."),
("languages","LANGUAGE CONSISTENCY","Supported languages are presentation layers over the same MUBA identity. Translation changes language, not underlying project facts."),
("failure","FAILURE BEHAVIOR","A failed or uncertain operation must not silently become a successful state; critical uncertainty stops protected development flow."),
("history","HISTORY PRESERVATION","Recorded ecosystem knowledge and development history are append-oriented. New records extend the archive instead of silently deleting established records."),
("limits","PUBLIC TRANSPARENCY LIMITS","Transparency explains public behavior and architecture without exposing secrets, credentials, exploitable security details or private DEV operations.")],
"tr":[
("map","EKOSİSTEM HARİTASI","MUBA; bilgi, topluluk yönlendirmesi, yenilikler, güvenlik, üretim, hikâye, web erişimi ve oyunları ayırarak her işleve net bir görev verir."),
("lifecycle","İÇERİK YAŞAM DÖNGÜSÜ","Kamusal içerik üretim, gerektiğinde inceleme veya doğrulama, yayın ve daha sonra tarihsel referans aşamalarından geçebilir. Her içerik türü tüm aşamaları kullanmaz."),
("control","OTOMASYON VE İNSAN KONTROLÜ","Rutin işler otomatikleşebilir; yetki hassasiyeti taşıyan işlemler ve tanımlı onaylar insan kontrolünde kalır."),
("integrity","BİLGİ BÜTÜNLÜĞÜ","Doğrulanmış bilgi, yaratıcı anlatı ve mizah farklı bilgi sınıflarıdır ve sessizce birbirine dönüşmemelidir."),
("languages","DİL TUTARLILIĞI","Desteklenen diller aynı MUBA kimliğinin sunum katmanlarıdır. Çeviri dili değiştirir, temel proje gerçeklerini değiştirmez."),
("failure","HATA DAVRANIŞI","Başarısız veya belirsiz işlem sessizce başarılı duruma dönüşmez; kritik belirsizlik korumalı geliştirme akışını durdurur."),
("history","GEÇMİŞİN KORUNMASI","Kayıtlı ekosistem bilgisi ve geliştirme geçmişi ekleme odaklıdır. Yeni kayıtlar mevcut kayıtları sessizce silmek yerine arşivi genişletir."),
("limits","KAMUSAL ŞEFFAFLIK SINIRLARI","Şeffaflık kamusal davranışı ve mimariyi açıklar; gizli bilgiler, kimlik bilgileri, istismar edilebilir güvenlik ayrıntıları veya özel DEV işlemlerini açığa çıkarmaz.")],
"zh":[
("map","生态系统地图","MUBA 将知识、社区导航、更新、安全、创作、故事、网页访问和游戏分开，使每个功能职责清晰。"),
("lifecycle","内容生命周期","公开内容可以经过创作、必要时的审核或验证、发布以及后续历史引用。并非每类内容都使用所有阶段。"),
("control","自动化与人工控制","日常工作可以自动化，而涉及权限的操作和明确审批仍由人工控制。"),
("integrity","知识完整性","已验证信息、创意叙事和幽默属于不同信息类型，不应悄然互相替代。"),
("languages","语言一致性","支持的语言是同一 MUBA 身份的展示层。翻译改变语言，不改变项目事实。"),
("failure","失败行为","失败或不确定的操作不能悄然变成成功状态；关键不确定性会停止受保护的开发流程。"),
("history","历史保存","已记录的生态知识和开发历史以追加为原则。新记录扩展档案，而不是静默删除既有记录。"),
("limits","公开透明边界","透明度解释公开行为和架构，但不暴露秘密、凭证、可利用的安全细节或私有 DEV 操作。")],
"ar":[
("map","خريطة المنظومة","يفصل MUBA المعرفة وتوجيه المجتمع والتحديثات والأمان والإبداع والقصة والويب والألعاب بحيث تكون مسؤولية كل وظيفة واضحة."),
("lifecycle","دورة حياة المحتوى","يمكن أن يمر المحتوى العام بالإنتاج ثم المراجعة أو التحقق عند الحاجة ثم النشر والرجوع التاريخي لاحقاً. ليست كل الأنواع بحاجة لكل المراحل."),
("control","الأتمتة والتحكم البشري","يمكن أتمتة الأعمال الروتينية بينما تبقى الإجراءات الحساسة للصلاحيات والموافقات المحددة تحت التحكم البشري."),
("integrity","سلامة المعرفة","المعلومات الموثقة والسرد الإبداعي والفكاهة أنواع مختلفة من المعلومات ولا ينبغي أن تتحول إلى بعضها بصمت."),
("languages","اتساق اللغات","اللغات المدعومة طبقات عرض لهوية MUBA نفسها. الترجمة تغير اللغة ولا تغير حقائق المشروع."),
("failure","سلوك الفشل","لا تتحول العملية الفاشلة أو غير المؤكدة بصمت إلى نجاح؛ عدم اليقين الحرج يوقف مسار التطوير المحمي."),
("history","حفظ التاريخ","معرفة المنظومة وتاريخ التطوير المسجلان يعتمدان الإضافة. السجلات الجديدة توسع الأرشيف ولا تحذف السجلات القائمة بصمت."),
("limits","حدود الشفافية العامة","تشرح الشفافية السلوك العام والبنية دون كشف الأسرار أو بيانات الاعتماد أو تفاصيل الأمان القابلة للاستغلال أو عمليات DEV الخاصة.")],
"hi":[
("map","इकोसिस्टम मानचित्र","MUBA knowledge, community navigation, updates, security, creation, story, web access और games को अलग रखता है ताकि हर function की जिम्मेदारी स्पष्ट हो।"),
("lifecycle","कंटेंट जीवनचक्र","Public content creation, जरूरत पर review या verification, publication और बाद में historical reference से गुजर सकता है। हर content type सभी stages उपयोग नहीं करता।"),
("control","ऑटोमेशन और मानव नियंत्रण","Routine work automate हो सकता है, जबकि authority-sensitive actions और defined approvals human control में रहते हैं।"),
("integrity","ज्ञान अखंडता","Verified information, creative narrative और humor अलग information classes हैं और चुपचाप एक-दूसरे में नहीं बदलने चाहिए।"),
("languages","भाषा स्थिरता","Supported languages एक ही MUBA identity की presentation layers हैं। Translation भाषा बदलती है, project facts नहीं।"),
("failure","विफलता व्यवहार","Failed या uncertain operation चुपचाप success नहीं बनता; critical uncertainty protected development flow को रोकती है।"),
("history","इतिहास संरक्षण","Recorded ecosystem knowledge और development history append-oriented हैं। नए records archive बढ़ाते हैं, पुराने records चुपचाप नहीं मिटाते।"),
("limits","सार्वजनिक पारदर्शिता सीमाएँ","Transparency public behavior और architecture समझाती है, लेकिन secrets, credentials, exploitable security details या private DEV operations उजागर नहीं करती।")]}

def validate_archive():
    for registry in (COMMUNITY_RECORDS,ASK_RECORDS,TRANSPARENCY_RECORDS):
        for lang,items in registry.items():
            ids=[item[0] for item in items]
            if len(ids)!=len(set(ids)): raise ValueError("Duplicate ecosystem record id: "+lang)
    return True
validate_archive()
