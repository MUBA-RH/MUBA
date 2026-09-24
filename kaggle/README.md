# MUBA Daily Story — Kaggle runtime

Kaggle is the on-demand free-compute worker for Daily Story. Telegram remains the DEV inbox/outbox and web publishing remains approval-gated.

## Production flow
Telegram fresh reference -> Render bot -> authenticated Kaggle kernel push -> T4 x2 batch -> four PNG outputs -> Telegram review -> explicit WEB YAYINLA.

The worker is a finite batch job. It starts only when a fresh Daily Story reference is submitted, generates exactly four sequential frames, writes 01.png through 04.png, then exits. There is no keep-alive or idle GPU process.

## Required Render secrets
- KAGGLE_USERNAME
- KAGGLE_KEY

Optional:
- MUBA_KAGGLE_OWNER (default: mubarh)
- MUBA_KAGGLE_KERNEL (default: muba-daily-story-runtime)
- MUBA_KAGGLE_TIMEOUT (default: 1800 seconds)

Never commit Kaggle credentials to GitHub. The bot fails closed if credentials are absent.

## Safety boundary
Kaggle is compute only. Guardian, Assistant, Gallery, Studio and web approval remain isolated. Failed Kaggle runs do not publish or replace the current Daily Story.
