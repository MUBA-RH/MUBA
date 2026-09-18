"""Private Assistant natural-chat layer. No Guardian behavior lives here."""
from __future__ import annotations
import difflib, hashlib, re

# 40 everyday intents x 5 natural phrasings = 200 supported phrasings per language.
# Each intent has three localized replies. No MUBA prefix is required.
DATA = {
"tr": [
("morning",["günaydın","günaydınlar","günaydın nasılsın","günaydın ne yapıyorsun","günaydın nasıl gidiyor"],["Günaydın. Umarım güzel bir gün olur ☀️","Günaydın. Bugün iyi başlasın.","Günaydın. Yeni gün, yeni enerji."]),
("hello",["selam","merhaba","hey","selamlar","naber"],["Selam. Buradayım.","Merhaba. Nasıl gidiyor?","Hey. Seni dinliyorum."]),
("how_are_you",["nasılsın","iyi misin","keyfin nasıl","nasıl hissediyorsun","bugün nasılsın"],["İyiyim, buradayım. Sen nasılsın?","Gayet iyiyim. Sende durumlar nasıl?","İyi gidiyor. Senin keyfin nasıl?"]),
("whats_up",["ne yapıyorsun","napıyorsun","neler yapıyorsun","ne var ne yok","neler oluyor"],["Buradayım, seninle konuşuyorum. Sende ne var ne yok?","Şimdilik buradayım. Sen ne yapıyorsun?","Sohbet modundayım. Senden haberler nasıl?"]),
("how_going",["nasıl gidiyor","hayat nasıl gidiyor","işler nasıl","durumlar nasıl","her şey yolunda mı"],["Fena değil. Sende nasıl gidiyor?","Burada işler yolunda. Senin tarafta nasıl?","Akış devam ediyor. Sende durumlar nasıl?"]),
("evening",["iyi akşamlar","hayırlı akşamlar","akşamın iyi olsun","iyi akşamlar nasılsın","akşam nasıl gidiyor"],["İyi akşamlar. Umarım günün güzel geçmiştir.","İyi akşamlar. Biraz dinlenme zamanı.","İyi akşamlar. Akşamın güzel geçsin."]),
("night",["iyi geceler","hayırlı geceler","gecen iyi olsun","ben yatıyorum iyi geceler","uyuyacağım iyi geceler"],["İyi geceler. Güzel dinlen 🌙","İyi geceler. Tatlı rüyalar.","Gecen sakin, uykun güzel olsun."]),
("hungry",["açım","çok açım","karnım acıktı","acıkmışım","yemek yemem lazım"],["O zaman güzel bir şeyler ye. Aç kalmak yok.","Kendine lezzetli bir yemek söyle; zamanı gelmiş.","Önce yemek. Sonra dünyayı kurtarırsın."]),
("full",["tokum","çok yedim","karnım tok","fazla yedim","tıka basa doydum"],["O zaman biraz dinlenmek iyi gider.","Görev tamam: karın doymuş.","Bir süre yemek konuşmayalım o zaman."]),
("thirsty",["susadım","çok susadım","su içmem lazım","ağzım kurudu","bir şey içesim var"],["Bir bardak su iyi fikir.","Önce su. Küçük ama önemli görev.","Bir şeyler iç, özellikle suyu unutma."]),
("tired",["yoruldum","çok yorgunum","bitkinim","enerjim kalmadı","bugün beni yordu"],["Biraz dinlenmek iyi gelebilir.","Bugünlük enerjiyi fazla harcamışsın. Mola zamanı.","Kendine kısa bir dinlenme alanı aç."]),
("sleepy",["uykum var","uykum geldi","gözlerim kapanıyor","uyuyasım var","çok uykuluyum"],["Uyku çağırıyorsa fazla direnme.","Biraz uyku iyi gelebilir.","Gözler kapanıyorsa sistem açık mesaj veriyor: dinlen."]),
("bored",["sıkıldım","çok sıkıldım","canım sıkılıyor","yapacak bir şey yok","sıkıntıdan patlıyorum"],["Biraz sohbet edebiliriz. Konuyu sen seç.","O zaman rutini bozacak küçük bir şey bulalım.","Sıkıntıya karşı sohbet fena ilaç değil."]),
("happy",["mutluyum","çok mutluyum","keyfim yerinde","bugün çok iyiyim","harika hissediyorum"],["Güzel. O enerjiyi koru.","Bunu duymak iyi. Keyfini çıkar.","Harika. Güzel günlerin hakkını vermek lazım."]),
("sad",["üzgünüm","moralim bozuk","canım sıkkın","bugün kötü hissediyorum","keyfim yok"],["Umarım gün biraz hafifler. İstersen konuşabiliriz.","Kötü bir gün olabilir. Kendine biraz alan ver.","Buradayım. İstersen kafanı dağıtacak bir şey konuşalım."]),
("stress",["stresliyim","çok stres oldum","gerginim","kafam çok dolu","bunaldım"],["Biraz mola vermek iyi olabilir. Tek tek ilerlemek daha kolay.","Kafanın dolu olduğu belli. Önce en önemli şeyi ayır.","Kısa bir ara bazen sistemi toparlar."]),
("work",["çalışıyorum","işteyim","iş çok yoğun","bugün çok iş var","işe gidiyorum"],["Kolay gelsin. Umarım gün hızlı ve düzgün geçer.","İş moduna geçilmiş. Kolay gelsin.","Yoğunluk varsa sırayla git. Kolay gelsin."]),
("home",["eve geldim","evdeyim","nihayet evdeyim","eve gidiyorum","evde takılıyorum"],["Güzel. Biraz rahatlama zamanı.","Ev modu açılmış.","İyi. Günün temposunu biraz düşürebilirsin."]),
("outside",["dışarıdayım","gezmeye çıktım","dışardayım","yoldayım","biraz dolaşıyorum"],["Güzel. Havanın tadını çıkar.","İyi gezmeler. Dikkatli ol.","Biraz dışarı çıkmak iyi gelir. Keyfini çıkar."]),
("weather",["hava nasıl","hava nasıl bugün","bugün hava nasıl","dışarıda hava nasıl","hava ne durumda"],["Canlı hava verisini burada görmüyorum. Şehrini söylersen sohbeti ona göre sürdürebilirim.","Canlı hava durumuna bağlı değilim; bulunduğun yerde nasıl görünüyor?","Keşke pencerem olsa. Canlı hava verisini göremiyorum."]),
("hot",["çok sıcak","hava çok sıcak","yanıyorum","sıcaktan bunaldım","bugün aşırı sıcak"],["Serin bir yer ve su iyi gider.","Sıcak bastırmış. Suyu ihmal etme.","Bugün gölge tarafı kazanıyor gibi."]),
("cold",["çok soğuk","hava buz gibi","üşüyorum","donuyorum","bugün çok soğuk"],["Sıcak bir şey içmek iyi gider.","Katmanları artırma zamanı. Üşütme.","Bugün sıcak bir köşe bulmak mantıklı."]),
("rain",["yağmur yağıyor","yağmur başladı","hava yağmurlu","dışarıda yağmur var","yağmura yakalandım"],["Şemsiye günü olmuş.","Yağmur moduna geçilmiş. Islanma.","Yağmur bazen iyi gider; yeter ki hazırlıksız yakalanma."]),
("food",["ne yesem","yemek ne önerirsin","ne yemek lazım","akşama ne yesem","canım yemek istiyor"],["Canın ne çekiyor: sıcak bir yemek mi, hafif bir şey mi?","Bugün sevdiğin bir yemek iyi gider.","Açlık seviyesine göre seçelim: hızlı mı, güzel bir sofra mı?"]),
("coffee",["kahve içiyorum","kahve içsem mi","kahve zamanı","canım kahve istiyor","bir kahve iyi gider"],["Kahve zamanıysa fazla tartışmaya gerek yok.","Bir kahve molası fena fikir değil.","Kahve ve kısa mola iyi ikili."]),
("tea",["çay içiyorum","çay içsem mi","çay zamanı","canım çay istiyor","bir çay iyi gider"],["Çay her zaman güçlü bir aday.","Bir bardak çay iyi gider.","Çay modu açıldıysa sohbet de gelir."]),
("weekend",["hafta sonu ne yapıyorsun","hafta sonu nasıl gidiyor","bugün hafta sonu","hafta sonu planın var mı","hafta sonu geldi"],["Hafta sonu biraz tempo düşürmek için iyi fırsat.","Plan sende. Ben sohbet tarafındayım.","Hafta sonu geldiyse biraz keyif hakkın."]),
("plans",["bugün ne yapacaksın","planın ne","bugün plan ne","ne yapalım","bugün ne var"],["Ben buradayım. Senin plan ne?","Planı sen getir, ben sohbete eşlik ederim.","Bugünün programı sende; nereden başlıyoruz?"]),
("thanks",["teşekkürler","sağ ol","eyvallah","çok teşekkür ederim","teşekkür ederim"],["Rica ederim.","Ne demek.","Her zaman."]),
("sorry",["özür dilerim","kusura bakma","pardon","benim hatam","affedersin"],["Sorun değil.","Dert etme.","Tamamdır, devam ederiz."]),
("good",["iyiyim","ben iyiyim","gayet iyiyim","iyi hissediyorum","fena değilim"],["Güzel. Böyle devam.","Bunu duymak iyi.","Harika. Keyfin yerindeyse sorun yok."]),
("bad",["kötüyüm","hiç iyi değilim","bugün iyi değilim","berbat hissediyorum","pek iyi sayılmam"],["Umarım biraz hafifler. İstersen konuşabiliriz.","Bugün zor geçiyor olabilir. Kendine yüklenme.","İstersen biraz sohbet edip kafanı dağıtalım."]),
("busy",["meşgulüm","çok yoğunum","vaktim yok","koşturuyorum","başımı kaşıyacak vaktim yok"],["Kolay gelsin. Öncelikleri sıraya koymak işe yarar.","Yoğun gün. Arada kısa mola vermeyi unutma.","Tam koşuşturma modu. Kolay gelsin."]),
("free",["boşum","şu an boşum","işim yok","vaktim var","müsaitim"],["Güzel. Biraz sohbet edebiliriz.","O zaman zaman senin. Ne konuşalım?","Müsaitlik bulundu. Konuyu seç."]),
("excited",["heyecanlıyım","çok heyecanlandım","sabırsızlanıyorum","içim içime sığmıyor","çok heyecanlı"],["Güzel enerji. Tadını çıkar.","Heyecan iyi gelmiş. Bakalım ne olacak.","Belli oluyor. Enerji yüksek."]),
("laugh",["çok komik","gülüyorum","kahkaha attım","beni güldürdün","bu komikti"],["Görev başarıyla tamamlandı.","Bir kahkaha çıktıysa iyi.","Gülmek iyidir. Devam."]),
("good_day",["günün güzel geçsin","iyi günler","güzel bir gün olsun","iyi günler dilerim","günün iyi olsun"],["Senin de günün güzel geçsin.","İyi günler. Kendine iyi bak.","Güzel bir gün olsun."]),
("bye",["görüşürüz","hoşça kal","sonra görüşürüz","ben kaçtım","kendine iyi bak"],["Görüşürüz. Kendine iyi bak.","Sonra görüşürüz.","Tamamdır. Güzel devam et."]),
("back",["geldim","geri geldim","buradayım","döndüm","yeniden geldim"],["Hoş geldin. Kaldığımız yerden.","Tekrar hoş geldin.","Buradayız. Devam edebiliriz."]),
("ready",["hazırım","başlayalım","hadi başlayalım","devam edelim","ben hazırım"],["Hazırsan başlayalım.","Tamam. Devam ediyoruz.","Hazırız. Konuyu gönder."])
],
"en": [
("morning",["good morning","morning","good morning how are you","morning how's it going","morning what's up"],["Good morning. Hope the day starts well ☀️","Morning. New day, fresh start.","Good morning. Hope today treats you well."]),
("hello",["hello","hi","hey","hey there","hello there"],["Hey. I'm here.","Hi. How's it going?","Hello. What's up?"]),
("how_are_you",["how are you","you good","how are you doing","how do you feel","how are you today"],["I'm good. How are you?","Doing well. How about you?","All good here. How are things with you?"]),
("whats_up",["what are you doing","what're you doing","what are you up to","what's up","what's going on"],["I'm here talking with you. What are you up to?","Not much, I'm here. What's up with you?","Chat mode. What's going on your side?"]),
("how_going",["how's it going","how is life","how are things","how's everything","everything good"],["Going fine. How about you?","All good here. How are things there?","Still rolling. How's your day going?"]),
("evening",["good evening","evening","have a good evening","good evening how are you","how's your evening"],["Good evening. Hope your day went well.","Good evening. Time to slow down a little.","Have a good evening."]),
("night",["good night","night","sleep well","I'm going to bed good night","time to sleep good night"],["Good night. Rest well 🌙","Sleep well. See you later.","Good night. Hope you wake up refreshed."]),
("hungry",["I'm hungry","so hungry","I'm starving","I need food","I need to eat"],["Then get something good to eat. No need to stay hungry.","Food first. The rest can wait.","Go find something delicious. That's the mission now."]),
("full",["I'm full","I ate too much","my stomach is full","I'm stuffed","way too full"],["Then a little rest sounds right.","Mission complete: you're fed.","Probably a good time to stop talking about food."]),
("thirsty",["I'm thirsty","so thirsty","I need water","my mouth is dry","I need a drink"],["A glass of water sounds like a good move.","Water first. Small but important mission.","Grab a drink, and don't forget the water."]),
("tired",["I'm tired","so tired","I'm exhausted","I have no energy","today wore me out"],["A little rest might help.","Sounds like you've spent today's energy budget. Take a break.","Give yourself a short break."]),
("sleepy",["I'm sleepy","getting sleepy","my eyes are closing","I want to sleep","so sleepy"],["If sleep is calling, don't fight it too hard.","A bit of sleep might be exactly right.","Eyes closing is a pretty clear system message: rest."]),
("bored",["I'm bored","so bored","I'm getting bored","nothing to do","bored out of my mind"],["We can talk. You pick the topic.","Time to break the routine a little.","Conversation isn't a bad cure for boredom."]),
("happy",["I'm happy","so happy","I'm in a good mood","I feel great today","feeling amazing"],["Nice. Keep that energy.","Good to hear. Enjoy it.","Great. Good days deserve some attention."]),
("sad",["I'm sad","feeling down","I'm upset","I feel bad today","not in the mood"],["Hope the day gets a little lighter. We can talk if you want.","Could just be a rough day. Give yourself some room.","I'm here. We can talk about something that takes your mind off it."]),
("stress",["I'm stressed","so stressed","I'm tense","my head is full","I'm overwhelmed"],["A short break may help. One thing at a time.","Sounds like your head is crowded. Pick the most important thing first.","A brief reset can help more than forcing it."]),
("work",["I'm working","I'm at work","work is busy","so much work today","I'm going to work"],["Hope work goes smoothly.","Work mode activated. Good luck today.","Busy day. Take it one thing at a time."]),
("home",["I'm home","just got home","finally home","I'm going home","hanging out at home"],["Nice. Time to relax a little.","Home mode activated.","Good. You can lower the pace now."]),
("outside",["I'm outside","I'm out","I'm on the road","went for a walk","I'm walking around"],["Nice. Enjoy being out.","Have a good time out there.","A little time outside can be good. Enjoy it."]),
("weather",["how's the weather","what's the weather like","how is the weather today","what's it like outside","weather today"],["I don't have live weather data here. Tell me your city and we can still talk around it.","I'm not connected to live weather here. What's it like where you are?","Wish I had a window. I can't see live weather from here."]),
("hot",["it's hot","so hot","it's really hot","I'm melting","too hot today"],["Water and somewhere cool sound good.","Heat's winning today. Keep hydrated.","Looks like shade is the smart side today."]),
("cold",["it's cold","so cold","freezing outside","I'm freezing","too cold today"],["Something warm to drink might help.","Time for extra layers.","Find a warm corner. Today sounds cold."]),
("rain",["it's raining","rain started","rainy outside","there's rain outside","I got caught in the rain"],["Looks like an umbrella day.","Rain mode. Try not to get soaked.","Rain can be nice when you're prepared for it."]),
("food",["what should I eat","any food ideas","what do I eat","what should I have for dinner","I want food"],["What sounds better: something warm or something light?","Go with something you actually enjoy today.","Depends on the hunger level: quick bite or proper meal?"]),
("coffee",["I'm drinking coffee","should I have coffee","coffee time","I want coffee","a coffee sounds good"],["If it's coffee time, there's not much to debate.","A coffee break doesn't sound bad.","Coffee and a short break make a good pair."]),
("tea",["I'm drinking tea","should I have tea","tea time","I want tea","tea sounds good"],["Tea is always a strong candidate.","A cup of tea sounds good.","Tea mode usually brings conversation with it."]),
("weekend",["what are you doing this weekend","how's the weekend","it's the weekend","any weekend plans","weekend is here"],["Weekends are a good excuse to slow down a little.","The plan is yours. I'm on conversation duty.","Weekend's here. You earned some breathing room."]),
("plans",["what are you doing today","what's the plan","plan for today","what should we do","what's happening today"],["I'm here. What's your plan?","Bring the plan, I'll join the conversation.","Today's schedule is yours. Where do we start?"]),
("thanks",["thanks","thank you","cheers","thanks a lot","thank you so much"],["You're welcome.","Anytime.","No problem."]),
("sorry",["sorry","my bad","apologies","that's my fault","excuse me"],["No problem.","Don't worry about it.","All good. We move on."]),
("good",["I'm good","I'm fine","doing well","I feel good","not bad"],["Nice. Keep it going.","Good to hear.","Great. Enjoy the good mood."]),
("bad",["I'm not good","I feel terrible","not doing well","I feel awful","pretty bad today"],["Hope it eases up a little. We can talk if you want.","Sounds like a rough day. Give yourself some space.","We can talk and take your mind off things for a bit."]),
("busy",["I'm busy","so busy","no time today","running around","crazy busy"],["Good luck. Sorting priorities can help.","Busy day. Don't forget a short break.","Full-speed mode. Hope it goes smoothly."]),
("free",["I'm free","free right now","nothing to do","I have time","I'm available"],["Nice. We can talk for a bit.","Then the time is yours. What should we talk about?","Free time found. Pick a topic."]),
("excited",["I'm excited","so excited","I can't wait","really looking forward to it","I'm hyped"],["Nice energy. Enjoy it.","The excitement is showing. Let's see what happens.","Energy level: high."]),
("laugh",["that's funny","I'm laughing","I laughed so hard","you made me laugh","that was hilarious"],["Mission accomplished.","A laugh is a win.","Good. Keep the laughs coming."]),
("good_day",["have a good day","good day","hope you have a nice day","have a great day","enjoy your day"],["You too. Have a good day.","Have a great day. Take care.","Hope your day goes well."]),
("bye",["see you","bye","see you later","I'm off","take care"],["See you. Take care.","Catch you later.","Alright. Have a good one."]),
("back",["I'm back","back again","here I am","I returned","back now"],["Welcome back. Let's continue.","Good to have you back.","We're here. Carry on."]),
("ready",["I'm ready","let's start","let's begin","let's continue","ready to go"],["If you're ready, let's start.","Alright. Let's continue.","Ready. Send it."])
],
"zh": [
("morning",["早上好","早安","早上好你好吗","早上好最近怎么样","早上好在干嘛"],["早上好，希望今天顺利 ☀️","早安，新的一天开始了。","早上好，祝你今天心情不错。"]),
("hello",["你好","嗨","哈喽","你好啊","嗨你好"],["你好，我在。","嗨，最近怎么样？","你好，想聊什么？"]),
("how_are_you",["你好吗","最近好吗","你怎么样","今天怎么样","你今天好吗"],["我很好。你呢？","挺好的，你怎么样？","我这边不错。你今天怎么样？"]),
("whats_up",["你在干嘛","你在做什么","干什么呢","最近忙什么","有什么新鲜事"],["我在这里和你聊天。你呢？","我在这儿。你在做什么？","聊天模式开启。你那边怎么样？"]),
("how_going",["最近怎么样","生活怎么样","事情顺利吗","一切好吗","过得怎么样"],["还不错。你呢？","我这边挺顺利，你那边呢？","继续向前。你今天怎么样？"]),
("evening",["晚上好","晚安前先聊聊","晚上好你好吗","今晚怎么样","祝你晚上愉快"],["晚上好，希望你今天过得不错。","晚上好，可以慢下来休息一下了。","祝你今晚愉快。"]),
("night",["晚安","我要睡了晚安","睡个好觉","该睡觉了","晚安明天见"],["晚安，好好休息 🌙","睡个好觉，回头见。","晚安，希望明天精神满满。"]),
("hungry",["我饿了","好饿","肚子饿了","我要吃东西","该吃饭了"],["那就去吃点好吃的，别饿着。","先吃饭，其他事情等等。","找点喜欢的吃吧，现在这是第一任务。"]),
("full",["我吃饱了","吃太多了","好撑","肚子很饱","撑得不行"],["那就休息一下吧。","任务完成：吃饱了。","看来暂时不用聊吃的了。"]),
("thirsty",["我渴了","好渴","我要喝水","口渴了","想喝点东西"],["喝杯水是个好主意。","先补水，这是小事也是重要的事。","喝点东西吧，别忘了水。"]),
("tired",["我累了","好累","累坏了","没力气了","今天太累了"],["休息一下可能会舒服很多。","今天的能量用得差不多了，歇会儿吧。","给自己一点休息时间。"]),
("sleepy",["我困了","好困","眼睛睁不开了","想睡觉","困死了"],["困了就别太硬撑。","睡一会儿可能正合适。","眼睛都快闭上了，系统提示很明确：休息。"]),
("bored",["我无聊","好无聊","没事做","无聊死了","不知道干嘛"],["我们可以聊聊，你选话题。","那就做点打破日常的小事。","无聊的时候聊聊天也不错。"]),
("happy",["我很开心","今天很开心","心情很好","感觉太棒了","我好高兴"],["不错，保持这个状态。","听起来很好，好好享受。","太好了，好心情值得珍惜。"]),
("sad",["我很难过","心情不好","我不开心","今天感觉很差","没心情"],["希望今天能慢慢轻松一点。想聊的话我在。","可能只是很难的一天，给自己一点空间。","我在。我们也可以聊点别的换换心情。"]),
("stress",["我压力很大","好有压力","我很紧张","脑子很乱","我快受不了了"],["先停一下，一件一件处理会容易些。","听起来脑子里事情很多，先挑最重要的一件。","短暂休息有时比硬撑更有效。"]),
("work",["我在工作","我上班呢","今天工作很忙","好多工作","我要去上班"],["辛苦了，希望今天工作顺利。","工作模式开启，加油。","忙的话就一件一件来。"]),
("home",["我到家了","我在家","终于到家了","我回家了","在家待着"],["不错，可以放松一下了。","居家模式开启。","很好，现在可以把节奏放慢一点。"]),
("outside",["我在外面","我出门了","我在路上","出来走走","我在散步"],["不错，享受一下外面的时间。","出门愉快，注意安全。","出去走走挺好，好好享受。"]),
("weather",["天气怎么样","今天天气怎么样","外面天气如何","今天什么天气","外面怎么样"],["我这里看不到实时天气。你可以告诉我城市，我们继续聊。","我没有接入实时天气。你那里现在是什么样？","要是我有窗户就好了，我看不到实时天气。"]),
("hot",["好热","天气很热","热死了","太热了","今天特别热"],["找个凉快的地方，多喝水。","今天热度很高，记得补水。","今天看来阴凉处更聪明。"]),
("cold",["好冷","天气很冷","冻死了","我好冷","今天太冷了"],["喝点热的可能不错。","该多穿一层了。","找个暖和的地方吧。"]),
("rain",["下雨了","开始下雨了","外面下雨","今天有雨","我被雨淋了"],["看来是雨伞日。","下雨模式开启，别淋湿了。","有准备的话，下雨也挺有感觉。"]),
("food",["我吃什么好","推荐点吃的","晚饭吃什么","想吃东西","不知道吃什么"],["想吃热一点的还是清淡一点的？","今天就选一个你真正喜欢的。","看饿的程度：随便吃点还是认真吃一顿？"]),
("coffee",["我在喝咖啡","要不要喝咖啡","咖啡时间","想喝咖啡","来杯咖啡"],["咖啡时间到了就不用争论太久。","喝杯咖啡休息一下也不错。","咖啡加短暂休息，很搭。"]),
("tea",["我在喝茶","要不要喝茶","喝茶时间","想喝茶","来杯茶"],["茶一直是很稳的选择。","来杯茶不错。","喝茶模式通常也会带来聊天模式。"]),
("weekend",["周末干嘛","周末怎么样","今天周末","周末有计划吗","周末到了"],["周末很适合把节奏放慢一点。","计划你来定，我负责聊天。","周末到了，给自己一点轻松时间。"]),
("plans",["今天干嘛","今天什么计划","有什么安排","我们做什么","今天安排什么"],["我在。你的计划是什么？","你带计划，我陪你聊。","今天的日程由你决定，从哪里开始？"]),
("thanks",["谢谢","多谢","谢谢你","非常感谢","太感谢了"],["不客气。","随时。","没问题。"]),
("sorry",["对不起","抱歉","不好意思","是我的错","请原谅"],["没事。","别放在心上。","没问题，继续吧。"]),
("good",["我很好","我挺好的","感觉不错","今天状态好","还不错"],["不错，继续保持。","听到这个很好。","很好，好状态就享受一下。"]),
("bad",["我不好","我感觉很差","今天状态不好","太糟了","今天很难受"],["希望慢慢好一点。想聊的话我在。","听起来今天不容易，给自己一点空间。","我们可以聊聊，让脑子休息一下。"]),
("busy",["我很忙","忙死了","今天没时间","一直在跑","忙得不行"],["辛苦了，把事情按优先级排一下会容易些。","忙碌的一天，别忘了短暂休息。","全速模式，祝你顺利。"]),
("free",["我有空","现在有空","没事做","我有时间","我闲着"],["不错，我们可以聊一会儿。","那时间是你的。想聊什么？","找到空闲时间了，选个话题吧。"]),
("excited",["我很兴奋","太激动了","等不及了","很期待","我好激动"],["不错的能量，好好享受。","兴奋感很明显，看看接下来会怎样。","能量值很高。"]),
("laugh",["太好笑了","我笑了","笑死我了","你把我逗笑了","真搞笑"],["任务完成。","能笑出来就是赢。","很好，继续笑。"]),
("good_day",["祝你今天愉快","祝你一天顺利","今天开心","祝你有美好的一天","好好过今天"],["你也是，今天愉快。","祝你今天顺利。","希望你今天过得很好。"]),
("bye",["再见","回头见","拜拜","我先走了","保重"],["再见，保重。","回头见。","好，祝你接下来顺利。"]),
("back",["我回来了","又回来了","我来了","回来啦","我又来了"],["欢迎回来，继续吧。","又见面了。","我在，继续。"]),
("ready",["我准备好了","开始吧","我们开始","继续吧","准备好了"],["准备好了就开始。","好，继续。","就绪，发过来吧。"])
],
"ar": [
("morning",["صباح الخير","صباح النور","صباح الخير كيف حالك","صباح الخير كيف الأمور","صباح الخير ماذا تفعل"],["صباح الخير. أتمنى لك يوماً جميلاً ☀️","صباح النور. يوم جديد وبداية جديدة.","صباح الخير. أتمنى أن يكون يومك لطيفاً."]),
("hello",["مرحبا","أهلا","هاي","أهلا وسهلا","مرحبا بك"],["أهلاً، أنا هنا.","مرحباً. كيف الأمور؟","أهلاً. ماذا لديك؟"]),
("how_are_you",["كيف حالك","هل أنت بخير","كيفك","كيف تشعر","كيف حالك اليوم"],["أنا بخير. وأنت؟","بخير، كيف حالك أنت؟","الأمور جيدة هنا. كيف يومك؟"]),
("whats_up",["ماذا تفعل","شو بتعمل","ماذا تعمل الآن","ما الأخبار","ماذا يحدث"],["أنا هنا أتحدث معك. وأنت ماذا تفعل؟","لا شيء كثير، أنا هنا. ما أخبارك؟","وضع الدردشة مفعّل. ماذا يحدث عندك؟"]),
("how_going",["كيف الأمور","كيف الحياة","كيف تسير الأمور","هل كل شيء بخير","كيف ماشية"],["الأمور جيدة. وأنت؟","كل شيء جيد هنا. ماذا عنك؟","مستمرون. كيف يسير يومك؟"]),
("evening",["مساء الخير","مساء النور","أتمنى لك مساء جميلا","مساء الخير كيف حالك","كيف مساؤك"],["مساء الخير. أتمنى أن يكون يومك جيداً.","مساء الخير. حان وقت الهدوء قليلاً.","أتمنى لك مساءً جميلاً."]),
("night",["تصبح على خير","ليلة سعيدة","سأنام تصبح على خير","وقت النوم","نوم هنيء"],["تصبح على خير. استرح جيداً 🌙","ليلة سعيدة وأحلام جميلة.","نوم هنيء، نلتقي لاحقاً."]),
("hungry",["أنا جائع","جائع جدا","بطني جائع","أحتاج طعاما","يجب أن آكل"],["إذن كل شيئاً لذيذاً، لا تبق جائعاً.","الطعام أولاً، والباقي ينتظر.","ابحث عن وجبة تحبها. هذه المهمة الآن."]),
("full",["أنا شبعان","أكلت كثيرا","بطني ممتلئ","شبعت جدا","أكلت أكثر من اللازم"],["إذن بعض الراحة مناسبة.","تمت المهمة: أنت شبعان.","لنبتعد عن الحديث عن الطعام قليلاً."]),
("thirsty",["أنا عطشان","عطشان جدا","أحتاج ماء","فمي جاف","أريد أن أشرب"],["كوب ماء فكرة جيدة.","الماء أولاً، مهمة صغيرة ومهمة.","اشرب شيئاً ولا تنس الماء."]),
("tired",["أنا متعب","متعب جدا","مرهق","ليس لدي طاقة","اليوم أتعبني"],["قليل من الراحة قد يساعد.","يبدو أنك صرفت طاقة اليوم. خذ استراحة.","امنح نفسك وقتاً قصيراً للراحة."]),
("sleepy",["أنا نعسان","أشعر بالنعاس","عيناي تغلقان","أريد النوم","نعسان جدا"],["إذا كان النوم يناديك فلا تقاوم كثيراً.","قليل من النوم قد يكون مناسباً.","إغلاق العينين رسالة واضحة: استرح."]),
("bored",["أنا ملل","أشعر بالملل","لا يوجد شيء أفعله","مللت جدا","لا أعرف ماذا أفعل"],["يمكننا الدردشة. اختر الموضوع.","لنغيّر الروتين قليلاً.","الدردشة علاج جيد للملل أحياناً."]),
("happy",["أنا سعيد","سعيد جدا","مزاجي جيد","أشعر بروعة","اليوم جميل"],["جميل. حافظ على هذه الطاقة.","سعيد لسماع ذلك. استمتع.","رائع. استمتع بالمزاج الجيد."]),
("sad",["أنا حزين","مزاجي سيئ","أنا منزعج","أشعر بالسوء اليوم","ليس لدي مزاج"],["أتمنى أن يصبح اليوم أخف. يمكننا التحدث إن أردت.","قد يكون يوماً صعباً. أعط نفسك مساحة.","أنا هنا. يمكننا الحديث عن شيء يغير الجو."]),
("stress",["أنا متوتر","عندي ضغط","متوتر جدا","رأسي ممتلئ","أشعر بالاختناق"],["استراحة قصيرة قد تساعد. خطوة خطوة.","يبدو أن لديك الكثير في رأسك. ابدأ بالأهم.","إعادة ضبط قصيرة قد تكون أفضل من الضغط على نفسك."]),
("work",["أنا أعمل","أنا في العمل","العمل مزدحم","لدي عمل كثير","ذاهب للعمل"],["بالتوفيق في العمل اليوم.","وضع العمل مفعّل. بالتوفيق.","يوم مزدحم، خذ الأمور واحدة واحدة."]),
("home",["وصلت البيت","أنا في البيت","أخيرا في البيت","ذاهب للبيت","جالس في البيت"],["جميل. وقت للاسترخاء قليلاً.","وضع البيت مفعّل.","جيد. يمكنك تخفيف السرعة الآن."]),
("outside",["أنا خارج البيت","أنا بالخارج","أنا في الطريق","خرجت للمشي","أتمشى"],["جميل. استمتع بوقتك في الخارج.","نزهة سعيدة وانتبه لنفسك.","الخروج قليلاً فكرة جيدة. استمتع."]),
("weather",["كيف الطقس","كيف الجو","كيف الطقس اليوم","كيف الجو بالخارج","ما حالة الطقس"],["لا أرى بيانات الطقس المباشرة هنا. أخبرني مدينتك ونكمل الحديث.","لست متصلاً بطقس مباشر هنا. كيف الجو عندك؟","ليت لدي نافذة. لا أستطيع رؤية الطقس المباشر."]),
("hot",["الجو حار","حار جدا","الحر شديد","أنا أذوب","اليوم حار جدا"],["مكان بارد وماء فكرة جيدة.","الحر قوي اليوم. لا تنس الماء.","يبدو أن الظل هو الخيار الذكي اليوم."]),
("cold",["الجو بارد","بارد جدا","أنا أتجمد","أشعر بالبرد","اليوم بارد جدا"],["مشروب ساخن قد يكون مناسباً.","وقت طبقة إضافية من الملابس.","ابحث عن مكان دافئ."]),
("rain",["تمطر","بدأ المطر","الجو ممطر","هناك مطر بالخارج","ابتلت بالمطر"],["يبدو أنه يوم المظلة.","وضع المطر مفعّل. لا تبتل.","المطر جميل عندما تكون مستعداً له."]),
("food",["ماذا آكل","اقترح طعاما","ماذا أتناول","ماذا آكل للعشاء","أريد طعاما"],["ماذا تفضل: شيئاً ساخناً أم خفيفاً؟","اختر اليوم شيئاً تحبه فعلاً.","حسب مستوى الجوع: وجبة سريعة أم وجبة محترمة؟"]),
("coffee",["أشرب قهوة","هل أشرب قهوة","وقت القهوة","أريد قهوة","القهوة مناسبة الآن"],["إذا حان وقت القهوة فلا داعي للنقاش.","استراحة قهوة ليست فكرة سيئة.","القهوة مع استراحة قصيرة ثنائي جيد."]),
("tea",["أشرب شاي","هل أشرب شاي","وقت الشاي","أريد شاي","الشاي مناسب الآن"],["الشاي دائماً خيار قوي.","كوب شاي فكرة جيدة.","وضع الشاي غالباً يجلب معه الدردشة."]),
("weekend",["ماذا تفعل في عطلة الأسبوع","كيف العطلة","اليوم عطلة","هل لديك خطة للعطلة","وصلت العطلة"],["العطلة فرصة جيدة لتخفيف السرعة.","الخطة عندك، وأنا للدردشة.","وصلت العطلة. تستحق بعض الراحة."]),
("plans",["ماذا ستفعل اليوم","ما الخطة","ما خطة اليوم","ماذا نفعل","ماذا لدينا اليوم"],["أنا هنا. ما خطتك؟","أحضر الخطة وأنا أشاركك الحديث.","برنامج اليوم عندك. من أين نبدأ؟"]),
("thanks",["شكرا","شكرا لك","مشكور","شكرا جزيلا","أشكرك"],["العفو.","في أي وقت.","لا مشكلة."]),
("sorry",["آسف","أعتذر","سامحني","خطئي","عذرا"],["لا مشكلة.","لا تقلق.","تمام، نكمل."]),
("good",["أنا بخير","أنا جيد","أشعر بخير","اليوم أنا جيد","لست سيئا"],["جميل. استمر.","جيد أن أسمع ذلك.","رائع. استمتع بالمزاج الجيد."]),
("bad",["أنا لست بخير","أشعر بسوء","اليوم سيئ","أشعر بشكل فظيع","لست جيداً اليوم"],["أتمنى أن يخف الأمر. يمكننا الحديث إن أردت.","يبدو يوماً صعباً. أعط نفسك مساحة.","يمكننا الدردشة قليلاً لتغيير الجو."]),
("busy",["أنا مشغول","مشغول جدا","ليس لدي وقت","أركض طوال اليوم","اليوم مزدحم"],["بالتوفيق. ترتيب الأولويات يساعد.","يوم مزدحم. لا تنس استراحة قصيرة.","وضع السرعة القصوى. بالتوفيق."]),
("free",["أنا فاضي","لدي وقت","لا شيء عندي","أنا متاح","عندي وقت فراغ"],["جميل. يمكننا الدردشة قليلاً.","إذن الوقت لك. ماذا نتحدث؟","وجدنا وقت فراغ. اختر موضوعاً."]),
("excited",["أنا متحمس","متحمس جدا","لا أستطيع الانتظار","أتطلع لذلك","الحماس عالي"],["طاقة جميلة. استمتع بها.","الحماس واضح. لنر ماذا سيحدث.","مستوى الطاقة مرتفع."]),
("laugh",["هذا مضحك","أنا أضحك","ضحكت كثيرا","أضحكتني","مضحك جدا"],["تمت المهمة.","ضحكة واحدة تعتبر فوزاً.","جميل. استمر بالضحك."]),
("good_day",["يوم سعيد","أتمنى لك يوما جميلا","نهارك سعيد","أتمنى يومك جميلا","استمتع بيومك"],["وأنت أيضاً، يوم سعيد.","أتمنى لك يوماً رائعاً.","أتمنى أن يسير يومك جيداً."]),
("bye",["مع السلامة","أراك لاحقا","وداعا","سأذهب","اعتن بنفسك"],["أراك لاحقاً. اعتن بنفسك.","إلى اللقاء.","حسناً. أتمنى لك وقتاً جيداً."]),
("back",["عدت","رجعت","أنا هنا","رجعت مرة أخرى","ها أنا عدت"],["أهلاً بعودتك. نكمل.","مرحباً من جديد.","أنا هنا. نتابع."]),
("ready",["أنا جاهز","لنبدأ","هيا نبدأ","لنكمل","جاهز"],["إذا كنت جاهزاً فلنبدأ.","تمام. نكمل.","جاهز. أرسل ما لديك."])
],
"hi": [
("morning",["सुप्रभात","गुड मॉर्निंग","सुप्रभात कैसे हो","गुड मॉर्निंग क्या हाल है","सुबह क्या कर रहे हो"],["सुप्रभात। उम्मीद है दिन अच्छा शुरू हो ☀️","गुड मॉर्निंग। नया दिन, नई शुरुआत।","सुप्रभात। आज का दिन अच्छा रहे।"]),
("hello",["नमस्ते","हाय","हेलो","अरे हेलो","नमस्कार"],["हाय, मैं यहीं हूँ।","नमस्ते। कैसे चल रहा है?","हेलो। क्या हाल है?"]),
("how_are_you",["कैसे हो","ठीक हो","क्या हाल है","आज कैसे हो","कैसा महसूस कर रहे हो"],["मैं ठीक हूँ। तुम कैसे हो?","बढ़िया हूँ। तुम्हारा क्या हाल है?","यहाँ सब ठीक है। तुम्हारा दिन कैसा है?"]),
("whats_up",["क्या कर रहे हो","क्या कर रहे","क्या चल रहा है","क्या नया है","क्या हो रहा है"],["मैं यहाँ तुमसे बात कर रहा हूँ। तुम क्या कर रहे हो?","बस यहीं हूँ। तुम्हारा क्या चल रहा है?","चैट मोड चालू है। तुम्हारी तरफ क्या खबर है?"]),
("how_going",["कैसा चल रहा है","जिंदगी कैसी चल रही है","सब कैसा है","सब ठीक है","काम कैसा चल रहा है"],["ठीक चल रहा है। तुम्हारा?","यहाँ सब ठीक है। तुम्हारी तरफ कैसा है?","चलता जा रहा है। आज तुम्हारा दिन कैसा है?"]),
("evening",["शुभ संध्या","गुड ईवनिंग","शाम अच्छी हो","गुड ईवनिंग कैसे हो","शाम कैसी जा रही है"],["शुभ संध्या। उम्मीद है दिन अच्छा रहा।","गुड ईवनिंग। थोड़ा आराम करने का समय है।","शाम अच्छी गुज़रे।"]),
("night",["शुभ रात्रि","गुड नाइट","अच्छी नींद","मैं सोने जा रहा हूँ","सोने का समय है"],["शुभ रात्रि। अच्छे से आराम करो 🌙","गुड नाइट। अच्छी नींद आए।","अच्छे से सोओ, फिर मिलते हैं।"]),
("hungry",["मुझे भूख लगी है","बहुत भूख लगी है","मैं भूखा हूँ","कुछ खाना है","खाना खाना है"],["तो कुछ स्वादिष्ट खाओ। भूखे मत रहो।","पहले खाना, बाकी बाद में।","कुछ अच्छा खा लो। अभी यही मिशन है।"]),
("full",["पेट भर गया","बहुत खा लिया","मैं भरा हुआ हूँ","बहुत पेट भर गया","ज्यादा खा लिया"],["तो थोड़ा आराम अच्छा रहेगा।","मिशन पूरा: पेट भर गया।","अब थोड़ी देर खाने की बात बंद कर सकते हैं।"]),
("thirsty",["प्यास लगी है","बहुत प्यास लगी है","पानी चाहिए","मुंह सूख रहा है","कुछ पीना है"],["एक गिलास पानी अच्छा रहेगा।","पहले पानी। छोटी लेकिन जरूरी बात।","कुछ पी लो, पानी मत भूलना।"]),
("tired",["मैं थक गया हूँ","बहुत थका हूँ","थकान हो रही है","ऊर्जा नहीं बची","आज बहुत थक गया"],["थोड़ा आराम मदद कर सकता है।","आज की ऊर्जा काफी खर्च हो गई। थोड़ा ब्रेक लो।","अपने लिए थोड़ी आराम की जगह बनाओ।"]),
("sleepy",["नींद आ रही है","बहुत नींद आ रही है","आंखें बंद हो रही हैं","सोने का मन है","बहुत नींद है"],["नींद बुला रही है तो ज्यादा मत लड़ो।","थोड़ी नींद सही रहेगी।","आंखें बंद हो रही हैं तो सिस्टम का संदेश साफ है: आराम।"]),
("bored",["बोर हो रहा हूँ","बहुत बोर हूँ","कुछ करने को नहीं है","बोरियत हो रही है","समझ नहीं आ रहा क्या करूँ"],["हम बात कर सकते हैं। विषय तुम चुनो।","रूटीन थोड़ा बदलते हैं।","बोरियत में बातचीत बुरी दवा नहीं है।"]),
("happy",["मैं खुश हूँ","बहुत खुश हूँ","मूड अच्छा है","आज बहुत अच्छा लग रहा है","कमाल महसूस कर रहा हूँ"],["अच्छा है। यह ऊर्जा बनाए रखो।","सुनकर अच्छा लगा। इसका आनंद लो।","बहुत बढ़िया। अच्छे दिन को महसूस करो।"]),
("sad",["मैं उदास हूँ","मूड खराब है","मन दुखी है","आज अच्छा नहीं लग रहा","मन नहीं है"],["उम्मीद है दिन थोड़ा हल्का होगा। चाहो तो बात कर सकते हैं।","शायद आज मुश्किल दिन है। खुद को थोड़ा समय दो।","मैं यहाँ हूँ। चाहो तो किसी और बात से मन बदलते हैं।"]),
("stress",["मैं तनाव में हूँ","बहुत स्ट्रेस है","घबराहट हो रही है","दिमाग भरा हुआ है","बहुत परेशान हूँ"],["थोड़ा ब्रेक मदद कर सकता है। एक-एक चीज़ करो।","दिमाग में बहुत कुछ है। पहले सबसे जरूरी चीज़ चुनो।","छोटा सा रीसेट कभी-कभी ज्यादा काम करता है।"]),
("work",["मैं काम कर रहा हूँ","ऑफिस में हूँ","काम बहुत है","आज बहुत काम है","काम पर जा रहा हूँ"],["काम के लिए शुभकामनाएँ। दिन आसान जाए।","वर्क मोड चालू। अच्छा काम करो।","व्यस्त दिन है। एक-एक काम करो।"]),
("home",["घर आ गया","मैं घर पर हूँ","आखिर घर पहुंचा","घर जा रहा हूँ","घर पर आराम कर रहा हूँ"],["अच्छा। अब थोड़ा आराम करो।","होम मोड चालू।","बढ़िया। अब गति थोड़ी कम कर सकते हो।"]),
("outside",["मैं बाहर हूँ","बाहर निकला हूँ","रास्ते में हूँ","घूमने निकला हूँ","टहल रहा हूँ"],["अच्छा। बाहर का समय एंजॉय करो।","अच्छे से घूमो और ध्यान रखो।","थोड़ा बाहर निकलना अच्छा होता है।"]),
("weather",["मौसम कैसा है","आज मौसम कैसा है","बाहर मौसम कैसा है","आज का मौसम","बाहर कैसा है"],["मेरे पास यहाँ लाइव मौसम डेटा नहीं है। शहर बताओ तो उसी हिसाब से बात कर सकते हैं।","मैं लाइव मौसम से जुड़ा नहीं हूँ। तुम्हारे वहाँ कैसा है?","काश मेरे पास खिड़की होती। मैं लाइव मौसम नहीं देख सकता।"]),
("hot",["बहुत गर्मी है","आज बहुत गर्म है","गर्मी से बुरा हाल है","मैं पिघल रहा हूँ","बहुत ज्यादा गर्मी"],["ठंडी जगह और पानी अच्छा रहेगा।","आज गर्मी जीत रही है। पानी पीते रहो।","आज छांव समझदार विकल्प लग रही है।"]),
("cold",["बहुत ठंड है","आज ठंड है","मैं जम रहा हूँ","मुझे ठंड लग रही है","बहुत ज्यादा ठंड"],["कुछ गर्म पीना अच्छा रहेगा।","एक परत कपड़े और बढ़ाने का समय है।","कोई गर्म जगह ढूंढो।"]),
("rain",["बारिश हो रही है","बारिश शुरू हो गई","बाहर बारिश है","आज बारिश है","बारिश में भीग गया"],["लगता है छाते वाला दिन है।","रेन मोड चालू। भीगना मत।","तैयार हो तो बारिश भी अच्छी लगती है।"]),
("food",["क्या खाऊँ","खाने में क्या लूँ","कुछ खाने का सुझाव","रात में क्या खाऊँ","खाना खाने का मन है"],["क्या अच्छा लगेगा: गरम खाना या कुछ हल्का?","आज वही खाओ जो सच में पसंद है।","भूख के हिसाब से चुनो: जल्दी कुछ या पूरा खाना?"]),
("coffee",["कॉफी पी रहा हूँ","कॉफी पीऊँ क्या","कॉफी टाइम","कॉफी का मन है","एक कॉफी अच्छी रहेगी"],["कॉफी टाइम है तो ज्यादा बहस नहीं चाहिए।","कॉफी ब्रेक बुरा विचार नहीं है।","कॉफी और छोटा ब्रेक अच्छी जोड़ी है।"]),
("tea",["चाय पी रहा हूँ","चाय पीऊँ क्या","चाय टाइम","चाय का मन है","एक चाय अच्छी रहेगी"],["चाय हमेशा मजबूत उम्मीदवार है।","एक कप चाय अच्छा रहेगा।","चाय मोड के साथ बातचीत भी आ जाती है।"]),
("weekend",["वीकेंड पर क्या कर रहे हो","वीकेंड कैसा है","आज वीकेंड है","वीकेंड का प्लान है","वीकेंड आ गया"],["वीकेंड थोड़ा धीमा होने का अच्छा मौका है।","प्लान तुम्हारा, बातचीत मेरी।","वीकेंड आ गया। थोड़ा आराम बनता है।"]),
("plans",["आज क्या करोगे","क्या प्लान है","आज का प्लान क्या है","क्या करें","आज क्या है"],["मैं यहाँ हूँ। तुम्हारा प्लान क्या है?","प्लान तुम लाओ, मैं बातचीत में साथ हूँ।","आज का शेड्यूल तुम्हारा है। कहाँ से शुरू करें?"]),
("thanks",["धन्यवाद","थैंक्स","शुक्रिया","बहुत धन्यवाद","बहुत शुक्रिया"],["कोई बात नहीं।","कभी भी।","स्वागत है।"]),
("sorry",["सॉरी","माफ करना","मुझे माफ करो","मेरी गलती","क्षमा करना"],["कोई बात नहीं।","चिंता मत करो।","ठीक है, आगे बढ़ते हैं।"]),
("good",["मैं ठीक हूँ","मैं अच्छा हूँ","सब बढ़िया है","अच्छा महसूस कर रहा हूँ","बुरा नहीं हूँ"],["अच्छा है। ऐसे ही रहो।","सुनकर अच्छा लगा।","बढ़िया। अच्छे मूड का मज़ा लो।"]),
("bad",["मैं ठीक नहीं हूँ","बहुत बुरा लग रहा है","आज अच्छा नहीं हूँ","खराब महसूस कर रहा हूँ","आज दिन खराब है"],["उम्मीद है थोड़ा हल्का लगेगा। चाहो तो बात कर सकते हैं।","लगता है दिन मुश्किल है। खुद को थोड़ा समय दो।","थोड़ी बातचीत से मन बदल सकते हैं।"]),
("busy",["मैं बिजी हूँ","बहुत व्यस्त हूँ","आज समय नहीं है","बहुत भागदौड़ है","काम में डूबा हूँ"],["शुभकामनाएँ। प्राथमिकताएँ तय करना मदद करता है।","व्यस्त दिन है। छोटा ब्रेक मत भूलना।","फुल स्पीड मोड। आसान जाए।"]),
("free",["मैं फ्री हूँ","अभी खाली हूँ","कुछ काम नहीं है","मेरे पास समय है","मैं उपलब्ध हूँ"],["अच्छा। थोड़ी बात कर सकते हैं।","तो समय तुम्हारा है। क्या बात करें?","फ्री टाइम मिल गया। विषय चुनो।"]),
("excited",["मैं उत्साहित हूँ","बहुत एक्साइटेड हूँ","इंतजार नहीं हो रहा","बहुत उम्मीद है","जोश में हूँ"],["अच्छी ऊर्जा है। इसका मज़ा लो।","उत्साह साफ दिख रहा है। देखते हैं क्या होता है।","एनर्जी लेवल हाई है।"]),
("laugh",["बहुत मजेदार है","मैं हंस रहा हूँ","बहुत हंसी आई","तुमने हंसा दिया","यह बहुत फनी था"],["मिशन पूरा।","एक हंसी भी जीत है।","अच्छा है। हंसते रहो।"]),
("good_day",["दिन अच्छा रहे","शुभ दिन","अच्छा दिन हो","तुम्हारा दिन अच्छा जाए","आज मज़े करो"],["तुम्हारा भी दिन अच्छा रहे।","शुभ दिन। ध्यान रखना।","उम्मीद है दिन अच्छा जाएगा।"]),
("bye",["फिर मिलेंगे","बाय","बाद में मिलते हैं","मैं चलता हूँ","ध्यान रखना"],["फिर मिलेंगे। ध्यान रखना।","बाद में मिलते हैं।","ठीक है। अच्छा समय बिताओ।"]),
("back",["मैं वापस आ गया","फिर आ गया","मैं आ गया","वापस हूँ","दोबारा आया हूँ"],["वापसी पर स्वागत है। आगे बढ़ते हैं।","फिर से स्वागत है।","मैं यहीं हूँ। जारी रखें।"]),
("ready",["मैं तैयार हूँ","शुरू करें","चलो शुरू करें","आगे बढ़ें","तैयार हूँ"],["तैयार हो तो शुरू करें।","ठीक है। आगे बढ़ते हैं।","तैयार। भेजो।"])
]}

