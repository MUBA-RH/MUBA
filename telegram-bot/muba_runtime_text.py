"""Five-language Camera and Guardian runtime messages."""
LANGS=('en','tr','zh','ar','hi')
ROWS={
'provider_quota':('The provider quota is unavailable. Image generation is temporarily paused; your daily allowance was not used. Other MUBA areas remain available.','Sağlayıcı kotası kullanılamıyor. Görsel üretim geçici olarak duraklatıldı; günlük hakkın kullanılmadı. MUBA’nın diğer alanları çalışmaya devam ediyor.','服务商配额暂不可用。图片生成已暂停，未扣除你的每日次数。MUBA 其他功能仍可使用。','حصة المزوّد غير متاحة. أُوقف إنتاج الصور مؤقتاً دون استخدام فرصتك اليومية. تبقى بقية خدمات MUBA متاحة.','प्रदाता का कोटा उपलब्ध नहीं है। चित्र निर्माण अस्थायी रूप से रुका है; आपका दैनिक मौका नहीं कटा। MUBA के बाकी हिस्से उपलब्ध हैं।'),
'back':('⬅ MAIN MENU','⬅ ANA MENÜ','⬅ 主菜单','⬅ القائمة الرئيسية','⬅ मुख्य मेनू'),
'received':('Photo and request received ✓','Fotoğraf ve isteğin alındı ✓','已收到照片和请求 ✓','تم استلام الصورة والطلب ✓','फोटो और अनुरोध मिला ✓'),
'processing':('Preparing MUBA…','MUBA hazırlanıyor…','正在准备 MUBA…','جارٍ إعداد MUBA…','MUBA तैयार हो रहा है…'),
'sending':('Image created; sending to Telegram…','Görsel üretildi; Telegram’a gönderiliyor…','图片已生成，正在发送到 Telegram…','تم إنشاء الصورة؛ جارٍ إرسالها إلى Telegram…','चित्र बन गया; Telegram पर भेज रहे हैं…'),
'delivery_unconfirmed':('Image created, but Telegram delivery could not be confirmed. Check the chat before starting another generation.','Görsel üretildi, ancak Telegram teslimatı doğrulanamadı. Yeni üretim başlatmadan sohbeti kontrol et.','图片已生成，但无法确认 Telegram 是否已送达。再次生成前请检查聊天。','تم إنشاء الصورة، لكن تعذّر تأكيد تسليمها إلى Telegram. تحقق من المحادثة قبل إنشاء صورة أخرى.','चित्र बन गया, लेकिन Telegram पर पहुँचने की पुष्टि नहीं हुई। नया चित्र बनाने से पहले चैट देखें।'),
'ready':('Your MUBA is ready ✓',"MUBA’n hazır ✓",'你的 MUBA 已准备好 ✓','MUBA الخاص بك جاهز ✓','आपका MUBA तैयार है ✓'),
'privacy':('The source photo was not permanently saved by MUBA or published to Gallery.','Kaynak fotoğraf MUBA tarafından kalıcı kaydedilmedi; Gallery’ye yayınlanmadı.','MUBA 未永久保存原照片，也未将其发布到 Gallery。','لم يحفظ MUBA الصورة الأصلية بشكل دائم ولم ينشرها في Gallery.','MUBA ने मूल फोटो स्थायी रूप से नहीं सहेजी और Gallery में प्रकाशित नहीं की।'),
'failed':('Transformation failed. Your daily allowance was not used. Try again.','Dönüşüm başarısız. Günlük hakkın kullanılmadı; tekrar deneyebilirsin.','转换失败，未消耗每日次数。请重试。','فشل التحويل. لم تُستهلك فرصتك اليومية. حاول مجدداً.','रूपांतरण विफल हुआ। दैनिक मौका नहीं कटा। फिर कोशिश करें।'),
'photo_failed':('Could not receive the photo. Your daily allowance was not used.','Fotoğraf alınamadı. Günlük hakkın kullanılmadı.','无法接收照片，未消耗每日次数。','تعذر استلام الصورة. لم تُستهلك فرصتك اليومية.','फोटो नहीं मिली। दैनिक मौका नहीं कटा।'),
'photo_missing':('Photo unavailable. Open MUBA Camera again.','Fotoğraf bulunamadı. MUBA Camera’yı yeniden aç.','照片不可用。请重新打开 MUBA Camera。','الصورة غير متاحة. افتح MUBA Camera مجدداً.','फोटो उपलब्ध नहीं है। MUBA Camera फिर खोलें।'),
'request':('Briefly describe what you want in one message.','Ne istediğini tek mesajla kısaca yaz.','请用一条简短消息说明你的要求。','اكتب طلبك باختصار في رسالة واحدة.','एक संदेश में संक्षेप में अपना अनुरोध लिखें।'),
'permissions_failed':('Guardian could not change group permissions. Check bot admin permissions.','Guardian grup izinlerini değiştiremedi. Botun yönetici izinlerini kontrol et.','Guardian 无法修改群组权限。请检查机器人管理员权限。','تعذر على Guardian تغيير صلاحيات المجموعة. تحقق من صلاحيات إدارة البوت.','Guardian समूह की अनुमतियाँ नहीं बदल सका। बॉट की व्यवस्थापक अनुमतियाँ जाँचें।'),
'action_failed':('Guardian action could not be completed. Check bot admin permissions.','Guardian işlemi tamamlanamadı. Botun yönetici izinlerini kontrol et.','Guardian 操作未完成。请检查机器人管理员权限。','تعذر إكمال إجراء Guardian. تحقق من صلاحيات إدارة البوت.','Guardian की कार्रवाई पूरी नहीं हुई। बॉट की व्यवस्थापक अनुमतियाँ जाँचें।'),
'deleted':('Message deleted.','Mesaj silindi.','消息已删除。','تم حذف الرسالة.','संदेश हटा दिया गया।'),
'warning':('Guardian warning for','Guardian uyarısı:','Guardian 警告：','تحذير Guardian إلى','Guardian की चेतावनी:'),
'reply_user':("Reply to a user's message with {command}.",'{command} komutunu kullanıcının mesajına yanıt olarak gönder.','请回复用户消息并发送 {command}。','أرسل {command} رداً على رسالة المستخدم.','उपयोगकर्ता के संदेश का जवाब देकर {command} भेजें।'),
'dev_protected':('DEV is protected.','DEV korunuyor.','DEV 受保护。','DEV محمي.','DEV सुरक्षित है।'),
'ban':('User banned.','Kullanıcı yasaklandı.','用户已被封禁。','تم حظر المستخدم.','उपयोगकर्ता प्रतिबंधित है।'),
'mute':('User muted.','Kullanıcı susturuldu.','用户已被禁言。','تم كتم المستخدم.','उपयोगकर्ता म्यूट है।'),
'unmute':('User unmuted.','Kullanıcının susturması kaldırıldı.','用户禁言已解除。','تم إلغاء كتم المستخدم.','उपयोगकर्ता का म्यूट हटाया गया।'),
'unban':('User unbanned.','Kullanıcının yasağı kaldırıldı.','用户封禁已解除。','تم إلغاء حظر المستخدم.','उपयोगकर्ता का प्रतिबंध हटाया गया।'),
'unban_usage':('Use: #UNBAN <user_id>','Kullanım: #UNBAN <kullanıcı_id>','用法：#UNBAN <用户ID>','الاستخدام: #UNBAN <معرّف_المستخدم>','प्रयोग: #UNBAN <उपयोगकर्ता_ID>'),
'fake_ca':('Fake/unverified contract address detected.','Sahte/doğrulanmamış kontrat adresi tespit edildi.','检测到虚假或未经验证的合约地址。','تم اكتشاف عنوان عقد مزيف أو غير موثّق.','नकली या अप्रमाणित कॉन्ट्रैक्ट पता मिला।'),
'phishing':('High-risk phishing pattern detected.','Yüksek riskli kimlik avı tespit edildi.','检测到高风险钓鱼行为。','تم اكتشاف نمط تصيد عالي الخطورة.','उच्च जोखिम वाला फ़िशिंग पैटर्न मिला।'),
'credential_theft':('Credential-theft pattern detected.','Gizli giriş bilgilerini çalma girişimi tespit edildi.','检测到窃取凭据的行为。','تم اكتشاف محاولة سرقة بيانات الدخول.','गुप्त लॉगिन जानकारी चुराने का पैटर्न मिला।'),
'blocked_link':('Only official MUBA links are allowed.','Yalnızca resmî MUBA bağlantılarına izin verilir.','仅允许 MUBA 官方链接。','يُسمح فقط بروابط MUBA الرسمية.','केवल आधिकारिक MUBA लिंक की अनुमति है।'),
'scam':('Scam-like content detected. Trust only official MUBA sources.','Dolandırıcılık benzeri içerik tespit edildi. Yalnızca resmî MUBA kaynaklarına güven.','检测到疑似诈骗内容。请仅信任 MUBA 官方来源。','تم اكتشاف محتوى يشبه الاحتيال. ثق فقط بمصادر MUBA الرسمية.','धोखाधड़ी जैसा संदेश मिला। केवल आधिकारिक MUBA स्रोतों पर भरोसा करें।'),
'flood':('Flood/spam activity detected.','Tekrarlanan mesaj/spam tespit edildi.','检测到刷屏或垃圾消息。','تم اكتشاف رسائل متكررة أو مزعجة.','लगातार दोहराए गए या स्पैम संदेश मिले।'),
'ca_warning':('Do not trust unofficial contract addresses.','Resmî olmayan kontrat adreslerine güvenme.','不要信任非官方合约地址。','لا تثق بعناوين العقود غير الرسمية.','गैर-आधिकारिक कॉन्ट्रैक्ट पतों पर भरोसा न करें।'),
'soon':('Soon.','Yakında.','即将推出。','قريباً.','जल्द।'),
'active':('ACTIVE','AKTİF','运行中','نشط','सक्रिय'),
'paused':('PAUSED','DURAKLATILDI','已暂停','متوقف','रुका हुआ'),
'lockdown':('LOCKDOWN','SIKI KORUMA','严格保护','حماية مشددة','सख्त सुरक्षा'),
'normal':('NORMAL','NORMAL','正常','عادي','सामान्य'),
'status':('Main group: LOCKED\nCommand authority: MUBA DEV ONLY\nSecurity: {mode}','Ana grup: KORUNUYOR\nKomut yetkisi: YALNIZCA MUBA DEV\nGüvenlik: {mode}','主群：受保护\n命令权限：仅限 MUBA DEV\n安全模式：{mode}','المجموعة الرئيسية: محمية\nصلاحية الأوامر: MUBA DEV فقط\nالأمان: {mode}','मुख्य समूह: सुरक्षित\nकमांड अधिकार: केवल MUBA DEV\nसुरक्षा: {mode}'),
'security':('','Güvenlik: {state}\nMod: {mode}\nSahte kontrat: ilk ihlal=SUSTUR / tekrar=YASAKLA\nHarici bağlantılar: SİL\nSpam denetimi: AÇIK\nDenetim duraklatılmışsa #START ile başlar.','安全状态：{state}\n模式：{mode}\n虚假合约：首次禁言，再次封禁\n外部链接：删除\n刷屏检测：启用\n暂停后用 #START 恢复。','الأمان: {state}\nالوضع: {mode}\nالعقد المزيف: كتم أول مرة وحظر عند التكرار\nالروابط الخارجية: حذف\nكشف الرسائل المزعجة: مفعّل\nاستأنف الحماية المتوقفة باستخدام #START.','सुरक्षा: {state}\nमोड: {mode}\nनकली कॉन्ट्रैक्ट: पहली बार म्यूट, दोबारा प्रतिबंध\nबाहरी लिंक: हटाएँ\nस्पैम जाँच: चालू\nरुकी सुरक्षा #START से फिर चालू करें।'),
'help':('','#START / #STOP — başlat / duraklat\n#STATUS / #GUARDIAN — durum\n#SECURITY — güvenlik\n#LOCKDOWN / #NORMAL — koruma modu\n#WARN — yanıtlanan kullanıcıyı uyar\n#MUTE / #UNMUTE — sustur / kaldır\n#BAN — yanıtlanan kullanıcıyı yasakla\n#UNBAN <kullanıcı_id> — yasağı kaldır\n#DELETE — yanıtlanan mesajı sil\n#HELP — komut listesi','#START / #STOP — 启动 / 暂停\n#STATUS / #GUARDIAN — 状态\n#SECURITY — 安全\n#LOCKDOWN / #NORMAL — 保护模式\n#WARN — 警告所回复的用户\n#MUTE / #UNMUTE — 禁言 / 解除\n#BAN — 封禁所回复的用户\n#UNBAN <用户ID> — 解除封禁\n#DELETE — 删除所回复的消息\n#HELP — 命令列表','#START / #STOP — تشغيل / إيقاف\n#STATUS / #GUARDIAN — الحالة\n#SECURITY — الأمان\n#LOCKDOWN / #NORMAL — وضع الحماية\n#WARN — تحذير المستخدم المردود عليه\n#MUTE / #UNMUTE — كتم / إلغاء الكتم\n#BAN — حظر المستخدم المردود عليه\n#UNBAN <معرّف_المستخدم> — إلغاء الحظر\n#DELETE — حذف الرسالة المردود عليها\n#HELP — قائمة الأوامر','#START / #STOP — चालू / रोकें\n#STATUS / #GUARDIAN — स्थिति\n#SECURITY — सुरक्षा\n#LOCKDOWN / #NORMAL — सुरक्षा मोड\n#WARN — जवाब दिए उपयोगकर्ता को चेतावनी\n#MUTE / #UNMUTE — म्यूट / हटाएँ\n#BAN — जवाब दिए उपयोगकर्ता पर प्रतिबंध\n#UNBAN <उपयोगकर्ता_ID> — प्रतिबंध हटाएँ\n#DELETE — जवाब दिए संदेश को हटाएँ\n#HELP — कमांड सूची'),
}
TEXT={lang:{key:values[i] for key,values in ROWS.items()} for i,lang in enumerate(LANGS)}
def runtime_text(lang,key,**values):
 return TEXT.get(lang,TEXT['en'])[key].format(**values)
