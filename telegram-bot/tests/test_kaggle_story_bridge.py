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
        source=bridge._worker_source(b"reference",["one"],"https://private.example/upload")
        compile(source,"story_worker.py","exec")
        self.assertIn("kaggle_bootstrap.py",source)
        self.assertIn('"--lowvram"',source)
        self.assertIn("reference.png",source)
        self.assertIn("'one'",source)
        self.assertIn('shutil.rmtree("/kaggle/working/ComfyUI"',source)
        self.assertIn('method="PUT"',source)
        self.assertNotIn("Qwen-Image-Edit",source)

    def test_completed_gpu_image_arrives_from_private_archive_without_kaggle_output_listing(self):
        calls=[]
        image=io.BytesIO()
        Image.new("RGB",(1024,576),"red").save(image,format="PNG")
        reads=0
        def fake_run(args,timeout=120):
            calls.append(args)
            if args[:2]==["kernels","status"]: return "complete"
            return ""
        def read(key):
            nonlocal reads
            reads+=1
            return image.getvalue() if reads>1 else None
        with patch.object(bridge,"configured",return_value=True),patch.object(bridge,"_run",side_effect=fake_run),patch.object(bridge,"_r2_upload_url",return_value="https://private.example/upload"),patch.object(bridge,"_r2_image",side_effect=read):
            result=bridge._generate(b"reference",["one"],day="2026-09-27")
            self.assertEqual(len(result),1)
        self.assertTrue(any(args[:2]==["kernels","push"] for args in calls))
        self.assertFalse(any(args[:2]==["kernels","output"] for args in calls))

    def test_rate_limited_download_resumes_completed_gpu_job_without_another_push(self):
        from state import MemoryRepository
        import muba_story
        store=MemoryRepository()
        calls=[]
        attempts=0
        image=io.BytesIO()
        Image.new("RGB",(1024,576),"red").save(image,format="PNG")
        def fake_run(args,timeout=120):
            nonlocal attempts
            calls.append(args)
            if args[:2]==["kernels","status"]: return "complete"
            if args[:2]==["kernels","output"]:
                attempts+=1
                raise RuntimeError("429 Client Error: Too Many Requests for url: ListKernelSessionOutput")
            return ""
        with patch.object(muba_story,"STORE",store),patch.object(bridge,"configured",return_value=True),patch.object(bridge,"_run",side_effect=fake_run),patch.object(bridge,"_r2_upload_url",return_value="https://private.example/upload"),patch.object(bridge,"_r2_image",side_effect=[None]*5+[None,image.getvalue()]),patch.object(bridge,"_download_output",side_effect=lambda kernel,out: fake_run(["kernels","output",kernel,"-p",str(out)])),patch.object(bridge.time,"sleep"):
            with self.assertRaisesRegex(RuntimeError,"429"):
                bridge._generate(b"reference",["one"],day="2026-09-27")
            self.assertEqual(len(bridge._generate(b"reference",["one"],day="2026-09-27")),1)
        self.assertEqual(sum(args[:2]==["kernels","push"] for args in calls),1)

    def test_archived_image_is_reused_after_restart_without_a_kaggle_request(self):
        calls=[]
        image=io.BytesIO()
        Image.new("RGB",(1024,576),"red").save(image,format="PNG")
        with patch.object(bridge,"configured",return_value=True),patch.object(bridge,"_run",side_effect=lambda *a,**kw: calls.append(a)),patch.object(bridge,"_r2_image",return_value=image.getvalue()):
            result=bridge._generate(b"reference",["one"],day="2026-09-26")
        self.assertEqual(len(result),1)
        self.assertFalse(calls)

    def test_upload_url_is_scoped_to_one_private_object_without_exposing_credentials(self):
        from muba_gallery import _r2_config
        with patch("muba_gallery._r2_config",return_value={"account":"acct","access":"access","secret":"hidden","bucket":"bucket"}):
            url=bridge._r2_upload_url("daily-story/kaggle/2026-09-27/abc.png")
        self.assertIn("X-Amz-Signature=",url)
        self.assertIn("X-Amz-Expires=21600",url)
        self.assertIn("/bucket/daily-story/kaggle/2026-09-27/abc.png",url)
        self.assertNotIn("hidden",url)


if __name__=="__main__": unittest.main()
