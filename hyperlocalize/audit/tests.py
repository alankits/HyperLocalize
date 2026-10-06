from django.db import DatabaseError, connection, transaction
from django.test import TestCase

from hyperlocalize.accounts.models import User
from hyperlocalize.testing import AuditSafeTransactionTestCase

from . import services
from .models import AuditRecord


class AuditChainTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="x-Pass-12345")

    def _record(self, action="TEST_ACTION", **details):
        with transaction.atomic():
            return services.record(actor=self.user, action=action, entity=("test", 1), details=details)

    def test_chain_links_and_verifies(self):
        a = self._record(n=1)
        b = self._record(n=2)
        self.assertEqual(a.seq, 1)
        self.assertEqual(b.seq, 2)
        self.assertEqual(b.prev_hash, a.hash)
        ok, count, bad, _ = services.verify_chain()
        self.assertTrue(ok)
        self.assertEqual(count, 2)
        self.assertIsNone(bad)

    def test_floats_rejected(self):
        with self.assertRaises(services.AuditError):
            self._record(score=0.5)

    def test_raw_content_keys_rejected(self):
        with self.assertRaises(services.AuditError):
            self._record(source_text="secret words")

    def test_system_actor(self):
        with transaction.atomic():
            rec = services.record(actor=None, action="SYSTEM_EVENT", entity=("test", 2))
        self.assertEqual(rec.actor_label, "system")
        self.assertIsNone(rec.actor_id)

    def test_canonical_json_is_order_independent(self):
        self.assertEqual(services.canonical_json({"b": 1, "a": 2}), services.canonical_json({"a": 2, "b": 1}))


class AppendOnlyTriggerTests(AuditSafeTransactionTestCase):
    """The database itself rejects edits (ADR 0007). Negative cases first."""

    def test_record_requires_transaction(self):
        # Outside an atomic block the record would not share the action's transaction.
        with self.assertRaises(services.AuditError):
            services.record(actor=None, action="X", entity=("test", 1))

    def setUp(self):
        with transaction.atomic():
            self.rec = services.record(actor=None, action="SEED", entity=("test", 1))

    def test_update_rejected(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            AuditRecord.objects.filter(pk=self.rec.pk).update(action="TAMPERED")

    def test_delete_rejected(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            AuditRecord.objects.filter(pk=self.rec.pk).delete()

    def test_truncate_rejected(self):
        with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
            cur.execute("TRUNCATE audit_record")

    def test_tampering_with_trigger_disabled_is_detected(self):
        # Simulates someone with table-owner rights disabling the trigger and editing a record.
        with transaction.atomic():
            services.record(actor=None, action="SECOND", entity=("test", 2))
        with connection.cursor() as cur:
            cur.execute("ALTER TABLE audit_record DISABLE TRIGGER audit_record_no_update_delete")
            cur.execute("UPDATE audit_record SET action = 'TAMPERED' WHERE seq = 1")
            cur.execute("ALTER TABLE audit_record ENABLE TRIGGER audit_record_no_update_delete")
        ok, _, bad, message = services.verify_chain()
        self.assertFalse(ok)
        self.assertEqual(bad, 1)
        self.assertIn("hash mismatch", message)
