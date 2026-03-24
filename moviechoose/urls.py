from django.contrib import admin
from django.urls import include, path
from decouple import config
import os
import sys

ADMIN_URL = config("ADMIN_URL", default="")
if not ADMIN_URL:
    current_settings = os.environ.get("DJANGO_SETTINGS_MODULE", "")
    if not current_settings.endswith("production"):
        ADMIN_URL = "dev-admin/"
    else:
        raise ValueError(
            "ADMIN_URL must be set in .env before production use. Example: ADMIN_URL=xk72ma-panel-9f3b/"
        )

urlpatterns = [
    path(ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
    path("pick/", include("apps.picker.urls")),
    path("movies/", include("apps.movies.urls")),
]

handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"
