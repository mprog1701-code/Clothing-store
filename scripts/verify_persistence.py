import os
import sys
import time
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings')
import django
django.setup()

from core.models import Store, User, Product, ProductColor, ProductVariant, ProductImage
from django.db import IntegrityError

def main():
    ts = str(int(time.time()))
    user, _ = User.objects.get_or_create(
        username='super_owner',
        defaults={'phone': '07700000000', 'role': 'admin', 'city': 'بغداد', 'is_staff': True, 'is_superuser': True}
    )
    user.set_password('admin123456')
    user.save()

    store, _ = Store.objects.get_or_create(
        name=f'Resp Test Store {ts}',
        defaults={'owner': user, 'city': 'بغداد', 'address': 'شارع التجربة', 'description': 'متجر للتحقق', 'is_active': True}
    )
    print('StoreID', store.id)

    product, _ = Product.objects.get_or_create(
        name=f'Resp Test Product {ts}',
        store=store,
        defaults={'category': 'men', 'description': 'منتج تحقق مرن', 'base_price': Decimal('99.99'), 'size_type': 'symbolic', 'is_active': True}
    )
    print('ProductID', product.id)

    color, _ = ProductColor.objects.get_or_create(product=product, name='أزرق', defaults={'code': '#0000FF'})
    print('ColorID', color.id)

    variant, _ = ProductVariant.objects.get_or_create(
        product=product, color_obj=color, size='M', defaults={'stock_qty': 7, 'price_override': Decimal('89.99')}
    )
    print('VariantID', variant.id, 'stock', variant.stock_qty)

    image = ProductImage.objects.create(product=product, color=color, image_url=f'https://example.com/test-{ts}.jpg', is_main=True)
    print('ImageID', image.id, 'URL', image.image_url)

    dup_prevented = False
    dup_error = None
    try:
        ProductVariant.objects.create(product=product, color_obj=color, size='M', stock_qty=5)
    except Exception as e:
        dup_prevented = True
        dup_error = str(e)

    print('DuplicatePrevented', dup_prevented, 'Error', dup_error)

    # Read back to confirm persistence
    s2 = Store.objects.get(id=store.id)
    p2 = Product.objects.get(id=product.id)
    v2 = ProductVariant.objects.get(id=variant.id)
    imgs = list(ProductImage.objects.filter(product=product))
    print('VerifyReadBack', {'store': s2.name, 'product': p2.name, 'variant': (v2.size, v2.color), 'images_count': len(imgs)})

if __name__ == '__main__':
    main()
