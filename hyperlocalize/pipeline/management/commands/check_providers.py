from django.core.management.base import BaseCommand

from hyperlocalize.pipeline.checks_report import report


class Command(BaseCommand):
    help = "Check providers, media tools, usage and drift before a demo (ADR 0012 item 1, ADR 0020 §4)."

    def handle(self, *args, **options):
        lines, warnings = report()
        for line in lines:
            self.stdout.write(line)
        for w in warnings:
            self.stdout.write(self.style.WARNING(f"WARNING: {w}"))
        if not warnings:
            self.stdout.write(self.style.SUCCESS("No warnings."))
