"""Throwaway spike tooling for HyperLocalize (docs/SPIKE_PLAN.md).

Nothing in this package is imported by the application. It uses only the
Python standard library so that it runs on the demo laptop without installs.
"""

from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SPIKE_DIR / "data"
REPO_DIR = SPIKE_DIR.parent
