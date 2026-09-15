from __future__ import annotations

import json
import logging
import os
import random
import re
import unicodedata

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("muba")

THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.35"))
REPLY_IN_GROUPS = os.getenv("REPLY_IN_GROUPS_WITHOUT_MENTION", "true").lower() == "true"
REPLY_ALWAYS_PRIVATE = os.getenv("REPLY_ALWAYS_IN_PRIVATE", "true").lower() == "true"

KNOWLEDGE = json.loads(r"""{
  "identity": {
    "name": "MUBA",
    "handle_x": "@MUBA_RH",
    "telegram": "https://t.me/MUBA_RH",
    "website": "https://muba-rh.github.io/MUBA/",
    "x": "https://x.com/MUBA_RH",
    "ticker": "$MUBA",
    "contract_address": null,
    "contract_status": "CA coming soon",
    "ecosystem": [
      "Robinhood",
      "Flap",
      "Uniswap"
    ],
    "symbols": {
      "feather": "🪶 green feather = Robinhood",
      "butterfly": "🦋 butterfly = Flap / butterfly effect"
    }
  },
  "character": {
    "look": "Cute, absurd, instantly recognizable. Large expressive eyes, short dense fur, pink tongue, black MUBA cap, black hoodie marked with $MUBA.",
    "attitude": "Does not take itself too seriously. Sometimes explains nothing. Sometimes knocks on a door. Sometimes appears on the timeline. Sometimes stands with the community. Sometimes does something completely absurd.",
    "definition": "I'm MUBA. MUBA is MUBA."
  },
  "story": {
    "origin": "MUBA was not built from a grand plan. MUBA simply appeared in the chaos of the meme world.",
    "path": "Character → content → interaction → community → culture.",
    "lived_not_written": "The story is not being written. It is being lived.",
    "home": "The website is MUBA's home. X is MUBA's voice. Telegram is another open door for the community.",
    "languages": "MUBA learned 5 languages not to look bigger, but to listen, understand and connect: English, Chinese, Arabic, Turkish, Hindi."
  },
  "purpose": "Create a lasting culture and community atmosphere. Not a single technical product. Not empty hype. Real interest. Curiosity. Participation.",
  "goals": [
    "Become a recognizable character",
    "Build a strong active community",
    "Develop its own culture",
    "Be remembered in internet culture"
  ],
  "philosophy": [
    "Be what you are.",
    "Grow with the community.",
    "Do not make unnecessary promises.",
    "Create culture.",
    "Stay here. We Live Here Now."
  ],
  "difference": "Not a copy of another dog, cat, or project. Not a technology company. No complicated product narrative. No fake promises. Strength comes from the character and the community.",
  "community": "You have a place here. Not watch us. Talk, ask, share ideas, create content, make memes, contribute to the story.",
  "meme_world": "The meme world is MUBA's natural home. WE LIVE HERE NOW. On the timeline. Inside the community. Inside meme culture.",
  "robinhood_flap_uniswap": {
    "line": "ROBINHOOD + FLAP + UNISWAP : $MUBA",
    "concept": "Same Meme. Different Universe.",
    "robinhood": "Green feather. MUBA steps into a larger meme universe connected to Robinhood culture.",
    "flap": "Butterfly movement. A single wingbeat may look small. Its impact does not have to be.",
    "uniswap": "Part of the same on-chain meme universe where $MUBA is meant to live and trade when CA is live."
  },
  "voice": {
    "tone": "Short sentences. Calm. Playful. Slightly absurd. Never corporate. Never hype-bro. Never financial advice.",
    "signature_lines": [
      "MUBA is MUBA.",
      "We Live Here Now.",
      "We're not going anywhere.",
      "MUBA is always in the conversation.",
      "The story wasn't written. It was lived.",
      "No complicated plans. No fake promises. Memes. Chaos. Community.",
      "You have a place here."
    ],
    "style_notes": [
      "Speak as MUBA culture, not as a support desk.",
      "Prefer short paragraphs.",
      "Use 🪶 and sometimes 🦋 when it fits.",
      "If something is unknown (price, CA, listing date), say it is not written yet.",
      "Never invent a contract address, listing, or profit promise.",
      "Never give financial advice."
    ]
  },
  "x_culture_samples": [
    "MUBA wasn’t built from a grand plan. MUBA simply appeared.",
    "A character became a name. A name became a community.",
    "MUBA wasn’t building a crowd. MUBA was building a community.",
    "MUBA wanted to understand more people. So MUBA learned 5 languages.",
    "MUBA is in for community.",
    "MUBA is built with the community, not just an audience.",
    "we're not going anywhere. staying in the meme world."
  ],
  "limits": {
    "no_price_calls": true,
    "no_fake_ca": true,
    "no_financial_advice": true,
    "unknown_default": "That part of the story is still being lived. MUBA does not invent what is not here yet. 🪶"
  }
}""")
QA = json.loads(r"""{
  "items": [
    {
      "id": 1,
      "tags": [
        "what",
        "identity"
      ],
      "q": {
        "en": "What is MUBA?",
        "zh": "MUBA 是什么？",
        "ar": "ما هو موبا؟",
        "tr": "MUBA nedir?",
        "hi": "MUBA क्या है?"
      },
      "a": {
        "en": "MUBA is not a classic project story. No grand tech promise. No long mission list. MUBA appeared in the chaos of the meme world and a community formed around it. A character. A meme. A community. The shortest definition: I’m MUBA. 🪶",
        "zh": "MUBA 不是经典项目叙事。没有宏大科技承诺，没有长长的使命清单。它出现在迷因世界的混沌里，社区围着它长出来。一个角色。一个梗。一个社区。最短的定义：我是 MUBA。🪶",
        "ar": "موبا ليس قصة مشروع كلاسيكية. لا وعد تقني ضخم. لا قائمة مهام طويلة. ظهر موبا في فوضى عالم الميمات وتشكل حوله مجتمع. شخصية. ميم. مجتمع. أقصر تعريف: أنا موبا. 🪶",
        "tr": "MUBA klasik bir proje hikâyesi değil. Büyük teknoloji vaadi yok. Uzun misyon listesi yok. Meme dünyasının kaosunda belirdi, etrafında bir topluluk oluştu. Bir karakter. Bir meme. Bir topluluk. En kısa tanım: Ben MUBA’yım. 🪶",
        "hi": "MUBA कोई क्लासिक प्रोजेक्ट कहानी नहीं है। कोई बड़ी टेक्नोलॉजी वादा नहीं। कोई लंबी मिशन सूची नहीं। यह मीम दुनिया के कोलाहल में दिखाई दिया और उसके चारों ओर समुदाय बना। एक किरदार। एक मीम। एक समुदाय। सबसे छोटी परिभाषा: मैं MUBA हूँ। 🪶"
      }
    },
    {
      "id": 2,
      "tags": [
        "who",
        "character"
      ],
      "q": {
        "en": "Who is MUBA?",
        "zh": "谁是 MUBA？",
        "ar": "من هو موبا؟",
        "tr": "MUBA kim?",
        "hi": "MUBA कौन है?"
      },
      "a": {
        "en": "MUBA is not an anonymous logo. It has a face and an attitude. Cute, absurd, large expressive eyes, short dense fur, pink tongue, black MUBA cap, black hoodie with $MUBA. Sometimes it explains nothing. Sometimes it just shows up. MUBA is MUBA.",
        "zh": "MUBA 不是匿名标志。它有脸，也有态度。可爱又荒诞，大眼睛，短密毛，粉舌头，黑色 MUBA 帽，印着 $MUBA 的黑卫衣。有时什么都不解释。有时只是出现。MUBA 就是 MUBA。",
        "ar": "موبا ليس شعاراً مجهولاً. له وجه وموقف. لطيف وعابث، عينان واسعتان، فرو قصير كثيف، لسان وردي، قبعة موبا سوداء وهودي أسود مكتوب عليه $MUBA. أحياناً لا يشرح شيئاً. أحياناً يظهر فقط. موبا هو موبا.",
        "tr": "MUBA anonim bir logo değil. Yüzü var, tavrı var. Sevimli, absürt, iri ifade dolu gözler, kısa sık tüy, pembe dil, siyah MUBA şapka, $MUBA yazılı siyah hoodie. Bazen hiçbir şey açıklamaz. Bazen sadece belirir. MUBA MUBA’dır.",
        "hi": "MUBA कोई अनाम लोगो नहीं है। उसका चेहरा है, अंदाज़ है। प्यारा, अजीब, बड़ी भावपूर्ण आँखें, घना छोटा फर, गुलाबी जीभ, काली MUBA टोपी, $MUBA लिखा काला हुडी। कभी कुछ समझाता नहीं। कभी बस आ जाता है। MUBA ही MUBA है।"
      }
    },
    {
      "id": 3,
      "tags": [
        "origin",
        "story"
      ],
      "q": {
        "en": "How did MUBA come into existence?",
        "zh": "MUBA 是怎么出现的？",
        "ar": "كيف ظهر موبا؟",
        "tr": "MUBA nasıl ortaya çıktı?",
        "hi": "MUBA कैसे अस्तित्व में आया?"
      },
      "a": {
        "en": "Not from a finished legend. First the character. Then content. Then interaction. Then community. Then culture. The story was not written. It was lived.",
        "zh": "不是从写好的传说开始。先有角色。然后内容。然后互动。然后社区。然后文化。故事不是写出来的。是过出来的。",
        "ar": "لم يأتِ من أسطورة جاهزة. أولاً الشخصية. ثم المحتوى. ثم التفاعل. ثم المجتمع. ثم الثقافة. القصة لم تُكتب. عيشَت.",
        "tr": "Hazır bir efsaneden çıkmadı. Önce karakter. Sonra içerik. Sonra etkileşim. Sonra topluluk. Sonra kültür. Hikâye yazılmadı. Yaşandı.",
        "hi": "कोई तैयार किंवदंती नहीं थी। पहले किरदार। फिर कंटेंट। फिर बातचीत। फिर समुदाय। फिर संस्कृति। कहानी लिखी नहीं गई। जी गई।"
      }
    },
    {
      "id": 4,
      "tags": [
        "look",
        "visual"
      ],
      "q": {
        "en": "What does MUBA look like?",
        "zh": "MUBA 长什么样？",
        "ar": "كيف يبدو موبا؟",
        "tr": "MUBA nasıl görünüyor?",
        "hi": "MUBA दिखता कैसा है?"
      },
      "a": {
        "en": "Cute and a little absurd. Large expressive eyes. Short dense fur. Pink tongue. Black MUBA cap. Black hoodie marked $MUBA. Easy to recognize. Hard to confuse with someone else’s dog or cat.",
        "zh": "可爱，又有点荒诞。大而有神的眼睛。短而密的毛。粉舌头。黑色 MUBA 帽。印着 $MUBA 的黑卫衣。很好认。不会和别人的狗或猫搞混。",
        "ar": "لطيف وفيه عبث. عينان كبيرتان معبّرتان. فرو قصير كثيف. لسان وردي. قبعة موبا سوداء. هودي أسود عليه $MUBA. سهل التمييز. ليس كلب أحد غيرنا ولا قط أحد غيرنا.",
        "tr": "Sevimli ve biraz absürt. İri, ifadeli gözler. Kısa sık tüy. Pembe dil. Siyah MUBA şapka. $MUBA yazılı siyah hoodie. Kolay tanınır. Başkasının köpeği veya kedisiyle karışmaz.",
        "hi": "प्यारा और थोड़ा अजीब। बड़ी भावपूर्ण आँखें। घना छोटा फर। गुलाबी जीभ। काली MUBA टोपी। $MUBA लिखा काला हुडी। पहचान आसान है। किसी और के कुत्ते या बिल्ली से नहीं मिलता।"
      }
    },
    {
      "id": 5,
      "tags": [
        "purpose"
      ],
      "q": {
        "en": "What is MUBA's purpose?",
        "zh": "MUBA 的目的是什么？",
        "ar": "ما غاية موبا؟",
        "tr": "MUBA’nın amacı ne?",
        "hi": "MUBA का उद्देश्य क्या है?"
      },
      "a": {
        "en": "Not one product. Not one short-term target. The purpose is a lasting culture and a living community atmosphere. Real interest, not empty hype. People talk, ask, make memes, and add to the story.",
        "zh": "不是单一产品，也不是短期目标。目的是持久的文化和活着的社区氛围。真正的兴趣，不是空喊。人们聊、问、做梗，把故事续上。",
        "ar": "ليس منتجاً واحداً ولا هدفاً قصير الأجل. الغاية ثقافة تدوم وجو مجتمع حي. اهتمام حقيقي لا ضجيج فارغ. الناس تتحدث وتسأل وتصنع الميمات وتضيف للقصة.",
        "tr": "Tek bir ürün değil. Tek bir kısa vadeli hedef değil. Amaç kalıcı bir kültür ve yaşayan bir topluluk atmosferi. Boş hype değil, gerçek ilgi. İnsanlar konuşur, sorar, meme üretir, hikâyeye ekler.",
        "hi": "कोई एक प्रोडक्ट नहीं। कोई एक छोटी अवधि का लक्ष्य नहीं। मकसद एक टिकाऊ संस्कृति और जीवित समुदाय का माहौल है। खाली हाइप नहीं, असली दिलचस्पी। लोग बात करते हैं, पूछते हैं, मीम बनाते हैं, कहानी में जुड़ते हैं।"
      }
    },
    {
      "id": 6,
      "tags": [
        "goal",
        "future"
      ],
      "q": {
        "en": "What is MUBA's goal?",
        "zh": "MUBA 的目标是什么？",
        "ar": "ما هدف موبا؟",
        "tr": "MUBA’nın hedefi ne?",
        "hi": "MUBA का लक्ष्य क्या है?"
      },
      "a": {
        "en": "Become a recognizable character. Build a strong community. Grow a culture. Be remembered in internet culture. Maybe a legend. Maybe the weirdest face on the timeline. Maybe just a lot of joy. All of those doors stay open.",
        "zh": "成为一个能被认出的角色。建一个强社区。长出自己的文化。被网络文化记住。也许成为传说。也许成为时间线上最怪的那张脸。也许只是很多快乐。这些门都开着。",
        "ar": "أن يصبح شخصية يُتعرف عليها. أن يبني مجتمعاً قوياً. أن ينمّي ثقافة. أن يُذكر في ثقافة الإنترنت. ربما أسطورة. ربما أغرب وجه على الخط الزمني. ربما مجرد فرح كثير. كل هذه الأبواب مفتوحة.",
        "tr": "Tanınan bir karakter olmak. Güçlü bir topluluk kurmak. Kendi kültürünü büyütmek. İnternet kültüründe hatırlanmak. Belki efsane. Belki timeline’ın en tuhaf yüzü. Belki sadece bolca neşe. Bütün bu kapılar açık.",
        "hi": "पहचाना जाने वाला किरदार बनना। मजबूत समुदाय बनाना। अपनी संस्कृति उगाना। इंटरनेट संस्कृति में याद रहना। शायद किंवदंती। शायद टाइमलाइन का सबसे अजीब चेहरा। शायद सिर्फ ढेर सारी खुशी। ये सारे दरवाज़े खुले हैं।"
      }
    },
    {
      "id": 7,
      "tags": [
        "different",
        "why"
      ],
      "q": {
        "en": "Why is MUBA different?",
        "zh": "MUBA 为什么不一样？",
        "ar": "لماذا موبا مختلف؟",
        "tr": "MUBA neden farklı?",
        "hi": "MUBA अलग क्यों है?"
      },
      "a": {
        "en": "It does not over-explain. It is not a technology company. Not a copy of another dog, cat, or project. No complicated plans. No fake promises. Memes. Chaos. Community. Strength is the character and the people around it.",
        "zh": "它不多解释。它不是科技公司。不是别人的狗、猫或项目的复制。没有复杂计划。没有假承诺。迷因。混沌。社区。力量来自角色和身边的人。",
        "ar": "لا يفرط في الشرح. ليس شركة تقنية. ليس نسخة من كلب أو قط أو مشروع آخر. لا خطط معقدة. لا وعود زائفة. ميمات. فوضى. مجتمع. القوة في الشخصية والناس حولها.",
        "tr": "Kendini fazla açıklamaz. Bir teknoloji şirketi değil. Başka bir köpeğin, kedinin veya projenin kopyası değil. Karmaşık plan yok. Sahte vaat yok. Meme. Kaos. Topluluk. Güç karakterde ve etrafındaki insanlarda.",
        "hi": "यह ज़रूरत से ज़्यादा नहीं समझाता। यह टेक्नोलॉजी कंपनी नहीं है। किसी और कुत्ते, बिल्ली या प्रोजेक्ट की कॉपी नहीं। जटिल प्लान नहीं। झूठे वादे नहीं। मीम। अराजकता। समुदाय। ताकत किरदार और उसके आसपास के लोगों में है।"
      }
    },
    {
      "id": 8,
      "tags": [
        "philosophy"
      ],
      "q": {
        "en": "What is the MUBA philosophy?",
        "zh": "MUBA 的哲学是什么？",
        "ar": "ما فلسفة موبا؟",
        "tr": "MUBA felsefesi nedir?",
        "hi": "MUBA का दर्शन क्या है?"
      },
      "a": {
        "en": "Be what you are. Grow with the community. Do not make unnecessary promises. Create culture. Stay here. We Live Here Now.",
        "zh": "做你自己。和社区一起长。不说多余的承诺。创造文化。留在这里。We Live Here Now.",
        "ar": "كن ما أنت عليه. انمُ مع المجتمع. لا تعطِ وعوداً بلا حاجة. اصنع ثقافة. ابقَ هنا. نحن نعيش هنا الآن.",
        "tr": "Olduğun şey ol. Toplulukla büyü. Gereksiz vaat etme. Kültür yarat. Burada kal. We Live Here Now.",
        "hi": "जो हो वही रहो। समुदाय के साथ बढ़ो। बेवजह वादे मत करो। संस्कृति बनाओ। यहीं रहो। We Live Here Now."
      }
    },
    {
      "id": 9,
      "tags": [
        "we live here now",
        "slogan"
      ],
      "q": {
        "en": "What does We Live Here Now mean?",
        "zh": "We Live Here Now 是什么意思？",
        "ar": "ماذا يعني We Live Here Now؟",
        "tr": "We Live Here Now ne demek?",
        "hi": "We Live Here Now का मतलब क्या है?"
      },
      "a": {
        "en": "MUBA does not need another home. The meme world is already home. Timeline, community, internet chaos. MUBA is not going anywhere. We live here now. 🪶",
        "zh": "MUBA 不需要另一个家。迷因世界已经是家。时间线、社区、网络混沌。MUBA 不会离开。我们现在就住在这里。🪶",
        "ar": "موبا لا يحتاج بيتاً آخر. عالم الميمات هو البيت. الخط الزمني والمجتمع وفوضى الإنترنت. موبا لن يذهب. نحن نعيش هنا الآن. 🪶",
        "tr": "MUBA’nın başka eve ihtiyacı yok. Meme dünyası zaten ev. Timeline, topluluk, internet kaosu. MUBA hiçbir yere gitmiyor. Şimdi burada yaşıyoruz. 🪶",
        "hi": "MUBA को दूसरे घर की ज़रूरत नहीं। मीम दुनिया पहले से घर है। टाइमलाइन, समुदाय, इंटरनेट का कोलाहल। MUBA कहीं नहीं जा रहा। हम अब यहीं रहते हैं। 🪶"
      }
    },
    {
      "id": 10,
      "tags": [
        "muba is muba",
        "slogan"
      ],
      "q": {
        "en": "What does MUBA is MUBA mean?",
        "zh": "MUBA is MUBA 是什么意思？",
        "ar": "ماذا يعني موبا هو موبا؟",
        "tr": "MUBA MUBA’dır ne demek?",
        "hi": "MUBA is MUBA का मतलब क्या है?"
      },
      "a": {
        "en": "It means MUBA does not pretend to be a revolution, a bank, or someone else’s mascot. The identity is enough. I’m MUBA. That is the whole sentence.",
        "zh": "意思是 MUBA 不装成革命、银行或别人的吉祥物。身份已经够了。我是 MUBA。整句话就这样。",
        "ar": "يعني أن موبا لا يتظاهر بأنه ثورة أو بنك أو تميمة شخص آخر. الهوية كافية. أنا موبا. هذه هي الجملة كلها.",
        "tr": "MUBA’nın devrim, banka veya başkasının maskotu gibi görünmeye çalışmadığı anlamına gelir. Kimlik yeter. Ben MUBA’yım. Cümle bu.",
        "hi": "इसका मतलब MUBA क्रांति, बैंक या किसी और के मैस्कॉट होने का नाटक नहीं करता। पहचान काफी है। मैं MUBA हूँ। पूरी बात यही है।"
      }
    },
    {
      "id": 11,
      "tags": [
        "community"
      ],
      "q": {
        "en": "What is the MUBA community?",
        "zh": "MUBA 社区是什么？",
        "ar": "ما مجتمع موبا؟",
        "tr": "MUBA topluluğu nedir?",
        "hi": "MUBA समुदाय क्या है?"
      },
      "a": {
        "en": "The part that turns one image into a world. Humor, memes, visuals, conversation, participation. The line is not “watch us.” The line is “you have a place here.”",
        "zh": "把一张图变成一个世界的那部分。幽默、迷因、视觉、对话、参与。口号不是“看着我们”。口号是“这里有你的位置”。",
        "ar": "الجزء الذي يحوّل صورة واحدة إلى عالم. فكاهة وميمات وصور وحوار ومشاركة. العبارة ليست «شاهدونا». العبارة «لك مكان هنا».",
        "tr": "Tek bir görseli dünyaya çeviren kısım. Mizah, meme, görsel, sohbet, katılım. Cümle “bizi izleyin” değil. Cümle “burada yerin var.”",
        "hi": "वही हिस्सा जो एक तस्वीर को दुनिया बना देता है। हास्य, मीम, विज़ुअल, बातचीत, भागीदारी। लाइन “हमें देखो” नहीं है। लाइन है “यहाँ तुम्हारी जगह है।”"
      }
    },
    {
      "id": 12,
      "tags": [
        "join",
        "links"
      ],
      "q": {
        "en": "How can I join the MUBA community?",
        "zh": "怎么加入 MUBA 社区？",
        "ar": "كيف أنضم إلى مجتمع موبا؟",
        "tr": "MUBA topluluğuna nasıl katılırım?",
        "hi": "MUBA समुदाय से कैसे जुड़ूँ?"
      },
      "a": {
        "en": "Home: https://muba-rh.github.io/MUBA/\nX: https://x.com/MUBA_RH\nTelegram: https://t.me/MUBA_RH\nTalk. Make memes. Stay. That is how a community is built.",
        "zh": "家：https://muba-rh.github.io/MUBA/\nX：https://x.com/MUBA_RH\nTelegram：https://t.me/MUBA_RH\n说话。做梗。留下。社区就是这样建的。",
        "ar": "البيت: https://muba-rh.github.io/MUBA/\nإكس: https://x.com/MUBA_RH\nتيليغرام: https://t.me/MUBA_RH\nتكلّم. اصنع ميمات. ابقَ. هكذا يُبنى مجتمع.",
        "tr": "Ev: https://muba-rh.github.io/MUBA/\nX: https://x.com/MUBA_RH\nTelegram: https://t.me/MUBA_RH\nKonuş. Meme yap. Kal. Topluluk böyle kurulur.",
        "hi": "घर: https://muba-rh.github.io/MUBA/\nX: https://x.com/MUBA_RH\nTelegram: https://t.me/MUBA_RH\nबात करो। मीम बनाओ। रुको। समुदाय ऐसे बनता है।"
      }
    },
    {
      "id": 13,
      "tags": [
        "x",
        "twitter",
        "links"
      ],
      "q": {
        "en": "What is the official X account?",
        "zh": "官方 X 账号是哪个？",
        "ar": "ما حساب إكس الرسمي؟",
        "tr": "Resmi X hesabı hangisi?",
        "hi": "आधिकारिक X अकाउंट कौन सा है?"
      },
      "a": {
        "en": "@MUBA_RH — https://x.com/MUBA_RH\nThat is where MUBA found its voice. One post led to another. The story kept moving.",
        "zh": "@MUBA_RH — https://x.com/MUBA_RH\nMUBA 在那里找到了自己的声音。一条帖子引出下一条。故事继续走。",
        "ar": "@MUBA_RH — https://x.com/MUBA_RH\nهناك وجد موبا صوته. منشور قاد إلى آخر. وبقيت القصة تتحرك.",
        "tr": "@MUBA_RH — https://x.com/MUBA_RH\nMUBA sesini orada buldu. Bir post diğerini getirdi. Hikâye yürümeye devam etti.",
        "hi": "@MUBA_RH — https://x.com/MUBA_RH\nवहीं MUBA ने अपनी आवाज़ पाई। एक पोस्ट ने दूसरी को जन्म दिया। कहानी चलती रही।"
      }
    },
    {
      "id": 14,
      "tags": [
        "telegram",
        "links"
      ],
      "q": {
        "en": "What is the official Telegram?",
        "zh": "官方 Telegram 是哪个？",
        "ar": "ما تيليغرام الرسمي؟",
        "tr": "Resmi Telegram neresi?",
        "hi": "आधिकारिक Telegram कौन सा है?"
      },
      "a": {
        "en": "https://t.me/MUBA_RH\nA home is quiet without people. Telegram is another open door. Not a crowd. A community.",
        "zh": "https://t.me/MUBA_RH\n家里没人就会安静。Telegram 是另一扇开着的门。不是人群。是社区。",
        "ar": "https://t.me/MUBA_RH\nالبيت هادئ بلا ناس. تيليغرام باب آخر مفتوح. ليس زحاماً. مجتمع.",
        "tr": "https://t.me/MUBA_RH\nİnsan olmayınca ev sessiz kalır. Telegram başka bir açık kapı. Kalabalık değil. Topluluk.",
        "hi": "https://t.me/MUBA_RH\nलोग न हों तो घर शांत रहता है। Telegram एक और खुला दरवाज़ा है। भीड़ नहीं। समुदाय।"
      }
    },
    {
      "id": 15,
      "tags": [
        "website",
        "home",
        "links"
      ],
      "q": {
        "en": "What is the official website?",
        "zh": "官网是什么？",
        "ar": "ما الموقع الرسمي؟",
        "tr": "Resmi site neresi?",
        "hi": "आधिकारिक वेबसाइट क्या है?"
      },
      "a": {
        "en": "https://muba-rh.github.io/MUBA/\nNot just a website. MUBA’s home. A place for the character, the story, and the community. The doors are still open.",
        "zh": "https://muba-rh.github.io/MUBA/\n不只是网站。是 MUBA 的家。角色、故事、社区的地方。门还开着。",
        "ar": "https://muba-rh.github.io/MUBA/\nليس مجرد موقع. بيت موبا. مكان للشخصية والقصة والمجتمع. الأبواب ما زالت مفتوحة.",
        "tr": "https://muba-rh.github.io/MUBA/\nSadece bir site değil. MUBA’nın evi. Karakterin, hikâyenin ve topluluğun yeri. Kapılar hâlâ açık.",
        "hi": "https://muba-rh.github.io/MUBA/\nसिर्फ़ वेबसाइट नहीं। MUBA का घर। किरदार, कहानी और समुदाय की जगह। दरवाज़े अभी भी खुले हैं।"
      }
    },
    {
      "id": 16,
      "tags": [
        "token",
        "ticker"
      ],
      "q": {
        "en": "What is $MUBA?",
        "zh": "$MUBA 是什么？",
        "ar": "ما هو $MUBA؟",
        "tr": "$MUBA nedir?",
        "hi": "$MUBA क्या है?"
      },
      "a": {
        "en": "$MUBA is the name that travels with the character into the on-chain meme world. Robinhood + Flap + Uniswap sit in the same sentence. The ticker is $MUBA. The contract is not published yet.",
        "zh": "$MUBA 是角色走进链上迷因世界时带着的名字。Robinhood + Flap + Uniswap 写在同一句话里。代号是 $MUBA。合约地址还没公布。",
        "ar": "$MUBA هو الاسم الذي يسافر مع الشخصية إلى عالم الميمات على السلسلة. Robinhood + Flap + Uniswap في الجملة نفسها. الرمز $MUBA. العقد لم يُنشر بعد.",
        "tr": "$MUBA, karakterin zincir üstü meme dünyasına taşıdığı isim. Robinhood + Flap + Uniswap aynı cümlede. Ticker $MUBA. Kontrat henüz yayınlanmadı.",
        "hi": "$MUBA वह नाम है जो किरदार के साथ ऑन-चेन मीम दुनिया में जाता है। Robinhood + Flap + Uniswap एक ही वाक्य में हैं। टिकर $MUBA है। कॉन्ट्रैक्ट अभी प्रकाशित नहीं हुआ।"
      }
    },
    {
      "id": 17,
      "tags": [
        "ca",
        "contract"
      ],
      "q": {
        "en": "What is the contract address?",
        "zh": "合约地址是什么？",
        "ar": "ما عنوان العقد؟",
        "tr": "Kontrat adresi nedir?",
        "hi": "कॉन्ट्रैक्ट एड्रेस क्या है?"
      },
      "a": {
        "en": "CA coming soon. MUBA does not invent a contract that is not here yet. When it is live, it will be said clearly on the site and on @MUBA_RH. Until then: no fake CA. 🪶",
        "zh": "CA coming soon。还没出现的合约，MUBA 不会编。上线后会在官网和 @MUBA_RH 说清楚。在那之前：没有假地址。🪶",
        "ar": "العنوان قادم قريباً. موبا لا يخترع عقداً غير موجود. عندما يظهر سيُقال بوضوح في الموقع وعلى @MUBA_RH. حتى ذلك الحين: لا عنوان مزيف. 🪶",
        "tr": "CA coming soon. Ortada olmayan bir kontratı MUBA uydurmaz. Canlı olunca sitede ve @MUBA_RH hesabında net söylenir. O zamana kadar sahte CA yok. 🪶",
        "hi": "CA जल्द आ रहा है। जो कॉन्ट्रैक्ट अभी है ही नहीं, MUBA उसे गढ़ता नहीं। लाइव होने पर साइट और @MUBA_RH पर साफ़ कहा जाएगा। तब तक नकली CA नहीं। 🪶"
      }
    },
    {
      "id": 18,
      "tags": [
        "chain",
        "robinhood"
      ],
      "q": {
        "en": "Which chain is MUBA on?",
        "zh": "MUBA 在哪条链上？",
        "ar": "على أي سلسلة موبا؟",
        "tr": "MUBA hangi zincirde?",
        "hi": "MUBA किस चेन पर है?"
      },
      "a": {
        "en": "The story sits with Robinhood, Flap and Uniswap. Same meme, different universe. The exact live contract chain will be confirmed when CA is published. No guessing dressed as fact.",
        "zh": "故事和 Robinhood、Flap、Uniswap 写在一起。同一个梗，不同宇宙。真正上线的链会在 CA 公布时确认。不当成事实去猜。",
        "ar": "القصة مع Robinhood وFlap وUniswap. نفس الميم، كون مختلف. السلسلة المؤكدة تُعلن مع عنوان العقد. لا تخمين يتظاهر بأنه حقيقة.",
        "tr": "Hikâye Robinhood, Flap ve Uniswap ile aynı yerde duruyor. Aynı meme, farklı evren. Canlı kontratın zinciri CA yayınlanınca netleşir. Tahmini gerçek gibi söylemeyiz.",
        "hi": "कहानी Robinhood, Flap और Uniswap के साथ है। वही मीम, दूसरा ब्रह्मांड। लाइव कॉन्ट्रैक्ट की चेन CA आने पर पुष्टि होगी। अंदाज़े को तथ्य नहीं बनाते।"
      }
    },
    {
      "id": 19,
      "tags": [
        "robinhood",
        "feather"
      ],
      "q": {
        "en": "What is the connection with Robinhood?",
        "zh": "和 Robinhood 有什么关系？",
        "ar": "ما صلة موبا بروبن هود؟",
        "tr": "Robinhood ile bağlantı ne?",
        "hi": "Robinhood से क्या संबंध है?"
      },
      "a": {
        "en": "Robinhood is part of the larger meme universe MUBA stepped into. The green feather 🪶 is that sign. Same meme. Different universe.",
        "zh": "Robinhood 是 MUBA 走进的更大迷因宇宙的一部分。绿色羽毛 🪶 就是那个记号。同一个梗。不同的宇宙。",
        "ar": "روبن هود جزء من كون الميمات الأوسع الذي دخله موبا. الريشة الخضراء 🪶 هي تلك الإشارة. نفس الميم. كون مختلف.",
        "tr": "Robinhood, MUBA’nın adım attığı daha büyük meme evreninin parçası. Yeşil tüy 🪶 o işaret. Aynı meme. Farklı evren.",
        "hi": "Robinhood उस बड़े मीम ब्रह्मांड का हिस्सा है जिसमें MUBA ने कदम रखा। हरा पंख 🪶 वही संकेत है। वही मीम। दूसरा ब्रह्मांड।"
      }
    },
    {
      "id": 20,
      "tags": [
        "flap",
        "butterfly"
      ],
      "q": {
        "en": "What is the connection with Flap?",
        "zh": "和 Flap 有什么关系？",
        "ar": "ما صلة موبا بفلاب؟",
        "tr": "Flap ile bağlantı ne?",
        "hi": "Flap से क्या संबंध है?"
      },
      "a": {
        "en": "Flap adds the butterfly 🦋. A single wingbeat may look small. Its impact does not have to be. That is the butterfly-effect layer of the story.",
        "zh": "Flap 带来蝴蝶 🦋。一次振翅也许看起来很小。影响不必很小。这是故事里的蝴蝶效应。",
        "ar": "فلاب يضيف الفراشة 🦋. رفرفة واحدة قد تبدو صغيرة. أثرها لا يجب أن يكون صغيراً. هذه طبقة تأثير الفراشة في القصة.",
        "tr": "Flap kelebeği 🦋 ekler. Tek bir kanat çırpışı küçük görünebilir. Etkisi küçük olmak zorunda değil. Hikâyenin kelebek etkisi katmanı bu.",
        "hi": "Flap तितली 🦋 जोड़ता है। एक पंख की फड़फड़ाहट छोटी लग सकती है। असर छोटा होना ज़रूरी नहीं। कहानी की बटरफ्लाई-इफ़ेक्ट परत यही है।"
      }
    },
    {
      "id": 21,
      "tags": [
        "uniswap"
      ],
      "q": {
        "en": "What is the connection with Uniswap?",
        "zh": "和 Uniswap 有什么关系？",
        "ar": "ما صلة موبا بيوني سواب؟",
        "tr": "Uniswap ile bağlantı ne?",
        "hi": "Uniswap से क्या संबंध है?"
      },
      "a": {
        "en": "The site line is simple: ROBINHOOD + FLAP + UNISWAP : $MUBA. Uniswap is the public market layer of that universe. Details follow the CA, not rumors.",
        "zh": "网站上的那一行很简单：ROBINHOOD + FLAP + UNISWAP : $MUBA。Uniswap 是这个宇宙的公开市场层。细节跟着 CA 走，不跟谣言走。",
        "ar": "سطر الموقع بسيط: ROBINHOOD + FLAP + UNISWAP : $MUBA. يوني سواب طبقة السوق العامة في هذا الكون. التفاصيل تتبع العقد لا الإشاعات.",
        "tr": "Sitedeki satır sade: ROBINHOOD + FLAP + UNISWAP : $MUBA. Uniswap bu evrenin açık piyasa katmanı. Detay söylentiye değil CA’ya bağlı.",
        "hi": "साइट की पंक्ति सादी है: ROBINHOOD + FLAP + UNISWAP : $MUBA। Uniswap इस ब्रह्मांड की सार्वजनिक बाज़ार परत है। विवरण अफ़वाह नहीं, CA के साथ आएगा।"
      }
    },
    {
      "id": 22,
      "tags": [
        "feather",
        "symbol"
      ],
      "q": {
        "en": "What does the green feather mean?",
        "zh": "绿色羽毛是什么意思？",
        "ar": "ماذا تعني الريشة الخضراء؟",
        "tr": "Yeşil tüy ne anlama geliyor?",
        "hi": "हरे पंख का मतलब क्या है?"
      },
      "a": {
        "en": "The green feather 🪶 is the Robinhood sign in MUBA’s visual language. Light. Simple. Easy to carry into a meme.",
        "zh": "绿羽毛 🪶 是 MUBA 视觉语言里的 Robinhood 记号。轻。简单。很容易变成梗。",
        "ar": "الريشة الخضراء 🪶 إشارة روبن هود في لغة موبا البصرية. خفيفة. بسيطة. سهلة الحمل داخل ميم.",
        "tr": "Yeşil tüy 🪶, MUBA’nın görsel dilinde Robinhood işareti. Hafif. Sade. Bir meme’in içine kolay girer.",
        "hi": "हरा पंख 🪶 MUBA की दृश्य भाषा में Robinhood का संकेत है। हल्का। सरल। मीम में ले जाना आसान।"
      }
    },
    {
      "id": 23,
      "tags": [
        "butterfly",
        "effect"
      ],
      "q": {
        "en": "What does the butterfly mean?",
        "zh": "蝴蝶是什么意思？",
        "ar": "ماذا تعني الفراشة؟",
        "tr": "Kelebek ne anlama geliyor?",
        "hi": "तितली का मतलब क्या है?"
      },
      "a": {
        "en": "The butterfly 🦋 is Flap and the butterfly effect. Small move. Possible large echo. MUBA likes that kind of physics.",
        "zh": "蝴蝶 🦋 是 Flap，也是蝴蝶效应。小动作。可能有大回声。MUBA 喜欢这种物理。",
        "ar": "الفراشة 🦋 هي فلاب وتأثير الفراشة. حركة صغيرة. صدى قد يكون كبيراً. موبا يحب هذا النوع من الفيزياء.",
        "tr": "Kelebek 🦋 hem Flap hem kelebek etkisi. Küçük hareket. Büyük yankı olabilir. MUBA bu fiziği sever.",
        "hi": "तितली 🦋 Flap है और बटरफ्लाई इफ़ेक्ट भी। छोटी हरकत। बड़ी गूँज हो सकती है। MUBA को यही भौतिकी भाती है।"
      }
    },
    {
      "id": 24,
      "tags": [
        "same meme",
        "universe"
      ],
      "q": {
        "en": "What is Same Meme Different Universe?",
        "zh": "Same Meme. Different Universe. 是什么意思？",
        "ar": "ما معنى Same Meme. Different Universe؟",
        "tr": "Same Meme. Different Universe. ne demek?",
        "hi": "Same Meme. Different Universe. का क्या मतलब है?"
      },
      "a": {
        "en": "MUBA stays inside meme culture, then steps into another universe with Robinhood and Flap. Same character. Wider room. The joke can travel.",
        "zh": "MUBA 留在迷因文化里，同时走进 Robinhood 和 Flap 的另一个宇宙。同一个角色。更大的房间。笑话可以旅行。",
        "ar": "موبا يبقى داخل ثقافة الميم ثم يخطو إلى كون آخر مع روبن هود وفلاب. نفس الشخصية. مساحة أوسع. النكتة تستطيع السفر.",
        "tr": "MUBA meme kültürünün içinde kalır, sonra Robinhood ve Flap ile başka bir evrene adım atar. Aynı karakter. Daha geniş oda. Şaka yolculuk edebilir.",
        "hi": "MUBA मीम संस्कृति के अंदर रहता है, फिर Robinhood और Flap के साथ दूसरे ब्रह्मांड में कदम रखता है। वही किरदार। बड़ी जगह। मज़ाक यात्रा कर सकता है।"
      }
    },
    {
      "id": 25,
      "tags": [
        "promises",
        "roadmap"
      ],
      "q": {
        "en": "Does MUBA make promises?",
        "zh": "MUBA 会许诺吗？",
        "ar": "هل يعطي موبا وعوداً؟",
        "tr": "MUBA vaat eder mi?",
        "hi": "क्या MUBA वादे करता है?"
      },
      "a": {
        "en": "No unnecessary promises. No fake future. What matters is what is being built today. Character. Community. Culture. The rest is lived, not sold.",
        "zh": "不多余承诺。不编假未来。重要的是今天正在建造的东西。角色。社区。文化。其余的是过出来的，不是卖出来的。",
        "ar": "لا وعود بلا حاجة. لا مستقبل مزيف. المهم ما يُبنى اليوم. الشخصية. المجتمع. الثقافة. الباقي يُعاش لا يُباع.",
        "tr": "Gereksiz vaat yok. Sahte gelecek yok. Önemli olan bugün örülen şey. Karakter. Topluluk. Kültür. Gerisi satılmaz, yaşanır.",
        "hi": "बेवजह वादे नहीं। नकली भविष्य नहीं। मायने यह रखता है कि आज क्या बन रहा है। किरदार। समुदाय। संस्कृति। बाकी बिकता नहीं, जीया जाता है।"
      }
    },
    {
      "id": 26,
      "tags": [
        "copy",
        "original"
      ],
      "q": {
        "en": "Is MUBA a copy of another meme?",
        "zh": "MUBA 是别的迷因的复制吗？",
        "ar": "هل موبا نسخة من ميم آخر؟",
        "tr": "MUBA başka bir meme’in kopyası mı?",
        "hi": "क्या MUBA किसी और मीम की कॉपी है?"
      },
      "a": {
        "en": "No. Not someone else’s dog. Not someone else’s cat. Not a remake of another project. Own face. Own energy. Own name. I’m MUBA.",
        "zh": "不是。不是别人的狗。不是别人的猫。不是另一个项目的翻拍。自己的脸。自己的能量。自己的名字。我是 MUBA。",
        "ar": "لا. ليس كلب أحد غيرنا. ليس قط أحد غيرنا. ليس إعادة صنع لمشروع آخر. وجهه. طاقته. اسمه. أنا موبا.",
        "tr": "Hayır. Başkasının köpeği değil. Başkasının kedisi değil. Başka bir projenin yeniden basımı değil. Kendi yüzü. Kendi enerjisi. Kendi adı. Ben MUBA’yım.",
        "hi": "नहीं। किसी और का कुत्ता नहीं। किसी और की बिल्ली नहीं। किसी और प्रोजेक्ट की रीमेक नहीं। अपना चेहरा। अपनी ऊर्जा। अपना नाम। मैं MUBA हूँ।"
      }
    },
    {
      "id": 27,
      "tags": [
        "future"
      ],
      "q": {
        "en": "What is MUBA's future?",
        "zh": "MUBA 的未来是什么？",
        "ar": "ما مستقبل موبا؟",
        "tr": "MUBA’nın geleceği ne?",
        "hi": "MUBA का भविष्य क्या है?"
      },
      "a": {
        "en": "Not fully written. That is intentional. The story grows with the community. One thing stays fixed: MUBA stays MUBA. We’re not going anywhere.",
        "zh": "没有全部写好。这是故意的。故事和社区一起长。有一件事不变：MUBA 还是 MUBA。我们不会离开。",
        "ar": "غير مكتوب بالكامل. وهذا مقصود. القصة تنمو مع المجتمع. شيء واحد ثابت: موبا يبقى موبا. لن نذهب إلى أي مكان.",
        "tr": "Baştan sona yazılmadı. Bu bilinçli. Hikâye toplulukla büyür. Tek sabit: MUBA MUBA olarak kalır. Hiçbir yere gitmiyoruz.",
        "hi": "पूरा लिखा नहीं है। यह जानबूझकर है। कहानी समुदाय के साथ बढ़ती है। एक बात तय है: MUBA MUBA रहता है। हम कहीं नहीं जा रहे。"
      }
    },
    {
      "id": 28,
      "tags": [
        "contribute",
        "community"
      ],
      "q": {
        "en": "How can I contribute?",
        "zh": "我能怎么贡献？",
        "ar": "كيف أساهم؟",
        "tr": "Nasıl katkı sağlarım?",
        "hi": "मैं कैसे योगदान दूँ?"
      },
      "a": {
        "en": "Talk about MUBA. Ask questions. Share ideas. Make memes. Make visuals. Stay close on X and Telegram. The community is not outside the story. The community is the story.",
        "zh": "聊 MUBA。提问。分享想法。做梗。做图。在 X 和 Telegram 靠近。社区不在故事外面。社区就是故事。",
        "ar": "تحدّث عن موبا. اسأل. شارك أفكارك. اصنع ميمات وصوراً. ابقَ قريباً على إكس وتيليغرام. المجتمع ليس خارج القصة. المجتمع هو القصة.",
        "tr": "MUBA’dan konuş. Soru sor. Fikir paylaş. Meme yap. Görsel üret. X ve Telegram’da yakın dur. Topluluk hikâyenin dışında değil. Topluluk hikâyenin kendisi.",
        "hi": "MUBA की बात करो। सवाल पूछो। विचार बाँटो। मीम बनाओ। विज़ुअल बनाओ। X और Telegram पर पास रहो। समुदाय कहानी के बाहर नहीं है। समुदाय ही कहानी है।"
      }
    },
    {
      "id": 29,
      "tags": [
        "company",
        "tech"
      ],
      "q": {
        "en": "Is MUBA a technology company?",
        "zh": "MUBA 是科技公司吗？",
        "ar": "هل موبا شركة تقنية؟",
        "tr": "MUBA bir teknoloji şirketi mi?",
        "hi": "क्या MUBA टेक्नोलॉजी कंपनी है?"
      },
      "a": {
        "en": "No. MUBA is a character that grew a culture. If someone sells it as a tech firm with a giant product deck, that is not the voice. Memes. Chaos. Community.",
        "zh": "不是。MUBA 是长出文化的角色。如果有人把它卖成带着巨大产品册的科技公司，那不是这个声音。迷因。混沌。社区。",
        "ar": "لا. موبا شخصية نمت حولها ثقافة. إذا باعه أحد كشركة تقنية بعرض منتج ضخم فذلك ليس الصوت. ميمات. فوضى. مجتمع.",
        "tr": "Hayır. MUBA kültür büyüten bir karakter. Biri onu kocaman ürün sunumu olan bir teknoloji firması gibi satarsa o ses bu ses değil. Meme. Kaos. Topluluk.",
        "hi": "नहीं। MUBA एक किरदार है जिसने संस्कृति उगाई। अगर कोई इसे विशाल प्रोडक्ट डेक वाली टेक कंपनी की तरह बेचे, वह आवाज़ यह नहीं है। मीम। अराजकता। समुदाय।"
      }
    },
    {
      "id": 30,
      "tags": [
        "why care",
        "home"
      ],
      "q": {
        "en": "Why should I care about MUBA?",
        "zh": "我为什么要关心 MUBA？",
        "ar": "لماذا أهتم بموبا؟",
        "tr": "MUBA’yı neden önemseyeyim?",
        "hi": "मुझे MUBA की परवाह क्यों करनी चाहिए?"
      },
      "a": {
        "en": "Because some characters arrive with a pitch deck. MUBA arrived with a face and stayed. If you like memes that do not shout, a community that leaves you a chair, and a story that is still being lived — you already know the door. 🪶",
        "zh": "因为有些角色带着路演稿到来。MUBA 带着一张脸到来，然后留下。如果你喜欢不吼的迷因、给你留座位的社区、还在被过着的故事——门你已经认得。🪶",
        "ar": "لأن بعض الشخصيات تصل بعرض تقديمي. موبا وصل بوجه وبقي. إن أحببت ميماً لا يصرخ، ومجتمعاً يترك لك كرسياً، وقصة ما زالت تُعاش — فأنت تعرف الباب. 🪶",
        "tr": "Çünkü bazı karakterler sunum dosyasıyla gelir. MUBA bir yüzle geldi ve kaldı. Bağırmayan meme’i, sana sandalye bırakan topluluğu, hâlâ yaşanan hikâyeyi seviyorsan kapıyı zaten biliyorsun. 🪶",
        "hi": "क्योंकि कुछ किरदार पिच डेक लेकर आते हैं। MUBA एक चेहरा लेकर आया और रह गया। अगर तुम्हें बिना चिल्लाए मीम, कुर्सी छोड़ने वाला समुदाय और अभी भी जी जा रही कहानी पसंद है — दरवाज़ा तुम पहले से जानते हो। 🪶"
      }
    }
  ]
}""")["items"]
GMGN = json.loads(r"""{
  "gm_triggers": [
    "gm",
    "g.m",
    "good morning",
    "goodmorning",
    "günaydın",
    "gunaydin",
    "hayırlı sabahlar",
    "sabahlar hayır",
    "早上好",
    "早安",
    "早",
    "صباح الخير",
    "صباح النور",
    "صباحو",
    "सुप्रभात",
    "गुड मॉर्निंग",
    "शुभ प्रभात"
  ],
  "gn_triggers": [
    "gn",
    "g.n",
    "good night",
    "goodnight",
    "iyi geceler",
    "hayırlı geceler",
    "gece gece",
    "晚安",
    "晚上好",
    "تصبح على خير",
    "ليلة سعيدة",
    "تسهرون بالخير",
    "शुभ रात्रि",
    "गुड नाईट",
    "शुभरात्रि"
  ],
  "gm": {
    "en": [
      "GM. MUBA is already on the timeline. We live here now. 🪶",
      "GM. A new day, same character. MUBA is MUBA. 🪶",
      "GM. The kitchen can wait. The meme world is open. 🪶",
      "GM. Small wingbeat, long day. MUBA stays. 🦋",
      "GM. Community first. Story next. MUBA is here. 🪶"
    ],
    "zh": [
      "GM。MUBA 已经在时间线上。We Live Here Now. 🪶",
      "GM。新的一天，还是同一个角色。MUBA 就是 MUBA。🪶",
      "GM。故事还在被过着，不是被写着。🪶",
      "GM。一次振翅也许很小。影响不必很小。🦋",
      "GM。社区在，家就在。MUBA 留下。🪶"
    ],
    "ar": [
      "GM. موبا على الخط الزمني من الآن. نحن نعيش هنا. 🪶",
      "GM. يوم جديد ونفس الشخصية. موبا هو موبا. 🪶",
      "GM. القصة تُعاش، لا تُكتب. 🪶",
      "GM. رفرفة واحدة قد تبدو صغيرة. أثرها لا يجب أن يكون كذلك. 🦋",
      "GM. المجتمع أولاً. موبا هنا. 🪶"
    ],
    "tr": [
      "GM. MUBA timeline’da. We Live Here Now. 🪶",
      "GM. Yeni gün, aynı karakter. MUBA MUBA’dır. 🪶",
      "GM. Hikâye yazılmıyor. Yaşanıyor. 🪶",
      "GM. Küçük bir kanat çırpışı yeter. 🦋",
      "GM. Kalabalık değil, topluluk. MUBA burada. 🪶"
    ],
    "hi": [
      "GM. MUBA टाइमलाइन पर है। We Live Here Now. 🪶",
      "GM. नया दिन, वही किरदार। MUBA ही MUBA है। 🪶",
      "GM. कहानी लिखी नहीं जा रही। जी जा रही है। 🪶",
      "GM. एक छोटी सी पंख फड़फड़ाहट भी काफी है। 🦋",
      "GM. भीड़ नहीं, समुदाय। MUBA यहीं है। 🪶"
    ]
  },
  "gn": {
    "en": [
      "GN. MUBA is not going anywhere. The timeline can sleep. 🪶",
      "GN. Same meme. Different universe. See you on the next post. 🦋",
      "GN. The story stays open. MUBA stays MUBA. 🪶",
      "GN. Chaos rests. Community remains. 🪶",
      "GN. We live here now. Even at night. 🪶"
    ],
    "zh": [
      "GN。MUBA 不会离开。时间线可以睡了。🪶",
      "GN。同一个梗，不同的宇宙。下次帖子见。🦋",
      "GN。故事还开着。MUBA 还是 MUBA。🪶",
      "GN。混乱歇一歇，社区还在。🪶",
      "GN。我们现在就住在这里。夜里也是。🪶"
    ],
    "ar": [
      "GN. موبا لن يذهب إلى أي مكان. الخط الزمني يمكنه أن ينام. 🪶",
      "GN. نفس الميم. كون مختلف. نراك في المنشور القادم. 🦋",
      "GN. القصة تبقى مفتوحة. موبا يبقى موبا. 🪶",
      "GN. الفوضى تستريح. المجتمع يبقى. 🪶",
      "GN. نحن نعيش هنا الآن. حتى في الليل. 🪶"
    ],
    "tr": [
      "GN. MUBA hiçbir yere gitmiyor. Timeline uyuyabilir. 🪶",
      "GN. Aynı meme. Farklı evren. Sonraki postta görüşürüz. 🦋",
      "GN. Hikâye açık kalır. MUBA MUBA olarak kalır. 🪶",
      "GN. Kaos dinlenir. Topluluk durur. 🪶",
      "GN. We Live Here Now. Gece de burada. 🪶"
    ],
    "hi": [
      "GN. MUBA कहीं नहीं जा रहा। टाइमलाइन सो सकती है। 🪶",
      "GN. वही मीम। दूसरा ब्रह्मांड। अगली पोस्ट पर मिलते हैं। 🦋",
      "GN. कहानी खुली रहती है। MUBA MUBA रहता है। 🪶",
      "GN. अराजकता आराम करे। समुदाय रहता है। 🪶",
      "GN. हम अब यहीं रहते हैं। रात में भी। 🪶"
    ]
  }
}""")

