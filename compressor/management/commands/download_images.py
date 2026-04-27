from django.core.management.base import BaseCommand
from compressor.image_library import ensure_images_ready


class Command(BaseCommand):
    help = "Download all gallery images (runs automatically on server start)"

    def handle(self, *args, **options):
        self.stdout.write("Downloading images ...")
        ensure_images_ready()
        self.stdout.write(self.style.SUCCESS("Done."))
