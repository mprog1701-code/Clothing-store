from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Product, Variant, VariantImage, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_active']

class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 1
    readonly_fields = ['preview']

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="80" style="border-radius:5px;"/>', obj.image.url)
        return "-"
    preview.short_description = 'معاينة'

class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ['color_name', 'size', 'stock', 'price_override', 'sku']
    show_change_link = True

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['thumbnail', 'title', 'store', 'category', 'price_display', 'stock_badge', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category', 'store', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'is_featured']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)} if hasattr(Product, 'slug') else {}
    inlines = [VariantInline]

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'store', 'category')
        }),
        ('التفاصيل', {
            'fields': ('description', 'base_price', 'is_active', 'is_featured')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def thumbnail(self, obj):
        # Try to find an image from the first variant
        variant = obj.variants.first()
        if variant:
            img = variant.images.first()
            if img and img.image:
                return format_html('<img src="{}" width="60" height="60" style="border-radius:8px;"/>', img.image.url)
        return "🖼️"
    thumbnail.short_description = 'صورة'

    def price_display(self, obj):
        return format_html('<strong style="color:#27ae60;">{:,} د.ع</strong>', int(obj.base_price))
    price_display.short_description = 'السعر'

    def stock_badge(self, obj):
        total = sum(v.stock for v in obj.variants.all())
        if total > 10:
            return format_html('<span style="background:#27ae60;color:white;padding:3px 10px;border-radius:5px;">✓ متوفر ({})</span>', total)
        elif total > 0:
            return format_html('<span style="background:#f39c12;color:white;padding:3px 10px;border-radius:5px;">⚠ محدود ({})</span>', total)
        else:
            return format_html('<span style="background:#e74c3c;color:white;padding:3px 10px;border-radius:5px;">✗ نفذ</span>')
    stock_badge.short_description = 'المخزون'

    actions = ['activate', 'deactivate']

    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = 'تفعيل المنتجات'

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = 'إلغاء التفعيل'

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'sku', 'color_name', 'size', 'stock', 'price_override']
    search_fields = ['sku', 'product__title']
    inlines = [VariantImageInline]

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
