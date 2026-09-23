# Daily Story approved drawing reference

The DEV approved `1000307689.png` on 2026-09-23 as the Daily Story character
and drawing-style reference. The uploaded bytes are JPEG despite that original
filename. The unmodified image is bundled at
`telegram-bot/assets/daily-story/muba-approved-chibi-v2.jpg`.

- SHA-256: `175a87e2331228d079487b7e0a1119c7a182649a72f877e3069407f16a8b88a0`
- Contract: `muba-daily-story-approved-chibi-v2`
- Role: identity **and** drawing style, not a required scene/composition.

## Keep / vary

Keep the rounded caramel/cream face, large white oval eyes with black pupils,
small black nose, pink cheek patches/tongue, black MUBA cap, plain black hoodie,
short chibi proportions, clean contours and simple soft cel shading.

Let expressions, gaze, pose, camera, lighting and setting follow the story.
The green door, wooden box, street and paper scraps are example scenery, not
mandatory props. Do not add them to an unrelated episode.

## Runtime

`muba_daily_story_reference.load_reference()` verifies the bundled bytes before
generation. Every one of the four panel calls receives those exact bytes with
the correct JPEG media type. Missing/tampered assets stop Story generation;
there is no fallback to the former social-profile portrait and no extra anchor
generation call. Default output is 1024 x 576 (16:9); explicit dimension
overrides must also be 16:9.

The old shared `muba_face_architecture.py` rules conflict with this approved
drawing (notably pink cheeks and eye geometry), so Story no longer imports
them. Studio, the website hero and the shared face module remain untouched.

Generated image batches carry a reference version/checksum in Story state.
Unapproved batches from an older/unknown reference are not offered for
publication or treated as today's completed preparation. Their archived bytes
are not deleted. Already-published images are retained and cannot be replaced
through the generator. New images still require the existing DEV web-approval
flow; no automatic web or X publication is added.

## Validation boundary

Tests verify asset integrity, prompt isolation, four-call reference forwarding,
request media type/dimensions, stale-draft handling and approval protection.
They do not prove artistic similarity or train/fine-tune the image model.
The four actual Telegram outputs still need visual review against this image.
