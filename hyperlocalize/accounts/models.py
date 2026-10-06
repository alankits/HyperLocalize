"""Users, project memberships and roles (ADR 0011), and admin policies (UC8)."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Global flag (ADR 0011). Administrators manage users, providers and policies.
    # They cannot grant consent on anyone's behalf.
    is_administrator = models.BooleanField(default=False)

    class Meta:
        db_table = "accounts_user"


class Role(models.TextChoices):
    LOCALIZATION_MANAGER = "LOCALIZATION_MANAGER", "Localization Manager"
    REVIEWER = "REVIEWER", "Reviewer / Linguist"
    MEDIA_OPERATOR = "MEDIA_OPERATOR", "Media Operator"
    AUDITOR = "AUDITOR", "Auditor"


class ProjectMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=32, choices=Role.choices)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "project", "role"], name="uniq_membership_role")]

    def __str__(self):
        return f"{self.user} {self.role} @ {self.project_id}"


class Policy(models.Model):
    """Administrator-editable policy values (ADR 0004 retention, ADR 0011 separation of duties,
    ADR 0015 whether voice cloning / synthesis is allowed)."""

    key = models.CharField(max_length=64, unique=True)
    value = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    DEFAULTS = {
        "separation_of_duties": True,  # ADR 0011, Q13
        "cloning_allowed": True,  # ADR 0015 (resolved per speaker by the backend)
        "synthesis_allowed": True,  # False → SUBTITLES_ONLY (ADR 0015)
        "preview_retention_days": 30,  # ADR 0004, Q15
        "export_retention_days": 90,  # ADR 0004, Q15
    }

    def __str__(self):
        return f"{self.key}={self.value}"

    @classmethod
    def get(cls, key):
        row = cls.objects.filter(key=key).first()
        return row.value if row else cls.DEFAULTS[key]
