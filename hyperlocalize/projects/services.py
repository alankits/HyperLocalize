"""UC1 Create and configure a localization project; UC2 upload and validate the source video."""
import os
import re
import tempfile

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import URLValidator
from django.db import transaction

from hyperlocalize import media_tools
from hyperlocalize.accounts.models import ProjectMembership, Role, User
from hyperlocalize.accounts.permissions import require_role
from hyperlocalize.audit import services as audit
from hyperlocalize.localization.models import Localization
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.providers.manual import parse_subtitles

from .models import AudienceProfile, GlossaryTerm, Project, SpeakerTrack, Video
from .storage import get_storage


def _source_provenance(data_classification, source_url, source_licence, source_attribution):
    """ADR 0021: published public content must record where it came from and why reuse is permitted."""
    if data_classification not in Project.DataClassification.values:
        raise ValidationError("Unknown data classification.")
    source_url, source_licence, source_attribution = source_url.strip(), source_licence.strip(), source_attribution.strip()
    if data_classification != Project.DataClassification.PUBLISHED_PUBLIC:
        return "", "", ""  # provenance fields only mean something for published content
    if not source_url or not source_licence:
        raise ValidationError("Published public content needs the source URL and the licence or reuse permission.")
    if len(source_url) > 500 or len(source_licence) > 300 or len(source_attribution) > 300:
        raise ValidationError("The source URL (500), licence (300) or attribution (300) is too long.")
    licence = source_licence.upper().replace("-", " ")
    if re.search(r"\bND\b|NODERIV|NO DERIV", licence):
        raise ValidationError("A NoDerivatives licence does not permit translation; this content cannot be localized.")
    if re.search(r"\bCC BY\b", licence) and not source_attribution:
        raise ValidationError("CC BY licences require attribution: enter the credit line.")
    try:
        URLValidator(schemes=["http", "https"])(source_url)
    except ValidationError:
        raise ValidationError("The source URL must be a full http(s) address.") from None
    return source_url, source_licence, source_attribution


@transaction.atomic
def create_project(actor, *, name, source_language, target_locale, domain="", data_classification=Project.DataClassification.PERSONAL,
                   formality="neutral", reading_level="general", cultural_notes="",
                   source_url="", source_licence="", source_attribution=""):
    """The creator becomes the project's Localization Manager (ADR 0011)."""
    if not actor.is_authenticated:
        raise PermissionDenied("Sign in first.")
    if not name.strip():
        raise ValidationError("A project name is required.")
    source_url, source_licence, source_attribution = _source_provenance(
        data_classification, source_url, source_licence, source_attribution)
    project = Project.objects.create(
        name=name.strip(), source_language=source_language.strip().lower(), domain=domain.strip(),
        data_classification=data_classification, source_url=source_url, source_licence=source_licence,
        source_attribution=source_attribution, created_by=actor,
    )
    AudienceProfile.objects.create(project=project, locale=target_locale.strip(), formality=formality,
                                   reading_level=reading_level, cultural_notes=cultural_notes)
    Localization.objects.create(project=project, target_locale=target_locale.strip())
    ProjectMembership.objects.create(user=actor, project=project, role=Role.LOCALIZATION_MANAGER)
    audit.record(actor=actor, action="PROJECT_CREATED", entity=project, project_id=project.pk,
                 details={"source_language": project.source_language, "target_locale": target_locale.strip(),
                          "data_classification": data_classification, "source_url": source_url,
                          "source_licence": source_licence, "source_attribution": source_attribution})
    return project


@transaction.atomic
def add_member(actor, project, username, role):
    require_role(actor, project, Role.LOCALIZATION_MANAGER)
    if role not in Role.values:
        raise ValidationError("Unknown role.")
    user = User.objects.filter(username=username).first()
    if user is None:
        raise ValidationError(f"No user called {username!r}.")
    membership, created = ProjectMembership.objects.get_or_create(user=user, project=project, role=role)
    if created:
        audit.record(actor=actor, action="MEMBER_ADDED", entity=membership, project_id=project.pk,
                     details={"user": user.username, "role": role})
    return membership


@transaction.atomic
def update_audience(actor, project, *, formality, reading_level, cultural_notes, unit_conversions=None):
    require_role(actor, project, Role.LOCALIZATION_MANAGER)
    audience = project.audience
    audience.formality, audience.reading_level, audience.cultural_notes = formality, reading_level, cultural_notes
    if unit_conversions is not None:
        audience.unit_conversions = unit_conversions
    audience.save()
    audit.record(actor=actor, action="AUDIENCE_UPDATED", entity=audience, project_id=project.pk,
                 details={"formality": formality, "reading_level": reading_level})
    return audience


