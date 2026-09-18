"""Free, deterministic semantic conversation knowledge for MUBA.

No external API, model download, token, or paid service is required. Protected
topics remain owned by the existing specialist layers.
"""
TOPICS={
"origin":{
"en":"MUBA did not begin with a grand project story or a prewritten legend. The character came first; people saw it, shared it, commented, created around it, and a community formed naturally.",
"tr":"MUBA büyük bir proje hikâyesi veya önceden yazılmış bir efsaneyle başlamadı. Önce karakter vardı; insanlar onu gördü, paylaştı, yorumladı, içerik üretti ve topluluk doğal biçimde oluştu.",
"zh":"MUBA 并不是从宏大的项目故事或预先写好的传奇开始的。最先出现的是这个角色；人们看到它、分享它、评论并围绕它创作，社区由此自然形成。",
"ar":"لم يبدأ MUBA بقصة مشروع ضخمة أو أسطورة مكتوبة مسبقاً. ظهرت الشخصية أولاً؛ رآها الناس وشاركوها وعلقوا عليها وصنعوا محتوى حولها، ثم تشكّل المجتمع بشكل طبيعي.",
"hi":"MUBA किसी बड़ी project story या पहले से लिखी legend के साथ शुरू नहीं हुआ। पहले character आया; लोगों ने उसे देखा, share किया, comment किया, content बनाया और community स्वाभाविक रूप से बनी।"},
"identity":{
"en":"MUBA is an original meme character and community shaped by culture, creativity, participation, and consistency.",
"tr":"MUBA; kültür, yaratıcılık, katılım ve istikrar etrafında şekillenen özgün bir meme karakteri ve topluluğudur.",
"zh":"MUBA 是一个围绕文化、创造力、参与和持续建设形成的原创 meme 角色与社区。",
"ar":"MUBA شخصية ميم أصلية ومجتمع تشكّلا حول الثقافة والإبداع والمشاركة والاستمرارية.",
"hi":"MUBA एक मौलिक meme character और community है, जो culture, creativity, participation और consistency के इर्द-गिर्द बना है।"},
"difference":{
"en":"MUBA is not a copy of another project's dog, cat, or character. It has its own face, personality, identity, and community culture.",
"tr":"MUBA başka bir projenin köpek, kedi veya karakterinin kopyası değildir. Kendi yüzü, kişiliği, kimliği ve topluluk kültürü vardır.",
"zh":"MUBA 不是其他项目的狗、猫或角色的复制品。它有自己的外观、个性、身份和社区文化。",
"ar":"MUBA ليس نسخة من كلب أو قطة أو شخصية لمشروع آخر. له مظهره وشخصيته وهويته وثقافة مجتمعه الخاصة.",
"hi":"MUBA किसी दूसरे project के dog, cat या character की copy नहीं है। इसका अपना चेहरा, personality, identity और community culture है।"},
"purpose":{
"en":"MUBA's purpose is to grow an original meme culture and community through creativity, participation, social presence, and consistent building—not through invented technological promises.",
"tr":"MUBA'nın amacı; uydurma teknolojik vaatlerle değil, yaratıcılık, katılım, sosyal görünürlük ve istikrarlı üretimle özgün bir meme kültürü ve topluluğu büyütmektir.",
"zh":"MUBA 的目标不是靠虚构的技术承诺，而是通过创造力、参与、社交影响力和持续建设来发展原创 meme 文化与社区。",
"ar":"هدف MUBA هو تنمية ثقافة ميم ومجتمع أصليين عبر الإبداع والمشاركة والحضور الاجتماعي والبناء المستمر، لا عبر وعود تقنية مختلقة.",
"hi":"MUBA का उद्देश्य काल्पनिक technological promises से नहीं, बल्कि creativity, participation, social presence और लगातार building के जरिए एक मौलिक meme culture और community बढ़ाना है।"},
"plan":{
"en":"The plan is practical: grow the community, create original content, strengthen MUBA's identity, encourage participation, improve social presence and community experience, and announce only what is confirmed.",
"tr":"Plan pratik: topluluğu büyütmek, özgün içerik üretmek, MUBA kimliğini güçlendirmek, katılımı artırmak, sosyal görünürlüğü ve topluluk deneyimini geliştirmek ve yalnızca doğrulanmış gelişmeleri duyurmak.",
"zh":"计划很实际：发展社区、创作原创内容、强化 MUBA 身份、鼓励参与、提升社交影响力和社区体验，并只公布已确认的进展。",
"ar":"الخطة عملية: تنمية المجتمع، إنتاج محتوى أصلي، تقوية هوية MUBA، تشجيع المشاركة، تحسين الحضور الاجتماعي وتجربة المجتمع، وإعلان ما تم تأكيده فقط.",
"hi":"योजना व्यावहारिक है: community बढ़ाना, original content बनाना, MUBA identity मजबूत करना, participation बढ़ाना, social presence और community experience सुधारना, और केवल confirmed developments घोषित करना।"},
"community":{
"en":"The community is central: people share MUBA, comment, create their own content, participate in the culture, and help the character's story develop organically.",
"tr":"Topluluk merkezde yer alır: insanlar MUBA'yı paylaşır, yorumlar, kendi içeriklerini üretir, kültüre katılır ve karakterin hikâyesinin doğal biçimde gelişmesine katkı sağlar.",
"zh":"社区处于核心位置：人们分享 MUBA、评论、创作自己的内容、参与文化，并让这个角色的故事自然发展。",
"ar":"المجتمع في المركز: يشارك الناس MUBA ويعلقون ويصنعون محتواهم ويشاركون في الثقافة ويساعدون قصة الشخصية على التطور بشكل طبيعي.",
"hi":"Community केंद्र में है: लोग MUBA को share करते हैं, comment करते हैं, अपना content बनाते हैं, culture में भाग लेते हैं और character की story को स्वाभाविक रूप से आगे बढ़ाते हैं।"}
}
