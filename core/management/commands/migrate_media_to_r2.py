from pathlib import Path
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.management.base import BaseCommand
from core.models import Store, ProductImage, Campaign


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') or not getattr(settings, 'AWS_S3_ENDPOINT_URL', ''):
            return
        bases = []
        rv = Path(os.environ.get('RAILWAY_VOLUME_PATH', '/data')) / 'media'
        try:
            bases.append(rv)
        except Exception:
            pass
        bases.append(settings.BASE_DIR / 'media')

        def find_local(name: str):
            for b in bases:
                p = Path(b) / name
                if p.exists() and p.is_file():
                    return p
            return None

        def ensure_uploaded(name: str):
            if not name:
                return False
            if default_storage.exists(name):
                return True
            lp = find_local(name)
            if not lp:
                return False
            data = lp.read_bytes()
            default_storage.save(name, ContentFile(data))
            return True

        for s in Store.objects.all():
            if s.logo and s.logo.name:
                ensure_uploaded(s.logo.name)

        for pi in ProductImage.objects.all():
            if pi.image and pi.image.name:
                ensure_uploaded(pi.image.name)

        for c in Campaign.objects.all():
            if c.banner_image and c.banner_image.name:
                ensure_uploaded(c.banner_image.name)
