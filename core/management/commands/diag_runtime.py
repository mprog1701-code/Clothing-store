from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import caches
from django.db import connections
from core.models import User
import os

class Command(BaseCommand):
    help = 'Prints basic runtime diagnostics: env flags and counts'

    def handle(self, *args, **options):
        has_mapbox = bool((os.environ.get('MAPBOX_ACCESS_TOKEN') or '').strip())
        debug = getattr(settings, 'DEBUG', False)
        # Database engine
        try:
            db_engine = settings.DATABASES['default']['ENGINE']
        except Exception:
            db_engine = 'unknown'
        # Cache backend
        try:
            cache_backend = type(caches['default']).__name__
        except Exception:
            cache_backend = 'unknown'
        # Counts
        try:
            owners_count = User.objects.filter(role='store_admin').count()
        except Exception:
            owners_count = -1

        self.stdout.write('Runtime Diagnostics')
        self.stdout.write(f"has MAPBOX_ACCESS_TOKEN: {has_mapbox}")
        self.stdout.write(f"DEBUG: {debug}")
        self.stdout.write(f"DB engine: {db_engine}")
        self.stdout.write(f"Cache backend: {cache_backend}")
        self.stdout.write(f"owners (store_admin) count: {owners_count}")
