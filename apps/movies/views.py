from django.shortcuts import render
from django.http import JsonResponse
from apps.movies.services.tmdb import TMDBService


def search_movies_view(request):
    """
    Renders search page.
    """
    try:
        from apps.analytics.models import GlobalCounter
        total_picks = GlobalCounter.get_value("total_picks")
    except Exception:
        total_picks = 0

    return render(request, "movies/search.html", {
        "total_picks": total_picks,
    })


def search_api(request):
    """
    AJAX endpoint. Returns search results as JSON.
    Includes streaming providers for each result.
    Only shows movies streaming in India (or exact title matches).
    """
    query = request.GET.get("q", "").strip()
    page = int(request.GET.get("page", 1))

    if len(query) < 2:
        return JsonResponse({"error": "Query too short"}, status=400)

    if len(query) > 200:
        return JsonResponse({"error": "Query too long"}, status=400)

    tmdb = TMDBService()
    raw = tmdb.search_movies(query=query, page=page)
    results = raw.get("results", [])

    movies = []
    for m in results[:20]:  # Check more to find streaming ones
        if len(movies) >= 10:
            break

        tmdb_id = m.get("id")
        if not tmdb_id:
            continue

        # Check streaming availability in India
        providers = tmdb.get_watch_providers_india(tmdb_id)
        streaming = providers.get("streaming", [])

        # Only include if streaming somewhere in India
        # OR if it is a direct title search match
        title_match = query.lower() in m.get("title", "").lower()
        if not streaming and not title_match:
            continue  # Skip non-streaming, non-match

        poster_path = m.get("poster_path") or ""
        streaming_logos = [
            {
                "name": p.get("provider_name", ""),
                "logo_url": (
                    f"https://image.tmdb.org/t/p/w45{p.get('logo_path', '')}"
                    if p.get("logo_path")
                    else ""
                ),
            }
            for p in streaming
        ]

        movies.append({
            "tmdb_id": tmdb_id,
            "title": m.get("title", ""),
            "overview": (
                m.get("overview", "")[:200] + "..."
                if len(m.get("overview", "")) > 200
                else m.get("overview", "")
            ),
            "release_year": (m.get("release_date", "") or "")[:4],
            "vote_average": m.get("vote_average", 0),
            "original_language": m.get("original_language", "en"),
            "poster_url": (
                f"https://image.tmdb.org/t/p/w500{poster_path}"
                if poster_path
                else "/static/images/no-poster.jpg"
            ),
            "streaming_providers": streaming_logos,
            "streaming_text": (
                ", ".join([p.get("provider_name", "") for p in streaming])
                if streaming
                else "Check availability"
            ),
            "is_streaming": len(streaming) > 0,
            "tmdb_watch_url": providers.get("tmdb_watch_url", ""),
        })

    return JsonResponse({
        "results": movies,
        "query": query,
        "total_found": len(movies),
    })