"""Inference subprocess owned by the worker (ADR 0003, ADR 0005).

Speech models run in a child process, one model loaded at a time. While waiting
for an answer the worker checks cancellation and consent about once a second and
KILLS the child on cancel, so revocation stops synthesis within seconds
(ADR 0006 §6). The child is restarted on the next call.

Protocol: one JSON request per line on stdin, one JSON response per line on stdout.
"""
import json
import os
import queue
import subprocess
import sys
import threading
import time

POLL_SECONDS = 1.0


class InferenceError(Exception):
    pass


class InferenceProcess:
    def __init__(self):
        self.proc = None
        self._lines = None

    def _start(self):
        env = dict(os.environ)
        env.setdefault("DJANGO_SETTINGS_MODULE", "hyperlocalize.settings")
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "hyperlocalize.pipeline.inference"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
        )
        self._lines = queue.Queue()
        proc = self.proc
        threading.Thread(target=lambda: [self._lines.put(ln) for ln in proc.stdout], daemon=True).start()

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def kill(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=10)
        self.proc = None

    def call(self, request, *, poll=None, timeout=600):
        """Send a request and wait. `poll()` runs every second and may raise to abort (the child is killed)."""
        if not self.alive():
            self._start()
        self.proc.stdin.write(json.dumps(request) + "\n")
        self.proc.stdin.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                line = self._lines.get(timeout=POLL_SECONDS)
            except queue.Empty:
                line = None
            if line:
                response = json.loads(line)
                if response.get("error"):
                    raise InferenceError(response["error"])
                return response
            if self.proc.poll() is not None:
                self.proc = None
                raise InferenceError("inference process exited unexpectedly")
            if poll is not None:
                try:
                    poll()
                except BaseException:
                    self.kill()  # cancel immediately (ADR 0006 §6)
                    raise
            if time.monotonic() > deadline:
                self.kill()
                raise InferenceError("inference timed out")


def _child_main():
    import django

    django.setup()
    from hyperlocalize.pipeline.providers.base import get_adapter, registered

    registered()  # load adapters
    for line in sys.stdin:
        try:
            req = json.loads(line)
            adapter = get_adapter(req["adapter"])
            if adapter is None:
                raise InferenceError(f"adapter {req['adapter']!r} not available in this mode")
            result = adapter.synthesize(
                req["text"],
                req["language"],
                req["out_path"],
                voice=req.get("voice"),
                reference_clip=req.get("reference_clip"),
                reference_text=req.get("reference_text"),
            )
            out = {"wav_path": result.wav_path, "duration_ms": result.duration_ms, "model": result.model}
        except Exception as exc:  # report to the parent; never crash silently
            out = {"error": f"{type(exc).__name__}: {exc}"}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    _child_main()
