"""Isolated, fail-closed official-source news pool for Web and Telegram."""
from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import tempfile
import threading
import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from xml.etree import ElementTree as ET

from muba_gallery import _r2_request, _local_storage_root, storage_status

LOG=logging.getLogger("muba.news")
KEY="news/v1/pool.json"
LOCK=threading.RLock()
CATEGORIES=("BTC","ETH","MARKET","ETF","REGULATION","EXCHANGE","SECURITY","STABLECOIN","PROTOCOL","MUBA")
SOURCES=(
    ("SEC", "https://www.sec.gov/news/pressreleases.rss", "www.sec.gov"),
    ("CFTC", "https://www.cftc.gov/RSS/RSSGP/rssgp.xml", "www.cftc.gov"),
    ("Ethereum Foundation", "https://blog.ethereum.org/en/feed.xml", "blog.ethereum.org"),
    ("Bitcoin.org", "https://bitcoin.org/en/rss/blog.xml", "bitcoin.org"),
    ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml", "www.federalreserve.gov"),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss", "www.coindesk.com"),
    ("The Block", "https://www.theblock.co/rss.xml", "www.theblock.co"),
    ("Cointelegraph", "https://cointelegraph.com/rss", "cointelegraph.com"),
    ("Decrypt", "https://decrypt.co/feed", "decrypt.co"),
)
MEDIA_HOSTS={"www.coindesk.com","www.theblock.co","cointelegraph.com","decrypt.co"}
OFFICIAL_HOSTS={"www.sec.gov","www.cftc.gov","www.federalreserve.gov",
                "home.treasury.gov","bitcoin.org","ethereum.org","blog.ethereum.org"}
CRYPTO=re.compile(r"\bcrypto(?:currency)?\b|\bbitcoin\b|\bethereum\b|\bblockchain\b|\bdigital assets?\b|\bstablecoin\b|\btokeniz|\bweb3\b|\bdefi\b|\betf\b|\bbtc\b|\beth\b",re.I)
MACRO=re.compile(r"\binterest rates?\b|\bfederal funds rate\b|\bmonetary policy\b|\brate (?:increase|cut|hike)\b",re.I)
TOPICS={
    "ETF":r"\betf\b|exchange.traded fund",
    "SECURITY":r"\bhack\b|exploit|breach|vulnerabilit|security incident|stolen funds",
    "STABLECOIN":r"stablecoin|\busdc\b|\busdt\b",
    "REGULATION":r"regulat|commission|rulemaking|\bsec\b|\bcftc\b|legislat|sanction",
    "EXCHANGE":r"\bexchange\b|trading platform|coinbase|kraken|binance",
    "BTC":r"\bbitcoin\b|\bbtc\b",
    "ETH":r"\bethereum\b|\b(?:eth|pectra|fusaka)\b",
    "PROTOCOL":r"protocol|network upgrade|mainnet|consensus",
    "MARKET":r"\bmarket\b|macro|federal reserve|interest rate|monetary policy",
}
IMPORTANT=re.compile(r"\betf\b|approval|approves|adopts|proposes|exemption|final rule|launch|upgrade|incident|hack|exploit|breach|charges|enforcement|settlement|stablecoin|tokeniz|mainnet|hard fork",re.I)
RUMOR=re.compile(r"\brumou?r\b|unconfirmed|anonymous sources|price prediction|buy signal|sell signal",re.I)


def important(row):
    title=row["title"]
    return bool(row.get("corroborated") or IMPORTANT.search(title+" "+row["summary"]) or
                (MACRO.search(title) and row.get("source_name")=="Federal Reserve") or
                (re.search(r"\bcrypto(?:currency)?\b|\bblockchain\b|\bbitcoin\b|\bethereum\b",title,re.I)
                 and re.search(r"\bupdates?\b|\breleases?\b",title,re.I)))


def relevant(row):
    return bool(CRYPTO.search(row["title"]+" "+row["summary"]) or
                (row["source_name"]=="Federal Reserve" and MACRO.search(row["title"])))


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_url(value,host):
    try:
        url=urlparse(value.strip())
        if url.scheme!="https" or url.hostname!=host or url.username or url.password or url.port:
            return None
        return urlunparse(("https",host,url.path or "/","",url.query,""))
    except (ValueError,AttributeError):
        return None


def clean_text(value):
    return " ".join(html.unescape(re.sub(r"<[^>]*>"," ",value or "")).split())[:500]


def parsed_time(value):
    try:
        stamp=parsedate_to_datetime(value)
    except (ValueError,TypeError):
        try: stamp=datetime.fromisoformat(value.replace("Z","+00:00"))
        except (ValueError,TypeError,AttributeError): return None
    if not stamp or stamp.tzinfo is None: return None
    stamp=stamp.astimezone(timezone.utc)
    if stamp>datetime.now(timezone.utc)+timedelta(minutes=5): return None
    return stamp


