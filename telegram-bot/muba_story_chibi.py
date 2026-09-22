"""Living Story CHIBI-only visual layer.

Isolated from Studio, Gallery, and every general MUBA visual style.
Only THE LIVING STORY imports this policy.
"""
CHIBI_IDENTITY=(
    "LIVING STORY CHIBI ONLY. MUBA is the recurring actor, NOT the composition. Preserve only the minimum identity cues needed "
    "for recognizability: distinctive eye relationship, tan short fur, tiny nose, playful tongue when expression calls for it, "
    "black MUBA cap and black hoodie. Do NOT copy the reference pose, crop, camera angle, head scale, neon circle or portrait composition. "
    "Never replace MUBA with another character, but never let identity matching override the scene action. "
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
    "The four outputs are sequential panels of ONE chibi mini-story. STORY ACTION, STORY OBJECT and ENVIRONMENT are visually dominant; "
    "MUBA should usually occupy only about 20-45 percent of the frame, with full-body or action-oriented staging instead of close portraits. "
    "Preserve location, time, clothing, recurring objects and cause/effect continuity. The named plot object MUST be clearly visible whenever "
    "the action refers to it. Change camera distance, direction, body orientation and silhouette between panels. Every panel must advance the "
    "physical event and must NOT repeat the same standing pose. The identity reference's purple neon ring, crown, lighting and background are "
    "presentation decoration and MUST NOT be reproduced. "
)
def panel_prompt(title,premise,action,caption):
    return (
        f"{CHIBI_IDENTITY} {CHIBI_STYLE} {CHIBI_CONTINUITY} "
        f"EPISODE: {title}. PLOT: {premise} CONTINUITY: sequential seconds/minutes. {action} "
        f'Tiny integrated story word/phrase only: "{caption}". It must help carry the story into the next panel. '
        "No panel number, no 01/02/03/04, no speech balloon, no extra writing, no watermark. "
        "Use the MUBA reference only as a loose FACE/IDENTITY checksum. Prioritize the requested action, prop and environment over resemblance. "
        "Never center a large MUBA head. Never make a mascot portrait. Use wide/medium storytelling compositions and make the plot object readable."
    )
