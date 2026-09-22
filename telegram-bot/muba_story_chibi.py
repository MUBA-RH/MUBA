"""Living Story CHIBI character-anchor layer.

This module owns the Story character DNA and storyboard prompt contract only.
It is isolated from Studio, Gallery and all other MUBA visual systems.
"""

CHARACTER_DNA=(
    "MUBA CHARACTER IDENTITY ONLY: tan/brown short dense fur, distinctive huge expressive eyes, tiny dark nose, "
    "small playful mouth, black MUBA cap and black hoodie. Keep the same face, fur color and clothing in every panel. "
)

CHIBI_DNA=(
    "TRUE HAND-DRAWN 2D JAPANESE CHIBI / SUPER-DEFORMED ILLUSTRATION: exactly about 2 heads tall; oversized round head; "
    "tiny pear-shaped torso; very short rounded arms and legs; tiny simplified hands and feet; almost no neck; huge low-set eyes; "
    "rounded cheeks; bold clean manga outlines; flat cel colors with only one soft shadow tone. "
    "NO photorealism, NO realistic fur rendering, NO 3D, NO CGI, NO Pixar/Disney look, NO plush/toy, NO glossy render. "
)

STORYBOARD_DNA=(
    "SEQUENTIAL COMIC RULE: this image is one beat of the same four-scene story. Show a clear physical action, not a portrait. "
    "MUBA must be full-body or nearly full-body and only about 20-35 percent of the frame. The environment and plot object dominate the frame. "
    "Use ordinary natural daylight and a clean storybook environment. ABSOLUTELY NO purple neon ring, neon circle, halo, crown, dark purple studio backdrop, "
    "character-selection thumbnails, poster layout, UI, collage or portrait framing. ABSOLUTELY NO visible text, letters, numbers, captions, labels, "
    "signs, speech balloons, watermarks or pseudo-writing. "
)

def character_anchor_prompt():
    return (
        f"{CHARACTER_DNA} {CHIBI_DNA} "
        "Create a clean reusable 2D CHIBI character reference: full body, three-quarter view, relaxed standing pose, plain warm off-white background. "
        "No scenery, no action, no ring, no neon, no crown, no poster design, no extra text or watermark."
    )

def panel_prompt(title,premise,action,caption=None):
    return (
        f"{CHARACTER_DNA} {CHIBI_DNA} {STORYBOARD_DNA} "
        f"EPISODE: {title}. STORY CONTEXT: {premise} CURRENT BEAT: {action} "
        "The supplied reference is only for MUBA identity. Do not copy its background, camera, pose, lighting or composition. "
        "Keep recurring props, street layout, time of day and character design visually consistent with the other panels."
    )
