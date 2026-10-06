from django.urls import include, path

urlpatterns = [
    path("", include("hyperlocalize.projects.urls")),
    path("", include("hyperlocalize.review.urls")),
    path("", include("hyperlocalize.exports.urls")),
    path("", include("hyperlocalize.audit.urls")),
    path("me/", include("hyperlocalize.identity.urls")),
    path("accounts/", include("hyperlocalize.accounts.urls")),
]
