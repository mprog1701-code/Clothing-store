from django.db import models
from django.conf import settings
from merchants.models import Store

class Category(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, verbose_name='منتج مميز')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["store"]),
        ]

    def __str__(self):
        return self.title

class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color_name = models.CharField(max_length=80, blank=True)
    color_hex = models.CharField(max_length=7, blank=True)
    size = models.CharField(max_length=40, blank=True)
    sku = models.CharField(max_length=80, unique=True)
    stock = models.IntegerField(default=0)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["product"]),
        ]
        unique_together = [("product", "color_name", "size")]

    def __str__(self):
        return f"{self.product_id}:{self.sku}"

class VariantImage(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="catalog/variant_images/")
    sort_order = models.IntegerField(default=0)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")
        indexes = [
            models.Index(fields=["variant"]),
            models.Index(fields=["sort_order"]),
        ]

    def __str__(self):
        return f"{self.variant_id}:{self.id}"
