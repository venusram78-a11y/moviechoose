import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates a timestamped backup of the SQLite database"

    def handle(self, *args, **options):
        db_path = Path(settings.DATABASES["default"]["NAME"])
        if not db_path.exists():
            self.stdout.write(self.style.ERROR("Database file not found"))
            return

        backup_dir = settings.BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"db_backup_{timestamp}.sqlite3"
        shutil.copy2(db_path, backup_path)

        backups = sorted(backup_dir.glob("db_backup_*.sqlite3"))
        for old_backup in backups[:-7]:
            old_backup.unlink()
            self.stdout.write(f"Removed old backup: {old_backup.name}")

        size_kb = backup_path.stat().st_size // 1024
        self.stdout.write(
            self.style.SUCCESS(f"Backup created: {backup_path.name} ({size_kb}KB)")
        )
