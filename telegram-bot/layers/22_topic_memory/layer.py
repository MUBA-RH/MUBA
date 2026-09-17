from layers.common import SpecialistLayer

def match(message, context):
    return None

LAYER = SpecialistLayer('topic_memory', 100, match)
