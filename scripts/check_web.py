#!/usr/bin/env python3
"""Static smoke checks for the public MUBA website."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"index.html"
HISTORY=ROOT/"muba_history.json"

class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if "id" in values:
            self.ids.append(values["id"])

def main():
    html=INDEX.read_text(encoding="utf-8")
    parser=IdParser(); parser.feed(html)
    duplicates=sorted({x for x in parser.ids if parser.ids.count(x)>1})
    if duplicates:
        raise SystemExit("duplicate HTML ids: "+", ".join(duplicates))
    required={
        "studio","gallery","gallery-strip","twt","development","dev-entry",
        "create-web","studio-result-img","menu-btn","site-nav"
    }
    missing=sorted(required-set(parser.ids))
    if missing:
        raise SystemExit("missing required HTML ids: "+", ".join(missing))
    for needle in (
        'fetch("./muba_history.json"',
        'loadDevelopmentHistory();',
        'loadGallery();',
        '/studio/web-generate',
        'id="gallery-strip"',
        'scroll-snap-type: x proximity',
    ):
        if needle not in html:
            raise SystemExit("missing web behavior: "+needle)
    data=json.loads(HISTORY.read_text(encoding="utf-8"))
    if not data.get("entries"):
        raise SystemExit("muba_history.json has no entries")

    scripts=re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,flags=re.S|re.I)
    inline="\n".join(part for part in scripts if part.strip())
    node=shutil.which("node")
    if node and inline:
        with tempfile.NamedTemporaryFile("w",suffix=".js",encoding="utf-8",delete=False) as fh:
            fh.write(inline)
            path=fh.name
        result=subprocess.run([node,"--check",path],text=True,capture_output=True)
        Path(path).unlink(missing_ok=True)
        if result.returncode:
            raise SystemExit(result.stderr or result.stdout or "JavaScript syntax check failed")
    print(f"Web smoke OK: {len(parser.ids)} IDs, {len(data['entries'])} history entries.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