def guardian_status(paused,lockdown,lang='en',security=False):
 state=runtime_text(lang,'paused' if paused else 'active')
 mode=runtime_text(lang,'lockdown' if lockdown else 'normal')
 if security:return '🛡️ '+runtime_text(lang,'security',state=state,mode=mode)
 return '🛡️ GUARDIAN — '+state+'\n'+runtime_text(lang,'status',mode=mode)
def guardian_help(lang):return '🛡️ GUARDIAN\n'+runtime_text(lang,'help')
def guardian_event_text(event,lang):
 key=event.get('subkind') or ('flood' if event['kind']=='flood' else 'scam')
 if key not in TEXT['en']:key='scam'
 result='🛡️ GUARDIAN: '+runtime_text(lang,key)
 if event.get('action') in ('mute','ban'):result+=' '+runtime_text(lang,event['action'])
 return result

MORE={
'dev_here':('MUBA DEV is here','MUBA DEV burada','MUBA DEV 在这里','MUBA DEV هنا','MUBA DEV यहाँ है'),
'community':('MUBA community','MUBA topluluğu','MUBA 社区','مجتمع MUBA','MUBA समुदाय'),
'unauthorized_deleted':('Unauthorized command message deleted.','Yetkisiz komut mesajı silindi.','未经授权的命令消息已删除。','تم حذف رسالة أمر غير مصرح به.','अनधिकृत कमांड संदेश हटा दिया गया।'),
'protected_admin':('Automatic moderation skipped for protected/admin user.','Otomatik moderasyon korunan/yönetici kullanıcı için uygulanmadı.','未对受保护用户或管理员执行自动管理。','لم تُطبّق الإدارة التلقائية على المستخدم المحمي أو المسؤول.','सुरक्षित उपयोगकर्ता या व्यवस्थापक पर स्वचालित कार्रवाई नहीं की गई।'),
}
for i,lang in enumerate(LANGS):
 for key,values in MORE.items():TEXT[lang][key]=values[i]
