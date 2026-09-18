from layers.common import SpecialistLayer, signal

def match(message, context):
    v=message.text.lower()
    if any(x in v for x in ('moderation','moderator','report this','moderatör','yönetime bildir','举报','管理','أبلغ المشرف','إشراف','मॉडरेशन','रिपोर्ट')):
        return signal('moderation','moderation',.82,'moderation request semantics')
    return None

LAYER = SpecialistLayer('moderation', 100, match)
