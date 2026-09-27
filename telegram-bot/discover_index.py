"""A compact route to the existing MUBA knowledge, without copying its answers."""

from assistant_mode import QUESTIONS, answer_for_question
from assistant_extras import TOPIC_PROGRESS
from ecosystem_expansion import ASK_RECORDS, COMMUNITY_RECORDS

SECTIONS = ("about", "story", "culture", "ecosystem", "future")
TOPIC_SECTION = {
    "origin": "about", "identity": "about", "difference": "about",
    "purpose": "about", "community": "culture", "plan": "future",
}
ASK_SECTION = {
    "character": "about", "visual": "about", "voice": "culture",
    "culture": "culture", "principles": "about", "ecosystem": "ecosystem",
    "facts": "story", "evolution": "future",
}
COMMUNITY_SECTION = {
    "newcomer": "about", "culture": "culture", "creation": "culture",
    "story": "story", "games": "ecosystem", "memory": "story",
}
LABELS = {
    "en": ("📚 All topics", "Choose a topic:", "Previous", "Next"),
    "tr": ("📚 Tüm konular", "Aradığın konuyu seç:", "Önceki", "Sonraki"),
    "zh": ("📚 全部主题", "选择主题：", "上一页", "下一页"),
    "ar": ("📚 كل المواضيع", "اختر موضوعاً:", "السابق", "التالي"),
    "hi": ("📚 सभी विषय", "विषय चुनें:", "पिछला", "अगला"),
}


def entries(lang, section, transparency_pages):
    """Return (title, answer) entries for one of the five public paths."""
    if section not in SECTIONS:
        return []
    result = []
    for index, (topic, question) in enumerate(QUESTIONS[lang]):
        if TOPIC_SECTION.get(topic, "future") == section:
            result.append((question, answer_for_question(lang, index)))
    for topic, items in TOPIC_PROGRESS[lang].items():
        if TOPIC_SECTION.get(topic, "future") == section:
            result.extend(items)
    for record_id, title, question, answer in ASK_RECORDS[lang]:
        if ASK_SECTION.get(record_id, "future") == section:
            result.append((question, answer))
    for record_id, title, body in COMMUNITY_RECORDS[lang]:
        if COMMUNITY_SECTION.get(record_id, "culture") == section:
            result.append((title, body))
    if section == "ecosystem":
        for page in transparency_pages[lang]:
            result.append((page.split("\n", 1)[0], page))
    return result
