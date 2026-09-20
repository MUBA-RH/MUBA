"""Five-language public explanation of the current MUBA system.

This module is informational only. It has no Guardian/moderation side effects.
Each locale contains the same transparency topics, split into Telegram-safe pages.
"""

TRANSPARENCY_LABELS={
"en":"🔎 MUBA — SYSTEM TRANSPARENCY",
"tr":"🔎 MUBA — SİSTEM ŞEFFAFLIĞI",
"zh":"🔎 MUBA — 系统透明度",
"ar":"🔎 MUBA — شفافية النظام",
"hi":"🔎 MUBA — सिस्टम पारदर्शिता",
}

TRANSPARENCY_NAV={
"en":{"intro":"MUBA System Transparency","page":"Page","prev":"⬅️ Previous","next":"Next ➡️","back":"⬅️ Main Menu"},
"tr":{"intro":"MUBA Sistem Şeffaflığı","page":"Sayfa","prev":"⬅️ Önceki","next":"Sonraki ➡️","back":"⬅️ Ana Menü"},
"zh":{"intro":"MUBA 系统透明度","page":"页","prev":"⬅️ 上一页","next":"下一页 ➡️","back":"⬅️ 主菜单"},
"ar":{"intro":"شفافية نظام MUBA","page":"صفحة","prev":"⬅️ السابق","next":"التالي ➡️","back":"⬅️ القائمة الرئيسية"},
"hi":{"intro":"MUBA सिस्टम पारदर्शिता","page":"पृष्ठ","prev":"⬅️ पिछला","next":"अगला ➡️","back":"⬅️ मुख्य मेनू"},
}

