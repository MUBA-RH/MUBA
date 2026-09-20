"""Isolated MUBA DEV MTProto translator V2.

Uses a Telegram user authorization session, never the Bot API, so outgoing
translations are normal user messages with no inline-bot invocation.

Required environment:
  TELEGRAM_API_ID
  TELEGRAM_API_HASH
  MUBA_DEV_SESSION   (Telethon StringSession; never commit this value)

Commands:
  python dev_mtproto_translator.py login
  python dev_mtproto_translator.py send <peer> "Turkish text"
  python dev_mtproto_translator.py chat <peer>

Chat mode keeps one selected Telegram conversation open. Type only Turkish text;
each non-empty line is translated to English and sent from the authorized user
account. Type /quit to leave. No @MUBA_RH_AI_Bot prefix is used.
"""
import asyncio
import os
import sys


def _credentials():
    api_id=os.getenv("TELEGRAM_API_ID","").strip()
    api_hash=os.getenv("TELEGRAM_API_HASH","").strip()
    if not api_id or not api_hash:
        raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH are required")
    return int(api_id),api_hash


def _telethon():
    try:
        from telethon import TelegramClient, functions, types
        from telethon.sessions import StringSession
    except ImportError as exc:
        raise RuntimeError("Install translator dependencies: pip install -r requirements-translator.txt") from exc
    return TelegramClient,functions,types,StringSession


def _client(session=""):
    TelegramClient,_,_,StringSession=_telethon()
    api_id,api_hash=_credentials()
    return TelegramClient(StringSession(session),api_id,api_hash)


def _session():
    session=os.getenv("MUBA_DEV_SESSION","").strip()
    if session:
        return session
    secret_path=os.path.expanduser("~/muba_dev_session.secret")
    try:
        with open(secret_path,"r",encoding="utf-8") as handle:
            session=handle.read().strip()
    except OSError:
        session=""
    if not session:
        raise RuntimeError("MUBA_DEV_SESSION is required; run the login command first")
    return session


async def create_session():
    client=_client()
    await client.start()
    session=client.session.save()
    me=await client.get_me()
    print(f"Authorized Telegram user id: {me.id}")
    print("Store the following value only as the MUBA_DEV_SESSION secret:")
    print(session)
    await client.disconnect()


async def translate_to_english(client,text):
    _,functions,types,_=_telethon()
    clean=(text or "").strip()
    if not clean:
        raise ValueError("Text is empty")
    result=await client(functions.messages.TranslateTextRequest(
        text=[types.TextWithEntities(text=clean,entities=[])],
        to_lang="en",
    ))
    if not result.result:
        raise RuntimeError("Telegram returned no translation")
    return result.result[0].text


async def _authorized_client():
    client=_client(_session())
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError("MUBA_DEV_SESSION is not authorized")
    return client


async def translate_and_send(peer,text):
    client=await _authorized_client()
    try:
        translated=await translate_to_english(client,text)
        await client.send_message(peer,translated)
        print(translated)
    finally:
        await client.disconnect()


async def chat_mode(peer):
    """Keep one recipient selected so DEV types only Turkish messages."""
    client=await _authorized_client()
    try:
        entity=await client.get_entity(peer)
        print("MUBA DEV Translator V2 — CHAT MODE")
        print("Recipient selected. Type Turkish only; /quit exits.")
        while True:
            try:
                text=await asyncio.to_thread(input,"> ")
            except (EOFError,KeyboardInterrupt):
                break
            if text.strip().lower() in {"/quit","/exit"}:
                break
            if not text.strip():
                continue
            try:
                translated=await translate_to_english(client,text)
                await client.send_message(entity,translated)
                print(f"✓ {translated}")
            except Exception as exc:
                print(f"✗ NOT SENT: {exc}")
    finally:
        await client.disconnect()


def main(argv=None):
    argv=list(argv or sys.argv[1:])
    if argv==["login"]:
        asyncio.run(create_session()); return
    if len(argv)==3 and argv[0]=="send":
        asyncio.run(translate_and_send(argv[1],argv[2])); return
    if len(argv)==2 and argv[0]=="chat":
        asyncio.run(chat_mode(argv[1])); return
    raise SystemExit('Usage: dev_mtproto_translator.py login | send <peer> "Turkish text" | chat <peer>')


if __name__=="__main__":
    main()
