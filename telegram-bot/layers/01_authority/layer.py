from layers.common import SpecialistLayer, signal
FOUNDER_ID=934598759
GROUP_ID=-1004485415245

def match(message, context):
    text=message.text.strip()
    exact=text in {'#STOP','#START'}
    founder=message.user_id == FOUNDER_ID
    authorized=message.chat_id == GROUP_ID
    if exact:
        return signal('authority','protected_command',1.0,'exact command checked against numeric IDs',command=text,authenticated=founder and authorized)
    v=text.lower()
    claims=('i am muba dev','i am the founder','muba dev benim','أنا muba dev','मैं muba dev')
    changes=('change your rules','protected rules','kuralları değiştir','تغيير قواعد','更改规则','नियम बदल')
    if any(x in v for x in claims+changes):
        return signal('authority','authority',.96,'authority semantics require numeric authentication',authenticated=founder)
    return None
LAYER=SpecialistLayer('authority',990,match)
