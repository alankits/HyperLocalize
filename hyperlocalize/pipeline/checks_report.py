"""The `check_providers` report (ADR 0012 item 1, amended by ADR 0020 §4).

Reports which adapters can run, the media tools, recent provider usage, and drift warnings:
unregistered files in media/offline/, files whose hash matches a deleted copy, and a golden
project that uses identity. These are warnings for ACCIDENTAL drift, not tamper resistance.
"""
import os
from datetime import timedelta

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from hyperlocalize import media_tools

from .models import ProviderUsage
from .providers.base import DEFAULT_CHAINS, chain_for, get_adapter, registered


def report():
    lines, warnings = [], []
    lines.append(f"Mode: {settings.HYPERLOCALIZE_MODE}")
    registered()
    for stage in DEFAULT_CHAINS:
        parts = []
        for name in chain_for(stage):
            a = get_adapter(name)
            state = "not registered in this mode" if a is None else ("ready" if a.available() else "not configured")
            mock = " MOCK" if a is not None and a.is_mock else ""
            parts.append(f"{name}{mock} ({state})")
        lines.append(f"{stage}: " + " → ".join(parts))
        if not any(get_adapter(n) and get_adapter(n).available() for n in chain_for(stage)):
            warnings.append(f"no adapter can run for stage '{stage}'")
    for tool in ("ffmpeg", "ffprobe"):
        try:
            lines.append(f"{tool}: {getattr(media_tools, tool)()}")
        except media_tools.MediaError as exc:
            warnings.append(str(exc))
    since = timezone.now() - timedelta(hours=24)
    for row in ProviderUsage.objects.filter(created_at__gte=since).values("adapter", "unit_type").annotate(n=Sum("units")):
        lines.append(f"usage (24 h): {row['adapter']} {row['n']} {row['unit_type']} "
                     "(free-tier limits are not configured; check the provider's console)")
    warnings += drift_warnings()
    return lines, warnings


def drift_warnings():
    from hyperlocalize.identity.models import OfflineCopy, VoiceProfile
    from hyperlocalize.projects.storage import get_storage

    storage = get_storage()
    out = []
    registered_keys = set(OfflineCopy.objects.values_list("storage_key", flat=True))
    for key in storage.offline_files():
        if key not in registered_keys:
            out.append(f"unregistered file in media/offline/: {key}")
    deleted = set(OfflineCopy.objects.filter(status="DELETED").values_list("sha256", flat=True)) | set(
        VoiceProfile.objects.filter(status="DELETED").values_list("sha256", flat=True))
    if deleted:
        for key in storage.all_files():
            try:
                if storage.sha256(key) in deleted:
                    out.append(f"file matches a DELETED identity copy (exact hash): {key}")
            except OSError:
                continue
    golden = os.environ.get("GOLDEN_PROJECT_ID") or os.environ.get("HL_GOLDEN_PROJECT_ID")
    if golden:
        from hyperlocalize.identity.models import Consent
        from hyperlocalize.rendering.models import SynthesisedSegment

        if (Consent.objects.filter(project_id=golden).exists() or VoiceProfile.objects.filter(consent__project_id=golden).exists()
                or SynthesisedSegment.objects.filter(localization__project_id=golden, rendering_mode="CLONED_VOICE").exists()):
            out.append(f"golden project #{golden} uses identity; it must use stock voices only (ADR 0020 §2)")
    return out
