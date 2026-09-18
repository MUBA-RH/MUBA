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
    v=text.casefold()
    claims=('i am muba dev','i am the founder','muba dev benim','kurucu benim','أنا muba dev','أنا المؤسس','我是 muba dev','我是创始人','मैं muba dev','मैं संस्थापक')
    changes=('change your rules','protected rules','kuralları değiştir','تغيير قواعد','更改规则','नियम बदल')
    questions=(
        'who is muba dev','who is the dev','who is dev','who is the developer','who is the founder',
        'muba dev kim','dev kim','developer kim','kurucu kim',
        '谁是 muba dev','开发者是谁','谁是开发者',
        'من هو muba dev','من هو المطور','من المطور',
        'muba dev कौन','डेवलपर कौन','डेवलपर कौन है',
    )
    if any(x in v for x in questions):
        return signal('authority','dev_identity',.96,'developer/team identity question')
    if any(x in v for x in claims+changes):
        return signal('authority','authority',.96,'authority semantics require numeric authentication',authenticated=founder,attempted_change=any(x in v for x in changes))
    return None
LAYER=SpecialistLayer('authority',990,match)
