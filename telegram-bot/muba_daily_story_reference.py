"""Locked MUBA Daily Story reference/continuity layer.

This is the only identity source the Daily Story generator may use. The public
canonical asset URL points at the same MUBA master artwork used by the site.
Changing this layer is a deliberate DEV change; story prompts must never invent
or substitute another mascot.
"""
from muba_face_architecture import identity_prompt

REFERENCE_LAYER_VERSION="muba-daily-story-reference-v1"
REFERENCE_URL="https://pbs.twimg.com/profile_images/2096316602623156224/FZ7iqD2r.jpg"
REFERENCE_ROLE="identity-only"

REFERENCE_RULES=(
    "Always inspect and condition on the locked MUBA master reference before every Daily Story panel. "
    "The reference defines MUBA identity only: face geometry, enormous asymmetric white eyes, tiny dark nose, crooked mouth, hanging pink tongue, warm tan-brown short fur, black MUBA cap and black $MUBA hoodie. "
    "Never copy the reference background, purple neon ring, crown, camera crop or portrait composition into a story scene. "
    "Never substitute a cat, dog, hamster, bear, mouse, plush mascot or generic kawaii character. "
)

CONTINUITY_RULES=(
    "FOUR-PANEL CONTINUITY CONTRACT. First write one complete small story with a setup, action, consequence and payoff. "
    "Then split that exact story into panels 1, 2, 3 and 4. Panel N+1 must begin from the physical state left by panel N. "
    "Keep MUBA's clothing, face, body scale, recurring props, environment layout, time of day and lighting direction consistent. "
    "Do not create four unrelated illustrations. Do not reset the scene between panels. "
    "Every prompt must explicitly state the previous-panel state and the current action. "
)

def story_identity_prompt()->str:
    return identity_prompt()+" "+REFERENCE_RULES+" "+CONTINUITY_RULES
