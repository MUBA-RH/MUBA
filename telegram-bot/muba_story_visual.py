"""MUBA Daily Story visual contract — Master Identity + Chapter Engine V8.

The master identity is immutable. A fresh DEV reference can guide the current
production batch, while narrative continuity is carried by Story State rather
than by copying pixels or composition from a previous generated frame.
"""

VISUAL_STYLE="daily-story-approved-2d-chibi-v10"
REFERENCE_ROLE="master-identity-plus-daily-reference"

REFERENCE_RULES=(
    "CURRENT DEV REFERENCE is a batch visual guide; canonical MUBA identity remains authoritative. "
    "Its deterministic fingerprint must remain bound to the entire four-chapter batch. "
    "Match canonical face geometry, eye construction, nose, mouth/tongue, tan-brown fur, black MUBA cap, black $MUBA hoodie, upright biped proportions and bare feet. "
    "EYE GEOMETRY LOCK: preserve exactly two eyes with the canonical asymmetric placement, relative size, iris/pupil construction, gaze anatomy and spacing from the master landmarks. Never enlarge one eye arbitrarily, swap eye sizes, add an eye, merge eyes, create mismatched pupils, or turn the face into a generic cute mascot. "
    "Use the DEV-approved hand-drawn 2D chibi comic style: a large head and small body, clean dark outlines, warm soft cel shading, expressive canonical eyes and simple coherent backgrounds. Avoid photorealism and 3D rendering. Do not import older MUBA styles, neon-ring/crown backgrounds, bundled legacy assets or unrelated references. "
    "The reference guides visual language; Story State and the current chapter define pose, expression, camera, environment, lighting and action. "
)

CONTINUITY_RULES=(
    "FOUR-CHAPTER STORY CONTRACT. Produce four separate full-bleed 16:9 images, never a collage, grid, comic page or split frame. "
    "Together they tell one fluid daily story: chapter 1 setup, chapter 2 development, chapter 3 consequence/turn, chapter 4 payoff/ending. "
    "CHAPTER ISOLATION: generate exactly one image for the current chapter. Never copy a previous frame composition and never combine multiple chapters in one image. "
    "NARRATIVE CONTINUITY comes from Story State: location, important object, resolved event, unresolved thread and next-day hook. "
    "FACE/BODY IDENTITY LOCK: all four images depict the same canonical MUBA; identity geometry and visual language must not drift. "
    "Expression, pose, camera, environment and lighting may change naturally with each chapter, but eye anatomy and identity geometry stay locked. "
    "SCENE-GROUNDING LOCK: the chapter-specific required object, location and physical action must be clearly visible. A neutral standing portrait is invalid when the chapter describes discovery, map study, travel/climbing or reward discovery. "
    "No visible captions, speech bubbles, watermarks or invented writing; existing MUBA lettering from the canonical identity may remain. "
)

def story_identity_prompt():
    from muba_master_identity import identity_prompt
    return identity_prompt()+" "+REFERENCE_RULES+" "+CONTINUITY_RULES
