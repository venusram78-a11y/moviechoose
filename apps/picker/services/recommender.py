import logging

from apps.movies.services.tmdb import TMDBService

logger = logging.getLogger("apps.picker")


class MovieRecommender:
    def get_recommendation(self, mood, language, session_key, exclude_tmdb_ids=None):
        from apps.analytics.models import PickSession

        session_pick_count = PickSession.objects.filter(session_key=session_key).count()
        if session_pick_count < 3:
            logger.info(f"Cold start: serving seed film for mood={mood} lang={language}")
            return self._get_seed_recommendation(mood, language, exclude_tmdb_ids)

        tmdb_service = TMDBService()
        raw_data = tmdb_service.get_movies_by_mood_and_language(mood, language)
        candidates = raw_data.get("results", [])
        if not candidates:
            return self._get_seed_recommendation(mood, language, exclude_tmdb_ids)

        if exclude_tmdb_ids:
            candidates = [m for m in candidates if m.get("id") not in exclude_tmdb_ids]

        # Score all candidates
        scored = []
        for movie in candidates:
            score = self._score_movie(movie, mood)
            scored.append((score, movie))
        scored.sort(key=lambda x: x[0], reverse=True)

        # Try candidates in order until we find one that streams in India
        for _, candidate in scored[:15]:  # Check top 15
            tmdb_id = candidate.get("id")
            if not tmdb_id:
                continue

            # Skip if already seen this session
            if exclude_tmdb_ids and tmdb_id in exclude_tmdb_ids:
                continue

            providers = tmdb_service.get_watch_providers_india(tmdb_id)
            streaming = providers.get("streaming", [])

            if streaming:
                # This movie streams in India — use it
                result = self._format_result(candidate)
                result["streaming_providers"] = [
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
                result["tmdb_watch_url"] = providers.get("tmdb_watch_url", "")
                return result

        # Fallback: no streamable movie found in top 15
        # Return best scored result anyway with honest message
        if scored:
            _, best = scored[0]
            result = self._format_result(best)
            result["streaming_providers"] = []
            result["streaming_text"] = "Not on major Indian platforms — check TMDB for availability"
            result["tmdb_watch_url"] = (
                f"https://www.themoviedb.org/movie/{best.get('id')}/watch?locale=IN"
            )
            return result

        return None

    def _score_movie(self, movie, mood):
        score = 0.0
        vote = movie.get("vote_average", 0)
        score += (vote / 10) * 30
        vote_count = movie.get("vote_count", 0)
        score += min(vote_count / 1000, 1.0) * 20
        score += min(movie.get("popularity", 0) / 100, 1.0) * 20
        release_date = movie.get("release_date", "2000-01-01")
        try:
            year = int(release_date[:4])
            score += max(0, (year - 2000) / 25) * 15
        except Exception:
            pass
        target_genres = TMDBService.MOOD_TO_GENRES.get(mood, [])
        genre_matches = len(set(movie.get("genre_ids", [])) & set(target_genres))
        score += (genre_matches / max(len(target_genres), 1)) * 15
        return score

    def _get_seed_recommendation(self, mood, language, exclude_ids=None):
        from apps.movies.models import Movie

        qs = Movie.objects.filter(is_curated_seed=True, vote_average__gte=7.0)
        if language and language != "any":
            lang_code = TMDBService.LANGUAGE_CODES.get(language)
            if lang_code:
                qs = qs.filter(language=lang_code)
        if exclude_ids:
            qs = qs.exclude(tmdb_id__in=exclude_ids)

        import random

        movies = list(qs.order_by("?")[:20])
        tmdb = TMDBService()

        for chosen in movies:
            providers = tmdb.get_watch_providers_india(chosen.tmdb_id)
            if providers.get("streaming"):
                return {
                    "tmdb_id": chosen.tmdb_id,
                    "title": chosen.title,
                    "overview": chosen.overview,
                    "poster_url": chosen.get_poster_url(),
                    "backdrop_url": chosen.get_backdrop_url(),
                    "vote_average": chosen.vote_average,
                    "release_year": chosen.release_year,
                    "runtime": chosen.runtime,
                    "language": chosen.language,
                    "streaming_providers": [
                        {
                            "name": p.get("provider_name", ""),
                            "logo_url": (
                                f"https://image.tmdb.org/t/p/w45{p.get('logo_path', '')}"
                                if p.get("logo_path")
                                else ""
                            ),
                        }
                        for p in providers["streaming"]
                    ],
                    "tmdb_watch_url": providers.get("tmdb_watch_url", ""),
                    "source": "curated_seed",
                }

        # All seed films failed streaming check — return first one anyway
        if movies:
            chosen = movies[0]
            return {
                "tmdb_id": chosen.tmdb_id,
                "title": chosen.title,
                "overview": chosen.overview,
                "poster_url": chosen.get_poster_url(),
                "backdrop_url": chosen.get_backdrop_url(),
                "vote_average": chosen.vote_average,
                "release_year": chosen.release_year,
                "runtime": chosen.runtime,
                "language": chosen.language,
                "streaming_providers": [],
                "tmdb_watch_url": (
                    f"https://www.themoviedb.org/movie/{chosen.tmdb_id}/watch?locale=IN"
                ),
                "source": "curated_seed",
            }
        return None

    def _format_result(self, raw_movie):
        backdrop_path = raw_movie.get("backdrop_path") or ""
        poster_path = raw_movie.get("poster_path") or ""
        backdrop_url = (
            f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
            if backdrop_path and backdrop_path != "None"
            else ""
        )
        poster_url = (
            f"https://image.tmdb.org/t/p/w500{poster_path}"
            if poster_path and poster_path != "None"
            else "/static/images/no-poster.jpg"
        )
        og_image = (
            backdrop_url
            or poster_url
            or "https://moviechoose.com/static/images/og-default.jpg"
        )
        return {
            "tmdb_id": raw_movie.get("id"),
            "title": raw_movie.get("title", "Unknown Film"),
            "overview": raw_movie.get("overview", ""),
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "og_image": og_image,
            "vote_average": raw_movie.get("vote_average") or 0,
            "release_year": (raw_movie.get("release_date") or "")[:4],
            "runtime": raw_movie.get("runtime"),
            "language": raw_movie.get("original_language", "en"),
            "source": "tmdb_live",
        }
