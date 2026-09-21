# MUBA Gallery Storage

## Purpose
MUBA Gallery is the shared archive for successful creations from both Web Studio and Telegram Studio.

The archive stores only:
- generated image bytes;
- a short public gallery label derived from the concept;
- format: meme / image / sticker / emoji;
- source: web / telegram;
- creation time.

It does **not** store Telegram numeric IDs, usernames, or raw user prompts.

## Durable storage
The preferred production configuration is:

`MUBA_GALLERY_DIR=/var/data/muba-gallery`

where `/var/data` is a Render persistent disk mount.

If `MUBA_GALLERY_DIR` is not configured but `MUBA_MEMORY_FILE` points to persistent storage, Gallery automatically uses a sibling `muba-gallery` directory.

If neither durable path is configured, Gallery falls back to the host temporary directory. That fallback keeps Gallery functional but is not a disaster-recovery archive and may be lost on redeploy/replacement.

The public `GET /gallery` response exposes `persistent` and `writable` booleans so production durability can be verified without exposing filesystem paths.

## Public API
- `GET /gallery?limit=80`
- `GET /gallery?limit=80&kind=meme|image|sticker|emoji`
- `GET /gallery/image/<id>`

The JSON listing contains only safe public metadata and generated image URLs.

## Studio integration
Every successful AI creation calls the same archive function:
- Telegram Studio -> source `telegram`
- Web Studio -> source `web`

A Gallery write failure must never make a successful Studio generation fail. It is logged independently.

## Privacy
Do not add user IDs, usernames, raw prompts, IP addresses or authentication data to Gallery metadata.