def category_for(title,summary):
    text=f"{title} {summary}".lower()
    for category,pattern in TOPICS.items():
        if re.search(pattern,text,re.I): return category
    return None


def parse_feed(xml,source):
    name,_,host=source
    if len(xml)>2_000_000 or b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
        raise ValueError("Unsafe or oversized feed")
    root=ET.fromstring(xml)
    nodes=root.findall(".//item") or root.findall("{http://www.w3.org/2005/Atom}entry")
    rows=[]
    for node in nodes[:30]:
        def field(*tags):
            for tag in tags:
                element=node.find(tag)
                if element is not None:
                    return (element.text or element.get("href") or "").strip()
            return ""
        title=clean_text(field("title","{http://www.w3.org/2005/Atom}title"))[:180]
        summary=clean_text(field("description","{http://www.w3.org/2005/Atom}summary","{http://www.w3.org/2005/Atom}content"))[:320]
        url=canonical_url(field("link","{http://www.w3.org/2005/Atom}link"),host)
        published=parsed_time(field("pubDate","{http://www.w3.org/2005/Atom}published","{http://www.w3.org/2005/Atom}updated"))
        rows.append({"title":title,"summary":summary,"source_name":name,"source_url":url,
                     "published_at":published.isoformat(timespec="seconds") if published else None,
                     "category":category_for(title,summary)})
    return rows


def duplicate_hash(row):
    # Stable across tracking links, minor punctuation changes and feed ordering.
    title=" ".join(re.findall(r"[a-z0-9]+",row["title"].lower()))
    return hashlib.sha256((title+"|"+(row["published_at"] or "")[:10]).encode()).hexdigest()


def verified_row(row,article):
    if not row.get("source_url") or not row.get("published_at") or not row.get("title"):
        return "PENDING"
    if not row.get("category") or not important(row) or not relevant(row):
        return "REJECTED"
    if RUMOR.search(row["title"]+" "+row["summary"]): return "REJECTED"
    if not article: return "PENDING"
    # The official article must repeat the core headline. A feed alone is insufficient.
    words={w for w in re.findall(r"[a-z]{4,}",row["title"].lower()) if w not in {"with","from","that","this","about","their"}}
    body=set(re.findall(r"[a-z]{4,}",html.unescape(re.sub(r"<[^>]*>"," ",article.decode("utf-8","replace")[:800_000])).lower()))
    if len(words)<2 or len(words.intersection(body))/len(words)<0.6:
        return "PENDING"
    return "VERIFIED"


def event_match(a,b):
    if a["category"]!=b["category"] or not a.get("published_at") or not b.get("published_at"):
        return False
    if abs((datetime.fromisoformat(a["published_at"])-datetime.fromisoformat(b["published_at"])).total_seconds())>86400:
        return False
    if a["source_url"]==b["source_url"] or a["duplicate_hash"]==b["duplicate_hash"]:
        return True
    words=lambda title:set(re.findall(r"[a-z0-9]{4,}",title.lower()))
    left,right=words(a["title"]),words(b["title"])
    return (len(left & right)>=4 and len(left & right)/len(left | right)>=0.78) or corroborates(a,b)


def corroborates(a,b):
    """A second independent publisher must describe the same event, not just the same coin."""
    if a["source_name"]==b["source_name"] or a["category"]!=b["category"]: return False
    if not a.get("published_at") or not b.get("published_at"): return False
    if abs((datetime.fromisoformat(a["published_at"])-datetime.fromisoformat(b["published_at"])).total_seconds())>172800: return False
    skip={"crypto","market","says","after","with","from","that","about","today","latest","news"}
    terms=lambda row:{word for word in re.findall(r"[a-z]{4,}",row["title"].lower()) if word not in skip}
    left,right=terms(a),terms(b)
    return len(left & right)>=3 and len(left & right)/max(1,min(len(left),len(right)))>=0.35


def primary_links(article):
    if not article: return []
    urls=re.findall(r"href\s*=\s*['\"](https://[^'\"<>\s]+)['\"]",article.decode("utf-8","replace")[:800_000],re.I)
    result=[]
    for raw in urls:
        raw=html.unescape(raw)
        host=urlparse(raw).hostname
        if host in OFFICIAL_HOSTS:
            url=canonical_url(raw,host)
            if url: result.append(url)
    return list(dict.fromkeys(result))[:6]


def merge(pool,candidate):
    if candidate["verification_status"]!="VERIFIED": return False
    for old in reversed(pool):
        if event_match(old,candidate):
            if old["summary"]!=candidate["summary"] and old["source_url"]==candidate["source_url"]:
                old["status"]="ARCHIVED"
                candidate["status"]="CORRECTED" if re.search(r"\bcorrection\b|\bcorrected\b",candidate["title"],re.I) else "UPDATED"
                candidate["correction_of"]=old["id"]
                candidate["id"]=hashlib.sha256((candidate["source_url"]+candidate["summary"]).encode()).hexdigest()[:24]
                pool.append(candidate)
                return True
            return False
    pool.append(candidate)
    return True


