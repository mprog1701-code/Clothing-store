from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection

class Command(BaseCommand):
    help = 'Prints a concise health report for production readiness.'

    def handle(self, *args, **options):
        debug = getattr(settings, 'DEBUG', False)
        db_conf = settings.DATABASES.get('default', {})
        db_engine = db_conf.get('ENGINE') or ''
        storage_backend = f"{default_storage.__class__.__module__}.{default_storage.__class__.__name__}"
        sentry_enabled = bool(getattr(settings, 'SENTRY_ENABLED', False))

        from core.models import Product, Order, ProductImage
        products_count = Product.objects.count()
        orders_count = Order.objects.count()
        images_count = ProductImage.objects.count()

        self.stdout.write(f"DEBUG={debug}")
        self.stdout.write(f"DB_ENGINE={db_engine}")
        self.stdout.write(f"STORAGE_BACKEND={storage_backend}")
        self.stdout.write(f"SENTRY_ENABLED={sentry_enabled}")
        self.stdout.write(f"COUNTS: products={products_count}, orders={orders_count}, images={images_count}")
