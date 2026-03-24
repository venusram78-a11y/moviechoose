from django.db import models


class Genre(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    name_te = models.CharField(max_length=100, blank=True)
    name_hi = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=300)
    original_title = models.CharField(max_length=300)
    overview = models.TextField()
    release_year = models.IntegerField(null=True)
    runtime = models.IntegerField(null=True)
    vote_average = models.FloatField(default=0)
    vote_count = models.IntegerField(default=0)
    popularity = models.FloatField(default=0)
    language = models.CharField(max_length=10)
    genres = models.ManyToManyField(Genre)
    poster_path = models.CharField(max_length=200, blank=True)
    backdrop_path = models.CharField(max_length=200, blank=True)
    streaming_platforms = models.JSONField(default=dict)
    is_curated_seed = models.BooleanField(default=False)
    is_family_safe = models.BooleanField(default=True)
    content_warning = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_poster_url(self, size="w500"):
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/{size}{self.poster_path}"
        return "/static/images/no-poster.jpg"

    def get_backdrop_url(self, size="w1280"):
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/{size}{self.backdrop_path}"
        return None

    def __str__(self):
        return self.title


class ReportedPick(models.Model):
    REASONS = [
        ("wrong_mood", "Wrong mood"),
        ("wrong_language", "Wrong language"),
        ("inappropriate", "Inappropriate content"),
        ("already_seen", "Already seen this"),
        ("bad_quality", "Bad film quality"),
        ("other", "Other"),
    ]
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASONS)
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
