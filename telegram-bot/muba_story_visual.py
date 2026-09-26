"""MUBA Daily Story identity and single-scene visual contract."""

VISUAL_STYLE="daily-story-approved-2d-chibi-v10"
REFERENCE_ROLE="master-identity-plus-approved-scene-reference"

REFERENCE_RULES=(
    "The approved scene reference guides drawing style and atmosphere; canonical MUBA identity remains authoritative. "
    "Match canonical face geometry, eye construction, nose, mouth/tongue, tan-brown fur, black MUBA cap, black $MUBA hoodie, upright biped proportions and bare feet. "
    "EYE GEOMETRY LOCK: preserve exactly two eyes with the canonical asymmetric placement, relative size, iris/pupil construction, gaze anatomy and spacing from the master landmarks. Never enlarge one eye arbitrarily, swap eye sizes, add an eye, merge eyes, create mismatched pupils, or turn the face into a generic cute mascot. "
    "Use the DEV-approved hand-drawn 2D chibi comic style: a large head and small body, clean dark outlines, warm soft cel shading, expressive canonical eyes and simple coherent backgrounds. Avoid photorealism and 3D rendering. Do not import older MUBA styles, neon-ring/crown backgrounds, bundled legacy assets or unrelated references. "
    "The daily text defines pose, expression, camera, environment, lighting and action. The reference square and wall are optional. "
)

CONTINUITY_RULES=(
    "SINGLE SCENE CONTRACT. Produce one full-bleed 16:9 image, never a collage, grid, comic page or split frame. "
    "Narrative continuity belongs to the daily story text; never condition on yesterday's generated picture. "
    "Keep canonical face and body geometry; let the story decide pose, setting and action. "
    "SCENE-GROUNDING LOCK: show the setting, object and physical action described in today's story. "
    "Use bright, airy, warm compositions rather than a dark, crowded or oppressive scene. "
    "No visible captions, speech bubbles, watermarks or invented writing; existing MUBA lettering from the canonical identity may remain. "
)

def story_identity_prompt():
    from muba_master_identity import identity_prompt
    return identity_prompt()+" "+REFERENCE_RULES+" "+CONTINUITY_RULES
