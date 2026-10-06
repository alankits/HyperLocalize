from django.urls import path

from . import views

app_name = "review"
urlpatterns = [
    path("scenes/<int:scene_id>/", views.scene_review, name="scene"),
    path("scenes/<int:scene_id>/accept/", views.accept, name="accept"),
    path("scenes/<int:scene_id>/changes/", views.request_changes, name="changes"),
    path("segments/<int:segment_id>/edit/", views.edit_segment, name="edit"),
    path("checks/<int:check_id>/resolve/", views.resolve_check, name="resolve"),
    path("projects/<int:project_id>/approve/", views.approve, name="approve"),
    path("previews/<int:render_id>.mp4", views.preview_video, name="preview_video"),
    path("previews/<int:render_id>.vtt", views.preview_vtt, name="preview_vtt"),
]
