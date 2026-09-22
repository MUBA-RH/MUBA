"""Living Story CHIBI character-anchor layer.

This module owns the Story character DNA and storyboard prompt contract only.
It is isolated from Studio, Gallery and all other MUBA visual systems.
"""

CHARACTER_DNA=(
    "RECURRING CHARACTER DNA — repeat unchanged in every panel: MUBA, tan/brown short dense fur; "
    "distinctive very large expressive eyes; tiny dark nose; playful small mouth/tongue when emotion calls for it; "
    "black MUBA cap; black hoodie marked $MUBA. Preserve these identity markers, not the source portrait composition. "
)

CHIBI_DNA=(
    "STRICT 2D JAPANESE CHIBI / SUPER-DEFORMED DNA: approximately 2-head-tall body, oversized rounded head, tiny pear-shaped torso, "
    "very short rounded limbs, simplified mitten-like hands and feet, almost no neck, huge low-set sparkling eyes, tiny nose, rounded cheeks. "
    "Clean thick manga line art, flat/soft cel shading, simple graphic shapes. Absolutely no photorealism, no 3D, no CGI, no plush/toy render. "
)

STORYBOARD_DNA=(
    "This is ONE four-beat sequential comic, not four portraits. The CHARACTER DNA stays fixed while ACTION, POSE, CAMERA and STORY STATE change. "
    "The named plot object and environment must carry the narrative. Use wide or medium full-body staging; the character should normally occupy "
    "roughly 20-45 percent of the frame. Preserve geography, lighting, recurring props and cause/effect. Exaggerate chibi emotion and physical pose. "
    "Never copy the identity reference pose, crop, camera, purple neon ring/crown, lighting or background. "
)

def character_anchor_prompt():
    """Prompt used only to establish a reusable Chibi MUBA identity anchor."""
    return (
        f"{CHARACTER_DNA} {CHIBI_DNA} "
        "Create a neutral reusable CHARACTER SHEET anchor, not a story panel: plain light background, full body, three-quarter view, "
        "relaxed neutral stance, identity readable, no scenery, no action, no text, no panel number, no watermark."
    )

def panel_prompt(title,premise,action,caption):
    return (
        f"{CHARACTER_DNA} {CHIBI_DNA} {STORYBOARD_DNA} "
        f"EPISODE: {title}. PLOT: {premise} CONTINUITY: sequential seconds/minutes. {action} "
        f'Tiny integrated story word/phrase only: "{caption}". '
        "The character reference is an IDENTITY ANCHOR only. Do not imitate its stance or framing. "
        "Prioritize the current action, visible plot object, exaggerated emotion and spatial environment. "
        "No panel number, no 01/02/03/04, no speech balloon, no extra writing, no watermark."
    )
