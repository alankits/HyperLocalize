"""End-to-end validation over HTTP against a running server + worker (dev stack, MOCK providers).
Actions go through the web UI routes; outcomes are checked in the database.

Usage (uses a SEPARATE database, never your working one):
  export HL_DB_NAME=hyperlocalize_e2e HL_MEDIA_ROOT=/tmp/hl-e2e-media HL_E2E_PASSWORD=...
  create the database, migrate, createcachetable, seed_demo --password "$HL_E2E_PASSWORD"
  start: runserver 127.0.0.1:8766  and  run_worker --lane all
  python scripts/e2e_check.py
"""
import http.cookiejar
import os
import io
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hyperlocalize.settings")
import django  # noqa: E402

django.setup()
from hyperlocalize.audit.services import verify_chain  # noqa: E402
from hyperlocalize.exports.models import Export  # noqa: E402
from hyperlocalize.identity.models import IdentityOwner, VoiceProfile  # noqa: E402
from hyperlocalize.localization.models import CheckResult, Localization, Scene, Segment  # noqa: E402
from hyperlocalize.localization.services import blocking_checks, latest_translations  # noqa: E402
from hyperlocalize.pipeline.models import Job  # noqa: E402
from hyperlocalize.projects.models import Project, SpeakerTrack  # noqa: E402
from hyperlocalize.rendering.models import RenderedScene  # noqa: E402

BASE = os.environ.get("HL_E2E_BASE", "http://127.0.0.1:8766")
PASSWORD = os.environ["HL_E2E_PASSWORD"]
results = []


def step(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


class Session:
    def __init__(self, user):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar),
                                              urllib.request.HTTPRedirectHandler())
        page = self.get("/accounts/login/")
        self.post("/accounts/login/", {"username": user, "password": PASSWORD}, page=page)

    def token(self):
        for c in self.jar:
            if c.name == "csrftoken":
                return c.value
        return ""

    def get(self, path):
        try:
            with self.op.open(BASE + path) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def post(self, path, data, files=None, page=None):
        data = dict(data, csrfmiddlewaretoken=self.token())
        if files:
            boundary = uuid.uuid4().hex
            body = io.BytesIO()
            for k, v in data.items():
                body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
            for k, (fname, content, ctype) in files.items():
                body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\n"
                           f"Content-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n")
            body.write(f"--{boundary}--\r\n".encode())
            req = urllib.request.Request(BASE + path, data=body.getvalue(),
                                         headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Referer": BASE + path})
        else:
            req = urllib.request.Request(BASE + path, data=urllib.parse.urlencode(data, doseq=True).encode(),
                                         headers={"Referer": BASE + path})
        try:
            with self.op.open(req) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()


def wait_jobs(timeout=180):
    deadline = time.time() + timeout
    while Job.objects.filter(status__in=["QUEUED", "RUNNING"]).exclude(type__in=["consent_expiry_sweep", "retention_sweep"]).exists():
        if time.time() > deadline:
            return False
        time.sleep(0.5)
    return True


def ref_clip():
    from hyperlocalize import media_tools

    path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "hl-e2e-ref.wav")
    media_tools._run([media_tools.ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=220:duration=5",
                      "-ac", "1", "-ar", "16000", path])
    return open(path, "rb").read()


project = Project.objects.get(name__startswith="Demo: ")
loc = Localization.objects.get(project=project)
step("analysis and first previews finish", wait_jobs())
scenes = list(Scene.objects.filter(video__project=project).order_by("index"))
step("scenes built", len(scenes) >= 2, f"{len(scenes)} scenes")

# 1. Identity owner grants consent and uploads a reference clip.
speaker = Session("speaker")
owner = IdentityOwner.objects.get(user__username="speaker")
s, _ = speaker.post("/me/consent/standing/", {"uses": "voice_synthesis", "purposes": "STANDARD", "languages": "ta",
                                              "expires_on": "2026-12-31", "evidence_ref": "HL-SPIKE-CONSENT v1 / E2E-TEST"})
operator = Session("operator")
track = SpeakerTrack.objects.get(video__project=project)
operator.post(f"/projects/{project.pk}/speakers/{track.pk}/", {"identity_owner": owner.pk})
speaker.post(f"/me/consent/projects/{project.pk}/grant/", {"uses": "voice_synthesis", "languages": "ta"})
speaker.post(f"/me/consent/projects/{project.pk}/voice/", {"transcript": "This is my reference sentence.", "language": "ta"},
             files={"clip": ("ref.wav", ref_clip(), "audio/wav")})
step("consent granted and reference clip stored", VoiceProfile.objects.filter(identity_owner=owner, status="ACTIVE").exists())

