from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from merchants.models import Store
from catalog.models import Category, Product, Variant, VariantImage
from ads.models import Banner
from django.utils.text import slugify
from random import randint, choice
from decimal import Decimal

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(username="superadmin").exists():
            User.objects.create_superuser("superadmin", "admin@example.com", "admin123")
        stores = []
        for i in range(2):
            name = f"Store {i+1}"
            s, _ = Store.objects.get_or_create(slug=slugify(name), defaults={"name": name, "city": "Baghdad"})
            stores.append(s)
        cat, _ = Category.objects.get_or_create(slug="fashion", defaults={"title": "الأزياء"})
        for i in range(10):
            store = choice(stores)
            title = f"منتج {i+1}"
            p, _ = Product.objects.get_or_create(store=store, title=title, defaults={"category": cat, "description": "وصف", "base_price": Decimal("10000.00")})
            for j in range(randint(2,3)):
                sku = f"SKU-{i+1}-{j+1}"
                v, _ = Variant.objects.get_or_create(product=p, sku=sku, defaults={"color_name": f"لون {j+1}", "color_hex": "#FF8800", "size": "M", "stock": randint(0,10), "price_override": None})
                for k in range(3):
                    VariantImage.objects.get_or_create(variant=v, sort_order=k, defaults={"is_main": k==0, "image": "dummy/placeholder.png"})
        for i in range(3):
            Banner.objects.get_or_create(title=f"Banner {i+1}", defaults={"image": "dummy/banner.png", "placement": "home_top", "priority": i})
        self.stdout.write("Seeded demo data")
