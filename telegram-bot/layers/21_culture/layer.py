from layers.common import SpecialistLayer, signal

def match(message, context):
    v=message.text.lower()
    if any(x in v for x in ('meme culture','slang','inside joke','meme kültür','argo','梗文化','俚语','ثقافة الميم','عامية','मीम संस्कृति','स्लैंग')):
        return signal('culture','culture',.72,'low-risk culture semantics')
    return None

LAYER = SpecialistLayer('culture', 100, match)
