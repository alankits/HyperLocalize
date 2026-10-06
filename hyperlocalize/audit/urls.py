from django.urls import path

from . import views

app_name = "audit"
urlpatterns = [path("projects/<int:project_id>/audit/", views.project_audit, name="project")]
