from django.db import models


class GlobalCounter(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.BigIntegerField(default=0)

    @classmethod
    def increment(cls, key):
        cls.objects.get_or_create(key=key, defaults={"value": 0})
        cls.objects.filter(key=key).update(value=models.F("value") + 1)

    @classmethod
    def get_value(cls, key):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return 0


class PickSession(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    movie = models.ForeignKey("movies.Movie", on_delete=models.SET_NULL, null=True)
    mood = models.CharField(max_length=50)
    language = models.CharField(max_length=10)
    was_watched = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
