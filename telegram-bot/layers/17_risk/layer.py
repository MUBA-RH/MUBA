from layers.common import SpecialistLayer

def match(message, context):
    return None

LAYER = SpecialistLayer('risk', 100, match)
