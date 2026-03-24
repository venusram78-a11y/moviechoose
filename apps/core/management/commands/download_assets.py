from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Downloads third-party attribution assets for local serving"

    def handle(self, *args, **options):
        static_dir = settings.BASE_DIR / "static" / "images"
        static_dir.mkdir(parents=True, exist_ok=True)
        assets = [
            (
                "https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg",
                "tmdb-logo.svg",
            ),
        ]
        for url, filename in assets:
            dest = Path(static_dir) / filename
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                dest.write_bytes(r.content)
                self.stdout.write(self.style.SUCCESS(f"Downloaded: {filename}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed {filename}: {e}"))
