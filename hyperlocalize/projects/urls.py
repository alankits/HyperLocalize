from django.shortcuts import redirect
from django.urls import path

from . import views

app_name = "projects"
urlpatterns = [
    path("", lambda r: redirect("projects:list")),
    path("projects/", views.project_list, name="list"),
    path("projects/new/", views.project_create, name="create"),
    path("projects/<int:pk>/", views.project_detail, name="detail"),
    path("projects/<int:pk>/jobs/", views.project_jobs, name="jobs"),
    path("projects/<int:pk>/upload/", views.upload, name="upload"),
    path("projects/<int:pk>/members/", views.add_member, name="add_member"),
    path("projects/<int:pk>/audience/", views.update_audience, name="audience"),
    path("projects/<int:pk>/glossary/", views.add_glossary, name="glossary"),
    path("projects/<int:pk>/speakers/<int:track_id>/", views.assign_speaker, name="assign_speaker"),
    path("projects/<int:pk>/source.mp4", views.source_video, name="source_video"),
]
