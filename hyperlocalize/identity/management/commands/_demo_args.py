from django.core.management.base import CommandError

from hyperlocalize.accounts.models import User
from hyperlocalize.identity.models import IdentityOwner
from hyperlocalize.projects.models import Project


def add_common(parser, project=True):
    parser.add_argument("--admin", required=True, help="Username of the Administrator running the command (audited).")
    parser.add_argument("--owner", type=int, required=True, help="IdentityOwner id.")
    if project:
        parser.add_argument("--project", type=int, required=True, help="Source project id.")


def resolve(options, project=True):
    try:
        admin = User.objects.get(username=options["admin"])
        owner = IdentityOwner.objects.get(pk=options["owner"])
        proj = Project.objects.get(pk=options["project"]) if project else None
    except (User.DoesNotExist, IdentityOwner.DoesNotExist, Project.DoesNotExist) as exc:
        raise CommandError(str(exc)) from None
    return admin, owner, proj
