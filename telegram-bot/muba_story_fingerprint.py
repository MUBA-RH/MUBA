"""MUBA Daily Story reference fingerprint."""
from __future__ import annotations
import hashlib, json
from io import BytesIO
from PIL import Image, ImageOps, ImageStat

VERSION="muba-reference-fingerprint-v1"

def build(reference_bytes:bytes)->dict:
    with Image.open(BytesIO(reference_bytes)) as source:
        image=ImageOps.exif_transpose(source).convert("RGB")
        width,height=image.size
        stat=ImageStat.Stat(image)
        center=image.getpixel((width//2,height//2))
        thumb=image.resize((32,32),Image.Resampling.LANCZOS)
        digest=hashlib.sha256(reference_bytes).hexdigest()
        return {"version":VERSION,"source_sha256":digest,
                "pixel_matrix_sha256_32x32_rgb":hashlib.sha256(thumb.tobytes()).hexdigest(),
                "width":width,"height":height,"mode":"RGB","center_rgb":list(center),
                "mean_rgb":[round(v,3) for v in stat.mean[:3]],"binary_sha256":digest}

def canonical_json(fingerprint:dict)->str:
    return json.dumps(fingerprint,sort_keys=True,separators=(",",":"))

def matches(reference_bytes:bytes,fingerprint:dict)->bool:
    return build(reference_bytes)==fingerprint