# 2. Reviewer regenerates previews; the backend resolves CLONED_VOICE (MOCK tone).
reviewer = Session("reviewer")
for sc in scenes:
    reviewer.post(f"/scenes/{sc.pk}/changes/", {"target": "PREVIEW", "reason": "speaker linked"})
wait_jobs()
modes = {m["mode"] for sc in scenes for m in RenderedScene.objects.filter(scene=sc).order_by("-version").first().rendering_modes.values()}
step("previews use the identity-preserving mode", modes == {"CLONED_VOICE"}, str(modes))

# 3. Human review: edit every segment (human text), resolve checks, accept.
for seg in Segment.objects.filter(scene__video__project=project).order_by("index"):
    src = seg.source_text
    nums = " ".join(re.findall(r"\d+", src))
    reviewer.post(f"/segments/{seg.pk}/edit/", {"subtitle_text": f"தமிழ் வாக்கியம் {nums}".strip()})
wait_jobs()
for c in blocking_checks(loc):
    res = "OVERRIDDEN" if c.kind == "HARD" else "ACKNOWLEDGED"
    reviewer.post(f"/checks/{c.pk}/resolve/", {"resolution": res, "reason": "E2E: reviewed against the source"})
for sc in scenes:
    reviewer.post(f"/scenes/{sc.pk}/accept/", {})
step("all scenes accepted by the reviewer", all(Scene.objects.get(pk=sc.pk).status == "ACCEPTED" for sc in scenes))

# 4. Approval (separation of duties: the reviewer edited; a manager approves).
manager = Session("manager")
manager.post(f"/projects/{project.pk}/approve/", {})
loc.refresh_from_db()
step("manager approves", loc.status == "APPROVED", loc.status)

# 5. Export refused: the cloned voice is a MOCK.
s, body = manager.post(f"/projects/{project.pk}/export/", {})
step("export of MOCK output refused", not Export.objects.exists() and b"MOCK" in body)

# 6. Revocation: preview 410, approval invalidated, stock fallback.
cloned_render = RenderedScene.objects.filter(scene=scenes[0]).order_by("-version").first()
code_before, _ = reviewer.get(f"/previews/{cloned_render.pk}.mp4")
speaker.post(f"/me/consent/projects/{project.pk}/revoke/", {})
code_after, _ = reviewer.get(f"/previews/{cloned_render.pk}.mp4")
step("preview served before revocation, 410 after", (code_before, code_after) == (200, 410), f"{code_before}->{code_after}")
loc.refresh_from_db()
step("approval invalidated by revocation", loc.status == "IN_REVIEW", loc.status)
wait_jobs()
modes = {m["mode"] for sc in scenes for m in RenderedScene.objects.filter(scene=sc).order_by("-version").first().rendering_modes.values()}
step("fallback previews use the stock voice", modes == {"STOCK_VOICE"}, str(modes))
step("reference clip deleted", not VoiceProfile.objects.filter(identity_owner=owner, status="ACTIVE").exists())

# 7. Subtitles-only policy → re-render, re-review, approve, export a real (non-mock) package.
admin = Session("admin")
admin.post("/accounts/policies/", {"separation_of_duties": "on", "cloning_allowed": "on", "preview_retention_days": 30,
                                   "export_retention_days": 90})  # synthesis_allowed unticked → SUBTITLES_ONLY
for sc in scenes:
    reviewer.post(f"/scenes/{sc.pk}/changes/", {"target": "PREVIEW", "reason": "subtitles-only policy"})
wait_jobs()
for c in blocking_checks(loc):
    reviewer.post(f"/checks/{c.pk}/resolve/", {"resolution": "OVERRIDDEN" if c.kind == "HARD" else "ACKNOWLEDGED",
                                               "reason": "E2E: reviewed against the source"})
for sc in scenes:
    reviewer.post(f"/scenes/{sc.pk}/accept/", {})
manager.post(f"/projects/{project.pk}/approve/", {})
manager.post(f"/projects/{project.pk}/export/", {})
wait_jobs()
export = Export.objects.order_by("-pk").first()
step("non-mock export built", export is not None and export.status == "ACTIVE", export.status if export else "none")
if export:
    code, data = manager.get(f"/exports/{export.pk}/download/")
    names = zipfile.ZipFile(io.BytesIO(data)).namelist() if code == 200 else []
    step("package downloaded with evidence manifest", "evidence_manifest.json" in names and "localized_video.mp4" in names,
         ", ".join(names))

# 8. Auditor verifies the chain over HTTP.
auditor = Session("auditor")
code, body = auditor.get(f"/projects/{project.pk}/audit/?verify=1")
step("auditor chain verification", code == 200 and b"verified" in body)
step("chain verifies (direct)", verify_chain()[0])

failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} steps passed")
sys.exit(1 if failed else 0)
