import json,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_worker_parses(): ast.parse((ROOT/"worker.py").read_text())
def test_bootstrap_parses(): ast.parse((ROOT/"kaggle_bootstrap.py").read_text())
def test_contract():
    cfg=json.loads((ROOT/"config.json").read_text()); wf=json.loads((ROOT/cfg["workflow"]).read_text())
    assert cfg["chapters"]==4 and cfg["independent_chapters"] is True
    assert cfg["previous_frame_conditioning"] is False
    assert cfg["output"]=={"width":1024,"height":576,"format":"png"}
    assert "CheckpointLoaderSimple" in {x["class_type"] for x in wf.values()}
    assert "SaveImage" in {x["class_type"] for x in wf.values()}
