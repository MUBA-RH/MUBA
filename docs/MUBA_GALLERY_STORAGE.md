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

### Production: Cloudflare R2
The preferred production backend is the private Cloudflare R2 bucket `muba-gallery`.

Required runtime configuration:

- `MUBA_R2_ACCESS_KEY_ID`
- `MUBA_R2_SECRET_ACCESS_KEY`
- `MUBA_R2_BUCKET=muba-gallery`
- account ID from `MUBA_R2_ACCOUNT_ID`, or the existing `CLOUDFLARE_ACCOUNT_ID`

When all R2 values are present, Gallery stores generated image objects and its persistent archive index in R2. The R2 bucket can remain private: the public website continues to receive images through the MUBA backend's `/gallery/image/<id>` route.

When R2 is configured, an R2 error does **not** silently fall back to temporary local storage. Studio generation may still succeed, but archival failure is logged separately. This prevents temporary storage from being mistaken for a durable archive.

### Local fallback
When R2 is not configured, the previous storage order remains available:

1. `MUBA_GALLERY_DIR`;
2. a sibling `muba-gallery` directory beside `MUBA_MEMORY_FILE`;
3. a mounted Render `/var/data` persistent disk;
4. host temporary storage as a last-resort compatibility fallback.

The temporary fallback is not durable and may be lost on redeploy/replacement.

The public `GET /gallery` response and `/health/state` expose `persistent`, `writable` and a non-secret `backend` label so production durability can be verified without exposing credentials or filesystem paths.

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


## Moderation state
Every new Gallery record starts as `public`.

DEV may change a record to:
- `public` — listed and publicly served;
- `hidden` — retained in the archive but removed from public listing and image serving;
- `rejected` — retained as a moderation decision and not publicly listed or served.

Moderation changes only archive visibility. They do not add user identity data and do not delete the underlying historical record.
