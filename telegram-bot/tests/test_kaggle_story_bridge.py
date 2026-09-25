import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import muba_story_kaggle as bridge


class KaggleStoryBridgeTests(unittest.TestCase):
    def test_worker_receives_identity_and_approved_style_for_each_chapter(self):
        source=bridge._worker_source(b"reference",["one","two","three","four"])
        compile(source,"story_worker.py","exec")
        self.assertIn("image=[reference,style]",source)
        self.assertIn("change pose, action and background",source)
        self.assertNotIn("previous=pipe",source)

    def test_incomplete_or_malformed_batch_never_succeeds(self):
        calls=[]
        def fake_run(args,timeout=120):
            calls.append(args)
            if args[:2]==["kernels","status"]: return "complete"
            if args[:2]==["kernels","output"]:
                directory=Path(args[args.index("-p")+1])
                image=Image.new("RGB",(1024,576),"red")
                image.save(directory/"01.png")
            return ""
        with patch.object(bridge,"configured",return_value=True),patch.object(bridge,"_run",side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError,"missing 02.png"):
                bridge._generate(b"reference",["one","two","three","four"])
        self.assertTrue(any(args[:2]==["kernels","push"] for args in calls))


if __name__=="__main__": unittest.main()
