import os
from urllib.parse import urljoin
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.models import Product, ProductImage

class Command(BaseCommand):
    help = "Relink product images from a filesystem directory structure without deleting anything"

    def add_arguments(self, parser):
        parser.add_argument('--base-dir', type=str, required=True, help='Base directory containing subfolders per product id')
        parser.add_argument('--product-id', type=int, help='Relink images for a specific product id only')
        parser.add_argument('--media-url', type=str, help='Public media URL base (defaults to settings.MEDIA_URL)')
        parser.add_argument('--dry-run', action='store_true', help='Print actions without writing to the database')

    def handle(self, *args, **options):
        base_dir = options['base_dir']
        product_id = options.get('product_id')
        media_url = options.get('media_url') or getattr(settings, 'MEDIA_URL', '/media/')
        dry = options.get('dry_run', False)

        if not os.path.isdir(base_dir):
            raise CommandError(f'Base directory not found: {base_dir}')

        targets = []
        if product_id:
            targets = [str(product_id)]
        else:
            try:
                targets = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.isdigit()]
            except Exception as e:
                raise CommandError(f'Failed to list base dir: {e}')

        created_count = 0
        skipped_count = 0
        for pid_str in targets:
            pid = int(pid_str)
            product = Product.objects.filter(id=pid).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'Skip unknown product id: {pid}'))
                skipped_count += 1
                continue
            product_dir = os.path.join(base_dir, pid_str)
            try:
                files = [f for f in os.listdir(product_dir) if os.path.isfile(os.path.join(product_dir, f))]
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to list {product_dir}: {e}'))
                skipped_count += 1
                continue
            # Sort files to put likely main images first
            files.sort()
            order = 0
            for fname in files:
                rel_path = os.path.join('products', pid_str, fname).replace('\\', '/')
                public_url = urljoin(media_url, rel_path)
                exists = ProductImage.objects.filter(product=product, image_url=public_url).exists()
                if exists:
                    skipped_count += 1
                    continue
                if dry:
                    self.stdout.write(f'[DRY] Create ProductImage(product={pid}, image_url={public_url}, is_main={order==0}, order={order})')
                else:
                    try:
                        ProductImage.objects.create(
                            product=product,
                            image_url=public_url,
                            is_main=(order == 0),
                            order=order
                        )
                        created_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Failed to create image for product {pid}: {e}'))
                        continue
                order += 1

        self.stdout.write(self.style.SUCCESS(f'Relink finished: created={created_count}, skipped={skipped_count}'))
