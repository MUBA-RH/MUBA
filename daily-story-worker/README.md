# MUBA Daily Story Worker

Private DEV-only image worker for MUBA Daily Story.

Production boundary:
- Public MUBA Studio stays on its existing public generation path.
- Daily Story jobs use this isolated ComfyUI worker.
- One job contains four independent 16:9 chapters.
- Character identity comes from the canonical MUBA master/reference contract.
- Narrative continuity comes from Story State, never previous-frame pixels.
- No automatic web publication. Telegram DEV approval remains mandatory.

The worker is provider-neutral. Kaggle is the first GPU runtime; the same job/workflow contract can later move to another GPU host without changing MUBA Story State or Telegram approval semantics.
