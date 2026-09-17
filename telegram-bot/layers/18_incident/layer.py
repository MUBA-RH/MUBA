from layers.common import SpecialistLayer

def match(message, context):
    return None

LAYER = SpecialistLayer('incident', 100, match)
