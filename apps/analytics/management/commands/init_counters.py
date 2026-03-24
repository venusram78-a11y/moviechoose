from django.core.management.base import BaseCommand

from apps.analytics.models import GlobalCounter


class Command(BaseCommand):
    help = "Initializes analytics counters."

    def handle(self, *args, **options):
        GlobalCounter.objects.get_or_create(key="total_picks", defaults={"value": 0})
        GlobalCounter.objects.get_or_create(key="total_watched", defaults={"value": 0})
        self.stdout.write(self.style.SUCCESS("Global counters initialized."))
