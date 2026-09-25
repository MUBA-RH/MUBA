#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT = Path("/kaggle/working/MUBA/daily-story-worker")
COMFY = Path("/kaggle/working/ComfyUI")
OUT = Path("/kaggle/working/muba-smoke-test")
OUT.mkdir(parents=True, exist_ok=True)

pngs = sorted(ROOT.glob("*.png"))
contract = ROOT / "muba_master_reference_v1.json"
required = [
    COMFY / "models/checkpoints/sd_xl_base_1.0.safetensors",
    COMFY / "models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
    COMFY / "models/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors",
    COMFY / "custom_nodes/comfyui-ipadapter-plus",
]

print("MUBA REFERENCE SMOKE TEST — PRE-FLIGHT")
print("Reference PNGs:", len(pngs))
for p in pngs:
    print(" OK", p.name, p.stat().st_size, "bytes")

assert len(pngs) >= 2, "Two MUBA reference PNGs are required"
assert contract.exists(), "muba_master_reference_v1.json missing"
for p in required:
    assert p.exists(), f"Missing required asset: {p}"

data = json.loads(contract.read_text())
manifest = {
    "status": "READY",
    "identity_contract": contract.name,
    "references": [p.name for p in pngs],
    "reference_primary": pngs[0].name,
    "reference_architecture": pngs[1].name,
    "comfyui": str(COMFY),
    "output": str(OUT),
}
(OUT / "preflight.json").write_text(json.dumps(manifest, indent=2))
print("Identity contract: OK")
print("SDXL + CLIP Vision + IPAdapter Plus: OK")
print("MUBA references staged: OK")
print("READY TO EXECUTE MUBA IDENTITY GENERATION")
print("Manifest:", OUT / "preflight.json")
