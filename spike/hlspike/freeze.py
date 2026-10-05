"""Freeze the check rules before R2 writes the seeded errors (SPIKE_PLAN §4 M3).

`--write` records a SHA-256 for every rule file in spike/FROZEN_RULES.json
(commit that file). `--verify` lists files changed since the freeze.
hlspike.seeded_eval refuses to report results if anything changed, so the
catch rates cannot come from rules tuned after seeing the seeded errors.

Usage:
    python3 -m hlspike.freeze --write
    python3 -m hlspike.freeze --verify
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import SPIKE_DIR

FROZEN_FILE = SPIKE_DIR / "FROZEN_RULES.json"
RULE_FILES = [
    "hlspike/checks.py",
    "hlspike/numbers.py",
    "hlspike/lexicon_checks.py",
    "hlspike/english_numbers.py",
    "data/units.json",
    "data/glossary.json",
    "data/ta_number_word_stems.txt",
    "data/m1_normalisation.json",
]


def file_hashes(base: Path = SPIKE_DIR, files: list[str] = RULE_FILES) -> dict[str, str]:
    return {name: hashlib.sha256((base / name).read_bytes()).hexdigest() for name in files}


def _git_commit(base: Path) -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=base, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def write_freeze(base: Path = SPIKE_DIR, frozen_file: Path = FROZEN_FILE, files: list[str] = RULE_FILES) -> dict:
    record = {
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git_commit(base),
        "files": file_hashes(base, files),
    }
    frozen_file.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def changed_since_freeze(base: Path = SPIKE_DIR, frozen_file: Path = FROZEN_FILE) -> list[str] | None:
    """Files whose hash differs from the freeze record; None if never frozen."""
    if not frozen_file.exists():
        return None
    frozen = json.loads(frozen_file.read_text(encoding="utf-8"))["files"]
    current = file_hashes(base, list(frozen))
    return [name for name, digest in frozen.items() if current[name] != digest]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)

    if args.write:
        print(json.dumps(write_freeze(), indent=2))
        return
    changed = changed_since_freeze()
    if changed is None:
        sys.exit("Rules have never been frozen. Run: python3 -m hlspike.freeze --write")
    if changed:
        sys.exit("Changed since freeze: " + ", ".join(changed))
    print("Rules unchanged since freeze.")


if __name__ == "__main__":
    main()
