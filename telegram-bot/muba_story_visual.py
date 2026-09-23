"""MUBA Daily Story visual contract — reference-first V3.

There is no bundled character/style reference. Every production batch requires
a fresh DEV-uploaded reference image for that Istanbul calendar day.
"""

VISUAL_STYLE="daily-story-reference-first-v3"
REFERENCE_ROLE="dev-upload-per-production"

REFERENCE_RULES=(
    "CURRENT DEV REFERENCE IS THE ONLY MUBA IDENTITY AND VISUAL-STYLE SOURCE. "
    "Match the supplied MUBA reference closely: face geometry, eye construction, nose, mouth/tongue, fur/skin palette, cap, clothing, body proportions, line/render language and overall visual character. "
    "Do not import any older MUBA drawing style, chibi template, realistic template, bundled asset or previous reference. "
    "The reference defines identity and visual language only; the story defines pose, expression, camera, environment, lighting and action. "
)

CONTINUITY_RULES=(
    "FOUR-IMAGE STORY CONTRACT. Produce four separate full-bleed 16:9 images, never a collage, grid, comic page or split frame. "
    "Together they tell one fluid daily story: 1 setup, 2 development, 3 consequence/turn, 4 payoff/ending. "
    "Image N+1 begins from the physical and narrative state left by image N. "
    "FACE/IDENTITY LOCK: all four images must depict the same MUBA from the current DEV reference. Identity geometry and visual language must not drift. "
    "Expressions, gaze, pose and camera may change naturally with the story. Recurring location, props, time and lighting remain coherent. "
    "No visible captions, speech bubbles, watermarks or invented writing; existing MUBA lettering visible in the supplied reference may remain. "
)

def story_identity_prompt():
    return REFERENCE_RULES+" "+CONTINUITY_RULES
