from layers.common import SpecialistLayer

def match(message, context):
    return None

LAYER = SpecialistLayer('moderation', 100, match)
