"""MUBA Daily Story identity and single-scene visual contract."""

def normalize_ready_image(body):
    """Accept one DEV-supplied landscape scene and return an archive-ready PNG."""
    import io
    from PIL import Image, ImageOps
    if len(body)>15_000_000: raise ValueError("Image is too large")
    with Image.open(io.BytesIO(body)) as original:
        image=ImageOps.exif_transpose(original)
        # Image services sometimes round a 16:9 edge to the nearest pixel.
        if image.width*image.height>12_000_000 or abs(image.width*9-image.height*16)>16:
            raise ValueError("A single 16:9 image is required")
        if image.width<512: raise ValueError("Image resolution is too small")
        out=io.BytesIO()
        image.convert("RGB").resize((1024,576),Image.Resampling.LANCZOS).save(out,format="PNG")
        return out.getvalue()

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
