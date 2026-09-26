"""Telegram MUBA Camera Mini App.

The source selfie is captured by the user's browser and sent only after explicit action.
MUBA does not intentionally persist the source selfie. Generated output is returned in the
same response and is not published to Gallery in this test layer.
"""

def camera_html(base_url:str)->str:
    b=base_url.rstrip("/")
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-store"><script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#07040f;color:#fff;font-family:system-ui;padding:20px}}.card{{max-width:620px;margin:auto;background:#120a1f;border:1px solid #7c3aed;border-radius:22px;padding:20px}}h1{{margin:0 0 8px}}p,small{{color:#c8b9dc;line-height:1.45}}input{{width:100%;margin:14px 0;padding:12px;background:#090510;color:#fff;border:1px solid #51326f;border-radius:12px}}button,a{{width:100%;display:block;text-align:center;border:0;border-radius:13px;padding:14px;font-weight:750;text-decoration:none}}button{{background:linear-gradient(135deg,#b026ff,#7c3aed);color:#fff}}#out{{display:none;width:100%;margin-top:16px;border-radius:16px}}#save{{display:none;margin-top:10px;background:#241638;color:#fff}}#receipt{{margin-top:14px;color:#86efac;white-space:pre-line}}.privacy{{padding:12px;border:1px solid #51326f;border-radius:12px;background:#090510}}</style></head><body><div class="card">
<h1>📸 MUBA CAMERA</h1><div class="privacy"><strong>AL → İŞLE → VER</strong><p>Fotoğraf yalnızca MUBA dönüşümü için gönderilir. MUBA kaynak selfie'yi Gallery, veritabanı veya dosya deposuna kaydetmez. Bu testte üretilen sonuç da Gallery'ye gönderilmez.</p><small>AI işlemi harici model sağlayıcısında gerçekleşir; MUBA kendi sisteminde kaynak selfie'yi kalıcılaştırmaz.</small></div>
<input id="photo" type="file" accept="image/*" capture="user"><button id="go">MUBA'YA DÖNÜŞTÜR</button><div id="msg"></div><img id="out" alt="Generated MUBA"><a id="save" download="my-muba.png">⬇️ SONUCU KAYDET</a><div id="receipt"></div>
</div><script>
const tg=window.Telegram.WebApp;tg.ready();tg.expand();let resultUrl="";
document.getElementById("go").onclick=async()=>{{const file=document.getElementById("photo").files[0],msg=document.getElementById("msg"),receipt=document.getElementById("receipt");if(!file){{msg.textContent="Önce fotoğraf çek.";return}};const fd=new FormData();fd.append("photo",file);fd.append("initData",tg.initData||"");const q=new URLSearchParams(location.search);fd.append("uid",q.get("uid")||"");fd.append("studioToken",q.get("st")||"");msg.textContent="AL → İŞLE...";receipt.textContent="";try{{const r=await fetch("{b}/camera/generate",{{method:"POST",body:fd,cache:"no-store"}});if(!r.ok){{let e=await r.json();throw new Error(e.error||"İşlem başarısız.")}}const blob=await r.blob();if(resultUrl)URL.revokeObjectURL(resultUrl);resultUrl=URL.createObjectURL(blob);const out=document.getElementById("out"),save=document.getElementById("save");out.src=resultUrl;out.style.display="block";save.href=resultUrl;save.style.display="block";msg.textContent="VER ✓";receipt.textContent="PRIVACY RECEIPT ✓\nKaynak selfie: MUBA tarafından kalıcı kaydedilmedi\nGallery: yayınlanmadı\nSonuç: cihazına teslim edildi"}}catch(e){{msg.textContent=e.message}}finally{{document.getElementById("photo").value=""}}}};
</script></body></html>"""
