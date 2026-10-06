"""Consent gate tests (ADR 0006 as amended by ADR 0020). Negative cases first."""
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from hyperlocalize.audit.models import AuditRecord
from hyperlocalize.projects.models import Project
from hyperlocalize.testing import MediaRootMixin, make_owner_with_consent, make_project, make_users

from . import services as identity
from .models import Consent, IdentityOwner, OfflineCopy


class ConsentGateNegativeTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.users = make_users()
        self.project = make_project(self.users)
        self.owner = IdentityOwner.objects.create(name="Owner", user=self.users["speaker"])

    def test_no_consent_is_denied_and_audited(self):
        with self.assertRaises(identity.ConsentDenied) as cm:
            identity.require_active_consent(self.owner, "voice_synthesis", self.project, "ta", actor=self.users["manager"])
        self.assertEqual(cm.exception.reason, "NO_CONSENT")
        self.assertTrue(AuditRecord.objects.filter(action="CONSENT_DENIED").exists())

    def test_project_consent_needs_a_standing_consent(self):
        with self.assertRaises(identity.ConsentDenied):
            identity.grant_project_consent(self.users["speaker"], self.owner, self.project, uses=["voice_synthesis"],
                                           languages=["ta"], processors=[], expires_at=timezone.now() + timedelta(days=1))

    def test_administrator_cannot_grant_on_anyones_behalf(self):
        with self.assertRaises(PermissionDenied):
            identity.grant_standing_consent(self.users["admin"], self.owner, uses=["voice_synthesis"],
                                            permitted_purposes=["STANDARD"], permitted_copy_kinds=[], languages=["ta"],
                                            processors=[], expires_at=timezone.now() + timedelta(days=1), evidence_ref="F1")

    def test_other_user_cannot_grant(self):
        with self.assertRaises(PermissionDenied):
            identity.grant_standing_consent(self.users["manager"], self.owner, uses=["voice_synthesis"],
                                            permitted_purposes=["STANDARD"], permitted_copy_kinds=[], languages=["ta"],
                                            processors=[], expires_at=timezone.now() + timedelta(days=1), evidence_ref="F1")

    def test_evidence_is_required(self):
        with self.assertRaises(ValidationError):
            identity.grant_standing_consent(self.users["speaker"], self.owner, uses=["voice_synthesis"],
                                            permitted_purposes=["STANDARD"], permitted_copy_kinds=[], languages=["ta"],
                                            processors=[], expires_at=timezone.now() + timedelta(days=1), evidence_ref=" ")

    def test_project_consent_cannot_be_wider_than_standing(self):
        exp = timezone.now() + timedelta(days=10)
        identity.grant_standing_consent(self.users["speaker"], self.owner, uses=["voice_synthesis"],
                                        permitted_purposes=["STANDARD"], permitted_copy_kinds=[], languages=["ta"],
                                        processors=[], expires_at=exp, evidence_ref="F1")
        for kwargs in ({"languages": ["ta", "hi"]}, {"expires_at": exp + timedelta(days=1)},
                       {"uses": ["voice_synthesis", "remote_voice_processing"]}, {"processors": ["kaggle"]}):
            args = {"uses": ["voice_synthesis"], "languages": ["ta"], "processors": [], "expires_at": exp, **kwargs}
            with self.assertRaises(identity.ConsentDenied, msg=str(kwargs)):
                identity.grant_project_consent(self.users["speaker"], self.owner, self.project, **args)

    def test_rehearsal_project_needs_both_purposes(self):
        rehearsal = Project.objects.create(name="Rehearsal", created_by=self.users["manager"], purpose="DEMO_REHEARSAL")
        exp = timezone.now() + timedelta(days=10)
        identity.grant_standing_consent(self.users["speaker"], self.owner, uses=["voice_synthesis"],
                                        permitted_purposes=["DEMO_REHEARSAL"], permitted_copy_kinds=[], languages=["ta"],
                                        processors=[], expires_at=exp, evidence_ref="F1")
        with self.assertRaises(identity.ConsentDenied):
            identity.grant_project_consent(self.users["speaker"], self.owner, rehearsal, uses=["voice_synthesis"],
                                           languages=["ta"], processors=[], expires_at=exp)


class ConsentLifecycleTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.users = make_users()
        self.project = make_project(self.users)
        self.owner = make_owner_with_consent(self.users, self.project)

    def test_valid_consent_passes(self):
        check = identity.require_active_consent(self.owner, "voice_synthesis", self.project, "ta")
        self.assertEqual(check.project_id, self.project.pk)

    def test_wrong_use_or_language_is_denied(self):
        for use, lang, reason in [("remote_voice_processing", "ta", "USE_NOT_GRANTED"), ("voice_synthesis", "hi", "LANGUAGE_NOT_GRANTED")]:
            self.assertEqual(identity.evaluate(self.owner, use, self.project, lang)[1], reason)

    def test_revoked_consent_is_denied(self):
        identity.revoke_project_consent(self.users["speaker"], self.owner, self.project)
        check, reason = identity.evaluate(self.owner, "voice_synthesis", self.project, "ta")
        self.assertIsNone(check)
        self.assertEqual(reason, "CONSENT_REVOKED")
        self.assertTrue(AuditRecord.objects.filter(action="CONSENT_REVOKED").exists())

    def test_only_the_owner_can_revoke_in_a_project(self):
        with self.assertRaises(PermissionDenied):
            identity.revoke_project_consent(self.users["admin"], self.owner, self.project)

    def test_expired_consent_is_denied(self):
        later = timezone.now() + timedelta(days=60)
        self.assertEqual(identity.evaluate(self.owner, "voice_synthesis", self.project, "ta", now=later)[1], "CONSENT_EXPIRED")

    def test_old_version_cannot_be_saved_after_revocation(self):
        check = identity.require_active_consent(self.owner, "voice_synthesis", self.project, "ta")
        identity.revoke_project_consent(self.users["speaker"], self.owner, self.project)
        self.assertFalse(identity.locked_save_allowed(check, self.project))

    def test_narrowing_a_language_cascades_project_scope(self):
        identity.narrow_standing_consent(self.users["speaker"], self.owner, remove={"languages": ["ta"]})
        pc = identity.latest_project_consent(self.owner, self.project)
        self.assertEqual(pc.status, Consent.Status.REVOKED)
        self.assertIsNone(identity.evaluate(self.owner, "voice_synthesis", self.project, "ta")[0])

    def test_removing_the_purpose_cascades(self):
        identity.narrow_standing_consent(self.users["speaker"], self.owner, remove={"permitted_purposes": ["STANDARD"]})
        self.assertIsNone(identity.evaluate(self.owner, "voice_synthesis", self.project, "ta")[0])

    def test_administrator_narrowing_needs_a_recorded_request(self):
        with self.assertRaises(PermissionDenied):
            identity.narrow_standing_consent(self.users["admin"], self.owner, remove={"languages": ["ta"]})
        identity.narrow_standing_consent(self.users["admin"], self.owner, remove={"languages": ["ta"]},
                                         request_ref="phone call to the withdrawal contact, 2026-10-06 10:00")
        self.assertIsNone(identity.evaluate(self.owner, "voice_synthesis", self.project, "ta")[0])

    def test_withdrawal_is_final(self):
        identity.withdraw(self.users["speaker"], self.owner)
        self.owner.refresh_from_db()
        self.assertIsNotNone(self.owner.withdrawn_at)
        self.assertEqual(identity.evaluate(self.owner, "voice_synthesis", self.project, "ta")[1], "WITHDRAWN")
        self.assertTrue(AuditRecord.objects.filter(action="IDENTITY_WITHDRAWN").exists())
        with self.assertRaises(identity.ConsentDenied):
            identity.grant_standing_consent(self.users["speaker"], self.owner, uses=["voice_synthesis"],
                                            permitted_purposes=["STANDARD"], permitted_copy_kinds=[], languages=["ta"],
                                            processors=[], expires_at=timezone.now() + timedelta(days=5), evidence_ref="NEW")

    def test_widening_needs_a_new_signed_form(self):
        st = identity.latest_standing(self.owner)
        with self.assertRaises(ValidationError):
            identity.grant_standing_consent(self.users["speaker"], self.owner, uses=["voice_synthesis"],
                                            permitted_purposes=["STANDARD", "DEMO_REHEARSAL"], permitted_copy_kinds=[],
                                            languages=["ta"], processors=[], expires_at=st.expires_at, evidence_ref=st.evidence_ref)
        identity.grant_standing_consent(self.users["speaker"], self.owner, uses=["voice_synthesis"],
                                        permitted_purposes=["STANDARD", "DEMO_REHEARSAL"], permitted_copy_kinds=[],
                                        languages=["ta"], processors=[], expires_at=st.expires_at, evidence_ref="FORM-2")

    def test_withdrawal_marks_offline_copies(self):
        st = identity.latest_standing(self.owner)
        copy = OfflineCopy.objects.create(identity_owner=self.owner, consent_version=st, kind="SCREEN_RECORDING",
                                          storage_key="aa/x.mp4", sha256="0" * 64)
        identity.withdraw(self.users["speaker"], self.owner)
        copy.refresh_from_db()
        self.assertEqual(copy.status, OfflineCopy.Status.DELETION_PENDING)

    def test_expiry_sweep(self):
        Consent.objects.filter(identity_owner=self.owner, kind="PROJECT").update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(identity.expire_due(), 1)
        self.assertEqual(identity.latest_project_consent(self.owner, self.project).status, Consent.Status.REVOKED)

    def test_every_consent_change_is_audited_with_its_version(self):
        records = AuditRecord.objects.filter(action="CONSENT_GRANTED")
        self.assertEqual(records.count(), 2)
        self.assertTrue(all(r.consent_version for r in records))
