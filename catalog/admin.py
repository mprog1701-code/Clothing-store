from django.contrib import admin
from .models import Category, Product, Variant, VariantImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "slug")
    readonly_fields = ("created_at", "updated_at")

class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0
    fields = ("sku", "color_name", "color_hex", "size", "stock", "price_override", "updated_at")
    readonly_fields = ("updated_at", "created_at")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "category", "is_active", "base_price", "updated_at")
    list_filter = ("is_active", "store", "category")
    search_fields = ("title",)
    autocomplete_fields = ("store", "category")
    inlines = [VariantInline]
    readonly_fields = ("created_at", "updated_at")

class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 0
    fields = ("image", "sort_order", "is_main", "updated_at")
    readonly_fields = ("updated_at", "created_at")

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "color_name", "size", "stock", "updated_at")
    list_filter = ("product", "color_name", "size")
    search_fields = ("sku", "color_name", "size")
    inlines = [VariantImageInline]
    autocomplete_fields = ("product",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(VariantImage)
class VariantImageAdmin(admin.ModelAdmin):
    list_display = ("variant", "sort_order", "is_main", "updated_at")
    list_filter = ("is_main",)
    autocomplete_fields = ("variant",)
    readonly_fields = ("created_at", "updated_at")
