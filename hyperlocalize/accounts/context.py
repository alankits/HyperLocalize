from django.conf import settings


def mode(request):
    """Expose the run mode so templates can show the MOCK / DEV banner (ADR 0005)."""
    return {"HL_MODE": settings.HYPERLOCALIZE_MODE}
