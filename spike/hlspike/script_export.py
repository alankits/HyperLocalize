"""Export the segments of docs/spike/TEST_SCRIPT.md §1 as JSONL or plain text.

The JSONL is the source side for the translation runs and the checks; the
plain text (one segment per line) is the starting point for the verbatim
reference transcript (which must then match what was actually said).

Usage:
    python3 -m hlspike.script_export [--format jsonl|text] [--script PATH]
"""

import argparse
import json
import re
from pathlib import Path

from . import REPO_DIR

SCRIPT_FILE = REPO_DIR / "docs" / "spike" / "TEST_SCRIPT.md"
ROW_RE = re.compile(r"^\| (S\d{2}) \| (.+?) \|$")
SCENE_RE = re.compile(r"^### Scene (\d+)")


def read_segments(path: Path = SCRIPT_FILE) -> list[dict]:
    """Rows of section 1 only (stops at the calibration section 1b)."""
    segments, scene, in_script = [], None, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 1."):
            in_script = True
        elif line.startswith("### 1b") or (in_script and line.startswith("## 2")):
            break
        elif in_script and (m := SCENE_RE.match(line)):
            scene = int(m.group(1))
        elif in_script and (m := ROW_RE.match(line)):
            segments.append({"id": m.group(1), "scene": scene, "text": m.group(2)})
    return segments


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--format", choices=["jsonl", "text"], default="jsonl")
    parser.add_argument("--script", type=Path, default=SCRIPT_FILE)
    args = parser.parse_args(argv)
    for seg in read_segments(args.script):
        print(json.dumps(seg, ensure_ascii=False) if args.format == "jsonl" else seg["text"])


if __name__ == "__main__":
    main()