TRANSPARENCY_PAGES={
"en":[
"""MUBA — SYSTEM TRANSPARENCY

MUBA is more than a Telegram bot. The current system brings together MUBA's verified knowledge base, five-language Assistant, natural conversation layer, community tools, Guardian security layer, creative tools and public web presence.

The central rule is simple: verified MUBA information is separated from unknown or unconfirmed information. The Assistant explains what the system knows; it must not invent a team, partnership, listing, roadmap date or other development that has not been confirmed.""",
"""KNOWLEDGE & ASSISTANT

The knowledge center covers what MUBA is, how it emerged, its identity, why it differs from copied meme characters, its purpose, community role, participation and its approach to future growth.

A member can enter the private MUBA Assistant, choose English, Turkish, Chinese, Arabic or Hindi, then use guided buttons or ask a MUBA question naturally. Origin, Identity, Difference, Purpose, Community and Future are separate knowledge areas.

The user does not have to reproduce a database question word for word: the system routes relevant natural questions toward its MUBA knowledge layers.""",
"""NATURAL CONVERSATION

MUBA Assistant is not only a static FAQ. Human Conversation, Natural Chat and Conversation Continuity layers allow greetings, short reactions and limited contextual follow-ups to feel more natural.

There are also everyday, humorous and absurd-question paths. Humor can be MUBA-native, but natural conversation does not authorize the system to invent a human biography or fabricate MUBA facts.

Knowledge and conversation remain distinct: knowledge should stay grounded; conversation can stay natural.""",
"""MUBA DAILY & COMMUNITY TOOLS

MUBA Daily provides structured access to MUBA's official/public information areas such as X, the website, Telegram and updates.

Story Mode explains MUBA's story as a living community narrative. Content Lab provides creative starting points for memes, posts and visual concepts. Community Guide explains the character, culture, official sources and basic safety practices.

These tools organize information already available to MUBA. They do not make the Assistant a live world-news engine; a new development that has not been supplied or confirmed cannot be known automatically.""",
"""SECURITY CHECK & CA

Security Check compares submitted links or contract-shaped addresses with the registered official MUBA sources. Its job is verification, not group moderation.

At present no official MUBA CA is published in the system. Therefore the Assistant does not invent or validate an unofficial contract address as MUBA's CA. When an official CA is confirmed, it can be added as verified information.

This fail-safe boundary is deliberate: unknown information should remain unknown rather than becoming a fabricated fact.""",
"""GUARDIAN

Guardian is separate from Assistant. Assistant handles information and conversation; Guardian is the security and management layer of the designated MUBA main Telegram group.

Guardian covers DEV-only management commands and security events such as fake/unverified CA attempts, suspicious external links, phishing/credential-theft patterns and flood/spam behavior. Depending on the event, the existing moderation flow can warn, delete, mute or ban.

Management authority is checked against the registered DEV ID; ordinary members cannot acquire DEV command authority.""",
"""DEV REPORTS & FIVE LANGUAGES

Guardian can send private event/management reports to the registered DEV ID. The report-language selector is also DEV-only.

The DEV can choose English, Turkish, Chinese, Arabic or Hindi. The reporting design therefore does not assume a developer nationality; it uses an explicitly selected locale.

Assistant language and Guardian report language are separate concerns. Guardian protects the group while Assistant serves members privately.""",
"""MUBA STUDIO & WEB

MUBA Studio is a separate creative-production area. Keeping creative generation separate from verified knowledge helps prevent creative output from being treated as project fact.

MUBA also has a public web layer hosted from its GitHub project. The website is the public-facing home; Telegram Assistant is the interactive knowledge/conversation interface; Guardian is the group-security layer.

These components belong to one ecosystem but have different responsibilities.""",
"""RUNTIME & ROUTING

The Telegram application is webhook-based. Incoming Telegram updates are routed to the relevant handler: private Assistant conversations, menu callbacks, the designated Guardian group, or Studio-related functions.

The runtime also keeps bounded duplicate-message protection so a redelivered Telegram message is not intentionally processed twice.

The architecture separates responsibilities rather than treating every message as one undifferentiated bot conversation.""",
"""INFORMATION POLICY

The core behavior is:

Known and verified → answer.
Registered official source → identify it.
Conversation → respond naturally.
Security event → Guardian handles it.
Unknown or unconfirmed → do not manufacture a fact.

MUBA's cultural voice can be creative while factual project information remains controlled. The Assistant cannot know a future or external development that has never been supplied to the system.""",
"""DEVELOPMENT & STABILITY

The production baseline lives on the main GitHub branch. Changes are developed in isolated branches, tested, reviewed through pull requests and merged only after the required checks succeed.

The operating workflow is: stable baseline → solution design → explicit authorization → isolated branch → implementation → tests/CI → pull request → merge → live verification when available → new stable baseline.

This protects the working Assistant, five-language system, Guardian, security and other modules from unrelated changes.""",
"""WHAT MUBA IS TODAY

The current ecosystem combines: MUBA Knowledge Base; guided and natural knowledge access; five-language Assistant; Human Conversation and Continuity; MUBA Daily; Story Mode; Content Lab; Community Guide; Security Check; MUBA Studio; Guardian; DEV-only controls; private Guardian DEV reports; the public web layer; and GitHub-based development/testing.

In short:
Group → entry point.
Assistant → knowledge and interaction.
Knowledge → verified MUBA information.
Conversation → natural communication.
Guide/Security → trusted-source guidance.
Studio → creative area.
Guardian → group security.
GitHub → technical backbone.

Current explicit information boundary: no official active CA is published in the system yet.""",
],
"tr":[
"""MUBA — SİSTEM ŞEFFAFLIĞI

MUBA yalnızca bir Telegram botu değildir. Mevcut sistem; MUBA'nın doğrulanmış bilgi tabanını, beş dilli Assistant'ı, doğal konuşma katmanını, topluluk araçlarını, Guardian güvenlik katmanını, yaratıcı araçları ve herkese açık web varlığını bir araya getirir.

Merkezdeki kural basittir: doğrulanmış MUBA bilgisi, bilinmeyen veya doğrulanmamış bilgiden ayrılır. Assistant sistemin bildiğini anlatır; doğrulanmamış ekip, ortaklık, listeleme, roadmap tarihi veya başka bir gelişmeyi uydurmamalıdır.""",
"""BİLGİ TABANI & ASSISTANT

Bilgi merkezi; MUBA'nın ne olduğunu, nasıl ortaya çıktığını, kimliğini, kopya meme karakterlerinden neden farklı olduğunu, amacını, topluluğun rolünü, katılımı ve gelecekteki büyümeye yaklaşımını kapsar.

Üye özel MUBA Assistant'a girer; İngilizce, Türkçe, Çince, Arapça veya Hintçe seçer; ardından yönlendirmeli butonları kullanabilir veya MUBA hakkında doğal şekilde soru sorabilir. Origin, Identity, Difference, Purpose, Community ve Future ayrı bilgi alanlarıdır.

Kullanıcının veritabanındaki soruyu kelimesi kelimesine yazması gerekmez; sistem ilgili doğal soruları MUBA bilgi katmanlarına yönlendirir.""",
"""DOĞAL KONUŞMA

MUBA Assistant yalnızca sabit bir SSS değildir. Human Conversation, Natural Chat ve Conversation Continuity katmanları; selamlaşmaların, kısa tepkilerin ve sınırlı bağlamsal devam mesajlarının daha doğal ilerlemesini sağlar.

Gündelik, mizahi ve absürt soru yolları da vardır. Mizah MUBA tarzında olabilir; ancak doğal konuşma sisteme insan biyografisi veya MUBA hakkında gerçek dışı bilgi uydurma yetkisi vermez.

Bilgi ile sohbet ayrı kalır: bilgi temellendirilmiş, konuşma doğal olmalıdır.""",
"""MUBA DAILY & TOPLULUK ARAÇLARI

MUBA Daily; X, web sitesi, Telegram ve güncellemeler gibi MUBA'nın resmî/herkese açık bilgi alanlarına düzenli erişim sağlar.

Story Mode, MUBA'nın hikâyesini yaşayan bir topluluk anlatısı olarak açıklar. Content Lab meme, gönderi ve görsel fikirleri için yaratıcı başlangıç noktaları sunar. Community Guide karakteri, kültürü, resmî kaynakları ve temel güvenlik uygulamalarını açıklar.

Bu araçlar MUBA'ya verilmiş bilgiyi düzenler. Assistant'ı canlı dünya haber motoruna dönüştürmez; sisteme verilmemiş veya doğrulanmamış yeni bir gelişme otomatik olarak bilinemez.""",
"""SECURITY CHECK & CA

Security Check, gönderilen linkleri veya kontrat biçimindeki adresleri kayıtlı resmî MUBA kaynaklarıyla karşılaştırır. Görevi doğrulamadır; grup moderasyonu değildir.

Şu anda sistemde yayımlanmış resmî MUBA CA bulunmuyor. Bu nedenle Assistant resmî olmayan bir kontrat adresini MUBA CA'sı olarak uydurmaz veya doğrulamaz. Resmî CA doğrulandığında sisteme doğrulanmış bilgi olarak eklenebilir.

Bu fail-safe sınırı bilinçlidir: bilinmeyen bilgi, uydurma gerçeğe dönüşmek yerine bilinmeyen kalmalıdır.""",
"""GUARDIAN

Guardian, Assistant'tan ayrıdır. Assistant bilgi ve sohbeti yönetirken Guardian, belirlenmiş MUBA ana Telegram grubunun güvenlik ve yönetim katmanıdır.

Guardian; DEV-only yönetim komutlarını ve sahte/doğrulanmamış CA girişimleri, şüpheli dış bağlantılar, phishing/kimlik bilgisi hırsızlığı örüntüleri ve flood/spam gibi güvenlik olaylarını kapsar. Olaya göre mevcut moderasyon akışı uyarı, silme, susturma veya ban uygulayabilir.

Yönetim yetkisi kayıtlı DEV ID üzerinden kontrol edilir; normal üyeler DEV komut yetkisi kazanamaz.""",
"""DEV RAPORLARI & BEŞ DİL

Guardian, kayıtlı DEV ID'ye özel olay/yönetim raporları gönderebilir. Rapor dili seçimi de yalnızca DEV'e açıktır.

DEV; İngilizce, Türkçe, Çince, Arapça veya Hintçe seçebilir. Böylece raporlama sistemi geliştiricinin milliyetini varsaymaz; açıkça seçilmiş dili kullanır.

Assistant dili ile Guardian rapor dili birbirinden ayrıdır. Guardian grubu korurken Assistant üyelere özel sohbetten hizmet verir.""",
"""MUBA STUDIO & WEB

MUBA Studio ayrı bir yaratıcı üretim alanıdır. Yaratıcı üretimi doğrulanmış bilgi katmanından ayırmak, yaratıcı çıktının proje gerçeği sanılmasını önlemeye yardımcı olur.

MUBA'nın GitHub projesinden yayımlanan herkese açık bir web katmanı da vardır. Web sitesi dışarıya açık ev; Telegram Assistant etkileşimli bilgi/sohbet arayüzü; Guardian ise grup güvenliği katmanıdır.

Bu bileşenler aynı ekosisteme aittir fakat sorumlulukları farklıdır.""",
"""RUNTIME & YÖNLENDİRME

Telegram uygulaması webhook tabanlıdır. Gelen Telegram güncellemeleri ilgili handler'a yönlendirilir: özel Assistant konuşmaları, menü callback'leri, belirlenmiş Guardian grubu veya Studio ile ilgili işlevler.

Runtime ayrıca sınırlı bir duplicate-message koruması tutar; Telegram'ın yeniden teslim ettiği aynı mesajın bilinçli olarak iki kez işlenmesini önler.

Mimari, her mesajı tek ve ayrışmamış bir bot sohbeti saymak yerine sorumlulukları ayırır.""",
"""BİLGİ POLİTİKASI

Temel davranış:

Biliniyor ve doğrulanmış → cevapla.
Kayıtlı resmî kaynak → tanımla.
Sohbet → doğal cevap ver.
Güvenlik olayı → Guardian işler.
Bilinmiyor veya doğrulanmamış → gerçek uydurma.

MUBA'nın kültürel sesi yaratıcı olabilirken proje gerçekleri kontrollü kalır. Assistant, kendisine hiç verilmemiş gelecekteki veya dış dünyadaki bir gelişmeyi bilemez.""",
"""GELİŞTİRME & STABİLİTE

Üretim baseline'ı GitHub main branch üzerinde yaşar. Değişiklikler izole branch'lerde geliştirilir, test edilir, pull request üzerinden incelenir ve gerekli kontroller başarılı olduktan sonra merge edilir.

Çalışma akışı: stabil baseline → çözüm tasarımı → açık yetkilendirme → izole branch → uygulama → test/CI → pull request → merge → mümkünse canlı doğrulama → yeni stabil baseline.

Bu yapı çalışan Assistant'ı, beş dil sistemini, Guardian'ı, güvenliği ve diğer modülleri ilgisiz değişikliklerden korur.""",
"""MUBA BUGÜN NEDİR?

Mevcut ekosistem şunları birleştirir: MUBA Knowledge Base; yönlendirmeli ve doğal bilgi erişimi; beş dilli Assistant; Human Conversation ve Continuity; MUBA Daily; Story Mode; Content Lab; Community Guide; Security Check; MUBA Studio; Guardian; DEV-only kontroller; özel Guardian DEV raporları; herkese açık web katmanı ve GitHub tabanlı geliştirme/test sistemi.

Kısaca:
Grup → giriş noktası.
Assistant → bilgi ve etkileşim.
Knowledge → doğrulanmış MUBA bilgisi.
Conversation → doğal iletişim.
Guide/Security → güvenilir kaynak yönlendirmesi.
Studio → yaratıcı alan.
Guardian → grup güvenliği.
GitHub → teknik omurga.

Mevcut açık bilgi sınırı: sistemde henüz yayımlanmış resmî aktif CA yoktur.""",
],
}

