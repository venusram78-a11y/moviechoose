from django.core.management.base import BaseCommand
from django.conf import settings

from apps.movies.services.tmdb import TMDBService


class Command(BaseCommand):
    help = "Pre-warms TMDB cache for most common mood+language combos"

    COMMON_COMBINATIONS = [
        ("happy", "hindi"),
        ("thrilled", "telugu"),
        ("romantic", "hindi"),
        ("mindblown", "english"),
        ("happy", "any"),
        ("thrilled", "any"),
        ("sad", "hindi"),
        ("inspired", "telugu"),
    ]

    def handle(self, *args, **options):
        service = TMDBService()
        tmdb_success = 0
        fallback_used = 0
        errors = 0

        for mood, language in self.COMMON_COMBINATIONS:
            try:
                data = service.get_movies_by_mood_and_language(mood, language)
                source = data.get("source", "tmdb")
                count = len(data.get("results", []))
                if source == "database_fallback":
                    fallback_used += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  FALLBACK (TMDB unreachable): {mood}/{language}"
                        )
                    )
                else:
                    tmdb_success += 1
                    self.stdout.write(f"  Warmed from TMDB: {mood}/{language} - {count} films")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error: {mood}/{language} - {e}"))
                errors += 1

        try:
            backdrops = service.get_backdrop_images_for_homepage()
            self.stdout.write(f"  Warmed: homepage backdrops - {len(backdrops)} images")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error: homepage backdrops - {e}"))
            errors += 1

        if fallback_used > 0:
            self.stdout.write(
                self.style.WARNING(
                    "\nWARNING: "
                    f"{fallback_used} combinations used DB fallback instead of real TMDB data. "
                    "Check that:\n"
                    "  1. TMDB_API_KEY is set in .env\n"
                    "  2. api.themoviedb.org is whitelisted (PythonAnywhere free tier)\n"
                    "  3. Your API key is valid at themoviedb.org"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCache warm: {tmdb_success} real TMDB, {fallback_used} fallback, {errors} errors"
            )
        )
        if tmdb_success == 0 and settings.TMDB_API_KEY:
            raise SystemExit(
                "CRITICAL: No real TMDB data was cached. Site will serve only seed films. Fix TMDB connection first."
            )
