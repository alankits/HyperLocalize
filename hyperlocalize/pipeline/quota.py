"""Free-quota warnings (ADR 0005): compare the ProviderUsage ledger with Administrator-entered limits.

The limits are typed in by the Administrator from each provider's own console. They are never
hard-coded, because free-tier limits change without notice. With no limit entered, an adapter is
reported as "no limit configured" and never as safe.

Windows are rolling (the last 24 hours or 7 days). Providers reset on their own calendars, so this
is an early warning for the team, not enforcement: nothing is blocked here. When a provider really
runs out, its adapter raises QuotaExhausted and the chain moves on (ADR 0005).
"""
from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from hyperlocalize.accounts.models import Policy

from .models import ProviderUsage

WARN_AT_PERCENT = 80  # ADR 0005
PERIODS = {"day": timedelta(hours=24), "week": timedelta(days=7)}
# Units that adapters actually write to ProviderUsage today. Add "tokens" or "audio_seconds" here
# only when an adapter records them; otherwise a limit in that unit would always read 0 used.
UNIT_TYPES = ("requests",)
# Stages whose adapters write ProviderUsage today (localization/services.py). A limit on any other
# stage would always read 0 used, which looks safe but isn't, so limits are only offered for these.
METERED_STAGES = ("localization", "meaning_check")


def is_metered(adapter):
    """True if this adapter writes ProviderUsage. Mocks are never counted (localization/services.py)."""
    return adapter.stage in METERED_STAGES and not adapter.is_mock


@dataclass
class QuotaRow:
    adapter: str
    unit_type: str
    period: str
    used: int
    limit: int

    @property
    def percent(self):
        return 100 * self.used // self.limit

    @property
    def level(self):
        if self.used >= self.limit:
            return "EXHAUSTED"
        return "WARN" if self.percent >= WARN_AT_PERCENT else "OK"


def clean_limit(raw):
    """Validate one limit entry; returns a clean dict, or None if the entry is missing or invalid."""
    if not isinstance(raw, dict):
        return None
    try:
        limit = int(raw.get("limit"))
    except (TypeError, ValueError):
        return None
    if limit < 1 or raw.get("period") not in PERIODS or raw.get("unit_type") not in UNIT_TYPES:
        return None
    return {"limit": limit, "period": raw["period"], "unit_type": raw["unit_type"]}


def configured_limits():
    """{adapter name: clean limit} for every valid entry in the provider_quota_limits policy."""
    limits = Policy.get("provider_quota_limits") or {}
    return {name: c for name, raw in limits.items() if (c := clean_limit(raw))}


def usage(adapter, unit_type, period, now=None):
    since = (now or timezone.now()) - PERIODS[period]
    total = ProviderUsage.objects.filter(adapter=adapter, unit_type=unit_type, created_at__gte=since).aggregate(n=Sum("units"))["n"]
    return total or 0


def quota_status(now=None):
    """One row per adapter that has a limit configured, sorted by adapter name."""
    return [QuotaRow(name, c["unit_type"], c["period"], usage(name, c["unit_type"], c["period"], now), c["limit"])
            for name, c in sorted(configured_limits().items())]


def quota_warnings(now=None):
    return [f"quota {row.level}: {row.adapter} used {row.used} of {row.limit} {row.unit_type} "
            f"in the last {row.period} ({row.percent}%); consider switching the chain to the free alternative"
            for row in quota_status(now) if row.level != "OK"]