# Full semantic translations for the remaining locales, matching the same 12 topics.
TRANSPARENCY_PAGES["zh"]=[
"""MUBA — 系统透明度

MUBA 不只是一个 Telegram 机器人。当前系统把 MUBA 的已验证知识库、五语言 Assistant、自然对话层、社区工具、Guardian 安全层、创意工具和公开网站整合在一起。

核心规则很简单：已验证的 MUBA 信息与未知或未确认的信息严格区分。Assistant 只解释系统真正知道的内容；不会编造未经确认的团队、合作、上币、路线图日期或其他进展。""",
"""知识库与 ASSISTANT

知识中心涵盖 MUBA 是什么、如何出现、身份、为什么不同于复制型 meme 角色、目的、社区作用、参与方式以及未来增长思路。

成员进入私聊 MUBA Assistant 后，可选择英语、土耳其语、中文、阿拉伯语或印地语，再通过引导按钮或自然提问了解 MUBA。Origin、Identity、Difference、Purpose、Community 和 Future 是独立知识区域。

用户无需逐字复述数据库问题；系统会把相关自然语言问题导向 MUBA 的知识层。""",
"""自然对话

MUBA Assistant 不只是静态 FAQ。Human Conversation、Natural Chat 和 Conversation Continuity 让问候、短回复和有限的上下文追问更自然。

系统也包含日常、幽默和荒诞问题路径。幽默可以保持 MUBA 风格，但自然对话不意味着可以虚构人类经历或 MUBA 事实。

知识与聊天保持分离：知识需要有依据，对话可以自然。""",
"""MUBA DAILY 与社区工具

MUBA Daily 对 X、网站、Telegram 和更新等 MUBA 官方/公开信息区域进行结构化整理。

Story Mode 把 MUBA 的故事解释为持续发展的社区叙事。Content Lab 为 meme、帖子和视觉概念提供创意起点。Community Guide 介绍角色、文化、官方来源和基本安全实践。

这些工具整理已经提供给 MUBA 的信息，并不会让 Assistant 变成实时全球新闻引擎；未提供或未确认的新事件不会自动被系统知道。""",
"""SECURITY CHECK 与 CA

Security Check 会把用户提交的链接或类似合约地址的字符串与已登记的 MUBA 官方来源比较。它负责验证，不负责群组管理。

目前系统中尚未发布 MUBA 官方 CA。因此 Assistant 不会虚构 CA，也不会把非官方合约地址认证为 MUBA 官方地址。官方 CA 一旦确认，就可以作为已验证信息加入系统。

这是有意设计的安全边界：未知信息应保持未知，而不是变成虚构事实。""",
"""GUARDIAN

Guardian 与 Assistant 相互独立。Assistant 负责信息和对话；Guardian 是指定 MUBA Telegram 主群的安全和管理层。

Guardian 处理仅 DEV 可用的管理命令，以及虚假/未验证 CA、可疑外部链接、钓鱼/凭证窃取模式和 flood/spam 等安全事件。根据事件，现有管理流程可以警告、删除、禁言或封禁。

管理权限依据登记的 DEV ID 验证；普通成员无法获得 DEV 命令权限。""",
"""DEV 报告与五种语言

Guardian 可以向登记的 DEV ID 私发事件/管理报告。报告语言选择器同样仅限 DEV。

DEV 可选择英语、土耳其语、中文、阿拉伯语或印地语。因此报告系统不推测开发者国籍，而是使用明确选择的语言。

Assistant 语言和 Guardian 报告语言是两个独立设置。Guardian 保护群组，Assistant 在私聊中服务成员。""",
"""MUBA STUDIO 与网站

MUBA Studio 是独立的创意生产区域。把创意生成与已验证知识分离，有助于避免把创意输出误认为项目事实。

MUBA 还有由 GitHub 项目发布的公开网站层。网站是公开主页；Telegram Assistant 是互动知识/对话界面；Guardian 是群组安全层。

这些组件属于同一生态，但承担不同职责。""",
"""运行与路由

Telegram 应用基于 webhook。收到的 Telegram 更新会被路由到对应 handler：私聊 Assistant、菜单 callback、指定 Guardian 群组或 Studio 相关功能。

运行时还保留有限的重复消息保护，避免 Telegram 重新投递同一消息时被有意处理两次。

架构按职责分离，而不是把所有消息都当成同一种机器人对话。""",
"""信息政策

核心行为：

已知且已验证 → 回答。
已登记官方来源 → 识别。
对话 → 自然回应。
安全事件 → 交给 Guardian。
未知或未确认 → 不制造事实。

MUBA 的文化表达可以有创意，但项目事实必须受控。Assistant 无法知道从未提供给系统的未来事件或外部新进展。""",
"""开发与稳定性

生产 baseline 位于 GitHub main 分支。变更在隔离分支开发、测试，通过 pull request 审查，并在必要检查成功后才 merge。

流程为：稳定 baseline → 方案设计 → 明确授权 → 隔离分支 → 实现 → 测试/CI → pull request → merge → 条件允许时进行线上验证 → 新稳定 baseline。

这样可以保护正在运行的 Assistant、五语言系统、Guardian、安全层和其他模块免受无关改动影响。""",
"""今天的 MUBA 是什么？

当前生态整合了：MUBA Knowledge Base、引导式和自然知识访问、五语言 Assistant、Human Conversation 与 Continuity、MUBA Daily、Story Mode、Content Lab、Community Guide、Security Check、MUBA Studio、Guardian、DEV-only 控制、Guardian 私人 DEV 报告、公开网站层以及基于 GitHub 的开发/测试系统。

简而言之：
群组 → 入口。
Assistant → 信息与互动。
Knowledge → 已验证 MUBA 信息。
Conversation → 自然交流。
Guide/Security → 可信来源指引。
Studio → 创意区域。
Guardian → 群组安全。
GitHub → 技术骨架。

当前明确的信息边界：系统中尚未发布官方有效 CA。""",
]
TRANSPARENCY_PAGES["ar"]=[
"""MUBA — شفافية النظام

MUBA ليس مجرد بوت Telegram. يجمع النظام الحالي قاعدة معرفة MUBA الموثقة، وAssistant بخمس لغات، وطبقة المحادثة الطبيعية، وأدوات المجتمع، وطبقة أمان Guardian، والأدوات الإبداعية، والحضور العام على الويب.

القاعدة المركزية بسيطة: يتم فصل معلومات MUBA الموثقة عن المعلومات المجهولة أو غير المؤكدة. يشرح Assistant ما يعرفه النظام فعلاً ولا يختلق فريقاً أو شراكة أو إدراجاً أو موعد خارطة طريق أو تطوراً غير مؤكد.""",
"""قاعدة المعرفة وASSISTANT

يغطي مركز المعرفة ماهية MUBA وكيف ظهر وهويته وسبب اختلافه عن شخصيات الميم المنسوخة وهدفه ودور المجتمع والمشاركة ونهجه تجاه النمو المستقبلي.

يمكن للعضو دخول MUBA Assistant الخاص واختيار الإنجليزية أو التركية أو الصينية أو العربية أو الهندية، ثم استخدام الأزرار الموجهة أو طرح سؤال طبيعي عن MUBA. Origin وIdentity وDifference وPurpose وCommunity وFuture مجالات معرفة منفصلة.

لا يحتاج المستخدم إلى كتابة سؤال قاعدة البيانات حرفياً؛ يوجّه النظام الأسئلة الطبيعية ذات الصلة إلى طبقات معرفة MUBA.""",
"""المحادثة الطبيعية

MUBA Assistant ليس FAQ ثابتاً فقط. تسمح طبقات Human Conversation وNatural Chat وConversation Continuity للتحيات والردود القصيرة والمتابعات السياقية المحدودة بأن تبدو أكثر طبيعية.

توجد أيضاً مسارات للأسئلة اليومية والفكاهية والغريبة. يمكن أن تكون الفكاهة بروح MUBA، لكن المحادثة الطبيعية لا تسمح باختلاق سيرة بشرية أو حقائق عن MUBA.

تبقى المعرفة والمحادثة منفصلتين: المعرفة موثقة والمحادثة طبيعية.""",
"""MUBA DAILY وأدوات المجتمع

يوفر MUBA Daily وصولاً منظماً إلى مناطق المعلومات الرسمية/العامة مثل X والموقع وTelegram والتحديثات.

يشرح Story Mode قصة MUBA كسرد مجتمعي حي. يقدم Content Lab بدايات إبداعية للميم والمنشورات والأفكار البصرية. يشرح Community Guide الشخصية والثقافة والمصادر الرسمية وممارسات الأمان الأساسية.

تنظم هذه الأدوات المعلومات المتاحة لـ MUBA ولا تجعل Assistant محرك أخبار عالمي مباشر؛ التطور الجديد الذي لم يُقدَّم أو يؤكد لا يمكن معرفته تلقائياً.""",
"""SECURITY CHECK وCA

يقارن Security Check الروابط أو العناوين الشبيهة بعقود بالمصادر الرسمية المسجلة لـ MUBA. مهمته التحقق وليس إدارة المجموعة.

حالياً لا يوجد CA رسمي لـ MUBA منشور في النظام. لذلك لا يختلق Assistant عنوان عقد ولا يعتمد عنواناً غير رسمي باعتباره CA لـ MUBA. عند تأكيد CA رسمي يمكن إضافته كمعلومة موثقة.

هذا حد أمان مقصود: المعلومة المجهولة تبقى مجهولة بدلاً من التحول إلى حقيقة مختلقة.""",
"""GUARDIAN

Guardian منفصل عن Assistant. يتولى Assistant المعلومات والمحادثة، بينما Guardian هو طبقة الأمان والإدارة لمجموعة MUBA الرئيسية المحددة على Telegram.

يغطي Guardian أوامر الإدارة الخاصة بـ DEV وأحداث الأمان مثل CA المزيف/غير الموثق والروابط الخارجية المشبوهة وأنماط التصيد/سرقة بيانات الاعتماد والإغراق/السبام. حسب الحدث يمكن لمسار الإشراف الحالي التحذير أو الحذف أو الكتم أو الحظر.

يتم التحقق من صلاحية الإدارة عبر DEV ID المسجل؛ لا يستطيع الأعضاء العاديون الحصول على صلاحية أوامر DEV.""",
"""تقارير DEV وخمس لغات

يمكن لـ Guardian إرسال تقارير خاصة بالأحداث/الإدارة إلى DEV ID المسجل. اختيار لغة التقرير متاح لـ DEV فقط أيضاً.

يمكن لـ DEV اختيار الإنجليزية أو التركية أو الصينية أو العربية أو الهندية. لذلك لا يفترض نظام التقارير جنسية المطور، بل يستخدم اللغة المختارة صراحة.

لغة Assistant ولغة تقارير Guardian منفصلتان. Guardian يحمي المجموعة بينما يخدم Assistant الأعضاء في المحادثة الخاصة.""",
"""MUBA STUDIO والويب

MUBA Studio مساحة مستقلة للإنتاج الإبداعي. فصل الإبداع عن المعرفة الموثقة يساعد على منع اعتبار المحتوى الإبداعي حقيقة عن المشروع.

لدى MUBA أيضاً طبقة ويب عامة منشورة من مشروع GitHub. الموقع هو الواجهة العامة؛ Telegram Assistant واجهة المعرفة/المحادثة التفاعلية؛ Guardian طبقة أمان المجموعة.

تنتمي هذه المكونات إلى نظام واحد لكن مسؤولياتها مختلفة.""",
"""التشغيل والتوجيه

تطبيق Telegram قائم على webhook. يتم توجيه تحديثات Telegram الواردة إلى المعالج المناسب: محادثات Assistant الخاصة أو callbacks للقوائم أو مجموعة Guardian المحددة أو وظائف Studio.

يحتفظ وقت التشغيل أيضاً بحماية محدودة من الرسائل المكررة حتى لا تتم معالجة الرسالة نفسها عمداً مرتين عند إعادة تسليمها من Telegram.

تفصل البنية المسؤوليات بدلاً من معاملة كل الرسائل كمحادثة بوت واحدة.""",
"""سياسة المعلومات

السلوك الأساسي:

معلوم وموثق → أجب.
مصدر رسمي مسجل → عرّفه.
محادثة → أجب بشكل طبيعي.
حدث أمني → يتولاه Guardian.
مجهول أو غير مؤكد → لا تختلق حقيقة.

يمكن لصوت MUBA الثقافي أن يكون إبداعياً بينما تبقى حقائق المشروع مضبوطة. لا يستطيع Assistant معرفة تطور مستقبلي أو خارجي لم يُقدَّم للنظام أصلاً.""",
"""التطوير والاستقرار

يعيش خط الإنتاج الأساسي على فرع GitHub main. يتم تطوير التغييرات في فروع معزولة واختبارها ومراجعتها عبر pull requests ودمجها فقط بعد نجاح الفحوص المطلوبة.

المسار: baseline مستقر → تصميم الحل → تفويض صريح → فرع معزول → تنفيذ → اختبارات/CI → pull request → merge → تحقق مباشر عند الإمكان → baseline مستقر جديد.

يحمي ذلك Assistant العامل ونظام اللغات الخمس وGuardian والأمان والوحدات الأخرى من التغييرات غير المرتبطة.""",
"""ما هو MUBA اليوم؟

يجمع النظام الحالي: MUBA Knowledge Base؛ الوصول الموجه والطبيعي للمعرفة؛ Assistant بخمس لغات؛ Human Conversation وContinuity؛ MUBA Daily؛ Story Mode؛ Content Lab؛ Community Guide؛ Security Check؛ MUBA Studio؛ Guardian؛ ضوابط DEV-only؛ تقارير Guardian الخاصة لـ DEV؛ طبقة الويب العامة؛ ونظام التطوير/الاختبار عبر GitHub.

باختصار:
المجموعة → نقطة الدخول.
Assistant → المعرفة والتفاعل.
Knowledge → معلومات MUBA الموثقة.
Conversation → تواصل طبيعي.
Guide/Security → إرشاد إلى المصادر الموثوقة.
Studio → مساحة إبداعية.
Guardian → أمان المجموعة.
GitHub → العمود التقني.

الحد الحالي الواضح للمعلومات: لا يوجد CA رسمي نشط منشور في النظام بعد.""",
]
TRANSPARENCY_PAGES["hi"]=[
"""MUBA — सिस्टम पारदर्शिता

MUBA केवल Telegram bot नहीं है। मौजूदा सिस्टम MUBA के verified knowledge base, पाँच-भाषा Assistant, natural conversation layer, community tools, Guardian security layer, creative tools और public web presence को एक साथ लाता है।

मुख्य नियम सरल है: verified MUBA information को unknown या unconfirmed information से अलग रखा जाता है। Assistant वही समझाता है जो सिस्टम वास्तव में जानता है; वह unconfirmed team, partnership, listing, roadmap date या अन्य development नहीं गढ़ता।""",
"""KNOWLEDGE & ASSISTANT

Knowledge center बताता है कि MUBA क्या है, कैसे उभरा, उसकी identity क्या है, copied meme characters से क्यों अलग है, उसका purpose, community की भूमिका, participation और future growth का approach क्या है।

Member private MUBA Assistant में जाकर English, Turkish, Chinese, Arabic या Hindi चुन सकता है, फिर guided buttons या natural MUBA question इस्तेमाल कर सकता है। Origin, Identity, Difference, Purpose, Community और Future अलग knowledge areas हैं।

User को database question शब्दशः लिखने की जरूरत नहीं; system relevant natural questions को MUBA knowledge layers तक route करता है।""",
"""NATURAL CONVERSATION

MUBA Assistant केवल static FAQ नहीं है। Human Conversation, Natural Chat और Conversation Continuity greetings, short reactions और सीमित contextual follow-ups को अधिक natural बनाते हैं।

Everyday, humorous और absurd-question paths भी हैं। Humor MUBA-native हो सकता है, लेकिन natural conversation system को human biography या MUBA facts गढ़ने की अनुमति नहीं देता।

Knowledge और conversation अलग रहते हैं: knowledge grounded रहता है, conversation natural रह सकता है।""",
"""MUBA DAILY & COMMUNITY TOOLS

MUBA Daily, X, website, Telegram और updates जैसे MUBA के official/public information areas तक structured access देता है।

Story Mode MUBA की story को living community narrative के रूप में समझाता है। Content Lab memes, posts और visual concepts के लिए creative starting points देता है। Community Guide character, culture, official sources और basic safety practices समझाता है।

ये tools MUBA को दी गई information व्यवस्थित करते हैं। वे Assistant को live world-news engine नहीं बनाते; जो नया development system को दिया या confirm नहीं किया गया, वह automatically ज्ञात नहीं हो सकता।""",
"""SECURITY CHECK & CA

Security Check submitted links या contract-जैसे addresses को registered official MUBA sources से compare करता है। इसका काम verification है, group moderation नहीं।

अभी system में कोई official MUBA CA published नहीं है। इसलिए Assistant कोई CA गढ़ता नहीं और unofficial contract address को MUBA का official CA verify नहीं करता। Official CA confirm होने पर verified information के रूप में जोड़ा जा सकता है।

यह जानबूझकर fail-safe boundary है: unknown information को fabricated fact बनाने के बजाय unknown रखा जाता है।""",
"""GUARDIAN

Guardian, Assistant से अलग है। Assistant information और conversation संभालता है; Guardian designated MUBA main Telegram group की security और management layer है।

Guardian DEV-only management commands और fake/unverified CA, suspicious external links, phishing/credential-theft patterns तथा flood/spam जैसे security events संभालता है। Event के अनुसार existing moderation flow warn, delete, mute या ban कर सकता है।

Management authority registered DEV ID से verify होती है; ordinary members DEV command authority हासिल नहीं कर सकते।""",
"""DEV REPORTS & FIVE LANGUAGES

Guardian registered DEV ID को private event/management reports भेज सकता है। Report-language selector भी DEV-only है।

DEV English, Turkish, Chinese, Arabic या Hindi चुन सकता है। इसलिए reporting system developer nationality assume नहीं करता; explicitly selected locale इस्तेमाल करता है।

Assistant language और Guardian report language अलग settings हैं। Guardian group को protect करता है, जबकि Assistant private chat में members की मदद करता है।""",
"""MUBA STUDIO & WEB

MUBA Studio अलग creative-production area है। Creative generation को verified knowledge से अलग रखने से creative output को project fact समझने का जोखिम कम होता है।

MUBA का GitHub project से published public web layer भी है। Website public-facing home है; Telegram Assistant interactive knowledge/conversation interface है; Guardian group-security layer है।

ये components एक ecosystem के हिस्से हैं, लेकिन उनकी responsibilities अलग हैं।""",
"""RUNTIME & ROUTING

Telegram application webhook-based है। Incoming Telegram updates relevant handler तक route होते हैं: private Assistant conversations, menu callbacks, designated Guardian group या Studio-related functions।

Runtime bounded duplicate-message protection भी रखता है ताकि Telegram द्वारा redelivered वही message जानबूझकर दो बार process न हो।

Architecture responsibilities को अलग करता है, हर message को एक ही undifferentiated bot conversation नहीं मानता।""",
"""INFORMATION POLICY

Core behavior:

Known और verified → answer.
Registered official source → identify.
Conversation → naturally respond.
Security event → Guardian handles it.
Unknown या unconfirmed → fact manufacture नहीं करना।

MUBA की cultural voice creative हो सकती है जबकि factual project information controlled रहती है। Assistant ऐसे future या external development को नहीं जान सकता जो system को कभी दिया ही नहीं गया।""",
"""DEVELOPMENT & STABILITY

Production baseline GitHub main branch पर रहता है। Changes isolated branches में develop और test होते हैं, pull requests से review होते हैं और required checks successful होने के बाद ही merge होते हैं।

Workflow: stable baseline → solution design → explicit authorization → isolated branch → implementation → tests/CI → pull request → merge → उपलब्ध होने पर live verification → new stable baseline.

यह working Assistant, five-language system, Guardian, security और अन्य modules को unrelated changes से बचाता है।""",
"""MUBA आज क्या है?

Current ecosystem में MUBA Knowledge Base; guided और natural knowledge access; five-language Assistant; Human Conversation और Continuity; MUBA Daily; Story Mode; Content Lab; Community Guide; Security Check; MUBA Studio; Guardian; DEV-only controls; private Guardian DEV reports; public web layer; और GitHub-based development/testing शामिल हैं।

संक्षेप में:
Group → entry point.
Assistant → knowledge और interaction.
Knowledge → verified MUBA information.
Conversation → natural communication.
Guide/Security → trusted-source guidance.
Studio → creative area.
Guardian → group security.
GitHub → technical backbone.

वर्तमान स्पष्ट information boundary: system में अभी कोई official active CA published नहीं है।""",
]

assert set(TRANSPARENCY_PAGES)=={"en","tr","zh","ar","hi"}
assert all(len(v)==12 for v in TRANSPARENCY_PAGES.values())
