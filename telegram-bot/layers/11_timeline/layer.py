from layers.common import SpecialistLayer

def match(message, context):
    return None

LAYER = SpecialistLayer('timeline', 100, match)
