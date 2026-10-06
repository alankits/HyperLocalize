from django.core.management.base import BaseCommand, CommandError

from hyperlocalize.audit.services import verify_chain


class Command(BaseCommand):
    help = "Recompute the audit hash chain and report the first mismatch (ADR 0007)."

    def handle(self, *args, **options):
        ok, count, bad_seq, message = verify_chain()
        if ok:
            self.stdout.write(self.style.SUCCESS(f"Audit chain OK: {count} records verified."))
            return
        raise CommandError(f"Audit chain FAILED after {count} good records at seq {bad_seq}: {message}")
