from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw


class Command(BaseCommand):
    help = "Generates favicon.ico for MovieChoose."

    def handle(self, *args, **options):
        out_dir = Path(settings.BASE_DIR) / "static" / "images"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "favicon.ico"

        img = Image.new("RGB", (32, 32), "#e50914")
        draw = ImageDraw.Draw(img)
        draw.text((16, 16), "M", fill="white", anchor="mm")
        img.save(out_path, format="ICO")

        self.stdout.write(self.style.SUCCESS(f"Generated favicon: {out_path}"))
