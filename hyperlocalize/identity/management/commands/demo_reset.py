from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from hyperlocalize.identity import demo

from ._demo_args import add_common, resolve


class Command(BaseCommand):
    help = "Build a fresh DEMO_REHEARSAL project from the source project and the seed. Never restores (ADR 0020)."

    def add_arguments(self, parser):
        add_common(parser)

    def handle(self, *args, **options):
        admin, owner, project = resolve(options)
        try:
            new = demo.demo_reset(admin, project, owner)
        except (ValidationError, PermissionDenied) as exc:
            raise CommandError(str(exc)) from None
        self.stdout.write(self.style.SUCCESS(f"Rehearsal project #{new.pk} created: {new.name}. Start a worker to render previews."))
