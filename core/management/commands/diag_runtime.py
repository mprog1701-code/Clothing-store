from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Print minimal runtime diagnostics'

    def handle(self, *args, **options):
        has_token = bool((os.environ.get('MAPBOX_ACCESS_TOKEN') or '').strip())
        debug = bool(getattr(settings, 'DEBUG', False))
        db_engine = str(getattr(settings, 'DATABASES', {}).get('default', {}).get('ENGINE', ''))
        cache_backend = str(getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', ''))
        try:
            from django.core.cache import cache
            if not cache_backend:
                cache_backend = f"{cache.__class__.__module__}.{cache.__class__.__name__}"
        except Exception:
            pass
        from core.models import User, Store, Product, Order
        owners_count = int(User.objects.filter(role='store_admin').count())
        stores_count = int(Store.objects.count())
        products_count = int(Product.objects.count())
        orders_count = int(Order.objects.count())
        self.stdout.write(f"has_MAPBOX_ACCESS_TOKEN: {'True' if has_token else 'False'}")
        self.stdout.write(f"DEBUG: {'True' if debug else 'False'}")
        self.stdout.write(f"DB_ENGINE: {db_engine}")
        self.stdout.write(f"CACHE_BACKEND: {cache_backend}")
        self.stdout.write(f"owners: {owners_count}")
        self.stdout.write(f"stores: {stores_count}")
        self.stdout.write(f"products: {products_count}")
        self.stdout.write(f"orders: {orders_count}")

