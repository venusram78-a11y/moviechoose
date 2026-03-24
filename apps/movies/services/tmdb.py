import logging
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("apps.movies")


class TMDBService:
    BASE_URL = settings.TMDB_BASE_URL
    API_KEY = settings.TMDB_API_KEY
    CACHE_TIMEOUT = settings.TMDB_CACHE_TIMEOUT

    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'application/json',
    }

    MOOD_TO_GENRES = {
        "happy": [35, 10751, 16],
        "sad": [18, 10749],
        "thrilled": [28, 53, 27],
        "romantic": [10749, 35, 18],
        "mindblown": [878, 9648, 14],
        "inspired": [18, 99, 36],
        "scared": [27, 53, 9648],
        "bored": [28, 12, 35],
    }

    LANGUAGE_CODES = {
        "telugu": "te",
        "hindi": "hi",
        "tamil": "ta",
        "malayalam": "ml",
        "english": "en",
        "kannada": "kn",
        "marathi": "mr",
        "bengali": "bn",
        "punjabi": "pa",
        "any": None,
    }

    INDIAN_LANGUAGES = {
        "te": "Telugu",
        "hi": "Hindi",
        "ta": "Tamil",
        "ml": "Malayalam",
        "kn": "Kannada",
        "mr": "Marathi",
        "bn": "Bengali",
        "pa": "Punjabi",
        "en": "English",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def get_movies_by_mood_and_language(self, mood, language, exclude_ids=None, page=1):
        cache_key = f"tmdb_movies_{mood}_{language}_{page}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        genre_ids = self.MOOD_TO_GENRES.get(mood, [18, 28])
        lang_code = self.LANGUAGE_CODES.get(language)
        params = {
            "api_key": self.API_KEY,
            "with_genres": ",".join(map(str, genre_ids[:2])),
            "vote_count.gte": 100,
            "vote_average.gte": 6.0,
            "sort_by": "popularity.desc",
            "page": page,
        }
        if lang_code:
            params["with_original_language"] = lang_code

        try:
            response = self.session.get(f"{self.BASE_URL}/discover/movie", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data, self.CACHE_TIMEOUT)
            return data
        except (requests.RequestException, Exception) as e:
            logger.warning(f"TMDB API error: {str(e)}", exc_info=True)
            return self._fallback_from_database(mood, language)

    def _fallback_from_database(self, mood, language):
        from apps.movies.models import Movie

        qs = Movie.objects.filter(vote_average__gte=6.0, vote_count__gte=50)
        if language and language != "any":
            lang_code = self.LANGUAGE_CODES.get(language)
            if lang_code:
                qs = qs.filter(language=lang_code)
        movies = list(qs.values())
        return {"results": movies, "source": "database_fallback"}

    def get_movie_detail(self, tmdb_id):
        cache_key = f"tmdb_movie_{tmdb_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        try:
            response = self.session.get(
                f"{self.BASE_URL}/movie/{tmdb_id}",
                params={"api_key": self.API_KEY, "append_to_response": "watch/providers"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data, self.CACHE_TIMEOUT)
            return data
        except Exception as e:
            logger.warning(f"TMDB API error: {str(e)}", exc_info=True)
            return None

    def get_backdrop_images_for_homepage(self):
        cache_key = "tmdb_homepage_backdrops"
        cached = cache.get(cache_key)
        if cached:
            return cached
        try:
            response = self.session.get(
                f"{self.BASE_URL}/movie/popular",
                params={"api_key": self.API_KEY, "page": 1},
                timeout=10,
            )
            data = response.json()
            backdrops = [
                f"https://image.tmdb.org/t/p/w1280{m['backdrop_path']}"
                for m in data.get("results", [])
                if m.get("backdrop_path")
            ][:20]
            cache.set(cache_key, backdrops, 3600)
            return backdrops
        except Exception as e:
            logger.warning(f"TMDB API error: {str(e)}", exc_info=True)
            return []

    def get_indian_movies_by_language(
        self, language_code, page=1, min_rating=6.0, min_votes=100
    ):
        """
        Fetches Indian movies by language from TMDB discover.
        Returns real movies with posters, overviews, ratings.
        Cached for 24 hours.
        """
        cache_key = f"indian_movies_{language_code}_{page}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            time.sleep(0.3)  # Polite rate limiting
            params = {
                "api_key": self.API_KEY,
                "with_original_language": language_code,
                "vote_count.gte": min_votes,
                "vote_average.gte": min_rating,
                "sort_by": "popularity.desc",
                "page": page,
                "region": "IN",
            }
            # For non-English Indian films, filter by production country India
            if language_code != "en":
                params["with_origin_country"] = "IN"

            response = self.session.get(
                f"{self.BASE_URL}/discover/movie",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data, self.CACHE_TIMEOUT)
            return data
        except Exception as e:
            logger.warning(f"TMDB Indian movies error: {e}")
            return {"results": [], "total_pages": 0}

    def search_movies(self, query, language="en-US", page=1):
        """
        Searches TMDB by title query.
        Used for the search feature.
        """
        cache_key = f"search_{query}_{language}_{page}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            time.sleep(0.2)
            response = self.session.get(
                f"{self.BASE_URL}/search/movie",
                params={
                    "api_key": self.API_KEY,
                    "query": query,
                    "language": language,
                    "page": page,
                    "include_adult": "false",
                    "region": "IN",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data, 3600)  # 1 hour cache
            return data
        except Exception as e:
            return {"results": [], "total_pages": 0}

    def get_watch_providers_india(self, tmdb_id):
        """
        Gets streaming providers for a movie in India.
        Returns flatrate (subscription streaming) providers.
        TMDB terms: link to TMDB watch page, show provider
        names/logos only — no direct streaming URLs.
        """
        cache_key = f"providers_IN_{tmdb_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            response = self.session.get(
                f"{self.BASE_URL}/movie/{tmdb_id}/watch/providers",
                params={"api_key": self.API_KEY},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            # Get India-specific providers
            india_data = data.get("results", {}).get("IN", {})
            result = {
                "streaming": india_data.get("flatrate", []),
                "rent": india_data.get("rent", []),
                "buy": india_data.get("buy", []),
                "tmdb_watch_url": (
                    f"https://www.themoviedb.org/movie"
                    f"/{tmdb_id}/watch?locale=IN"
                ),
            }
            cache.set(cache_key, result, 43200)  # 12 hours
            return result
        except Exception:
            return {
                "streaming": [],
                "rent": [],
                "buy": [],
                "tmdb_watch_url": (
                    f"https://www.themoviedb.org/movie"
                    f"/{tmdb_id}/watch?locale=IN"
                ),
            }

    def get_movie_trailer(self, tmdb_id):
        """
        Gets the official YouTube trailer for a movie.
        Returns YouTube video key or None.
        """
        cache_key = f"trailer_{tmdb_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = self.session.get(
                f"{self.BASE_URL}/movie/{tmdb_id}/videos",
                params={
                    "api_key": self.API_KEY,
                    "language": "en-US",
                },
                timeout=10,
            )
            response.raise_for_status()
            videos = response.json().get("results", [])

            # Prefer official trailer
            trailer_key = None
            for video in videos:
                if (
                    video.get("site") == "YouTube"
                    and video.get("type") == "Trailer"
                    and video.get("official", False)
                ):
                    trailer_key = video.get("key")
                    break

            # Fall back to any YouTube trailer
            if not trailer_key:
                for video in videos:
                    if (
                        video.get("site") == "YouTube"
                        and video.get("type") == "Trailer"
                    ):
                        trailer_key = video.get("key")
                        break

            # Fall back to any YouTube video
            if not trailer_key and videos:
                for video in videos:
                    if video.get("site") == "YouTube":
                        trailer_key = video.get("key")
                        break

            result = trailer_key or ""
            cache.set(cache_key, result, self.CACHE_TIMEOUT)
            return result
        except Exception:
            return ""

    def get_full_movie_detail(self, tmdb_id):
        """
        Gets complete movie details including:
        - overview, genres, runtime, cast
        - trailer key
        - streaming providers in India
        All fetched in parallel via append_to_response.
        """
        cache_key = f"full_detail_{tmdb_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            response = self.session.get(
                f"{self.BASE_URL}/movie/{tmdb_id}",
                params={
                    "api_key": self.API_KEY,
                    "language": "en-US",
                    "append_to_response": "videos,watch/providers,credits",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Extract trailer
            trailer_key = ""
            videos = data.get("videos", {}).get("results", [])
            for v in videos:
                if v.get("site") == "YouTube" and v.get("type") == "Trailer":
                    trailer_key = v.get("key", "")
                    break

            # Extract India providers
            providers_raw = (
                data.get("watch/providers", {})
                .get("results", {})
                .get("IN", {})
            )
            streaming = providers_raw.get("flatrate", [])

            # Extract top cast (max 5)
            cast = data.get("credits", {}).get("cast", [])[:5]

            poster_path = data.get("poster_path", "")
            backdrop_path = data.get("backdrop_path", "")

            result = {
                "tmdb_id": data.get("id"),
                "title": data.get("title", ""),
                "original_title": data.get("original_title", ""),
                "overview": data.get("overview", ""),
                "tagline": data.get("tagline", ""),
                "release_date": data.get("release_date", ""),
                "release_year": (data.get("release_date", "") or "")[:4],
                "runtime": data.get("runtime"),
                "vote_average": data.get("vote_average", 0),
                "vote_count": data.get("vote_count", 0),
                "popularity": data.get("popularity", 0),
                "original_language": data.get("original_language", "en"),
                "genres": [g["name"] for g in data.get("genres", [])],
                "poster_path": poster_path,
                "backdrop_path": backdrop_path,
                "poster_url": (
                    f"https://image.tmdb.org/t/p/w500{poster_path}"
                    if poster_path
                    else "/static/images/no-poster.jpg"
                ),
                "backdrop_url": (
                    f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
                    if backdrop_path
                    else ""
                ),
                "trailer_key": trailer_key,
                "trailer_url": (
                    f"https://www.youtube.com/embed/{trailer_key}"
                    f"?autoplay=1&rel=0"
                    if trailer_key
                    else ""
                ),
                "streaming_providers": [
                    {
                        "name": p.get("provider_name", ""),
                        "logo_url": (
                            f"https://image.tmdb.org/t/p/w45"
                            f"{p.get('logo_path', '')}"
                            if p.get("logo_path")
                            else ""
                        ),
                    }
                    for p in streaming
                ],
                "tmdb_watch_url": (
                    f"https://www.themoviedb.org/movie"
                    f"/{tmdb_id}/watch?locale=IN"
                ),
                "cast": [
                    {
                        "name": c.get("name", ""),
                        "character": c.get("character", ""),
                        "profile_url": (
                            f"https://image.tmdb.org/t/p/w185"
                            f"{c.get('profile_path', '')}"
                            if c.get("profile_path")
                            else ""
                        ),
                    }
                    for c in cast
                ],
            }
            cache.set(cache_key, result, self.CACHE_TIMEOUT)
            return result
        except Exception as e:
            logger.warning(f"Full detail error for {tmdb_id}: {e}")
            return None