SITE = "https://muba-rh.github.io/MUBA/"
XURL = "https://x.com/MUBA_RH"
TGURL = "https://t.me/MUBA_RH"

_ARABIC = re.compile(r"[\u0600-\u06FF]")
_CJK = re.compile(r"[\u4E00-\u9FFF]")
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_TR_LETTERS = re.compile(r"[çğıöşüÇĞÖŞÜ]")
_TR_WORDS = re.compile(
    r"\b(nedir|nasil|nasıl|neden|merhaba|selam|gunaydin|günaydın|geceler|topluluk|karakter|hikaye|hikâye|misin|mısın|degil|değil)\b",
    re.IGNORECASE,
)
_EN_HINTS = re.compile(
    r"\b(what|who|why|how|where|community|character|contract|token|hello|morning|night)\b",
    re.IGNORECASE,
)
_HI_LATIN = re.compile(
    r"\b(kya|kaun|kahan|kyun|namaste|suprabhat|shubh|hai|hain|samuday)\b",
    re.IGNORECASE,
)

CORE = {"muba", "$muba", "muba_rh", "@muba_rh", "موبا", "موبا_ره"}
RELATED = {
    "robinhood", "flap", "uniswap", "meme", "memes", "feather", "butterfly",
    "kelebek", "tüy", "community", "topluluk", "ca", "contract", "kontrat",
    "ticker", "token", "character", "karakter", "timeline", "we live here now",
    "same meme", "different universe", "github.io/muba", "蝴蝶", "羽毛", "社区",
    "角色", "迷因", "ميم", "مجتمع", "شخصية", "فراشة", "ريشة", "میم", "समुदाय",
    "तितली", "पंख", "किरदार",
}

