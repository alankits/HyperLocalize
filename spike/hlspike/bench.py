"""M6: timing harness for any model command (SPIKE_PLAN §4 M6, also M1 speed).

Runs a command N times and records, per run: wall time, peak RSS and exit code
(and the real-time factor if the command writes a WAV). The first run is the
cold run. Also records the hardware and, inside a container, the cgroup memory
limit (= the Docker memory limit). Each call appends one JSON line to --out.

Run this INSIDE the Docker Compose container (the plan measures CPU numbers
there). Peak RSS comes from os.wait4 for the child process; memory of
grandchildren may not be included [UNVERIFIED], so run the model in-process
in the command you pass (e.g. `python3 synth_one.py ...`), not via a shell.

Usage:
    python3 -m hlspike.bench --label indicf5_cpu_seg --runs 3 \
        [--output-wav out.wav] [--project-segments 40] [--out work/bench.jsonl] \
        -- python3 synth_one.py --text ...
"""

import argparse
import json
import os
import platform
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .timing_fit import wav_duration_s


def run_once(command: list[str]) -> dict:
    start = time.perf_counter()
    proc = subprocess.Popen(command)
    _, status, usage = os.wait4(proc.pid, 0)
    wall = time.perf_counter() - start
    proc.returncode = os.waitstatus_to_exitcode(status)  # tell Popen we reaped it
    return {"wall_s": wall, "peak_rss_mb": usage.ru_maxrss / 1024, "exit_code": proc.returncode}  # Linux: KiB


def cgroup_memory_limit_bytes() -> int | None:
    for path in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            raw = Path(path).read_text().strip()
        except OSError:
            continue
        if raw.isdigit() and int(raw) < 2**60:  # cgroup v1 reports a huge number for "no limit"
            return int(raw)
        return None
    return None


def environment() -> dict:
    info = {"python": platform.python_version(), "machine": platform.machine(), "cpu_count": os.cpu_count()}
    try:
        cpuinfo = Path("/proc/cpuinfo").read_text()
        info["cpu_model"] = next(line.split(":", 1)[1].strip() for line in cpuinfo.splitlines() if line.startswith("model name"))
        meminfo = Path("/proc/meminfo").read_text()
        info["mem_total_mb"] = int(next(line.split()[1] for line in meminfo.splitlines() if line.startswith("MemTotal"))) // 1024
    except (OSError, StopIteration):
        pass
    limit = cgroup_memory_limit_bytes()
    info["cgroup_memory_limit_mb"] = limit // 2**20 if limit else None
    return info


def summarise(runs: list[dict], project_segments: int | None = None) -> dict:
    walls = [r["wall_s"] for r in runs]
    summary = {
        "runs": len(runs),
        "cold_wall_s": walls[0],
        "median_wall_s": statistics.median(walls),
        "max_wall_s": max(walls),
        "peak_rss_mb": max(r["peak_rss_mb"] for r in runs),
        "all_succeeded": all(r["exit_code"] == 0 for r in runs),
    }
    rtfs = [r["rtf"] for r in runs if "rtf" in r]
    if rtfs:
        summary["median_rtf"] = statistics.median(rtfs)
    if project_segments:
        # Assumes one run synthesises one segment.
        summary["projected_hours_for_project"] = summary["median_wall_s"] * project_segments / 3600
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output-wav", type=Path, help="WAV the command writes; used for the real-time factor")
    parser.add_argument("--project-segments", type=int, help="cloned segments in the whole demo project (overnight projection)")
    parser.add_argument("--out", type=Path, default=Path("work/bench.jsonl"))
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("give the command to time after --")

    runs = []
    for _ in range(args.runs):
        run = run_once(command)
        if args.output_wav and run["exit_code"] == 0 and args.output_wav.exists():
            run["audio_s"] = wav_duration_s(args.output_wav)
            run["rtf"] = run["wall_s"] / run["audio_s"] if run["audio_s"] else None
        runs.append(run)

    record = {
        "label": args.label,
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": command,
        "environment": environment(),
        "per_run": runs,
        "summary": summarise(runs, args.project_segments),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