def load_pool():
    backend=storage_status()["backend"]
    if backend=="local-temporary": return []
    if backend=="r2":
        response=_r2_request("GET",KEY,allow_missing=True)
        data=json.loads(response.content) if response else []
    else:
        path=_local_storage_root()[0]/KEY
        data=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    if not isinstance(data,list): raise ValueError("Invalid news pool")
    return data


def save_pool(pool):
    backend=storage_status()["backend"]
    if backend=="local-temporary": raise RuntimeError("Persistent news storage required")
    body=json.dumps(pool,ensure_ascii=False,separators=(",",":")).encode()
    if backend=="r2":
        _r2_request("PUT",KEY,body=body,content_type="application/json")
    else:
        path=_local_storage_root()[0]/KEY
        path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as output:
            output.write(body)
            temporary=Path(output.name)
        temporary.replace(path)


async def collect(session,fetch=None):
    """Collect only independently reachable official articles; failures stay unpublished."""
    if not storage_status()["persistent"]: return []
    if fetch is None:
        async def fetch(url):
            async with session.get(url,allow_redirects=False,timeout=9) as response:
                if response.status!=200: raise ValueError(f"Source HTTP {response.status}")
                is_feed=url in {source[1] for source in SOURCES}
                data=await response.content.read(2_000_001 if is_feed else 800_000)
                if is_feed and len(data)>2_000_000: raise ValueError("Oversized feed")
                return data
    fresh=[]
    candidates=[]
    async def read_source(source):
        try: return parse_feed(await fetch(source[1]),source)
        except Exception:
            LOG.warning("News feed unavailable: %s",source[0],exc_info=True)
            return []
    for rows in await asyncio.gather(*(read_source(source) for source in SOURCES)):
        for row in rows[:20]:
            if not row["source_url"] or not row["published_at"]: continue
            if not row["category"] or not relevant(row): continue
            if RUMOR.search(row["title"]+" "+row["summary"]): continue
            if datetime.fromisoformat(row["published_at"])<datetime.now(timezone.utc)-timedelta(days=3): continue
            candidates.append(row)
    for row in candidates:
        if urlparse(row["source_url"]).hostname in MEDIA_HOSTS:
            row["corroborated"]=any(corroborates(row,other) and
                                    urlparse(other["source_url"]).hostname in MEDIA_HOSTS
                                    for other in candidates if other is not row)
    candidates=[row for row in candidates if important(row)]
    semaphore=asyncio.Semaphore(6)
    async def inspect(row):
        async with semaphore:
            try: return await fetch(row["source_url"])
            except Exception: return None
    articles=await asyncio.gather(*(inspect(row) for row in candidates))
    official_article_cache={}
    for row,article in zip(candidates,articles):
        media=urlparse(row["source_url"]).hostname in MEDIA_HOSTS
        row["verification_status"]=verified_row(row,article)
        if media and row["verification_status"]=="VERIFIED":
            confirmed=False
            for official in primary_links(article)[:3]:
                if official not in official_article_cache:
                    try: official_article_cache[official]=await fetch(official)
                    except Exception: official_article_cache[official]=None
                if verified_row(row,official_article_cache[official])=="VERIFIED":
                    confirmed=True
                    break
            if not confirmed:
                confirmed=any(other_article and urlparse(other["source_url"]).hostname in MEDIA_HOSTS
                              and corroborates(row,other) and verified_row(other,other_article)=="VERIFIED"
                              for other,other_article in zip(candidates,articles) if other is not row)
            if not confirmed: row["verification_status"]="PENDING"
        if row["verification_status"]=="VERIFIED":
            row.update({"id":hashlib.sha256(row["source_url"].encode()).hexdigest()[:24],
                        "collected_at":now_iso(),"importance":"HIGH","language_master":"EN",
                        "duplicate_hash":duplicate_hash(row),"correction_of":None,"status":"ACTIVE"})
            fresh.append(row)
    if not fresh: return []
    with LOCK:
        pool=load_pool()
        added=[]
        for row in fresh:
            if merge(pool,row): added.append(row)
        if added: save_pool(pool[-500:])
        return added


def public_news(category=None):
    if category and category not in CATEGORIES: return []
    with LOCK: rows=load_pool()
    return sorted((r for r in rows if r.get("verification_status")=="VERIFIED"
                   and r.get("status") in ("ACTIVE","UPDATED","CORRECTED","ARCHIVED")
                   and (not category or r["category"]==category)),key=lambda r:r["published_at"],reverse=True)


