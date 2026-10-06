from django.urls import include, path

urlpatterns = [
    path("", include("hyperlocalize.projects.urls")),
    path("accounts/", include("hyperlocalize.accounts.urls")),
]
