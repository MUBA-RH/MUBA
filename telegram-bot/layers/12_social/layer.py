from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower().strip()
 gm={'gm','good morning','günaydın','早上好','صباح الخير','सुप्रभात'}
 gn={'gn','good night','iyi geceler','晚安','تصبح على خير','शुभ रात्रि'}
 if v in gm: return signal('social','gm',.98,'distinct greeting wave candidate')
 if v in gn: return signal('social','gn',.98,'distinct greeting wave candidate')
 keys=('how are you','quiet today','what is happening in the group','when should you join','when should you stay silent','keyfin nasıl','nasılsın','ortam sessiz','ne oluyor','ne zaman sessiz','你好吗','什么时候加入','什么时候保持沉默','怎么这么安静','كيف حالك','متى تشارك','متى تصمت','لماذا أنت هادئ','कैसे हो','कब शामिल','कब चुप','आज इतने चुप')
 if any(x in v for x in keys): return signal('social','social',.9,'relational or participation semantics')
 if v == '/start': return signal('social','start',.95,'ordinary Telegram start, never authority')
 return None
LAYER=SpecialistLayer('social',600,match)
