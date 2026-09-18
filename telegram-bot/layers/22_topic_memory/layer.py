from layers.common import SpecialistLayer, signal

def match(message, context):
    v=message.text.lower()
    if any(x in v for x in ('topic memory','remember this topic','konu hafız','bu konuyu hatırla','主题记忆','记住这个主题','ذاكرة الموضوع','تذكر هذا الموضوع','विषय स्मृति','यह विषय याद')):
        return signal('topic_memory','topic_memory',.82,'topic-scoped memory semantics')
    return None

LAYER = SpecialistLayer('topic_memory', 100, match)
