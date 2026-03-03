from django.core.management.base import BaseCommand
from core.models import Product, ProductImage
import os

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--product-id', type=int)
        parser.add_argument('--check-files', action='store_true')
        parser.add_argument('--base-dir', type=str)

    def handle(self, *args, **options):
        pid = options.get('product_id')
        check_files = options.get('check_files', False)
        base_dir = options.get('base_dir') or ''
        qs = Product.objects.all()
        if pid:
            qs = qs.filter(id=pid)
        total = ProductImage.objects.count()
        self.stdout.write(f'ProductImage total={total}')
        for p in qs:
            imgs = list(ProductImage.objects.filter(product=p).order_by('order'))
            self.stdout.write(f'product={p.id} name="{p.name}" images={len(imgs)}')
            if check_files and base_dir:
                for im in imgs:
                    path = ''
                    if im.image and getattr(im.image, 'path', ''):
                        path = im.image.path
                    elif im.image_url:
                        path = os.path.join(base_dir, str(p.id), os.path.basename(im.image_url))
                    ok = os.path.exists(path) if path else False
                    self.stdout.write(f' - id={im.id} is_main={im.is_main} exists={ok} path="{path}"')
