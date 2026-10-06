"""Test helpers shared by the apps."""
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

_VIDEO_CACHE = {}


class AuditSafeTransactionTestCase(TransactionTestCase):
    """TransactionTestCase flushes tables with TRUNCATE after each test, which the
    append-only audit trigger (correctly) rejects. Only for test teardown, the
    trigger is disabled around the flush and re-enabled straight after."""

    def _fixture_teardown(self):
        with connection.cursor() as cur:
            cur.execute("ALTER TABLE audit_record DISABLE TRIGGER audit_record_no_truncate")
        try:
            super()._fixture_teardown()
        finally:
            with connection.cursor() as cur:
                cur.execute("ALTER TABLE audit_record ENABLE TRIGGER audit_record_no_truncate")


class MediaRootMixin:
    """Each test class gets a private, temporary media root (never the real one)."""

    @classmethod
    def setUpClass(cls):
        cls._media_dir = tempfile.mkdtemp(prefix="hl-test-media-")
        cls._media_override = override_settings(HL_MEDIA_ROOT=Path(cls._media_dir))
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)


def test_video_bytes(seconds=12):
    """A synthetic video (test patterns + a tone, with a cut half-way). Contains no real person."""
    if seconds not in _VIDEO_CACHE:
        from hyperlocalize import media_tools

        d = tempfile.mkdtemp()
        path = Path(d) / "v.mp4"
        media_tools.make_test_video(path, seconds)
        _VIDEO_CACHE[seconds] = path.read_bytes()
        shutil.rmtree(d)
    return _VIDEO_CACHE[seconds]


def video_upload(seconds=12, name="source.mp4"):
    return SimpleUploadedFile(name, test_video_bytes(seconds), content_type="video/mp4")


# A human-made transcript for the 12-second test video (English demo-scenario sentences).
TRANSCRIPT_VTT = """WEBVTT

00:00:00.500 --> 00:00:02.500
Speaker 1: Give 2 sachets of ORS every day.

00:00:03.000 --> 00:00:05.000
Speaker 1: Do not boil the mixture.

00:00:07.000 --> 00:00:09.500
Speaker 1: Mix one packet in 1 litre of clean water.

00:00:10.000 --> 00:00:11.500
Speaker 1: Ask a health worker for help.
"""


def transcript_upload(text=TRANSCRIPT_VTT):
    return SimpleUploadedFile("transcript.vtt", text.encode("utf-8"), content_type="text/vtt")


def make_users():
    from hyperlocalize.accounts.models import User

    names = ["manager", "manager2", "reviewer", "operator", "auditor", "speaker", "admin", "outsider"]
    users = {n: User.objects.create_user(n, password="Test-pass-12345") for n in names}
    users["admin"].is_administrator = True
    users["admin"].save()
    return users


def make_project(users, *, scripted=True):
    from hyperlocalize.accounts.models import ProjectMembership, Role
    from hyperlocalize.projects import services as projects

    project = projects.create_project(
        users["manager"], name="Demo project", source_language="en", target_locale="ta-IN",
        domain="health information (demo scenario)",
        data_classification="SCRIPTED_TEAM" if scripted else "PERSONAL",
    )
    for name, role in [("manager2", Role.LOCALIZATION_MANAGER), ("reviewer", Role.REVIEWER),
                       ("operator", Role.MEDIA_OPERATOR), ("auditor", Role.AUDITOR)]:
        ProjectMembership.objects.create(user=users[name], project=project, role=role)
    return project


def make_owner_with_consent(users, project, *, purposes=("STANDARD",), languages=("ta",), days=30):
    """An identity owner linked to the 'speaker' user, with a standing and a project consent."""
    from hyperlocalize.identity import services as identity
    from hyperlocalize.identity.models import IdentityOwner

    owner = IdentityOwner.objects.create(name="Speaker A (test)", user=users["speaker"])
    expires = timezone.now() + timedelta(days=days)
    identity.grant_standing_consent(
        users["speaker"], owner, uses=["voice_synthesis"], permitted_purposes=list(purposes),
        permitted_copy_kinds=[], languages=list(languages), processors=[], expires_at=expires,
        evidence_ref="HL-SPIKE-CONSENT v1 / TEST-FORM-1",
    )
    identity.grant_project_consent(users["speaker"], owner, project, uses=["voice_synthesis"],
                                   languages=list(languages), processors=[], expires_at=expires)
    return owner
