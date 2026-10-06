"""Test helpers shared by the apps."""
from django.db import connection
from django.test import TransactionTestCase


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