@transaction.atomic
def add_glossary_term(actor, project, *, source_term, target_term="", accepted_forms=(), do_not_translate=False, note=""):
    require_role(actor, project, Role.LOCALIZATION_MANAGER, Role.REVIEWER)
    if not source_term.strip():
        raise ValidationError("A source term is required.")
    term = GlossaryTerm.objects.create(
        project=project, source_term=source_term.strip(), target_term=target_term.strip(),
        accepted_forms=[f.strip() for f in accepted_forms if f.strip()], do_not_translate=do_not_translate, note=note,
    )
    audit.record(actor=actor, action="GLOSSARY_TERM_ADDED", entity=term, project_id=project.pk,
                 details={"term_id": term.pk, "do_not_translate": do_not_translate})
    return term


def _spool(uploaded, max_bytes):
    """Write an upload to a private temp file, enforcing the size limit while streaming."""
    fd, path = tempfile.mkstemp(prefix="hl-upload-", dir=_tmp_dir())
    size = 0
    try:
        with os.fdopen(fd, "wb") as out:
            for chunk in uploaded.chunks():
                size += len(chunk)
                if size > max_bytes:
                    raise ValidationError(f"The file is larger than the MVP limit of {max_bytes // (1024 * 1024)} MB.")
                out.write(chunk)
    except Exception:
        os.unlink(path)
        raise
    return path, size


def _tmp_dir():
    d = settings.HL_MEDIA_ROOT / "tmp"
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    return str(d)


def upload_video(actor, project, uploaded, transcript_upload=None):
    """UC2: validate with ffprobe BEFORE accepting (ADR 0004), store under a random key,
    then queue analysis. Rejections give a clear message and store nothing."""
    require_role(actor, project, Role.MEDIA_OPERATOR, Role.LOCALIZATION_MANAGER)
    if project.videos.exists():
        raise ValidationError("This project already has a source video (one per project in the MVP).")
    transcript_text = None
    if transcript_upload is not None:
        raw = transcript_upload.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValidationError("The transcript file is too large.")
        try:
            transcript_text = raw.decode("utf-8")
            parse_subtitles(transcript_text)
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValidationError(f"The transcript could not be read: {exc}") from None
    path, size = _spool(uploaded, settings.HL_MAX_UPLOAD_BYTES)
    try:
        try:
            info = media_tools.probe(path)
        except media_tools.MediaError:
            raise ValidationError("The file is not a readable video.") from None
        problems = media_tools.validate_source(info, max_seconds=settings.HL_MAX_VIDEO_SECONDS)
        if problems:
            raise ValidationError("The video was rejected: " + "; ".join(problems) + ".")
        storage = get_storage()
        key, sha = storage.save_file(path, ".mp4" if "mp4" in info["container"] else ".mkv")
    finally:
        os.unlink(path)
    transcript_key = ""
    if transcript_text is not None:
        transcript_key, _ = storage.save_bytes(transcript_text.encode("utf-8"), ".vtt")
    with transaction.atomic():
        video = Video.objects.create(
            project=project, original_name=os.path.basename(getattr(uploaded, "name", "video"))[:255],
            storage_key=key, transcript_key=transcript_key, sha256=sha, duration_ms=info["duration_ms"],
            container=info["container"], codecs={"video": info["video_codec"], "audio": info["audio_codec"]},
            size=size, uploaded_by=actor,
        )
        audit.record(actor=actor, action="VIDEO_UPLOADED", entity=video, project_id=project.pk,
                     details={"sha256": sha, "duration_ms": video.duration_ms, "size": size,
                              "human_transcript": bool(transcript_key)})
        jobs.enqueue("analyze_video", actor=actor, project=project, video=video)
    return video


@transaction.atomic
def assign_speaker(actor, speaker_track, identity_owner):
    """The Media Operator links a speaker in the video to an identity owner (ADR 0011).
    Linking alone grants nothing: identity use still needs the owner's consent."""
    project = speaker_track.video.project
    require_role(actor, project, Role.MEDIA_OPERATOR, Role.LOCALIZATION_MANAGER)
    speaker_track.identity_owner = identity_owner
    speaker_track.assigned_by = actor
    speaker_track.save(update_fields=["identity_owner", "assigned_by"])
    audit.record(actor=actor, action="SPEAKER_ASSIGNED", entity=speaker_track, project_id=project.pk,
                 details={"speaker": speaker_track.label, "identity_owner_id": identity_owner.pk if identity_owner else None})
    return speaker_track


def get_speaker_tracks(project):
    return SpeakerTrack.objects.filter(video__project=project).select_related("identity_owner")
