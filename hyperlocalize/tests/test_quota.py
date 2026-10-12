"""ADR 0005 free-quota warnings: Administrator-entered limits, an 80% warning, rolling windows,
and no warning (never a false "safe") when no limit is configured."""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from hyperlocalize.accounts.models import Policy
from hyperlocalize.audit.models import AuditRecord
from hyperlocalize.pipeline import quota
from hyperlocalize.pipeline.checks_report import report
from hyperlocalize.pipeline.models import ProviderUsage
from hyperlocalize.testing import make_users


def set_limits(limits):
    Policy.objects.update_or_create(key="provider_quota_limits", defaults={"value": limits})


def use(adapter, units, hours_ago=0, unit_type="requests"):
    row = ProviderUsage.objects.create(adapter=adapter, stage="localization", units=units, unit_type=unit_type)
    if hours_ago:
        ProviderUsage.objects.filter(pk=row.pk).update(created_at=timezone.now() - timedelta(hours=hours_ago))


class QuotaStatusTests(TestCase):
    def test_no_limit_configured_gives_no_rows_and_no_warnings(self):
        use("gemini_localization", 10_000)
        self.assertEqual(quota.quota_status(), [])
        self.assertEqual(quota.quota_warnings(), [])
        lines, _ = report()
        self.assertTrue(any("no free-tier limit configured" in line for line in lines))

    def test_levels_at_the_80_percent_and_100_percent_boundaries(self):
        set_limits({"gemini_localization": {"limit": 100, "period": "day", "unit_type": "requests"}})
        use("gemini_localization", 79)
        self.assertEqual(quota.quota_status()[0].level, "OK")
        use("gemini_localization", 1)
        self.assertEqual(quota.quota_status()[0].level, "WARN")
        use("gemini_localization", 20)
        row = quota.quota_status()[0]
        self.assertEqual((row.used, row.level), (100, "EXHAUSTED"))
        self.assertIn("quota EXHAUSTED: gemini_localization used 100 of 100", quota.quota_warnings()[0])

    def test_rolling_window_ignores_old_usage(self):
        set_limits({"a": {"limit": 10, "period": "day", "unit_type": "requests"},
                    "b": {"limit": 10, "period": "week", "unit_type": "requests"}})
        use("a", 9, hours_ago=25)
        use("b", 9, hours_ago=25)
        use("b", 9, hours_ago=24 * 8)
        rows = {r.adapter: r.used for r in quota.quota_status()}
        self.assertEqual(rows, {"a": 0, "b": 9})

    def test_unrecorded_unit_types_are_refused(self):
        # Only "requests" is written to the ledger today; a tokens limit would always read 0 used.
        set_limits({"a": {"limit": 10, "period": "day", "unit_type": "tokens"}})
        self.assertEqual(quota.configured_limits(), {})

    def test_invalid_entries_are_ignored(self):
        set_limits({"zero": {"limit": 0, "period": "day", "unit_type": "requests"},
                    "text": {"limit": "lots", "period": "day", "unit_type": "requests"},
                    "period": {"limit": 5, "period": "month", "unit_type": "requests"},
                    "unit": {"limit": 5, "period": "day", "unit_type": "gpu"},
                    "notadict": 5})
        self.assertEqual(quota.configured_limits(), {})

    def test_check_providers_reports_the_warning(self):
        set_limits({"gemini_localization": {"limit": 10, "period": "day", "unit_type": "requests"}})
        use("gemini_localization", 9)
        lines, warnings = report()
        self.assertTrue(any(line.startswith("quota: gemini_localization 9 / 10") for line in lines))
        self.assertTrue(any(w.startswith("quota WARN: gemini_localization") for w in warnings))


class QuotaPolicyPageTests(TestCase):
    def setUp(self):
        self.users = make_users()

    def post(self, user, **extra):
        self.client.force_login(self.users[user])
        data = {"preview_retention_days": 30, "export_retention_days": 90, "separation_of_duties": "on",
                "cloning_allowed": "on", "synthesis_allowed": "on", **extra}
        return self.client.post(reverse("accounts:policies"), data)

    def test_admin_saves_limits_and_the_change_is_audited(self):
        self.post("admin", quota_limit_gemini_localization="50", quota_period_gemini_localization="week",
                  quota_unit_gemini_localization="requests")
        self.assertEqual(Policy.get("provider_quota_limits"),
                         {"gemini_localization": {"limit": 50, "period": "week", "unit_type": "requests"}})
        self.assertEqual(Policy.get("preview_retention_days"), 30)  # scalar policies still saved
        last = AuditRecord.objects.filter(action="POLICY_CHANGED").latest("id")
        self.assertIn("provider_quota_limits", last.details)

    def test_blank_or_invalid_limit_removes_the_entry(self):
        set_limits({"gemini_localization": {"limit": 50, "period": "week", "unit_type": "requests"}})
        self.post("admin", quota_limit_gemini_localization="", quota_period_gemini_localization="week",
                  quota_unit_gemini_localization="requests", quota_limit_gemini_meaning_check="-3",
                  quota_period_gemini_meaning_check="day", quota_unit_gemini_meaning_check="requests")
        self.assertEqual(Policy.get("provider_quota_limits"), {})

    def test_unregistered_adapter_names_are_not_saved(self):
        self.post("admin", quota_limit_made_up="5", quota_period_made_up="day", quota_unit_made_up="requests")
        self.assertEqual(Policy.get("provider_quota_limits"), {})

    def test_non_admin_cannot_change_limits(self):
        r = self.post("manager", quota_limit_gemini_localization="5", quota_period_gemini_localization="day",
                      quota_unit_gemini_localization="requests")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Policy.get("provider_quota_limits"), {})

    def test_page_shows_the_warning_badge(self):
        set_limits({"gemini_localization": {"limit": 10, "period": "day", "unit_type": "requests"}})
        use("gemini_localization", 8)
        self.client.force_login(self.users["admin"])
        r = self.client.get(reverse("accounts:policies"))
        self.assertContains(r, "8 / 10 (80%)")
        self.assertContains(r, "near limit")
        self.assertContains(r, "no limit configured")

    def test_unmetered_adapters_get_no_limit_inputs(self):
        # Speech is not metered, and mocks are never counted: a limit there would always read 0 used.
        self.post("admin", quota_limit_mock_stock_voice="5", quota_period_mock_stock_voice="day",
                  quota_unit_mock_stock_voice="requests", quota_limit_mock_localization="5",
                  quota_period_mock_localization="day", quota_unit_mock_localization="requests")
        self.assertEqual(Policy.get("provider_quota_limits"), {})
        r = self.client.get(reverse("accounts:policies"))
        self.assertContains(r, "quota_limit_gemini_localization")
        self.assertNotContains(r, "quota_limit_mock_stock_voice")
        self.assertNotContains(r, "quota_limit_mock_localization")

    def test_policy_labels_are_readable(self):
        self.client.force_login(self.users["admin"])
        self.assertContains(self.client.get(reverse("accounts:policies")), "Separation of duties")
