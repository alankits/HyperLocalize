"""Create demo accounts and the current demo scenario (health information, English → Tamil).

The scenario is a TEST CASE for the general workflow, not the product's domain. The script
text comes from docs/spike/TEST_SCRIPT.md, whose health facts are [UNVERIFIED]. The video is
synthetic (test patterns and a tone); it contains no real person. No consent is created here:
consent can only be granted by the identity owner, in their own account (ADR 0011).
"""
import secrets
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction

from hyperlocalize import media_tools
from hyperlocalize.accounts.models import ProjectMembership, Role, User
from hyperlocalize.identity.models import IdentityOwner
from hyperlocalize.projects import services as projects
from hyperlocalize.projects.models import Project

SCRIPT = [  # TEST_SCRIPT.md scenes 1-2 (S01-S11); [UNVERIFIED] health facts, demo text only
    "Diarrhoea makes a child lose water and salts quickly.",
    "This is called dehydration, and it can be dangerous.",
    "Oral rehydration salts, or ORS, replace what is lost.",
    "Wash your hands with soap and water.",
    "Take 1 litre of clean water. If unsure, boil and cool it.",
    "Pour 1 sachet of ORS into the water.",
    "Stir until the powder dissolves.",
    "Do not add sugar or salt.",
    "Do not use less water than the packet says.",
    "Do not boil the solution after mixing.",
    "Throw away any solution left after 24 hours.",
]
GLOSSARY = ["diarrhoea", "dehydration", "ORS", "sachet"]
ACCOUNTS = [
    ("manager", "Localization Manager", Role.LOCALIZATION_MANAGER),
    ("manager2", "second Localization Manager (approves after edits; separation of duties)", Role.LOCALIZATION_MANAGER),
    ("reviewer", "Reviewer / Linguist", Role.REVIEWER),
    ("operator", "Media Operator", Role.MEDIA_OPERATOR),
    ("auditor", "Auditor / Faculty Evaluator", Role.AUDITOR),
    ("speaker", "Speaker / Identity Owner (no project access)", None),
    ("admin", "Administrator (users, providers, policies; cannot grant consent)", None),
]


def _vtt(lines, seg_ms=3600, gap_ms=600):
    def ts(ms):
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}"

    out, t = ["WEBVTT", ""], 500
    for line in lines:
        out += [f"{ts(t)} --> {ts(t + seg_ms)}", f"Speaker 1: {line}", ""]
        t += seg_ms + gap_ms
    return "\n".join(out), t


class Command(BaseCommand):
    help = "Create demo accounts and a demo project (synthetic video, human transcript). Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Password for every demo account (default: a random one, printed once).")

    def handle(self, *args, password=None, **options):
        password = password or secrets.token_urlsafe(9)
        created = []
        with transaction.atomic():
            for username, _desc, _role in ACCOUNTS:
                user, new = User.objects.get_or_create(username=username)
                if new:
                    user.set_password(password)
                    user.is_administrator = username == "admin"
                    user.save()
                    created.append(username)
            speaker = User.objects.get(username="speaker")
            IdentityOwner.objects.get_or_create(user=speaker, defaults={"name": "Demo speaker"})
        if Project.objects.filter(name__startswith="Demo: ").exists():
            self.stdout.write("Demo project already exists; nothing else to do.")
        else:
            manager = User.objects.get(username="manager")
            project = projects.create_project(
                manager, name="Demo: health information (ORS), English → Tamil", source_language="en", target_locale="ta-IN",
                domain="health information: current demo scenario, facts [UNVERIFIED]",
                data_classification="SCRIPTED_TEAM",
                cultural_notes="Audience: caregivers in Tamil Nadu. Plain, respectful language.",
            )
            for username, _desc, role in ACCOUNTS:
                if role and username != "manager":
                    ProjectMembership.objects.get_or_create(user=User.objects.get(username=username), project=project, role=role)
            for term in GLOSSARY:
                projects.add_glossary_term(manager, project, source_term=term,
                                           note="Tamil forms to be filled in by a Tamil-literate rater")
            vtt, end_ms = _vtt(SCRIPT)
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / "demo.mp4"
                media_tools.make_test_video(path, seconds=int(end_ms / 1000) + 2)
                upload = SimpleUploadedFile("demo-synthetic.mp4", path.read_bytes(), content_type="video/mp4")
            transcript = SimpleUploadedFile("demo.vtt", vtt.encode("utf-8"), content_type="text/vtt")
            projects.upload_video(User.objects.get(username="operator"), project, upload, transcript)
            self.stdout.write(self.style.SUCCESS(f"Created demo project #{project.pk}; analysis is queued (start a worker)."))
        if created:
            self.stdout.write(f"Created accounts: {', '.join(created)}")
            self.stdout.write(self.style.WARNING(f"Password for these demo accounts (shown once): {password}"))
        for username, desc, _role in ACCOUNTS:
            self.stdout.write(f"  {username:9s} {desc}")