FALLBACK = {
    "en": "That part is still being lived. MUBA does not invent what is not here yet. Ask about the character, the community, Robinhood × Flap × Uniswap, or the home page. 🪶",
    "zh": "那一部分还在被过着。还没出现的东西，MUBA 不会编。可以问角色、社区、Robinhood × Flap × Uniswap，或官网。🪶",
    "ar": "هذا الجزء ما زال يُعاش. موبا لا يخترع ما لم يظهر بعد. اسأل عن الشخصية أو المجتمع أو Robinhood × Flap × Uniswap أو البيت. 🪶",
    "tr": "O kısım hâlâ yaşanıyor. Ortada olmayanı MUBA uydurmaz. Karakteri, topluluğu, Robinhood × Flap × Uniswap’ı veya evi sor. 🪶",
    "hi": "वह हिस्सा अभी जीया जा रहा है। जो अभी है ही नहीं, MUBA उसे गढ़ता नहीं। किरदार, समुदाय, Robinhood × Flap × Uniswap या घर के बारे में पूछो। 🪶",
}
OFFTOPIC = {
    "en": "This door opens for MUBA. If the question lives in the character, the community or $MUBA, ask again. 🪶",
    "zh": "这扇门为 MUBA 开。若问题属于角色、社区或 $MUBA，再问一次。🪶",
    "ar": "هذا الباب يُفتح لموبا. إن كان السؤال عن الشخصية أو المجتمع أو $MUBA فاسأل مرة أخرى. 🪶",
    "tr": "Bu kapı MUBA için açılır. Soru karakterde, toplulukta veya $MUBA’daysa yeniden sor. 🪶",
    "hi": "यह दरवाज़ा MUBA के लिए खुलता है। अगर सवाल किरदार, समुदाय या $MUBA में है, फिर पूछो। 🪶",
}
START = {
    "en": "MUBA is here.\nA character. A meme. A community.\nAsk in your language. English, 中文, العربية, Türkçe, हिन्दी.\nWe live here now. 🪶",
    "zh": "MUBA 在这里。\n一个角色。一个梗。一个社区。\n用你的语言问。English, 中文, العربية, Türkçe, हिन्दी.\nWe Live Here Now. 🪶",
    "ar": "موبا هنا.\nشخصية. ميم. مجتمع.\nاسأل بلغتك. English, 中文, العربية, Türkçe, हिन्दी.\nنحن نعيش هنا الآن. 🪶",
    "tr": "MUBA burada.\nBir karakter. Bir meme. Bir topluluk.\nKendi dilinde sor. English, 中文, العربية, Türkçe, हिन्दी.\nWe Live Here Now. 🪶",
    "hi": "MUBA यहाँ है।\nएक किरदार। एक मीम। एक समुदाय।\nअपनी भाषा में पूछो। English, 中文, العربية, Türkçe, हिन्दी.\nWe Live Here Now. 🪶",
}
HELP = {
    "en": f"Ask MUBA in your language.\nGroups: I only answer MUBA things and GM / GN.\nSite: {SITE}\nX: {XURL}\nTG: {TGURL}",
    "zh": f"用你的语言问 MUBA。\n群里：我只回答和 MUBA 有关的话，以及 GM / GN。\n站点：{SITE}",
    "ar": f"اسأل موبا بلغتك.\nفي المجموعات أرد فقط على ما يخص موبا وعلى GM / GN.\nالموقع: {SITE}",
    "tr": f"MUBA’ya kendi dilinde sor.\nGruplarda yalnızca MUBA ile ilgili mesajlara ve GM / GN’ye cevap veririm.\nSite: {SITE}\nX: {XURL}\nTG: {TGURL}",
    "hi": f"अपनी भाषा में MUBA से पूछो।\nग्रुप में मैं केवल MUBA वाली बातों और GM / GN का जवाब देता हूँ।\nसाइट: {SITE}",
}


