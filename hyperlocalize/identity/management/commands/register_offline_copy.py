from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from hyperlocalize.identity import demo

from ._demo_args import add_common, resolve


class Command(BaseCommand):
    help = "Register a screen recording made outside the system, so withdrawal deletes it (ADR 0020 §4)."

    def add_arguments(self, parser):
        add_common(parser, project=False)
        parser.add_argument("file", help="Path of the recording to copy into media/offline/.")

    def handle(self, *args, file, **options):
        admin, owner, _ = resolve(options, project=False)
        try:
            copy = demo.register_offline_copy(admin, owner, file)
        except (ValidationError, PermissionDenied) as exc:
            raise CommandError(str(exc)) from None
        self.stdout.write(self.style.SUCCESS(f"Registered offline copy #{copy.pk}. Delete the original file yourself."))