LABELS={
    "en":("MUBA NEWS","No verified news yet.","Alerts on","Read source","Translation unavailable."),
    "tr":("MUBA HABERLER","Henüz doğrulanmış haber yok.","Bildirimler açık","Kaynağı oku","Çeviri şu anda kullanılamıyor."),
    "zh":("MUBA 新闻","暂无已核实新闻。","提醒已开启","阅读来源","翻译暂时不可用。"),
    "ar":("أخبار MUBA","لا توجد أخبار موثقة بعد.","تم تفعيل التنبيهات","اقرأ المصدر","الترجمة غير متاحة حالياً."),
    "hi":("MUBA समाचार","अभी कोई सत्यापित समाचार नहीं।","सूचनाएँ चालू","स्रोत पढ़ें","अनुवाद अभी उपलब्ध नहीं है।"),
}
TELEGRAM_FIELDS={
    "en":("VERIFIED","SOURCE","DATE","UPDATE","CORRECTION"),
    "tr":("DOĞRULANDI","KAYNAK","TARİH","GÜNCELLEME","DÜZELTME"),
    "zh":("已核实","来源","日期","更新","更正"),
    "ar":("موثق","المصدر","التاريخ","تحديث","تصحيح"),
    "hi":("सत्यापित","स्रोत","तारीख","अपडेट","सुधार"),
}


async def translate(text,lang,session):
    if lang=="en": return text
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID")
    token=os.getenv("CLOUDFLARE_API_TOKEN")
    if not account or not token: return None
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/meta/m2m100-1.2b"
    try:
        async with session.post(url,json={"text":text,"source_lang":"en","target_lang":lang},
                                headers={"Authorization":f"Bearer {token}"},timeout=20) as response:
            if response.status!=200: return None
            result=(await response.json()).get("result")
        if isinstance(result,list): result=result[0] if result else None
        if isinstance(result,dict):
            value=result.get("translated_text") or result.get("translation")
            return str(value).strip() if value else None
    except Exception:
        LOG.warning("News translation unavailable for %s",lang,exc_info=True)
    return None


async def telegram_news(row,lang,session):
    if lang not in LABELS or row.get("verification_status")!="VERIFIED": return None
    title=await translate(row["title"],lang,session)
    summary=await translate(row["summary"],lang,session)
    if not title or not summary: return None
    verified,source,time_label,update,correction=TELEGRAM_FIELDS[lang]
    prefix=correction+" · " if row["status"]=="CORRECTED" else update+" · " if row["status"]=="UPDATED" else ""
    return (f"📰 {prefix}{row['category']} · {verified}\n\n{title}\n\n{summary}\n\n"
            f"{source}: {row['source_name']}\n{time_label}: {row['published_at'][:10]}\n{LABELS[lang][3]}: {row['source_url']}")


def _subscribers_path():
    return _local_storage_root()[0]/"news/v1/subscribers.json"


def subscriptions():
    backend=storage_status()["backend"]
    if backend=="local-temporary": return {}
    if backend=="r2":
        response=_r2_request("GET","news/v1/subscribers.json",allow_missing=True)
        data=json.loads(response.content) if response else {}
    else:
        path=_subscribers_path()
        data=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return data if isinstance(data,dict) else {}


def _save_subscriptions(data):
    backend=storage_status()["backend"]
    body=json.dumps(data,separators=(",",":")).encode()
    if backend=="r2":
        _r2_request("PUT","news/v1/subscribers.json",body=body,content_type="application/json")
    elif backend=="local-persistent":
        path=_subscribers_path()
        path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as output:
            output.write(body)
            temporary=Path(output.name)
        temporary.replace(path)
    else: raise RuntimeError("Persistent news subscriptions required")


def subscribe(user_id,lang):
    if lang not in LABELS: raise ValueError("Unknown assistant language")
    with LOCK:
        data=subscriptions()
        data[str(int(user_id))]=data.get(str(int(user_id)),{"sent_ids":[]})|{"language":lang}
        _save_subscriptions(data)


async def notify_subscribers(rows,bot,session,get_language):
    with LOCK: data=subscriptions()
    for user_id,settings in data.items():
        lang=get_language(int(user_id))
        if lang not in LABELS: continue
        for row in rows:
            notification_id=row["id"]+":"+row["status"]
            if notification_id in settings.get("sent_ids",[]): continue
            message=await telegram_news(row,lang,session)
            if not message: continue
            try: await bot.send_message(chat_id=int(user_id),text=message,disable_web_page_preview=True)
            except Exception:
                LOG.warning("News delivery failed for subscriber",exc_info=True)
                continue
            with LOCK:
                current=subscriptions()
                target=current.get(user_id)
                if not target: continue
                target["sent_ids"]=(target.get("sent_ids",[])+[notification_id])[-100:]
                _save_subscriptions(current)
