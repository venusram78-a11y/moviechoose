from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST
import pytz

from apps.movies.services.tmdb import TMDBService
from apps.picker.services.recommender import MovieRecommender

VALID_MOODS = {
    "happy",
    "sad",
    "thrilled",
    "romantic",
    "mindblown",
    "inspired",
    "scared",
    "bored",
}
VALID_LANGUAGES = {
    "telugu",
    "hindi",
    "tamil",
    "malayalam",
    "english",
    "kannada",
    "marathi",
    "bengali",
    "punjabi",
    "any",
}
VALID_REASONS = {
    "wrong_mood",
    "wrong_language",
    "inappropriate",
    "already_seen",
    "bad_quality",
    "other",
}
IST = pytz.timezone("Asia/Kolkata")

def pick_movie(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    mood = request.POST.get("mood", "").strip().lower()
    language = request.POST.get("language", "any").strip().lower()
    if mood not in VALID_MOODS:
        return JsonResponse(
            {"error": "Invalid mood. Please select from the options."}, status=400
        )
    if language not in VALID_LANGUAGES:
        return JsonResponse({"error": "Invalid language selection."}, status=400)

    if not request.session.session_key:
        request.session.create()
    session_seen = request.session.get("seen_movie_ids", [])

    result = MovieRecommender().get_recommendation(
        mood=mood,
        language=language,
        session_key=request.session.session_key,
        exclude_tmdb_ids=session_seen,
    )
    if not result:
        return JsonResponse({"error": "No film found. Try a different mood!"}, status=404)

    session_seen.append(result["tmdb_id"])
    request.session["seen_movie_ids"] = session_seen[-50:]

    from datetime import timedelta
    now_ist = timezone.now().astimezone(IST)
    today_ist = now_ist.date().isoformat()
    last_pick_date = request.session.get("last_pick_date")
    streak = request.session.get("streak", 0)
    if last_pick_date != today_ist:
        yesterday_ist = (now_ist.date() - timedelta(days=1)).isoformat()
        if last_pick_date == yesterday_ist:
            streak += 1
        else:
            streak = 1
        request.session["streak"] = streak
        request.session["last_pick_date"] = today_ist

    from apps.analytics.models import GlobalCounter, PickSession

    GlobalCounter.increment("total_picks")
    analytics_consent = request.session.get("dpdp_consent", None)
    if analytics_consent == "accepted":
        PickSession.objects.create(
            session_key=request.session.session_key, mood=mood, language=language
        )

    title_q = result["title"].replace(" ", "+")
    result["watch_links"] = {
        "prime": f"https://www.amazon.in/s?k={title_q}&tag={settings.AFFILIATE_AMAZON}",
        "hotstar": f"https://www.hotstar.com/in/search?q={title_q}",
        "zee5": f"https://www.zee5.com/search?q={title_q}",
    }
    result["streak"] = streak
    result["whatsapp_share_text"] = (
        f"I just let MovieChoose pick my film tonight - and it chose *{result['title']}*! "
        "Try it: https://moviechoose.com"
    )
    result["share_url"] = f"https://moviechoose.com/pick/{result['tmdb_id']}/"
    result["og_image"] = result.get("backdrop_url") or result.get("poster_url")

    # Ensure current result is in session seen list before alternatives are fetched
    if result and result.get("tmdb_id"):
        seen = request.session.get("seen_movie_ids", [])
        if result["tmdb_id"] not in seen:
            seen.append(result["tmdb_id"])
        if len(seen) > 50:
            seen = seen[-50:]
        request.session["seen_movie_ids"] = seen
        request.session.modified = True

    # Enrich with full movie details including trailer and streaming providers
    if result and result.get("tmdb_id"):
        tmdb_service = TMDBService()
        full_detail = tmdb_service.get_full_movie_detail(result["tmdb_id"])
        if full_detail:
            result.update({
                "overview": full_detail.get("overview", result.get("overview", "")),
                "tagline": full_detail.get("tagline", ""),
                "genres": full_detail.get("genres", []),
                "cast": full_detail.get("cast", []),
                "trailer_key": full_detail.get("trailer_key", ""),
                "trailer_url": full_detail.get("trailer_url", ""),
                "streaming_providers": full_detail.get("streaming_providers", []),
                "tmdb_watch_url": full_detail.get("tmdb_watch_url", ""),
                "runtime": full_detail.get("runtime", result.get("runtime")),
                "poster_url": full_detail.get("poster_url", result.get("poster_url")),
                "backdrop_url": full_detail.get("backdrop_url", result.get("backdrop_url")),
            })
            # Build human-readable streaming string
            streaming_names = [p["name"] for p in result.get("streaming_providers", [])]
            result["streaming_text"] = (
                ", ".join(streaming_names)
                if streaming_names
                else "Check availability"
            )

    return JsonResponse(result)


@require_POST
def mark_watched(request):
    raw_tmdb_id = request.POST.get("tmdb_id", "").strip()
    try:
        tmdb_id = int(raw_tmdb_id)
        if tmdb_id <= 0 or tmdb_id >= 10000000:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid tmdb_id."}, status=400)
    from apps.analytics.models import GlobalCounter, PickSession

    GlobalCounter.increment("total_watched")
    if request.session.session_key:
        PickSession.objects.filter(
            session_key=request.session.session_key, movie__tmdb_id=tmdb_id
        ).update(was_watched=True)
    return JsonResponse({"status": "ok"})


@require_POST
def report_pick(request):
    from apps.movies.models import Movie, ReportedPick

    raw_tmdb_id = request.POST.get("tmdb_id", "").strip()
    try:
        tmdb_id = int(raw_tmdb_id)
        if tmdb_id <= 0 or tmdb_id >= 10000000:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid tmdb_id."}, status=400)
    reason = request.POST.get("reason", "other").strip().lower()
    if reason not in VALID_REASONS:
        reason = "other"
    reason = reason[:20]
    try:
        movie = Movie.objects.get(tmdb_id=tmdb_id)
        ReportedPick.objects.create(
            movie=movie, reason=reason, session_key=request.session.session_key or ""
        )
    except Movie.DoesNotExist:
        pass
    return JsonResponse({"status": "reported", "message": "Thank you for helping us improve!"})


def pick_detail(request, tmdb_id):
    from apps.analytics.models import GlobalCounter

    movie_data = TMDBService().get_movie_detail(tmdb_id)
    if not movie_data:
        raise Http404
    title = movie_data.get("title", "Movie")
    overview = movie_data.get("overview", "")
    backdrop = movie_data.get("backdrop_path") or ""
    poster = movie_data.get("poster_path") or ""
    if backdrop:
        og_image = f"https://image.tmdb.org/t/p/w1280{backdrop}"
    elif poster:
        og_image = f"https://image.tmdb.org/t/p/w500{poster}"
    else:
        og_image = "https://moviechoose.com/static/images/og-default.jpg"
    context = {
        "movie": movie_data,
        "og_title": f"Tonight's pick: {title} — MovieChoose",
        "og_description": f"{overview[:200]} | Picked by MovieChoose AI",
        "og_image": og_image,
        "og_url": f"https://moviechoose.com/pick/{tmdb_id}/",
        "og_type": "article",
        "total_picks": GlobalCounter.get_value("total_picks"),
    }
    return render(request, "picker/pick_detail.html", context)


@require_POST
def pick_alternatives(request):
    mood = request.POST.get("mood", "happy").strip().lower()
    language = request.POST.get("language", "any").strip().lower()
    # Get the current main pick to exclude it
    current_pick_id = request.POST.get("current_pick_id", "")

    if mood not in VALID_MOODS:
        mood = "happy"
    if language not in VALID_LANGUAGES:
        language = "any"

    # Build exclude list: session seen + current pick
    exclude_ids = list(request.session.get("seen_movie_ids", []))
    if current_pick_id:
        try:
            exclude_ids.append(int(current_pick_id))
        except (ValueError, TypeError):
            pass

    recommender = MovieRecommender()
    tmdb_service = TMDBService()
    raw = tmdb_service.get_movies_by_mood_and_language(mood, language)
    candidates = raw.get("results", [])

    # Explicitly filter out current pick and seen films
    candidates = [m for m in candidates if m.get("id") not in exclude_ids]

    scored = sorted(
        candidates, key=lambda m: recommender._score_movie(m, mood), reverse=True
    )

    # Take from positions 5-25 to avoid repeating the main pick
    pool = scored[5:25] if len(scored) > 5 else scored

    import random

    selected = random.sample(pool, min(3, len(pool))) if pool else []
    results = [recommender._format_result(m) for m in selected]
    return JsonResponse({"alternatives": results})


def get_trailer(request, tmdb_id):
    """
    Returns trailer key for any movie.
    Used by search page to lazy-load trailers.
    """
    try:
        tmdb_id = int(tmdb_id)
        if tmdb_id <= 0 or tmdb_id > 10000000:
            return JsonResponse({"error": "Invalid ID"}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid ID"}, status=400)

    tmdb = TMDBService()
    trailer_key = tmdb.get_movie_trailer(tmdb_id)
    return JsonResponse({
        "trailer_key": trailer_key,
        "trailer_url": (
            f"https://www.youtube.com/embed/{trailer_key}?autoplay=1&rel=0"
            if trailer_key
            else ""
        ),
    })
