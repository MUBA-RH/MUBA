"""Strict autonomous source policy and bounded retrieval."""
from __future__ import annotations
import urllib.parse, urllib.request

OFFICIAL_SOURCES = {'official_x':'@MUBA_RH','official_website':'https://muba-rh.github.io/MUBA/'}
ALLOWED_HOSTS = {
 'muba-rh.github.io':'official_muba',
 'wikipedia.org':'general','www.wikipedia.org':'general','en.wikipedia.org':'general','tr.wikipedia.org':'general','zh.wikipedia.org':'general','ar.wikipedia.org':'general','hi.wikipedia.org':'general',
 'wikimedia.org':'general','www.wikimedia.org':'general','commons.wikimedia.org':'general','api.wikimedia.org':'general',
 'wikidata.org':'general','www.wikidata.org':'general','query.wikidata.org':'general',
 'unicode.org':'language','www.unicode.org':'language','cldr.unicode.org':'language',
}
MAX_BYTES=262_144


def normalize_host(url: str) -> tuple[str,str]:
 p=urllib.parse.urlsplit(url.strip())
 if p.scheme.lower() != 'https' or p.username or p.password or not p.hostname or p.port not in (None,443): raise ValueError('invalid source URL')
 host=p.hostname.rstrip('.').lower().encode('idna').decode('ascii')
 return host, urllib.parse.urlunsplit(('https',p.netloc.lower(),p.path or '/',p.query,''))


def classify(url: str) -> str | None:
 try: host,_=normalize_host(url)
 except ValueError: return None
 return ALLOWED_HOSTS.get(host)

def relevant_for(subject: str, url: str) -> bool:
 """Prevent a permitted but irrelevant source from satisfying a query."""
 category=classify(url)
 normalized=(subject or '').casefold()
 if normalized in {'weather','price','news','score','status'}:
  return False  # The protected allowlist currently has no live provider.
 if normalized in {'muba','muba_identity','official_muba'}:
  return category == 'official_muba'
 if normalized in {'language','unicode','locale'}:
  return category == 'language'
 return category == 'general'


class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self, req, fp, code, msg, headers, newurl):
  raise ValueError('redirects are rejected and must be revalidated explicitly')


def retrieve(url: str, *, timeout: float=6.0, opener=None) -> dict:
 category=classify(url)
 if not category: return {'ok':False,'error':'source_not_allowed'}
 _,normalized=normalize_host(url)
 client=opener or urllib.request.build_opener(NoRedirect())
 try:
  response=client.open(urllib.request.Request(normalized,headers={'User-Agent':'MUBA-Local/3'}),timeout=timeout)
  final=response.geturl()
  if classify(final) != category: return {'ok':False,'error':'final_destination_not_allowed'}
  data=response.read(MAX_BYTES+1)
  if len(data)>MAX_BYTES: return {'ok':False,'error':'response_too_large'}
  return {'ok':True,'content':data.decode('utf-8','replace'),'evidence':{'source':final,'source_type':category,'temporary':True,'promotes_to_official':False}}
 except Exception as exc:
  return {'ok':False,'error':type(exc).__name__}
