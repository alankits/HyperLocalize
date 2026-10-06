from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from hyperlocalize.identity import demo

from ._demo_args import add_common, resolve


class Command(BaseCommand):
    help = "Register the owner's reference clip as the demo seed (ADR 0020 §3)."

    def add_arguments(self, parser):
        add_common(parser)

    def handle(self, *args, **options):
        admin, owner, project = resolve(options)
        try:
            copy = demo.build_demo_seed(admin, project, owner)
        except (ValidationError, PermissionDenied) as exc:
            raise CommandError(str(exc)) from None
        self.stdout.write(self.style.SUCCESS(f"Seed built: offline copy #{copy.pk} ({copy.kind})."))
