from django.urls import path

from . import views

urlpatterns = [
    path("", views.pick_movie, name="pick_movie"),
    path("alternatives/", views.pick_alternatives, name="pick_alternatives"),
    path("watched/", views.mark_watched, name="mark_watched"),
    path("report/", views.report_pick, name="report_pick"),
    path("trailer/<int:tmdb_id>/", views.get_trailer, name="get_trailer"),
    path("<int:tmdb_id>/", views.pick_detail, name="pick_detail"),
]
