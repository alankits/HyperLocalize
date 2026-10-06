from django.urls import path

from . import views

app_name = "identity"
urlpatterns = [
    path("consent/", views.consent_page, name="consent"),
    path("consent/standing/", views.grant_standing, name="grant_standing"),
    path("consent/narrow/", views.narrow, name="narrow"),
    path("consent/withdraw/", views.withdraw, name="withdraw"),
    path("owners/new/", views.invite_owner, name="invite_owner"),
    path("consent/projects/<int:project_id>/grant/", views.grant_project, name="grant_project"),
    path("consent/projects/<int:project_id>/revoke/", views.revoke_project, name="revoke_project"),
    path("consent/projects/<int:project_id>/voice/", views.upload_profile, name="upload_profile"),
]
