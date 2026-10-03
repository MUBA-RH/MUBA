"""Exercise Camera request forwarding and reference preparation without live AI calls."""
import ast
import asyncio
import io
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

import aiohttp
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from muba_studio import camera_ai_prompt, camera_ai_endpoint, camera_output_size, camera_reference_bytes, clean_camera_prompt, clean_prompt, ai_endpoint, AI_MODEL, CAMERA_AI_MODEL
from muba_runtime_text import runtime_text
import muba_free_quota as free_quota
from muba_free_quota import ProviderQuotaPaused, ensure_available, guard_response
from state import MemoryRepository

def photo(color,size=(80,120),orientation=None):
    image=Image.new('RGB',size,color)
    exif=Image.Exif()
    if orientation:exif[274]=orientation
    out=io.BytesIO()
    image.save(out,'JPEG',exif=exif)
    return out.getvalue()

def handler(name,scope):
    tree=ast.parse((ROOT/'bot_mention.py').read_text())
    node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name==name)
    for arg in node.args.args:arg.annotation=None
    node.returns=None
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<camera-runtime>','exec'),scope)
    return scope[name]

class SceneRequests(unittest.TestCase):
    def setUp(self):
        self.quota_store=mock.patch.object(free_quota,"_backend",MemoryRepository())
        self.quota_memory=mock.patch.object(free_quota,"_memory",{})
        self.quota_store.start();self.quota_memory.start()
        self.addCleanup(self.quota_store.stop);self.addCleanup(self.quota_memory.stop)

    def test_new_photo_replaces_old_source_while_waiting_for_instruction(self,caption=None):
        source = photo('blue')
        tg_file = SimpleNamespace(download_as_bytearray=mock.AsyncMock(return_value=source))
        bot = SimpleNamespace(get_file=mock.AsyncMock(return_value=tg_file))
        message = SimpleNamespace(photo=[SimpleNamespace(file_id='replacement-photo')],
                                  message_id=11, caption=caption,
                                  reply_text=mock.AsyncMock(return_value=SimpleNamespace(message_id=12)))
        update = SimpleNamespace(effective_message=message,
                                 effective_user=SimpleNamespace(id=71),
                                 effective_chat=SimpleNamespace(type='private'))
        context = SimpleNamespace(bot=bot, user_data={
            'muba_camera_waiting_photo': False,
            'muba_camera_waiting_instruction': True,
            'muba_camera_source_bytes': b'previous-photo',
        })
        scope = {'ChatType': SimpleNamespace(PRIVATE='private'),
                 'is_dev': lambda uid: True, 'ai_configured': lambda: True,
                 'get_assistant_language': lambda uid: 'tr', 'runtime_text': runtime_text,
                 'InlineKeyboardMarkup': lambda rows: rows,
                 'InlineKeyboardButton': lambda *args, **kwargs: kwargs,
                 'logger': mock.Mock(), 'clean_camera_prompt': clean_camera_prompt,
                 '_run_muba_camera_transform': mock.AsyncMock()}
        asyncio.run(handler('muba_camera_photo', scope)(update, context))
        bot.get_file.assert_awaited_once_with('replacement-photo', read_timeout=30)
        self.assertEqual(context.user_data['muba_camera_source_bytes'], source)
        self.assertTrue(context.user_data['muba_camera_waiting_instruction'])
        if caption:
            scope['_run_muba_camera_transform'].assert_awaited_once_with(message,context,71,source,clean_camera_prompt(caption))
            message.reply_text.assert_not_awaited()
        else:
            message.reply_text.assert_awaited_once()

    def test_photo_caption_starts_generation_without_asking_twice(self):
        self.test_new_photo_replaces_old_source_while_waiting_for_instruction(' MUBA ile akşam yemeğinde olalım.\nYüz hattımı koru. ')
    def test_camera_uses_original_4b_and_rejects_higher_cost_override(self):
        with mock.patch.dict(os.environ,{'CLOUDFLARE_ACCOUNT_ID':'test-account'},clear=True):
            self.assertTrue(camera_ai_endpoint().endswith(CAMERA_AI_MODEL))
            self.assertTrue(ai_endpoint().endswith(AI_MODEL))
            os.environ['MUBA_CAMERA_AI_MODEL']=AI_MODEL
            self.assertTrue(camera_ai_endpoint().endswith(AI_MODEL))
            for model in ('@cf/black-forest-labs/flux-2-klein-9b','invalid-model'):
                os.environ['MUBA_CAMERA_AI_MODEL']=model
                with self.assertRaises(ValueError):camera_ai_endpoint()

    def test_output_keeps_source_framing_including_exif_rotation(self):
        self.assertEqual(camera_output_size(photo('red',(864,1536))),(576,1024))
        self.assertEqual(camera_output_size(photo('red',(1536,864))),(1024,576))
        self.assertEqual(camera_output_size(photo('red',(1536,864),orientation=6)),(576,1024))
        self.assertEqual(camera_output_size(photo('red',(800,800))),(1024,1024))
    def test_extended_request_preserves_tail_constraints_without_changing_studio(self):
        request=('MUBA ile sahilde olalım. '*7)+'Yüzlerimizi ve yaşımızı koru; boneleri kaldır, kıyafetleri sahile uyarla.'
        normalized=clean_camera_prompt('\n '+request+'\t')
        self.assertEqual(normalized,request)
        self.assertIn('kıyafetleri sahile uyarla.',camera_ai_prompt(normalized))
        self.assertEqual(len(clean_camera_prompt('x'*900)),800)
        self.assertEqual(len(clean_prompt('x'*900)),120)

    def test_reference_exif_rotation_is_applied_and_metadata_is_removed(self):
        result=camera_reference_bytes(photo('red',(120,80),orientation=6))
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.size,(80,120))
            self.assertEqual(image.format,'JPEG')
            self.assertFalse(image.getexif())

    def test_large_reference_keeps_aspect_ratio_under_existing_provider_limit(self):
        result=camera_reference_bytes(photo('blue',(1600,800)))
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.size,(511,256))

    def test_native_request_sends_person_first_and_muba_second_and_clears_source(self,delivery_error=None,provider_status=200):
        source=photo('red');reference=photo('blue')
        result=b'generated-image'
        response=mock.MagicMock(status=provider_status,headers={'Content-Type':'image/png'})
        response.read=mock.AsyncMock(return_value=result if provider_status==200 else b'{"errors":[{"code":3030,"message":"private source secret"}]}')
        post_context=mock.MagicMock()
        post_context.__aenter__=mock.AsyncMock(return_value=response)
        session=mock.Mock(post=mock.Mock(return_value=post_context))
        status=mock.Mock(message_id=1,edit_text=mock.AsyncMock())
        message=mock.Mock(reply_text=mock.AsyncMock(return_value=status),reply_photo=mock.AsyncMock(return_value=mock.Mock(message_id=2)))
        message.reply_photo.side_effect=delivery_error
        context=SimpleNamespace(user_data={'muba_camera_source_bytes':source,'muba_camera_waiting_instruction':True},application=SimpleNamespace(bot_data={'news_session':session}))
        scope={'get_assistant_language':lambda uid:'tr','runtime_text':runtime_text,'STUDIO_REFERENCE_FILE':mock.Mock(exists=lambda:True,read_bytes=lambda:reference),'camera_reference_bytes':camera_reference_bytes,'camera_ai_prompt':camera_ai_prompt,'aiohttp':aiohttp,'os':os,'camera_ai_endpoint':lambda:'https://ai.example.invalid/flux-2-klein-4b','camera_output_size':camera_output_size,'is_dev':lambda uid:True,'ProviderQuotaPaused':ProviderQuotaPaused,'ensure_available':ensure_available,'guard_response':guard_response,'logger':mock.Mock(),'InlineKeyboardMarkup':lambda x:x,'InlineKeyboardButton':lambda *a,**kw:kw}
        request=('Sahilde MUBA ile birlikte olalım. '*6)+'Yüzlerimizi ve yaşımızı koru.'
        with mock.patch.dict(os.environ,{'CLOUDFLARE_API_TOKEN':'unit-test-only'}):
            asyncio.run(handler('_run_muba_camera_transform',scope)(message,context,71,source,request))
        if provider_status!=200:
            message.reply_photo.assert_not_awaited()
            self.assertEqual(context.user_data['muba_camera_source_bytes'],source)
            final=status.edit_text.await_args_list[-1].args[0]
            self.assertIn('DEV: CAMERA_HTTP_503_CF_3030',final)
            self.assertNotIn('private source secret',final)
            self.assertIn(runtime_text('tr','failed'),final)
            return
        form=session.post.call_args.kwargs['data']
        fields={field[0]['name']:field[2] for field in form._fields}
        self.assertEqual(fields['input_image_0'],camera_reference_bytes(source))
        self.assertEqual(fields['input_image_1'],camera_reference_bytes(reference))
        self.assertIn(request,fields['prompt'])
        self.assertEqual((int(fields['width']),int(fields['height'])),camera_output_size(source))
        self.assertTrue(session.post.call_args.args[0].endswith('flux-2-klein-4b'))
        message.reply_photo.assert_awaited_once()
        self.assertEqual(message.reply_photo.await_args.kwargs['photo'],result)
        self.assertEqual(message.reply_photo.await_args.kwargs['write_timeout'],120)
        self.assertEqual(message.reply_photo.await_args.kwargs['read_timeout'],120)
        self.assertNotIn('muba_camera_source_bytes',context.user_data)
        self.assertNotIn('muba_camera_waiting_instruction',context.user_data)
        self.assertIn(runtime_text('tr','processing'),status.edit_text.await_args_list[1].args[0])
        final=status.edit_text.await_args_list[-1].args[0]
        if delivery_error:
            self.assertIn(runtime_text('tr','delivery_unconfirmed'),final)
            self.assertNotIn(runtime_text('tr','failed'),final)
        else:
            self.assertIn('%100',final)
            self.assertIn(runtime_text('tr','ready'),final)

    def test_delivery_timeout_does_not_claim_generation_failed_or_allowance_unused(self):
        self.test_native_request_sends_person_first_and_muba_second_and_clears_source(TimeoutError('delivery timed out'))

    def test_provider_error_is_reported_safely_without_sending_image(self):
        self.test_native_request_sends_person_first_and_muba_second_and_clears_source(provider_status=503)

    def test_legacy_request_matches_native_reference_order_and_forwards_scene(self):
        from aiohttp import web
        source=photo('red');reference=photo('blue')
        response=mock.MagicMock(status=200,headers={'Content-Type':'image/png'})
        response.read=mock.AsyncMock(return_value=b'generated-image')
        post_context=mock.MagicMock()
        post_context.__aenter__=mock.AsyncMock(return_value=response)
        session=mock.Mock(post=mock.Mock(return_value=post_context))
        request_text='MUBA ile sahilde olalım. Yüzlerimizi ve yaşımızı koru.'
        parts=[mock.Mock(name='part') for _ in range(2)]
        parts[0].name='photo';parts[0].headers={'Content-Type':'image/jpeg'};parts[0].read=mock.AsyncMock(return_value=source)
        parts[1].name='prompt';parts[1].text=mock.AsyncMock(return_value=request_text)
        reader=mock.Mock(next=mock.AsyncMock(side_effect=[*parts,None]))
        request=SimpleNamespace(multipart=mock.AsyncMock(return_value=reader),app={'http_session':session})
        scope={'web':web,'validate_init_data':lambda *a:{'id':71},'TOKEN':'unit-test-only','is_dev':lambda uid:True,'ai_configured':lambda:True,'_studio_reference':mock.AsyncMock(return_value=reference),'camera_reference_bytes':camera_reference_bytes,'camera_ai_prompt':camera_ai_prompt,'camera_ai_endpoint':lambda:'https://ai.example.invalid/flux-2-klein-4b','camera_output_size':camera_output_size,'os':os,'consume':mock.Mock(),'ProviderQuotaPaused':ProviderQuotaPaused,'ensure_available':ensure_available,'guard_response':guard_response,'logger':mock.Mock(),'remaining':lambda uid:1}
        with mock.patch.dict(os.environ,{'CLOUDFLARE_API_TOKEN':'unit-test-only'}):
            returned=asyncio.run(handler('camera_generate_handler',scope)(request))
        fields={field[0]['name']:field[2] for field in session.post.call_args.kwargs['data']._fields}
        self.assertEqual(fields['input_image_0'],camera_reference_bytes(source))
        self.assertEqual(fields['input_image_1'],camera_reference_bytes(reference))
        self.assertIn(request_text,fields['prompt'])
        self.assertEqual((int(fields['width']),int(fields['height'])),camera_output_size(source))
        self.assertTrue(session.post.call_args.args[0].endswith('flux-2-klein-4b'))
        self.assertEqual(returned.status,200)
        self.assertEqual(returned.headers['X-MUBA-Source-Persisted'],'false')
        self.assertEqual(returned.headers['X-MUBA-Gallery-Published'],'false')
        scope['consume'].assert_called_once_with(71)

if __name__=='__main__':unittest.main()
