from django.core.cache import caches
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Creates database cache table for Django DB cache backend."

    def handle(self, *args, **options):
        table_name = "moviechoose_cache_table"
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    cache_key varchar(255) NOT NULL PRIMARY KEY,
                    value text NOT NULL,
                    expires datetime NOT NULL
                )
                """
            )
        self.stdout.write(self.style.SUCCESS(f"Cache table ensured: {table_name}"))
