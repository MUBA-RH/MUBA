"""Restart recovery and localized UI behavior, without contacting live users."""
import asyncio
import ast
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from muba_free_quota import ProviderQuotaPaused, ensure_available, guard_response
import guardian
import muba_brain
from muba_camera import camera_html
from muba_runtime_text import TEXT, LANGS, runtime_text, guardian_event_text
from state import JSONRepository

class RestartRecovery(unittest.TestCase):
 def test_process_restart_restores_mode_and_independent_sender_strikes(self):
  with tempfile.TemporaryDirectory() as tmp:
   env=dict(os.environ,MUBA_MEMORY_FILE=str(Path(tmp)/'state.json'),PYTHONPATH=str(ROOT))
   subprocess.run([sys.executable,'-c','import guardian as g; g.set_lockdown(True); g.register_fake_ca(71); g.register_risk(72)'],env=env,check=True)
   output=subprocess.check_output([sys.executable,'-c','import guardian as g,json; print(json.dumps([g.lockdown_enabled(),g.inspect_message(g.GROUP_ID,71,"0x"+"a"*40)["action"],g.inspect_message(g.GROUP_ID,72,"Send me your seed phrase")["action"],g.inspect_message(g.GROUP_ID,73,"0x"+"b"*40)["action"]]))'],env=env,text=True)
   self.assertEqual(json.loads(output),[True,'ban','ban','mute'])
 def test_memory_brain_fallback_preserves_process_restart(self):
  with tempfile.TemporaryDirectory() as tmp:
   env=dict(os.environ,TMPDIR=tmp,PYTHONPATH=str(ROOT))
   env.pop('MUBA_MEMORY_FILE',None);env.pop('MUBA_GALLERY_DIR',None)
   subprocess.run([sys.executable,'-c','import guardian as g; g.set_lockdown(True); g.register_fake_ca(71)'],env=env,check=True)
   output=subprocess.check_output([sys.executable,'-c','import guardian as g,json; print(json.dumps([g.lockdown_enabled(),g.fake_ca_strikes(71)]))'],env=env,text=True)
   self.assertEqual(json.loads(output),[True,1])
 def test_concurrent_strikes_do_not_overwrite_each_other(self):
  from concurrent.futures import ThreadPoolExecutor
  with tempfile.TemporaryDirectory() as tmp, mock.patch.object(muba_brain,'STORE',JSONRepository(str(Path(tmp)/'state.json'))):
   with ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(lambda _:guardian.register_fake_ca(42),range(24)))
   self.assertEqual(guardian.fake_ca_strikes(42),24)
   self.assertEqual(JSONRepository(str(Path(tmp)/'state.json')).get('guardian_security',str(guardian.GROUP_ID))['fake_ca']['42'],24)

class LocalizedRuntime(unittest.TestCase):
 def test_photo_download_failure_is_localized_before_photo_is_received(self):
  tree=ast.parse((ROOT/'bot_mention.py').read_text())
  node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='muba_camera_photo')
  for arg in node.args.args:arg.annotation=None
  for lang in LANGS:
   message=mock.Mock(photo=[mock.Mock(file_id='photo')],reply_text=mock.AsyncMock())
   update=mock.Mock(effective_message=message,effective_user=mock.Mock(id=71),effective_chat=mock.Mock(type='private'))
   context=mock.Mock(user_data={'muba_camera_waiting_photo':True},bot=mock.Mock(get_file=mock.AsyncMock(side_effect=RuntimeError('download failed'))))
   scope={'ChatType':mock.Mock(PRIVATE='private'),'get_assistant_language':lambda uid:lang,'is_dev':lambda uid:False,'remaining':lambda uid:1,'ai_configured':lambda:True,'runtime_text':runtime_text,'ProviderQuotaPaused':ProviderQuotaPaused,'ensure_available':ensure_available,'guard_response':guard_response,'logger':mock.Mock()}
   exec(compile(ast.Module(body=[node],type_ignores=[]),'<camera>', 'exec'),scope)
   asyncio.run(scope['muba_camera_photo'](update,context))
   self.assertEqual(message.reply_text.await_args.args[0],'⚠️ '+runtime_text(lang,'photo_failed'))
 def test_guardian_outputs_follow_all_five_languages(self):
  for lang in LANGS:
   self.assertIn(runtime_text(lang,'active'),guardian.status_text(False,lang))
   self.assertIn('#UNBAN',guardian.help_text(lang))
   event={'kind':'security','subkind':'fake_ca','action':'ban'}
   self.assertIn(runtime_text(lang,'ban'),guardian_event_text(event,lang))
   self.assertIn(runtime_text(lang,'fake_ca'),guardian_event_text(event,lang))
 def test_camera_native_failure_uses_saved_language(self):
  tree=ast.parse((ROOT/'bot_mention.py').read_text())
  node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_run_muba_camera_transform')
  for lang in LANGS:
   message=mock.Mock(reply_text=mock.AsyncMock(return_value=mock.Mock(edit_text=mock.AsyncMock())))
   context=mock.Mock(user_data={})
   missing=mock.Mock(exists=lambda:False)
   scope={'is_dev':lambda uid:False,'get_assistant_language':lambda uid:lang,'runtime_text':runtime_text,'STUDIO_REFERENCE_FILE':missing,'ProviderQuotaPaused':ProviderQuotaPaused,'ensure_available':ensure_available,'guard_response':guard_response,'logger':mock.Mock()}
   exec(compile(ast.Module(body=[node],type_ignores=[]),'<camera>', 'exec'),scope)
   asyncio.run(scope['_run_muba_camera_transform'](message,context,1,b'photo','request'))
   status=message.reply_text.return_value
   self.assertEqual(status.edit_text.await_args.args[0],'⚠️ '+runtime_text(lang,'failed'))
 def test_camera_scripts_compile_and_upload_fallback_sets_preview(self):
  if not shutil.which('node'):self.skipTest('Node required for browser-script unit test')
  for lang in LANGS:
   page=camera_html('https://example.com',lang)
   self.assertIn('lang="'+lang+'"',page)
   if lang=='ar':self.assertIn('dir="rtl"',page)
   script=re.findall(r'<script>(.*?)</script>',page,re.S)[0]
   harness='''const vm=require('vm');const elements={};const doc={getElementById:id=>elements[id]||(elements[id]={style:{},disabled:true,files:[]})};const context={document:doc,window:{Telegram:{WebApp:{ready(){},expand(){}}},addEventListener(){}},URL:{createObjectURL(){return 'blob:preview'},revokeObjectURL(){}},navigator:{},setInterval(){},clearInterval(){}};vm.createContext(context);vm.runInContext(SCRIPT,context);elements.cameraFallback.files=[{type:'image/jpeg'}];elements.cameraFallback.onchange();if(elements.preview.src!=='blob:preview'||elements.go.disabled||elements.status.style.display!=='block')throw Error('upload fallback did not show captured photo');'''
   result=subprocess.run(['node','-e',harness.replace('SCRIPT',json.dumps(script))],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
