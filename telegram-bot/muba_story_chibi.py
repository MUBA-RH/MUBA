"""Living Story CHIBI-only visual layer.

Isolated from Studio, Gallery, and every general MUBA visual style.
Only THE LIVING STORY imports this policy.
"""
CHIBI_IDENTITY=(
    "LIVING STORY CHIBI ONLY. Preserve MUBA's original facial identity and recognizability: "
    "same distinctive huge expressive eyes, tan short dense fur, tiny nose, playful tongue, black MUBA cap and black hoodie. "
    "Never replace MUBA with a generic animal, plush mascot or another character. "
)
CHIBI_STYLE=(
    "Render ONLY as polished Japanese chibi / super-deformed (SD) illustration. Use approximately 2-to-2.5-head-tall proportions: "
    "oversized head, very small soft rounded body, short simplified limbs, rounded hands/feet, soft cheeks and extremely expressive eyes. "
    "Keep the face recognizably MUBA while freely posing the compact body. MUBA may face left, right, up or down, lean, tumble, turn, "
    "run, crouch, jump or appear upside-down when the action needs it. Use clean manga/anime linework, refined cel shading and only a "
    "light digital-painted finish. High-quality illustration; not photorealistic, not 3D, not CGI, not plush/toy, not standard-proportion "
    "anime, and not any non-chibi style. "
)
CHIBI_CONTINUITY=(
    "The four outputs are sequential panels of ONE chibi mini-story. Preserve the same location, time, clothing, recurring objects and "
    "cause/effect continuity. Every panel must show a new action beat, never a repeated portrait. The identity reference's purple neon "
    "ring, crown and background are presentation decoration and MUST NOT be reproduced. "
)
def panel_prompt(title,premise,action,caption):
    return (
        f"{CHIBI_IDENTITY} {CHIBI_STYLE} {CHIBI_CONTINUITY} "
        f"EPISODE: {title}. PLOT: {premise} CONTINUITY: sequential seconds/minutes. {action} "
        f'Tiny integrated story word/phrase only: "{caption}". It must help carry the story into the next panel. '
        "No panel number, no 01/02/03/04, no speech balloon, no extra writing, no watermark. "
        "Use the MUBA reference for FACE/IDENTITY only; compose a real chibi action scene, never a centered mascot portrait."
    )
