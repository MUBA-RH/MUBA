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
    def test_output_rate_limit_retries_without_restarting_generation(self):
        attempts=[]
        def fake_run(args,timeout=120):
            attempts.append(args)
            if len(attempts)==1:
                raise RuntimeError("429 Client Error: Too Many Requests for url: ListKernelSessionOutput")
            return "downloaded"
        with patch.object(bridge,"_run",side_effect=fake_run),patch.object(bridge.time,"sleep") as pause:
            self.assertEqual(bridge._download_output("owner/kernel",Path("/tmp/output")),"downloaded")
        self.assertEqual(len(attempts),2)
        self.assertEqual(attempts[0],attempts[1])
        pause.assert_called_once_with(10)

    def test_worker_stages_comfyui_and_single_reference_conditioned_scene(self):
        source=bridge._worker_source(b"reference",["one"])
        compile(source,"story_worker.py","exec")
        self.assertIn("kaggle_bootstrap.py",source)
        self.assertIn('"--lowvram"',source)
        self.assertIn("reference.png",source)
        self.assertIn("'one'",source)
        self.assertIn('shutil.rmtree("/kaggle/working/ComfyUI"',source)
        self.assertNotIn("Qwen-Image-Edit",source)

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
            result=bridge._generate(b"reference",["one"])
            self.assertEqual(len(result),1)
        self.assertTrue(any(args[:2]==["kernels","push"] for args in calls))

    def test_rate_limited_download_resumes_completed_gpu_job_without_another_push(self):
        from state import MemoryRepository
        import muba_story
        store=MemoryRepository()
        calls=[]
        attempts=0
        def fake_run(args,timeout=120):
            nonlocal attempts
            calls.append(args)
            if args[:2]==["kernels","status"]: return "complete"
            if args[:2]==["kernels","output"]:
                attempts+=1
                if attempts==1: raise RuntimeError("429 Client Error: Too Many Requests for url: ListKernelSessionOutput")
                Image.new("RGB",(1024,576),"red").save(Path(args[args.index("-p")+1])/"01.png")
            return ""
        with patch.object(muba_story,"STORE",store),patch.object(bridge,"configured",return_value=True),patch.object(bridge,"_run",side_effect=fake_run),patch.object(bridge,"_download_output",side_effect=lambda kernel,out: fake_run(["kernels","output",kernel,"-p",str(out)])):
            with self.assertRaisesRegex(RuntimeError,"429"):
                bridge._generate(b"reference",["one"],day="2026-09-27")
            self.assertEqual(len(bridge._generate(b"reference",["one"],day="2026-09-27")),1)
        self.assertEqual(sum(args[:2]==["kernels","push"] for args in calls),1)

    def test_completed_legacy_run_can_be_adopted_without_pushing_again(self):
        from state import MemoryRepository
        import muba_story
        calls=[]
        def fake_run(args,timeout=120):
            calls.append(args)
            if args[:2]==["kernels","status"]: return "complete"
            if args[:2]==["kernels","output"]:
                Image.new("RGB",(1024,576),"red").save(Path(args[args.index("-p")+1])/"01.png")
            return ""
        with patch.object(muba_story,"STORE",MemoryRepository()),patch.object(bridge,"configured",return_value=True),patch.object(bridge,"_run",side_effect=fake_run):
            result=bridge._generate(b"reference",["one"],day="2026-09-26")
        self.assertEqual(len(result),1)
        self.assertFalse(any(args[:2]==["kernels","push"] for args in calls))


if __name__=="__main__": unittest.main()
