from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.core.cache import cache
from django.shortcuts import redirect, render

from hyperlocalize.audit import services as audit

from .models import Policy
from .permissions import require_administrator


def _key(request):
    username = (request.POST.get("username") or "").lower()[:150]
    return f"login-fail:{username}:{request.META.get('REMOTE_ADDR', '')}"


class LoginView(auth_views.LoginView):
    """Session login with a failure rate limit per username and address (ADR 0011)."""

    template_name = "accounts/login.html"

    def post(self, request, *args, **kwargs):
        if cache.get(_key(request), 0) >= settings.HL_LOGIN_MAX_FAILURES:
            form = self.get_form()
            form.add_error(None, "Too many failed attempts. Try again later.")
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        key = _key(self.request)
        cache.set(key, cache.get(key, 0) + 1, settings.HL_LOGIN_WINDOW_SECONDS)
        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(_key(self.request))
        return super().form_valid(form)


def policies(request):
    """UC8: the Administrator edits policies (ADR 0004, ADR 0011, ADR 0015) and provider chains (ADR 0005)."""
    from django.db import transaction

    from hyperlocalize.pipeline import quota
    from hyperlocalize.pipeline.models import ProviderConfig
    from hyperlocalize.pipeline.providers.base import DEFAULT_CHAINS, chain_for, registered

    require_administrator(request.user)
    if request.method == "POST":
        with transaction.atomic():
            for key, default in Policy.DEFAULTS.items():
                if isinstance(default, dict):
                    continue  # structured policies are saved below
                if isinstance(default, bool):
                    value = request.POST.get(key) == "on"
                else:
                    try:
                        value = max(1, int(request.POST.get(key, default)))
                    except ValueError:
                        value = default
                Policy.objects.update_or_create(key=key, defaults={"value": value})
            limits = {}
            for a in registered():
                if not quota.is_metered(a):
                    continue
                entry = quota.clean_limit({"limit": request.POST.get(f"quota_limit_{a.name}"),
                                           "period": request.POST.get(f"quota_period_{a.name}"),
                                           "unit_type": request.POST.get(f"quota_unit_{a.name}")})
                if entry:  # a blank or invalid limit removes the entry
                    limits[a.name] = entry
            Policy.objects.update_or_create(key="provider_quota_limits", defaults={"value": limits})
            for stage in DEFAULT_CHAINS:
                names = [n.strip() for n in request.POST.get(f"chain_{stage}", "").split(",") if n.strip()]
                if names:
                    ProviderConfig.objects.update_or_create(stage=stage, defaults={"adapters": names})
            audit.record(actor=request.user, action="POLICY_CHANGED", entity=("accounts.Policy", "all"),
                         details={k: Policy.get(k) for k in Policy.DEFAULTS})
        messages.success(request, "Policies saved.")
        return redirect("accounts:policies")
    adapters = registered()
    limits = quota.configured_limits()
    status = {row.adapter: row for row in quota.quota_status()}
    return render(request, "accounts/policies.html", {
        "policies": [(k, k.replace("_", " ").capitalize(), Policy.get(k), isinstance(d, bool))
                     for k, d in Policy.DEFAULTS.items() if not isinstance(d, dict)],
        "chains": [(stage, ", ".join(chain_for(stage))) for stage in DEFAULT_CHAINS],
        "adapters": adapters,
        "quota_rows": [(a, limits.get(a.name), status.get(a.name)) for a in adapters if quota.is_metered(a)],
        "periods": list(quota.PERIODS),
        "unit_types": quota.UNIT_TYPES,
        "warn_at": quota.WARN_AT_PERCENT,
    })