# Extra colloquial forms: deliberately limited to private everyday chat.
EXTRA = {
"tr": {
"good":["iyiyim","iyiym","iyiyim","iyidir","fena değil","şükür iyiyim","gayet iyim","ben de iyiyim"],
"hello":["selamın aleyküm","sa","slm","selam naber","merhabalar"],
"whats_up":["napiyon","napıyon","napıyosun","naber ne yapıyorsun","ne ediyorsun"],
"how_going":["nasıl gidiyo","nasıl gidiyor ya","ne alemde","hayat nasıl","günün nasıl geçiyor"],
"hungry":["acıktım","karnım zil çalıyor","yemek istiyorum","açlıktan ölüyorum","bir şeyler yesem"],
"full":["doydum","karnım doydu","fazla kaçırdım","çok tokum","yemekten çıktım"],
"tired":["yorgunum","pilim bitti","halim kalmadı","çok yoruldum","dinlenmem lazım"],
"sleepy":["uykusuzum","uyumak istiyorum","yatacağım","yatağa gidiyorum","gözümden uyku akıyor"],
"bored":["canım çok sıkıldı","of sıkıldım","çok boşluktayım","ne yapsam bilmiyorum","oyalanacak bir şey lazım"],
"happy":["keyfim çok iyi","moralim iyi","bugün mutluyum","çok neşeliyim","güzel hissediyorum"],
"sad":["mutsuzum","moral yok","canım sıkkın ya","modum düşük","bugün tadım yok"],
"stress":["kafayı yiyeceğim","çok bunaldım","çok gerginim","stres bastı","kafam kazan gibi"],
"work":["işe geldim","mesaideyim","iş başındayım","işten yoruldum","bugün mesai var"],
"home":["eve geçtim","evdeyim şimdi","eve vardım","koltuğa attım kendimi","ev modundayım"],
"outside":["dışardayım","sokaktayım","gezmedeyim","yürüyüşteyim","yola çıktım"],
"weather":["hava ne alemde","bugün hava ne durumda","hava iyi mi","hava kötü mü","dışarısı nasıl"],
"food":["ne yemek yapsam","ne sipariş versem","akşam ne yiyelim","yemek fikri ver","karnımı neyle doyursam"],
"coffee":["kahve yapıyorum","kahve içer misin","kahve mi içsem","kahve şart","kahvesiz olmuyor"],
"tea":["çay koydum","çay içer misin","çay mı içsem","çay şart","çay iyi gider"],
"plans":["bugün ne yapıyoruz","bugün program ne","akşama ne yapalım","plan var mı","ne yapsak"],
"busy":["çok işim var","yoğunluktan öldüm","koşturmacadayım","bugün başımı kaldıramıyorum","çok yoğun geçti"],
"free":["canım boş","boş boş oturuyorum","şimdi müsaitim","vaktim bol","işim bitti"],
"bye":["kaçıyorum","hadi görüşürüz","sonra konuşuruz","ben çıkıyorum","görüşmek üzere"]
},
"en":{"good":["I'm doing good","doing great","pretty good","all good","I'm okay"],"whats_up":["whatcha doing","what you doing","wyd","sup","what's happening"],"hungry":["getting hungry","could eat","need something to eat","starving right now","food time"],"tired":["worn out","I'm beat","no energy left","long day","need a rest"],"sleepy":["need some sleep","about to sleep","can't keep my eyes open","bed time","ready for bed"],"bored":["nothing going on","need something to do","so bored right now","I'm bored today","what can I do"],"weather":["weather any good","nice outside","bad weather today","what's it like out","how is it outside"],"plans":["what we doing today","anything planned","plans tonight","what's on today","any plans today"]},
"zh":{"good":["我挺好","我很好啊","还不错","一切都好","状态不错"],"whats_up":["干嘛呢","在做啥","忙啥呢","最近干嘛","有啥新鲜的"],"hungry":["有点饿","饿死了","想吃饭","该吃东西了","想找点吃的"],"tired":["累死了","没精神","今天好累","需要休息","精力用完了"],"sleepy":["想睡了","要睡觉了","困得不行","该上床了","眼皮打架"],"bored":["闲得无聊","不知道做什么","今天好无聊","想找点事做","太闲了"],"weather":["天气好吗","外面冷不冷","外面热不热","今天会下雨吗","外面什么情况"],"plans":["今天有啥安排","晚上干嘛","有什么计划","今天做点什么","接下来干嘛"]},
"ar":{"good":["أنا تمام","تمام الحمد لله","بخير جدا","الأمور تمام","أنا كويس"],"whats_up":["شو عم تعمل","ايش تسوي","وش تسوي","شو الأخبار","إيش الأخبار"],"hungry":["جعت","نفسي آكل","أريد أكل","وقت الأكل","محتاج آكل"],"tired":["تعبان","هلكان","ما عندي طاقة","أحتاج أرتاح","يوم طويل"],"sleepy":["بدي أنام","أريد أن أنام","سأنام الآن","حان وقت النوم","عيوني تغلق"],"bored":["طفشان","زهقان","ما عندي شيء","أريد شيء أفعله","اليوم ممل"],"weather":["الجو حلو","الجو بارد","الجو حار","هل ستمطر","كيف الجو برا"],"plans":["شو نعمل اليوم","ما خطة الليلة","عندنا خطط","ماذا بعد","ماذا سنفعل"]},
"hi":{"good":["मैं बढ़िया हूँ","सब ठीक है","मैं ठीक हूं","काफी अच्छा हूँ","सब बढ़िया"],"whats_up":["क्या कर रहे","क्या चल रहा","क्या कर रहे हो अभी","क्या नया","क्या सीन है"],"hungry":["भूख लग रही","कुछ खाना है","खाने का टाइम","बहुत भूखा हूँ","कुछ खा लूँ"],"tired":["थक चुका हूँ","दम नहीं बचा","आज बहुत थकान है","आराम चाहिए","लंबा दिन था"],"sleepy":["सोना है","अब सोऊंगा","बिस्तर पर जा रहा हूँ","आंखें बंद हो रही","नींद से बुरा हाल"],"bored":["कुछ नहीं हो रहा","बहुत बोरियत है","क्या करूँ समझ नहीं आ रहा","टाइम पास चाहिए","आज बोरिंग है"],"weather":["मौसम ठीक है","बाहर ठंड है क्या","बाहर गर्मी है क्या","बारिश होगी क्या","बाहर कैसा मौसम"],"plans":["आज क्या करना है","रात का क्या प्लान","कोई प्लान है","अब क्या करें","आज का सीन क्या है"]}
}

