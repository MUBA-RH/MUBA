"""Living Story CHIBI character-anchor layer.

This module owns the Story character DNA and storyboard prompt contract only.
It is isolated from Studio, Gallery and all other MUBA visual systems.
"""

from muba_daily_story_reference import story_identity_prompt

CHARACTER_DNA=(
    story_identity_prompt()+" "
    "The supplied artwork is already the approved 2D design: preserve it, do not re-interpret an older realistic portrait. "
)

CHIBI_DNA=(
    "TRUE HAND-DRAWN 2D JAPANESE CHIBI / SUPER-DEFORMED ILLUSTRATION: exactly about 2 heads tall; oversized round head; "
    "tiny pear-shaped torso; very short rounded arms and legs; tiny simplified hands and feet; almost no neck. Preserve the approved large white oval eyes, compact black pupils and face proportions. "
    "rounded cheeks; bold clean manga outlines; flat cel colors with only one soft shadow tone. "
    "NO photorealism, NO realistic fur rendering, NO 3D, NO CGI, NO Pixar/Disney look, NO plush/toy, NO glossy render. "
)

STORYBOARD_DNA=(
    "SEQUENTIAL STORY RULE: this file is exactly ONE scene/beat of the same four-image story. Render ONE continuous full-bleed 16:9 scene only. Never divide the canvas into panels, frames, boxes, strips, grids, collages, before/after views or multiple moments. Show one clear physical action, not a portrait. "
    "MUBA must be full-body or nearly full-body and only about 20-35 percent of the frame. The environment and plot object dominate the frame. "
    "VISUAL LANGUAGE V3: use the current supplied MUBA reference as the immutable identity anchor, then adapt camera, lighting, environment, expression and motion naturally to the story. The four outputs must feel like four consecutive shots from one illustrated film, not four independent redraws. Never force an older style over a newer DEV reference. "
    "Use story-appropriate natural light and a clean storybook environment in a landscape 16:9 frame. ABSOLUTELY NO purple neon ring, neon circle, halo, crown, dark purple studio backdrop, "
    "character-selection thumbnails, poster layout, UI, collage or portrait framing. NO visible text except the existing MUBA lettering on the cap; "
    "no captions, labels, signs, speech balloons, watermarks or pseudo-writing. Keep the hoodie plain black as in the approved reference. "
)

def character_anchor_prompt():
    return (
        f"{CHARACTER_DNA} {CHIBI_DNA} "
        "Create a clean reusable 2D CHIBI character reference: full body, three-quarter body pose but face readable almost front-on, relaxed standing pose, plain warm off-white background. Identity accuracy is more important than generic cuteness. "
        "No scenery, no action, no ring, no neon, no crown, no poster design, no extra text or watermark."
    )

def panel_prompt(title,premise,action,caption=None):
    return (
        f"{CHARACTER_DNA} {CHIBI_DNA} {STORYBOARD_DNA} "
        f"EPISODE: {title}. STORY CONTEXT: {premise} CURRENT BEAT: {action} "
        "REFERENCE GATE: generation requires the current DEV-supplied MUBA reference. If no current reference is available, stop and request it; never invent, substitute or silently fall back to another MUBA design. The supplied reference defines MUBA identity AND drawing style, not the plot. Do not copy its background, camera, pose, lighting or composition. "
        "Keep recurring props, street layout and time of day visually consistent with the other images. FACE LOCK: MUBA must remain recognizably the exact same approved character in every image; do not redesign or mutate the head, eyes, pupils, muzzle, nose, cheeks, mouth/tongue, cap, fur palette or proportions. Only story-required expression, gaze and pose may change."
    )
