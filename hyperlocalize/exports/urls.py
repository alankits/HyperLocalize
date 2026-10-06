from django.urls import path

from . import views

app_name = "exports"
urlpatterns = [
    path("projects/<int:project_id>/export/", views.request_export, name="request"),
    path("exports/<int:export_id>/download/", views.download, name="download"),
]