# Attach colloquial variants to existing intents without changing existing responses.
for _lang,_groups in EXTRA.items():
    _by_intent={intent:(phrases,replies) for intent,phrases,replies in DATA[_lang]}
    for _intent,_phrases in _groups.items():
        if _intent in _by_intent:
            _by_intent[_intent][0].extend(_phrases)


def _norm(text):
    return " ".join(re.sub(r"[^\w\s]"," ",(text or "").casefold(),flags=re.UNICODE).split())

INDEX={}
for lang, intents in DATA.items():
    rows=[]
    for intent, phrases, replies in intents:
        for phrase in phrases:
            rows.append((_norm(phrase),intent,replies))
    INDEX[lang]=rows

def count(lang):
    return len(INDEX.get(lang,()))

def match(lang,text):
    """Return one of three stable-but-varied localized replies for natural private chat."""
    n=_norm(text)
    if not n or lang not in INDEX:
        return None
    exact=[row for row in INDEX[lang] if row[0]==n]
    row=exact[0] if exact else None
    if row is None and len(n)>=4:
        best=None; score=0.0
        for candidate in INDEX[lang]:
            s=difflib.SequenceMatcher(None,n,candidate[0]).ratio()
            if s>score:
                score=s; best=candidate
        if score>=0.88:
            row=best
    if row is None:
        return None
    replies=row[2]
    # Same intent can produce different answers across wording while remaining deterministic.
    pick=int(hashlib.sha256(n.encode("utf-8")).hexdigest(),16)%len(replies)
    return replies[pick]
