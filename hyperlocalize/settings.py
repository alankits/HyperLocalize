"""Django settings for HyperLocalize.

All secrets and machine-specific values come from environment variables
(see `.env.example`). Nothing secret is committed.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name, default=None):
    value = os.environ.get(name)
    return default if value in (None, "") else value


def _load_dotenv(path):
    """Minimal .env loader (KEY=VALUE lines). Real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")

# dev | test | demo. Mock providers are registered only in dev and test (ADR 0005).
HYPERLOCALIZE_MODE = _env("HYPERLOCALIZE_MODE", "dev")
if HYPERLOCALIZE_MODE not in ("dev", "test", "demo"):
    raise ImproperlyConfigured("HYPERLOCALIZE_MODE must be dev, test or demo")

DEBUG = _env("HL_DEBUG", "1" if HYPERLOCALIZE_MODE == "dev" else "0") == "1"

SECRET_KEY = _env("HL_SECRET_KEY")
if not SECRET_KEY:
    if HYPERLOCALIZE_MODE == "demo":
        raise ImproperlyConfigured("HL_SECRET_KEY must be set in demo mode")
    SECRET_KEY = "dev-only-insecure-key-do-not-use-in-demo"

ALLOWED_HOSTS = [h.strip() for h in _env("HL_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "hyperlocalize.accounts",
    "hyperlocalize.audit",
    "hyperlocalize.projects",
    "hyperlocalize.identity",
    "hyperlocalize.localization",
    "hyperlocalize.rendering",
    "hyperlocalize.review",
    "hyperlocalize.exports",
    "hyperlocalize.pipeline",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "hyperlocalize.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "hyperlocalize" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "hyperlocalize.accounts.context.mode",
            ],
        },
    },
]

WSGI_APPLICATION = "hyperlocalize.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env("HL_DB_NAME", "hyperlocalize"),
        "USER": _env("HL_DB_USER", "hl"),
        "PASSWORD": _env("HL_DB_PASSWORD", ""),
        "HOST": os.path.expanduser(_env("HL_DB_HOST", "~/.local/hl-dev/run")),
        "PORT": _env("HL_DB_PORT", "5433"),
        "ATOMIC_REQUESTS": False,
    }
}

CACHES = {
    # A database cache, so the login rate limit is shared by all processes.
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "hl_cache",
    }
}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "projects:list"
LOGOUT_REDIRECT_URL = "accounts:login"

# Login rate limit (ADR 0011): failures per username+IP within the window.
HL_LOGIN_MAX_FAILURES = int(_env("HL_LOGIN_MAX_FAILURES", "5"))
HL_LOGIN_WINDOW_SECONDS = int(_env("HL_LOGIN_WINDOW_SECONDS", "900"))

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "hyperlocalize" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media lives outside the web root and outside the repository (ADR 0004).
# It is never served by a static handler; only by authorised views.
HL_MEDIA_ROOT = Path(os.path.expanduser(_env("HL_MEDIA_ROOT", "~/hl-media")))

# MVP upload limits (ADR 0004, Q16). These are MVP values, not product limits.
HL_MAX_UPLOAD_BYTES = int(_env("HL_MAX_UPLOAD_BYTES", str(500 * 1024 * 1024)))
HL_MAX_VIDEO_SECONDS = int(_env("HL_MAX_VIDEO_SECONDS", str(5 * 60)))
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# External tools. Empty means "look on PATH" (and, in dev, the static-ffmpeg package).
HL_FFMPEG = _env("HL_FFMPEG", "")
HL_FFPROBE = _env("HL_FFPROBE", "")

# Optional real-provider credentials. Absent keys simply disable that adapter.
HL_GEMINI_API_KEY = _env("HL_GEMINI_API_KEY", "")
HL_GEMINI_MODEL = _env("HL_GEMINI_MODEL", "gemini-2.5-flash")

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # htmx reads the token from the meta tag, not the cookie.
SESSION_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": _env("HL_LOG_LEVEL", "INFO")},
}
