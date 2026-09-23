# MUBA Daily Story — Kaggle runtime

This notebook is the free-compute fallback for Daily Story. It verifies Kaggle T4 x2 and smoke-loads Qwen-Image-Edit-2511.

## Safety boundary
Kaggle is compute only. Production Telegram state, approval, publishing, Guardian, Living Story, Studio and Gallery remain unchanged. The notebook does not publish a public endpoint or alter production automatically.

## Run
Import `muba_daily_story_gpu_setup.ipynb` into Kaggle, enable **GPU T4 x2** and **Internet**, then run the notebook.

Kaggle sessions are ephemeral. A live Telegram-to-Kaggle bridge must not be treated as stable until an externally reachable authenticated endpoint is available.