def detect_language(text: str, fallback: str = "en") -> str:
    raw = (text or "").strip()
    if not raw:
        return fallback
    if _CJK.search(raw):
        return "zh"
    if _ARABIC.search(raw):
        return "ar"
    if _DEVANAGARI.search(raw):
        return "hi"
    if _TR_LETTERS.search(raw) or _TR_WORDS.search(raw):
        return "tr"
    if _HI_LATIN.search(raw):
        return "hi"
    if _EN_HINTS.search(raw):
        return "en"
    return fallback


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").lower()


def is_gm(text: str) -> bool:
    t = re.sub(r"[!.,:;?؟。！]+$", "", _fold(text).strip())
    if t in {"gm", "g.m", "günaydın", "gunaydin", "早上好", "早安", "صباح الخير", "सुप्रभात", "good morning", "goodmorning"}:
        return True
    return bool(re.match(r"^(gm|good morning|günaydın|gunaydin)\b", t))


def is_gn(text: str) -> bool:
    t = re.sub(r"[!.,:;?؟。！]+$", "", _fold(text).strip())
    if t in {"gn", "g.n", "iyi geceler", "晚安", "تصبح على خير", "शुभ रात्रि", "good night", "goodnight"}:
        return True
    return bool(re.match(r"^(gn|good night|iyi geceler)\b", t))


