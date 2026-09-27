"""Write one prepared Daily Story episode and image to the private GitHub layer."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "telegram-bot"))
from muba_story_github import write_day


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: save_daily_story.py YYYY-MM-DD episode.json scene.png")
    day, episode_file, image_file = sys.argv[1:]
    episode = json.loads(Path(episode_file).read_text(encoding="utf-8"))
    write_day(day, episode, Path(image_file).read_bytes())
    print("Private Daily Story draft saved for", day)
