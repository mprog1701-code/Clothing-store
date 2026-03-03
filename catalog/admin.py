from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product, Variant, VariantImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status_badge", "is_active", "updated_at")
    list_display_links = ("title", "slug")
    list_filter = ("is_active", "updated_at")
    search_fields = ("title", "slug")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("المعلومات", {"fields": ("title", "slug", "is_active")}),
        ("التواريخ", {"fields": ("created_at", "updated_at")}),
    )
    def status_badge(self, obj):
        color = "#10b981" if obj.is_active else "#ef4444"
        text = "نشط" if obj.is_active else "موقوف"
        return mark_safe(f"<span style='padding:4px 8px;border-radius:10px;background:{color}22;color:{color};font-weight:600'>{text}</span>")
    status_badge.short_description = "الحالة"

class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0
    fields = ("sku", "color_name", "color_hex", "size", "stock", "price_override", "updated_at")
    readonly_fields = ("updated_at", "created_at")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "category", "status_badge", "is_active", "base_price", "updated_at")
    list_display_links = ("title",)
    list_filter = ("is_active", "store", "category", "updated_at")
    search_fields = ("title", "description")
    autocomplete_fields = ("store", "category")
    list_editable = ("is_active", "base_price")
    inlines = [VariantInline]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("التعريف", {"fields": ("store", "category", "title", "is_active")}),
        ("السعر", {"fields": ("base_price",)}),
        ("الوصف", {"fields": ("description",)}),
        ("التواريخ", {"fields": ("created_at", "updated_at")}),
    )
    def status_badge(self, obj):
        color = "#10b981" if obj.is_active else "#ef4444"
        text = "نشط" if obj.is_active else "موقوف"
        return mark_safe(f"<span style='padding:4px 8px;border-radius:10px;background:{color}22;color:{color};font-weight:600'>{text}</span>")
    status_badge.short_description = "الحالة"

class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 0
    fields = ("preview", "image", "sort_order", "is_main", "updated_at")
    readonly_fields = ("preview", "updated_at", "created_at")
    def preview(self, obj):
        if not obj or not getattr(obj, "image", None):
            return ""
        try:
            url = obj.image.url
            return mark_safe(f"<img src='{url}' style='width:60px;height:60px;object-fit:cover;border-radius:8px'/>")
        except Exception:
            return ""
    preview.short_description = "معاينة"

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "color_badge", "size", "stock", "price_override", "updated_at")
    list_display_links = ("sku",)
    list_filter = ("product", "color_name", "size", "updated_at")
    search_fields = ("sku", "color_name", "size")
    list_editable = ("stock", "price_override")
    inlines = [VariantImageInline]
    autocomplete_fields = ("product",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("التعريف", {"fields": ("product", "sku")}),
        ("الخصائص", {"fields": ("color_name", "color_hex", "size")}),
        ("التسعير والمخزون", {"fields": ("stock", "price_override")}),
        ("التواريخ", {"fields": ("created_at", "updated_at")}),
    )
    def color_badge(self, obj):
        hexv = (obj.color_hex or "#999999").strip() or "#999999"
        name = obj.color_name or ""
        return mark_safe(f"<span style='display:inline-flex;align-items:center;gap:6px'><span style='width:12px;height:12px;border-radius:50%;background:{hexv};border:1px solid #ddd'></span>{name}</span>")
    color_badge.short_description = "اللون"

@admin.register(VariantImage)
class VariantImageAdmin(admin.ModelAdmin):
    list_display = ("thumb", "variant", "sort_order", "is_main", "updated_at")
    list_display_links = ("variant",)
    list_filter = ("is_main", "updated_at")
    autocomplete_fields = ("variant",)
    readonly_fields = ("created_at", "updated_at", "thumb")
    def thumb(self, obj):
        try:
            url = obj.image.url
            return mark_safe(f"<img src='{url}' style='width:40px;height:40px;object-fit:cover;border-radius:6px'/>")
        except Exception:
            return ""
    thumb.short_description = "صورة"
