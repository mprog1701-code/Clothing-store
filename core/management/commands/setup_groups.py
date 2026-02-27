from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from merchants.models import Store
from catalog.models import Category, Product, Variant, VariantImage
from orders.models import Order, Cart
from ads.models import Banner

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        superadmin, _ = Group.objects.get_or_create(name="SuperAdmin")
        ops, _ = Group.objects.get_or_create(name="Ops")
        catalog, _ = Group.objects.get_or_create(name="Catalog")
        merchants, _ = Group.objects.get_or_create(name="Merchants")

        def add_all_perms(model, group):
            ct = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=ct)
            group.permissions.add(*perms)

        add_all_perms(Store, merchants)
        add_all_perms(Category, catalog)
        add_all_perms(Product, catalog)
        add_all_perms(Variant, catalog)
        add_all_perms(VariantImage, catalog)
        add_all_perms(Order, ops)
        add_all_perms(Cart, ops)
        add_all_perms(Banner, superadmin)

        for g in (ops, catalog, merchants):
            for p in Permission.objects.all():
                if p.codename.startswith("view_"):
                    g.permissions.add(p)

        self.stdout.write("Groups and permissions configured")
