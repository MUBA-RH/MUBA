"""Isolated MUBA DEV MTProto translator V2.

This module deliberately does not import or modify the production Bot API runtime.
It uses a Telegram *user* authorization session so a translated message is sent by
that user account, not via an inline bot.

Required environment:
  TELEGRAM_API_ID
  TELEGRAM_API_HASH
  MUBA_DEV_SESSION   (Telethon StringSession; never commit this value)

Interactive first-time session creation:
  python dev_mtproto_translator.py login

Manual send:
  python dev_mtproto_translator.py send <peer> "Turkish text"
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


async def create_session():
    """Interactive Telegram user authorization; prints the session once for secret storage."""
    client=_client()
    await client.start()
    session=client.session.save()
    me=await client.get_me()
    print(f"Authorized Telegram user id: {me.id}")
    print("Store the following value only as the MUBA_DEV_SESSION secret:")
    print(session)
    await client.disconnect()


async def translate_to_english(client,text):
    """Use Telegram's user-only messages.translateText method."""
    _,functions,types,_=_telethon()
    clean=" ".join((text or "").strip().split())
    if not clean:
        raise ValueError("Text is empty")
    result=await client(functions.messages.TranslateTextRequest(
        text=[types.TextWithEntities(text=clean,entities=[])],
        to_lang="en",
    ))
    if not result.result:
        raise RuntimeError("Telegram returned no translation")
    return result.result[0].text


async def translate_and_send(peer,text):
    """Translate Turkish input to English and send from the authorized user account."""
    session=os.getenv("MUBA_DEV_SESSION","").strip()
    if not session:
        raise RuntimeError("MUBA_DEV_SESSION is required; run the login command first")
    client=_client(session)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise RuntimeError("MUBA_DEV_SESSION is not authorized")
        translated=await translate_to_english(client,text)
        await client.send_message(peer,translated)
        print(translated)
    finally:
        await client.disconnect()


def main(argv=None):
    argv=list(argv or sys.argv[1:])
    if argv==["login"]:
        asyncio.run(create_session()); return
    if len(argv)==3 and argv[0]=="send":
        asyncio.run(translate_and_send(argv[1],argv[2])); return
    raise SystemExit('Usage: dev_mtproto_translator.py login | send <peer> "Turkish text"')


if __name__=="__main__":
    main()
