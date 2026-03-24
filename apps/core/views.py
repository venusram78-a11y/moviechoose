from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from apps.movies.services.tmdb import TMDBService


@ensure_csrf_cookie
def homepage(request):
    from apps.movies.services.tmdb import TMDBService
    from apps.analytics.models import GlobalCounter
    
    tmdb_service = TMDBService()
    backdrop_urls = tmdb_service.get_backdrop_images_for_homepage()
    
    context = {
        'backdrop_urls': backdrop_urls,
        'total_picks': GlobalCounter.get_value('total_picks'),
    }
    return render(request, 'core/homepage.html', context)

def about(request):
    return render(request, "core/about.html")


def privacy_policy(request):
    return render(request, "core/privacy_policy.html")


def terms_of_service(request):
    return render(request, "core/terms_of_service.html")


def robots_txt(request):
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /pick/report/",
            "Disallow: /pick/watched/",
            "Sitemap: https://moviechoose.com/sitemap.xml",
        ]
    )
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    from apps.analytics.models import PickSession
    from apps.movies.models import Movie

    top_picks = (
        PickSession.objects.values("movie_id")
        .annotate(pick_count=Count("id"))
        .order_by("-pick_count")[:100]
    )
    movie_ids = [p["movie_id"] for p in top_picks if p["movie_id"]]
    movies = Movie.objects.filter(id__in=movie_ids).values("tmdb_id", "updated_at")

    static_urls = [
        ("https://moviechoose.com/", "1.0", "daily"),
        ("https://moviechoose.com/about/", "0.8", "monthly"),
        ("https://moviechoose.com/privacy/", "0.5", "yearly"),
        ("https://moviechoose.com/terms/", "0.5", "yearly"),
    ]
    movie_urls = [
        (f"https://moviechoose.com/pick/{m['tmdb_id']}/", "0.6", "weekly")
        for m in movies
    ]

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url, priority, changefreq in static_urls + movie_urls:
        xml_parts.append(
            f"""  <url>
    <loc>{url}</loc>
    <priority>{priority}</priority>
    <changefreq>{changefreq}</changefreq>
  </url>"""
        )
    xml_parts.append("</urlset>")
    return HttpResponse("\n".join(xml_parts), content_type="application/xml")


def health_check(request):
    checks = {}
    try:
        connection.ensure_connection()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        cache.set("health_check", "1", 10)
        checks["cache"] = "ok" if cache.get("health_check") else "miss"
    except Exception:
        checks["cache"] = "error"

    from django.conf import settings

    checks["tmdb_key_set"] = bool(getattr(settings, "TMDB_API_KEY", ""))
    all_ok = all(v == "ok" for v in checks.values() if isinstance(v, str))
    return JsonResponse(
        {"status": "ok" if all_ok else "degraded", "checks": checks},
        status=200 if all_ok else 503,
    )


@csrf_exempt
@require_POST
def set_consent(request):
    value = request.POST.get("consent", "")
    if value in ("accepted", "declined"):
        request.session["dpdp_consent"] = value
        request.session.modified = True
        return JsonResponse({"status": "saved"})
    return JsonResponse({"error": "invalid"}, status=400)


def handler404(request, exception):
    return render(request, "core/404.html", status=404)


def handler500(request):
    return render(request, "core/500.html", status=500)