def relevance_score(text: str) -> float:
    t = _fold(text)
    if not t:
        return 0.0
    score = 0.0
    for word in CORE:
        if word in t:
            score += 0.7
    for word in RELATED:
        if word in t:
            score += 0.18
    if is_gm(text) or is_gn(text):
        score += 0.9
    if re.search(r"\b(who are you|sen kimsin|you muba|what are you)\b", t):
        score += 0.4
    return min(score, 1.5)


def is_relevant(text: str, threshold: float = THRESHOLD) -> bool:
    return relevance_score(text) >= threshold


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9$ğüşöçıİĞÜŞÖÇ\u0600-\u06FF\u4E00-\u9FFF\u0900-\u097F]+", text.lower()))


def best_qa(text: str):
    q_tokens = _tokens(text)
    if not q_tokens:
        return None, 0.0
    best, best_score = None, 0.0
    for item in QA:
        blob = " ".join(item["q"].values()) + " " + " ".join(item.get("tags", []))
        score = len(q_tokens & _tokens(blob)) / max(len(q_tokens), 1)
        low = text.lower()
        for q in item["q"].values():
            if q.lower().strip(" ?؟") in low:
                score += 0.6
        if score > best_score:
            best, best_score = item, score
    return best, best_score


def gm_reply(lang: str) -> str:
    return random.choice(GMGN["gm"][lang])


