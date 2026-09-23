"""DEV-approved Daily Story character AND drawing-style reference.

The bundled image is the unmodified 1000307689.png upload approved on
2026-09-23. Its actual encoding is JPEG, so it is stored/sent as JPEG.
This contract is Story-only: it does not replace the Studio/site reference or
the shared face-architecture module. A missing/changed asset fails closed.
"""
import hashlib
from pathlib import Path

REFERENCE_LAYER_VERSION="muba-daily-story-approved-chibi-v2"
REFERENCE_PATH=Path(__file__).resolve().parent/"assets"/"daily-story"/"muba-approved-chibi-v2.jpg"
REFERENCE_SHA256="175a87e2331228d079487b7e0a1119c7a182649a72f877e3069407f16a8b88a0"
REFERENCE_CONTENT_TYPE="image/jpeg"
REFERENCE_ROLE="identity-and-style"
VISUAL_STYLE="living-story-approved-2d-chibi-v2"

REFERENCE_RULES=(
    "DEV-APPROVED MUBA 2D CHIBI REFERENCE: use the supplied image for BOTH character identity and drawing style in every panel. "
    "Preserve the broad rounded caramel head, compact cream lower-face patch, very large white oval eyes with black pupils and white highlights, "
    "tiny black nose, expressive black eyebrows, pink cheek patches, pink tongue, black MUBA baseball cap and plain black hoodie. "
    "Keep the same short rounded body, small hands and feet, and subtle short tail when visible. "
    "Expressions, gaze, mouth movement and poses follow the action; do not freeze the reference's expression or force the old portrait's divergent bulging-eye geometry. "
    "Match the reference's bold clean contours, warm muted colors and simple soft cel shading, not realistic fur, 3D or a generic replacement mascot. "
    "The street, green door, wooden box, paper scraps, plants, camera crop and pose are EXAMPLE SCENERY, not required content. "
    "Use them only when the current story actually calls for them. Never copy the reference composition into every scene. "
)

CONTINUITY_RULES=(
    "FOUR-PANEL CONTINUITY CONTRACT. First write one complete small story with a setup, action, consequence and payoff. "
    "Then split that exact story into panels 1, 2, 3 and 4. Panel N+1 must begin from the physical state left by panel N. "
    "Keep MUBA's clothing, face, body scale, recurring props, environment layout, time of day and lighting direction consistent. "
    "Do not create four unrelated illustrations. Do not reset the scene between panels. "
    "Every prompt must explicitly state the previous-panel state and the current action. "
)

def story_identity_prompt()->str:
    return REFERENCE_RULES+" "+CONTINUITY_RULES

def reference_metadata()->dict:
    return {"version":REFERENCE_LAYER_VERSION,"sha256":REFERENCE_SHA256,
            "role":REFERENCE_ROLE,"style":VISUAL_STYLE}

def load_reference()->tuple[bytes,str]:
    """Load the exact approved bytes; never fall back to an older/public image."""
    try:
        body=REFERENCE_PATH.read_bytes()
    except OSError as exc:
        raise RuntimeError("Approved MUBA Daily Story reference unavailable") from exc
    if hashlib.sha256(body).hexdigest()!=REFERENCE_SHA256:
        raise RuntimeError("Approved MUBA Daily Story reference checksum mismatch")
    return body,REFERENCE_CONTENT_TYPE
