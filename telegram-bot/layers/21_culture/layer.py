from layers.common import SpecialistLayer

def match(message, context):
    return None

LAYER = SpecialistLayer('culture', 100, match)