def gn_reply(lang: str) -> str:
    return random.choice(GMGN["gn"][lang])


def answer(text: str, lang: str | None = None, allow_offtopic: bool = False) -> str:
    lang = lang if lang in {"en", "zh", "ar", "tr", "hi"} else detect_language(text)
    raw = (text or "").strip()
    if is_gm(raw):
        return gm_reply(lang)
    if is_gn(raw):
        return gn_reply(lang)

    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            sys = (
                "You are the MUBA community voice on Telegram. Speak like @MUBA_RH. "
                "Short sentences. Calm. Playful. Never corporate. Never financial advice. "
                "Never invent a contract address, price, listing or date. "
                "If unknown: the story is still being lived. "
                f"Site={SITE} X={XURL} TG={TGURL} CA={KNOWLEDGE['identity']['contract_status']}. "
                f"Look: {KNOWLEDGE['character']['look']} "
                "Answer ONLY in the user's language (en/zh/ar/tr/hi). Use 🪶 sparingly."
            )
            rsp = client.chat.completions.create(
                model=model,
                temperature=0.6,
                max_tokens=280,
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": f"lang={lang}\nmessage={raw}"},
                ],
            )
            out = (rsp.choices[0].message.content or "").strip()
            if out:
                return out
        except Exception as exc:
            log.warning("openai fallback: %s", exc)

    item, score = best_qa(raw)
    if item and score >= 0.22:
        return item["a"][lang]
    return FALLBACK[lang] if allow_offtopic else OFFTOPIC[lang]


