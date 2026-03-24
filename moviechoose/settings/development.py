from .base import *

DEBUG = config("DEBUG", default=True, cast=bool)
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
