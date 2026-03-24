import os

from django.core.wsgi import get_wsgi_application
import sys

path = '/home/venusram78/moviechoose/moviechoose'
if path not in sys.path:
    sys.path.insert(0, path)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moviechoose.settings.production")

application = get_wsgi_application()
