import time
from django.core.management.base import BaseCommand
from apps.movies.models import Movie
import requests
from django.conf import settings


class Command(BaseCommand):
    help = 'Seeds curated movies by searching TMDB by title'

    SEED_MOVIES = [
        # Telugu
        {'title': 'Baahubali: The Conclusion',  'year': 2017, 'language': 'te'},
        {'title': 'RRR',                         'year': 2022, 'language': 'te'},
        {'title': 'KGF: Chapter 2',              'year': 2022, 'language': 'te'},
        {'title': 'Vikram',                      'year': 2022, 'language': 'ta'},
        {'title': 'Eega',                        'year': 2012, 'language': 'te'},
        {'title': 'Mahanati',                    'year': 2018, 'language': 'te'},
        {'title': 'Ala Vaikunthapurramuloo',     'year': 2020, 'language': 'te'},
        {'title': 'Pushpa: The Rise',            'year': 2021, 'language': 'te'},
        {'title': 'Rangasthalam',                'year': 2018, 'language': 'te'},
        {'title': 'Sita Ramam',                  'year': 2022, 'language': 'te'},
        {'title': 'Jersey',                      'year': 2019, 'language': 'te'},
        {'title': 'Agent Sai Srinivasa Athreya', 'year': 2019, 'language': 'te'},

        # Tamil
        {'title': 'Super Deluxe',   'year': 2019, 'language': 'ta'},
        {'title': 'Kaithi',         'year': 2019, 'language': 'ta'},
        {'title': '96',             'year': 2018, 'language': 'ta'},
        {'title': 'Soorarai Pottru','year': 2020, 'language': 'ta'},
        {'title': 'Vada Chennai',   'year': 2018, 'language': 'ta'},
        {'title': 'Asuran',         'year': 2019, 'language': 'ta'},
        {'title': 'Mersal',         'year': 2017, 'language': 'ta'},

        # Malayalam
        {'title': 'Drishyam',          'year': 2013, 'language': 'ml'},
        {'title': 'Bangalore Days',    'year': 2014, 'language': 'ml'},
        {'title': 'Premam',            'year': 2015, 'language': 'ml'},
        {'title': 'Ustad Hotel',       'year': 2012, 'language': 'ml'},
        {'title': 'Kumbalangi Nights', 'year': 2019, 'language': 'ml'},

        # Hindi
        {'title': '3 Idiots',                   'year': 2009, 'language': 'hi'},
        {'title': 'Dil Chahta Hai',             'year': 2001, 'language': 'hi'},
        {'title': 'Dangal',                     'year': 2016, 'language': 'hi'},
        {'title': 'Tumbbad',                    'year': 2018, 'language': 'hi'},
        {'title': 'Andhadhun',                  'year': 2018, 'language': 'hi'},
        {'title': 'Zindagi Na Milegi Dobara',   'year': 2011, 'language': 'hi'},
        {'title': 'Queen',                      'year': 2014, 'language': 'hi'},
        {'title': 'Barfi',                      'year': 2012, 'language': 'hi'},
        {'title': 'Gully Boy',                  'year': 2019, 'language': 'hi'},
        {'title': 'Taare Zameen Par',           'year': 2007, 'language': 'hi'},
        {'title': 'Swades',                     'year': 2004, 'language': 'hi'},
        {'title': 'Article 15',                 'year': 2019, 'language': 'hi'},
        {'title': 'Chhichhore',                 'year': 2019, 'language': 'hi'},

        # English
        {'title': 'The Dark Knight',                       'year': 2008, 'language': 'en'},
        {'title': 'Parasite',                              'year': 2019, 'language': 'en'},
        {'title': 'Inception',                             'year': 2010, 'language': 'en'},
        {'title': 'Interstellar',                          'year': 2014, 'language': 'en'},
        {'title': 'The Prestige',                          'year': 2006, 'language': 'en'},
        {'title': 'The Shawshank Redemption',              'year': 1994, 'language': 'en'},
        {'title': 'Whiplash',                              'year': 2014, 'language': 'en'},
        {'title': 'Mad Max: Fury Road',                    'year': 2015, 'language': 'en'},
        {'title': 'The Martian',                           'year': 2015, 'language': 'en'},
        {'title': 'Spider-Man: Into the Spider-Verse',     'year': 2018, 'language': 'en'},
        {'title': 'Coco',                                  'year': 2017, 'language': 'en'},
        {'title': 'Ford v Ferrari',                        'year': 2019, 'language': 'en'},
        {'title': 'The Social Network',                    'year': 2010, 'language': 'en'},
    ]

    def search_tmdb(self, title, year, api_key):
        """Search TMDB by title and year. Returns movie data or None."""
        for attempt in range(3):
            try:
                time.sleep(0.5)  # Be polite to TMDB API
                r = requests.get(
                    'https://api.themoviedb.org/3/search/movie',
                    params={
                        'api_key': api_key,
                        'query': title,
                        'year': year,
                        'language': 'en-US',
                        'include_adult': 'false',
                    },
                    timeout=8
                )
                if r.status_code == 200:
                    results = r.json().get('results', [])
                    if results:
                        return results[0]  # First result is best match
                    return None
                elif r.status_code == 429:
                    # Rate limited — wait longer
                    self.stdout.write(self.style.WARNING(
                        f'  Rate limited — waiting 10 seconds...'
                    ))
                    time.sleep(10)
                    continue
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)  # Wait before retry
                    continue
                raise e
        return None

    def get_movie_detail(self, tmdb_id, api_key):
        """Get full movie details including runtime."""
        for attempt in range(3):
            try:
                time.sleep(0.3)
                r = requests.get(
                    f'https://api.themoviedb.org/3/movie/{tmdb_id}',
                    params={'api_key': api_key, 'language': 'en-US'},
                    timeout=8
                )
                if r.status_code == 200:
                    return r.json()
                elif r.status_code == 429:
                    time.sleep(10)
                    continue
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                    continue
        return None

    def handle(self, *args, **options):
        api_key = settings.TMDB_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR(
                'TMDB_API_KEY not set in .env'
            ))
            return

        # Delete old wrong seed movies first
        old_fake = Movie.objects.filter(
            tmdb_id__gte=1000, tmdb_id__lte=1049
        )
        if old_fake.exists():
            old_fake.delete()
            self.stdout.write('Deleted old fake seed movies.')

        seeded = 0
        failed = 0
        wrong_movie = 0

        for item in self.SEED_MOVIES:
            title = item['title']
            year = item['year']
            language = item['language']

            self.stdout.write(f'  Searching: {title} ({year})...')

            try:
                # Search by title + year
                result = self.search_tmdb(title, year, api_key)

                if not result:
                    self.stdout.write(self.style.WARNING(
                        f'  NOT FOUND: {title}'
                    ))
                    failed += 1
                    continue

                tmdb_id = result['id']
                found_title = result.get('title', '')

                # Get full details for runtime
                detail = self.get_movie_detail(tmdb_id, api_key)
                if detail:
                    result.update(detail)

                poster_path = result.get('poster_path') or ''
                backdrop_path = result.get('backdrop_path') or ''
                release_date = result.get('release_date') or ''

                movie, created = Movie.objects.update_or_create(
                    tmdb_id=tmdb_id,
                    defaults={
                        'title': found_title,
                        'original_title': result.get('original_title', found_title),
                        'overview': result.get('overview', ''),
                        'release_year': int(release_date[:4]) if release_date else year,
                        'runtime': result.get('runtime'),
                        'vote_average': result.get('vote_average', 0),
                        'vote_count': result.get('vote_count', 0),
                        'popularity': result.get('popularity', 0),
                        'language': language,
                        'poster_path': poster_path,
                        'backdrop_path': backdrop_path,
                        'is_curated_seed': True,
                        'is_family_safe': True,
                    }
                )

                action = 'Seeded' if created else 'Updated'
                poster_status = '✓ poster' if poster_path else '✗ no poster'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  {action}: {found_title} ({poster_status})'
                    )
                )
                seeded += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  ERROR: {title} — {str(e)}'
                ))
                failed += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done: {seeded} seeded, {failed} failed'
        ))
        if failed > 0:
            self.stdout.write(self.style.WARNING(
                f'Run again to retry the {failed} failed movies'
            ))