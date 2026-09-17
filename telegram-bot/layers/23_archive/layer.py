from layers.common import SpecialistLayer

def match(message, context):
    return None

LAYER = SpecialistLayer('archive', 100, match)
