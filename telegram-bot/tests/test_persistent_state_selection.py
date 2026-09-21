from __future__ import annotations
import os
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_brain

class PersistentStateSelectionTests(unittest.TestCase):
    def setUp(self):
        self.old_memory=os.environ.get("MUBA_MEMORY_FILE")
        self.old_gallery=os.environ.get("MUBA_GALLERY_DIR")
        os.environ.pop("MUBA_MEMORY_FILE",None)
        os.environ.pop("MUBA_GALLERY_DIR",None)

    def tearDown(self):
        if self.old_memory is None: os.environ.pop("MUBA_MEMORY_FILE",None)
        else: os.environ["MUBA_MEMORY_FILE"]=self.old_memory
        if self.old_gallery is None: os.environ.pop("MUBA_GALLERY_DIR",None)
        else: os.environ["MUBA_GALLERY_DIR"]=self.old_gallery

    def test_explicit_memory_file_wins(self):
        os.environ["MUBA_MEMORY_FILE"]="/tmp/muba-explicit.json"
        self.assertEqual(str(muba_brain._persistent_state_path()),"/tmp/muba-explicit.json")

    def test_gallery_persistent_root_supplies_state_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["MUBA_GALLERY_DIR"]=str(pathlib.Path(tmp)/"muba-gallery")
            expected=pathlib.Path(tmp).resolve()/"muba-state.json"
            self.assertEqual(muba_brain._persistent_state_path(),expected)
            status=muba_brain.state_storage_status()
            self.assertTrue(status["persistent"])
            self.assertEqual(status["backend"],"json")

if __name__=="__main__":
    unittest.main(verbosity=2)
