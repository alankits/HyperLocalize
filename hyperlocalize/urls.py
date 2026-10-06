from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "HyperLocalize administration (users and memberships)"

urlpatterns = [
    path("", include("hyperlocalize.projects.urls")),
    path("", include("hyperlocalize.review.urls")),
    path("", include("hyperlocalize.exports.urls")),
    path("", include("hyperlocalize.audit.urls")),
    path("me/", include("hyperlocalize.identity.urls")),
    path("accounts/", include("hyperlocalize.accounts.urls")),
    path("admin/", admin.site.urls),
]
