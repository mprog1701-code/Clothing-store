from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal, InvalidOperation
from core.models import Product, ProductVariant

class Command(BaseCommand):
    help = "Bulk set price_override for all variants of a product"

    def add_arguments(self, parser):
        parser.add_argument("--product", required=True, help="Product ID")
        parser.add_argument("--price", required=False, help="Price to set (omit or empty to clear)")

    def handle(self, *args, **options):
        pid_raw = (options.get("product") or "").strip()
        price_raw = (options.get("price") or "")
        if not pid_raw.isdigit():
            raise CommandError("Invalid --product")
        pid = int(pid_raw)
        try:
            product = Product.objects.get(id=pid)
        except Product.DoesNotExist:
            raise CommandError(f"Product id={pid} not found")
        price = None
        if price_raw is not None and str(price_raw).strip() != "":
            try:
                price = Decimal(str(price_raw).strip())
            except InvalidOperation:
                raise CommandError("Invalid --price")
        with transaction.atomic():
            qs = ProductVariant.objects.filter(product_id=pid)
            updated = qs.update(price_override=price)
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} variants for product {product.id}: price_override={'NULL' if price is None else price}"))