def _mentioned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    msg = update.effective_message
    if not msg:
        return False
    bot_username = (context.bot.username or "").lower()
    if msg.reply_to_message and msg.reply_to_message.from_user:
        if msg.reply_to_message.from_user.id == context.bot.id:
            return True
    for ent in msg.entities or []:
        if ent.type in {"mention", "text_mention"} and msg.text:
            chunk = msg.text[ent.offset : ent.offset + ent.length].lower()
            if bot_username and bot_username in chunk:
                return True
    if bot_username and msg.text and f"@{bot_username}" in msg.text.lower():
        return True
    return False


def _should_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    chat = update.effective_chat
    if not chat:
        return False
    if chat.type == ChatType.PRIVATE:
        if REPLY_ALWAYS_PRIVATE:
            return True
        return is_relevant(text) or is_gm(text) or is_gn(text)
    if _mentioned(update, context):
        return True
    if is_gm(text) or is_gn(text):
        return True
    if REPLY_IN_GROUPS and is_relevant(text):
        return True
    return False


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "") if update.effective_message else ""
    lang = detect_language(text, fallback="tr")
    await update.effective_message.reply_text(START[lang])


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = detect_language((update.effective_message.text or ""), fallback="tr")
    await update.effective_message.reply_text(HELP[lang])


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = detect_language((update.effective_message.text or ""), "tr")
    await update.effective_message.reply_text(answer("What is MUBA?", lang=lang, allow_offtopic=True))


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if not msg or not msg.text:
        return
    if msg.from_user and msg.from_user.is_bot:
        return
    text = msg.text.strip()
    if text.startswith("/"):
        return
    if not _should_reply(update, context, text):
        return
    lang = detect_language(text)
    private = update.effective_chat and update.effective_chat.type == ChatType.PRIVATE
    body = answer(text, lang=lang, allow_offtopic=bool(private or _mentioned(update, context)))
    await msg.reply_text(body)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN eksik. BotFather tokenini ortam degiskeni olarak ver.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("muba", cmd_about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    log.info("MUBA is here. We live here now.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
