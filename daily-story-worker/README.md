# MUBA Daily Story Worker

Private DEV-only image worker for MUBA Daily Story.

Production boundary:
- Public MUBA Studio stays on its existing public generation path.
- Daily Story jobs use this isolated ComfyUI worker.
- One job contains one 16:9 scene based on today's 150–170 character story.
- Character identity comes from the canonical MUBA master/reference contract.
- Narrative continuity comes from the published story text, never previous-frame pixels.
- The first seven episodes are seeded in the Story director. Later episodes are prepared once per day from the prior text by the Daily Story text provider and persisted before image generation. If the provider fails validation or is unavailable, the previous episode is not recycled.
- No automatic web publication. Telegram DEV approval remains mandatory.

The worker is provider-neutral. Kaggle is the first GPU runtime; the same job/workflow contract can later move to another GPU host without changing MUBA Story State or Telegram approval semantics.
