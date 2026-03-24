from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.search_movies_view, name="search"),
    path("search/api/", views.search_api, name="search_api"),
]