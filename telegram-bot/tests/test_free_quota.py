"""Quota exhaustion pauses providers without taking the bot or web server down."""
import ast
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aiohttp import web
import aiohttp
from aiohttp.test_utils import TestClient, TestServer
import muba_free_quota as quota
from state import MemoryRepository
import muba_story_cloudflare as images
import muba_story_zerogpu as hf
import muba_story_kaggle as kaggle
from muba_runtime_text import runtime_text

class QuotaTests(unittest.TestCase):
    def setUp(self):
        self.store=MemoryRepository()
        for name,value in (('_backend',self.store),('_memory',{})):
            patch=mock.patch.object(quota,name,value)
            patch.start();self.addCleanup(patch.stop)

    def test_provider_isolation_and_automatic_expiry_on_next_request(self):
        with mock.patch.object(quota.time,'time',return_value=1000):
            with self.assertRaises(quota.ProviderQuotaPaused):
                quota.guard_response('huggingface',429,'quota exhausted',{'Retry-After':'10'})
            quota.ensure_available('cloudflare_ai')
            quota.ensure_available('r2')
            with self.assertRaises(quota.ProviderQuotaPaused):quota.ensure_available('huggingface')
        with mock.patch.object(quota.time,'time',return_value=1011):
            quota.ensure_available('huggingface')

    def test_permissions_and_network_errors_are_not_treated_as_quota(self):
        quota.guard_response('github',403,'permission denied')
        quota.guard_response('r2',500,'internal error')
        quota.guard_exception('kaggle',RuntimeError('connection refused'))
        quota.ensure_available('github');quota.ensure_available('r2');quota.ensure_available('kaggle')

    def test_github_rate_limit_respects_reset_and_does_not_store_error_payload(self):
        with self.assertRaises(quota.ProviderQuotaPaused):
            quota.guard_response('github',403,'rate limit: secret-example-token',{'X-RateLimit-Remaining':'0','X-RateLimit-Reset':str(time.time()+60)})
        row=self.store.get('provider_quota','github')
        self.assertEqual(set(row),{'until'})
        self.assertNotIn('secret-example-token',json.dumps(row))

    def test_shared_cloudflare_pause_prevents_text_call_after_image_quota(self):
        tree=ast.parse((ROOT/'muba_story_text.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_ask')
        scope={'aiohttp':aiohttp,'ensure_available':quota.ensure_available,'guard_response':quota.guard_response}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<story-text>','exec'),scope)
        response=mock.Mock(status=429,headers={})
        response.read=mock.AsyncMock(return_value=b'daily free allocation exceeded')
        context=mock.MagicMock()
        context.__aenter__=mock.AsyncMock(return_value=response)
        session=mock.Mock(post=mock.Mock(return_value=context))
        with mock.patch.dict(os.environ,{'CLOUDFLARE_ACCOUNT_ID':'test','CLOUDFLARE_API_TOKEN':'unit-test-only'}):
            with self.assertRaises(quota.ProviderQuotaPaused):
                asyncio.run(images._request(session,'scene'))
            with self.assertRaises(quota.ProviderQuotaPaused):
                asyncio.run(scope['_ask'](session,'https://example.invalid',{},'story',max_tokens=10))
        session.post.assert_called_once()

    def test_hf_gpu_exhaustion_does_not_keep_submitting_jobs(self):
        with mock.patch.object(hf,'_predict',side_effect=RuntimeError('GPU quota exhausted')) as predict:
            with self.assertRaises(quota.ProviderQuotaPaused):
                asyncio.run(hf.generate(None,'scene',b'reference'))
            with self.assertRaises(quota.ProviderQuotaPaused):
                asyncio.run(hf.generate(None,'scene',b'reference'))
            predict.assert_called_once()

    def test_kaggle_quota_does_not_resubmit_cli_job(self):
        process=mock.Mock(returncode=1,stderr='GPU quota exhausted',stdout='')
        with mock.patch.dict(os.environ,{'KAGGLE_API_TOKEN':'unit-test-only'}),mock.patch.object(kaggle.subprocess,'run',return_value=process) as run:
            with self.assertRaises(quota.ProviderQuotaPaused):kaggle._run(['kernels','push'])
            with self.assertRaises(quota.ProviderQuotaPaused):kaggle._run(['kernels','push'])
            run.assert_called_once()

    def test_native_camera_quota_does_not_send_image_or_consume_allowance(self):
        tree=ast.parse((ROOT/'bot_mention.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_run_muba_camera_transform')
        status=mock.Mock(message_id=1,edit_text=mock.AsyncMock())
        message=mock.Mock(reply_text=mock.AsyncMock(return_value=status),reply_photo=mock.AsyncMock())
        response=mock.Mock(status=429,headers={})
        response.read=mock.AsyncMock(return_value=b'daily free allocation exceeded')
        post_context=mock.MagicMock()
        post_context.__aenter__=mock.AsyncMock(return_value=response)
        session=mock.Mock(post=mock.Mock(return_value=post_context))
        context=mock.Mock(user_data={},application=mock.Mock(bot_data={'news_session':session}))
        consume=mock.Mock(return_value=True)
        scope={'get_assistant_language':lambda uid:'tr','runtime_text':runtime_text,'STUDIO_REFERENCE_FILE':mock.Mock(exists=lambda:True,read_bytes=lambda:b'reference'),'camera_reference_bytes':lambda value:value,'camera_output_size':lambda value:(1024,1024),'camera_ai_prompt':lambda request:request,'camera_ai_endpoint':lambda:'https://example.invalid','aiohttp':aiohttp,'os':os,'is_dev':lambda uid:False,'consume':consume,'ensure_available':quota.ensure_available,'guard_response':quota.guard_response,'ProviderQuotaPaused':quota.ProviderQuotaPaused,'logger':mock.Mock()}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<native-camera>','exec'),scope)
        with mock.patch.dict(os.environ,{'CLOUDFLARE_API_TOKEN':'unit-test-only'}):
            for _ in range(2):asyncio.run(scope['_run_muba_camera_transform'](message,context,71,b'source','scene'))
        session.post.assert_called_once()
        message.reply_photo.assert_not_awaited()
        consume.assert_not_called()
        self.assertIn(runtime_text('tr','provider_quota'),status.edit_text.await_args.args[0])

    def test_pause_survives_process_restart_on_same_storage(self):
        with tempfile.TemporaryDirectory() as temp:
            env=dict(os.environ,PYTHONPATH=str(ROOT),MUBA_QUOTA_STATE_FILE=str(Path(temp)/'quota.json'))
            subprocess.run([sys.executable,'-c',"import muba_free_quota as q\ntry:q.guard_response('kaggle',429,'quota exhausted')\nexcept q.ProviderQuotaPaused:pass"],env=env,check=True)
            output=subprocess.check_output([sys.executable,'-c',"import muba_free_quota as q\ntry:q.ensure_available('kaggle')\nexcept q.ProviderQuotaPaused:print('paused')"],env=env,text=True)
            self.assertEqual(output.strip(),'paused')

    def test_web_server_keeps_health_available_while_one_route_is_paused(self):
        tree=ast.parse((ROOT/'bot_mention.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='quota_pause_middleware')
        node.decorator_list=[]
        scope={'web':web,'ProviderQuotaPaused':quota.ProviderQuotaPaused,'_gallery_cors_headers':lambda:{}}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<quota-middleware>','exec'),scope)
        async def run():
            app=web.Application(middlewares=[web.middleware(scope['quota_pause_middleware'])])
            async def paused(request):raise quota.ProviderQuotaPaused('r2',time.time()+60)
            async def health(request):return web.Response(text='MUBA is alive.')
            app.router.add_get('/gallery',paused);app.router.add_get('/health',health)
            async with TestClient(TestServer(app)) as client:
                response=await client.get('/gallery')
                self.assertEqual(response.status,503)
                self.assertEqual((await response.json())['code'],'provider_quota')
                self.assertIn('Retry-After',response.headers)
                response=await client.get('/health')
                self.assertEqual(response.status,200)
                self.assertEqual(await response.text(),'MUBA is alive.')
        asyncio.run(run())

    def test_story_capacity_failure_has_no_secondary_provider_fallback(self):
        tree=ast.parse((ROOT/'bot_mention.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_story_generate_images_unlocked')
        imports=[n.module for n in ast.walk(node) if isinstance(n,ast.ImportFrom)]
        self.assertNotIn('muba_story_fallback',imports)

if __name__=='__main__':unittest.main()
