"""Five localized paths to the existing, unchanged transparency pages."""

# Page order is shared by all five locales. Every existing page has one parent.
GROUP_PAGES = (
    (0, 8, 11, 13, 14),
    (1, 2, 3, 6, 18),
    (7, 15, 16),
    (4, 5, 12, 21),
    (9, 10, 17, 19, 20),
)
GROUP_LABELS = {
    "en": ("🧠 Ecosystem & structure", "💬 Assistant & languages", "🎨 Creation & publishing", "🛡️ Security & authority", "🔒 Information & continuity"),
    "tr": ("🧠 Ekosistem & yapı", "💬 Asistan & diller", "🎨 Üretim & yayın", "🛡️ Güvenlik & yetki", "🔒 Bilgi & süreklilik"),
    "zh": ("🧠 生态系统与结构", "💬 助手与语言", "🎨 创作与发布", "🛡️ 安全与权限", "🔒 信息与连续性"),
    "ar": ("🧠 النظام البيئي والبنية", "💬 المساعد واللغات", "🎨 الإبداع والنشر", "🛡️ الأمان والصلاحيات", "🔒 المعلومات والاستمرارية"),
    "hi": ("🧠 पारिस्थितिकी तंत्र और संरचना", "💬 सहायक और भाषाएँ", "🎨 निर्माण और प्रकाशन", "🛡️ सुरक्षा और अधिकार", "🔒 जानकारी और निरंतरता"),
}
GROUP_NAV = {
    "en": ("⬅️ Topic groups", "⬅️ Topics", "Previous", "Next", "Choose one of the five topic groups:"),
    "tr": ("⬅️ Konu grupları", "⬅️ Konular", "Önceki", "Sonraki", "Beş konu grubundan birini seç:"),
    "zh": ("⬅️ 主题组", "⬅️ 主题", "上一页", "下一页", "选择五个主题组之一："),
    "ar": ("⬅️ مجموعات المواضيع", "⬅️ المواضيع", "السابق", "التالي", "اختر إحدى مجموعات المواضيع الخمس:"),
    "hi": ("⬅️ विषय समूह", "⬅️ विषय", "पिछला", "अगला", "पाँच विषय समूहों में से एक चुनें:"),
}


def page_group(page):
    return next(index for index, pages in enumerate(GROUP_PAGES) if page in pages)