DETAIL_KEYS={
'Grup izinleri değiştirilemedi.':'permissions_failed',
'Manuel Guardian işlemi tamamlanamadı.':'action_failed',
'Yetkisiz Guardian komut girişimi silindi.':'unauthorized_deleted',
'Yetkisiz komut mesajı silinemedi.':'action_failed',
'Guardian bağlantı silme işlemi tamamlanamadı.':'action_failed',
'Otomatik moderasyon korunan/admin kullanıcı için uygulanmadı.':'protected_admin',
'Otomatik Guardian moderasyonu tamamlanamadı.':'action_failed',
}
def guardian_detail(detail,lang):
 if detail in DETAIL_KEYS:return runtime_text(lang,DETAIL_KEYS[detail])
 return detail or ''

TEXT['en']['help']='#START / #STOP — resume / pause\n#STATUS / #GUARDIAN — status\n#SECURITY — security\n#LOCKDOWN / #NORMAL — protection mode\n#WARN — warn replied user\n#MUTE / #UNMUTE — mute / unmute\n#BAN — ban replied user\n#UNBAN <user_id> — unban user\n#DELETE — delete replied message\n#HELP — command list'
TEXT['en']['security']='Security: {state}\nMode: {mode}\nFake CA: first=MUTE / repeat=BAN\nExternal links: DELETE\nFlood detection: ON\nResume paused protection with #START.'

CAMERA_ERRORS={
'quota_used':('Daily MUBA Camera allowance used — 1/1.','Günlük MUBA Camera hakkın kullanıldı — 1/1.','每日 MUBA Camera 次数已用完 — 1/1。','تم استهلاك فرصة MUBA Camera اليومية — 1/1.','दैनिक MUBA Camera मौका इस्तेमाल हो गया — 1/1।'),
'ai_unavailable':('MUBA AI is not ready. Your daily allowance was not used.','MUBA AI hazır değil. Günlük hakkın kullanılmadı.','MUBA AI 尚未就绪。未消耗每日次数。','MUBA AI غير جاهز. لم تُستهلك فرصتك اليومية.','MUBA AI तैयार नहीं है। दैनिक मौका नहीं कटा।'),
}
for i,lang in enumerate(LANGS):
 for key,values in CAMERA_ERRORS.items():TEXT[lang][key]=values[i]
