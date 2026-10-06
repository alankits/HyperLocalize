from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from hyperlocalize.accounts.models import Role
from hyperlocalize.accounts.permissions import require_member, require_role
from hyperlocalize.audit import services as audit
from hyperlocalize.localization.models import Localization
from hyperlocalize.projects.models import Project
from hyperlocalize.projects.storage import get_storage

from . import services
from .models import Export


@login_required
@require_POST
def request_export(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    require_member(request.user, project)
    try:
        services.request_export(request.user, Localization.objects.get(project=project))
        messages.success(request, "Export queued. The package appears below when the job finishes.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc))
    return redirect("projects:detail", project.pk)


@login_required
def download(request, export_id):
    export = get_object_or_404(Export.objects.select_related("approval__localization__project"), pk=export_id)
    project = export.approval.localization.project
    require_role(request.user, project, Role.LOCALIZATION_MANAGER, Role.AUDITOR)
    ok, reason = services.can_download(export)  # CP10
    if not ok:
        raise Http404(reason)
    with transaction.atomic():
        audit.record(actor=request.user, action="EXPORT_DOWNLOADED", entity=export, project_id=project.pk,
                     details={"package_sha256": export.package_sha256})
    return FileResponse(get_storage().open(export.package_key), as_attachment=True,
                        filename=f"hyperlocalize-export-{export.pk}.zip")
