"""Canonical MUBA visual identity architecture.

This is not human biometric recognition. It is a hand-authored character geometry
contract extracted from the canonical MUBA artwork and used to condition/validate
Living Story generations.
"""

FACE_ARCHITECTURE_VERSION="muba-face-architecture-v1"

FACE_ARCHITECTURE=(
    "CANONICAL MUBA FACE ARCHITECTURE — HARD IDENTITY CONSTRAINT. "
    "Head: broad rounded-square/soft trapezoid silhouette, noticeably wider through the cheeks than the forehead; very short lower face; no long muzzle. "
    "Eyes: the dominant feature, two enormous protruding near-spherical white eyes occupying most of the upper/middle face; deliberately asymmetric comic placement. "
    "Viewer-left eye sits higher and points up-left; viewer-right eye sits lower/farther outward and points down-right. Preserve very large white sclera around compact brown-black irises. "
    "Do NOT turn the eyes into small black chibi dots, almond eyes, symmetrical anime eyes, or ordinary animal eyes. "
    "Nose: extremely tiny dark brown/black nose centered low between the eyes; much smaller than either iris; short bridge. "
    "Muzzle: compact pale-tan muzzle pad around the tiny nose and mouth, integrated into the face rather than a protruding white hamster muzzle. "
    "Mouth: small crooked open smile below the nose; pink tongue hangs visibly downward from the center/right of the mouth. Tongue is a core identity marker. "
    "Cheeks/jaw: broad dense tan-brown furry cheeks taper into a very short rounded chin; no hamster pouches, no white beard, no canine snout. "
    "Fur: short dense warm medium-brown/tan fur, slightly darker around eye sockets and sides; muzzle only subtly lighter, never a large white mask. "
    "Ears: not identity-dominant; keep small/subtle and mostly hidden by cap/head silhouette. Never use large round mouse/hamster ears or pointed cat/dog ears. "
    "Cap: black low-profile baseball cap fitted close to the head. Clothing: black hoodie. "
    "Recognition priority: giant asymmetric bulging eyes > tiny nose > crooked mouth with hanging tongue > broad short furry face > black cap/hoodie. "
)

IDENTITY_NEGATIVES=(
    "IDENTITY REJECTION RULES: reject hamster, bear cub, mouse, cat, dog, fox, red panda, teddy bear, generic kawaii mascot; "
    "reject large round ears, pointed ears, long snout, white muzzle mask, symmetrical eyes, small dot eyes, rosy cheek circles, button nose, closed mouth, missing tongue. "
    "Never replace MUBA's eye geometry with conventional cute-animal proportions. "
)

def identity_prompt()->str:
    return FACE_ARCHITECTURE+" "+IDENTITY_NEGATIVES

def identity_checklist()->tuple[str,...]:
    return (
        "two enormous white protruding eyes",
        "intentional asymmetric eye placement/gaze",
        "tiny dark nose",
        "compact pale-tan muzzle without white mask",
        "crooked small mouth",
        "visible hanging pink tongue",
        "broad short tan-brown furry face",
        "ears small/subtle, not hamster-like",
        "black low-profile cap",
        "black hoodie",
    )
