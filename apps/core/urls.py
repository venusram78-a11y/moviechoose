from django.urls import path

from . import views

urlpatterns = [
    path("", views.homepage, name="home"),
    path("about/", views.about, name="about"),
    path("privacy/", views.privacy_policy, name="privacy"),
    path("terms/", views.terms_of_service, name="terms"),
    path("health/", views.health_check, name="health"),
    path("consent/", views.set_consent, name="set_consent"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),
]
