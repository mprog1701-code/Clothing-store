from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Store, Product, ProductImage, ProductVariant, Address, Order, OrderItem, SiteSettings, Campaign, ProductColor, AttributeColor, AttributeSize


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'phone', 'role', 'city', 'is_active']
    list_filter = ['role', 'is_active', 'city']
    search_fields = ['username', 'email', 'phone']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role', 'city')}),
    )
    list_per_page = 25


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'created_at']
    search_fields = ['name', 'owner__username']
    list_select_related = ('owner', 'owner_profile', 'owner_user')
    list_per_page = 25


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'category', 'size_type', 'base_price', 'is_active', 'created_at']
    list_filter = ['category', 'size_type', 'is_active', 'created_at']
    search_fields = ['name', 'store__name']
    inlines = []
    list_select_related = ('store',)
    list_per_page = 25

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 0
    fields = ['name', 'code']

ProductAdmin.inlines = []

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'code']
    list_filter = ['product']
    search_fields = ['product__name', 'name']
    inlines = []
    list_select_related = ('product',)
    list_per_page = 25

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['size', 'stock_qty', 'price_override']

ProductColorAdmin.inlines = [ProductVariantInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'variant', 'is_main']
    list_filter = ['is_main', 'color', 'variant']
    list_select_related = ('product', 'color', 'variant')
    list_per_page = 25
    

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ('variant', 'color', 'color_attr'):
            product_id = None
            if request.method == 'POST':
                product_id = request.POST.get('product')
            else:
                product_id = request.GET.get('product')
            try:
                product_id = int(product_id)
            except (TypeError, ValueError):
                product_id = None
            if db_field.name == 'variant':
                kwargs['queryset'] = ProductVariant.objects.filter(product_id=product_id) if product_id else ProductVariant.objects.none()
            elif db_field.name == 'color':
                kwargs['queryset'] = ProductColor.objects.filter(product_id=product_id) if product_id else ProductColor.objects.none()
            elif db_field.name == 'color_attr':
                if product_id:
                    color_ids = ProductVariant.objects.filter(product_id=product_id, color_attr__isnull=False).values_list('color_attr_id', flat=True).distinct()
                    kwargs['queryset'] = AttributeColor.objects.filter(id__in=list(color_ids))
                else:
                    kwargs['queryset'] = AttributeColor.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'color_attr', 'size_attr', 'size', 'stock_qty', 'price_override', 'is_enabled']
    list_filter = ['size', 'color_attr', 'size_attr', 'is_enabled']
    search_fields = ['product__name']
    list_select_related = ('product', 'color_attr', 'size_attr')
    list_per_page = 25


@admin.register(AttributeColor)
class AttributeColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']


@admin.register(AttributeSize)
class AttributeSizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    search_fields = ['name']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'area', 'street']
    search_fields = ['user__username', 'city', 'area']
    list_select_related = ('user',)
    list_per_page = 25


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'store', 'status', 'total_amount', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'store__name']
    inlines = [OrderItemInline]
    list_select_related = ('user', 'store')
    list_per_page = 25


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'variant', 'quantity', 'price']
    search_fields = ['order__id', 'product__name']
    list_select_related = ('order', 'product', 'variant')
    list_per_page = 25

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'featured_stores_count', 'featured_products_count']
    fieldsets = (
        ('الموقع', {'fields': ('site_name', 'site_description')}),
        ('التواصل', {'fields': ('contact_phone', 'contact_email', 'contact_address')}),
        ('الصفحة الرئيسية', {'fields': ('homepage_title', 'featured_stores_count', 'featured_products_count')}),
        ('التسليم', {'fields': ('delivery_fee', 'free_delivery_threshold')}),
        ('روابط التواصل', {'fields': ('facebook_url', 'instagram_url', 'twitter_url')}),
        ('الفوتر', {'fields': ('footer_store_name', 'footer_tagline', 'footer_description', 'footer_link_1', 'footer_link_1_url', 'footer_link_2', 'footer_link_2_url', 'footer_link_3', 'footer_link_3_url', 'footer_copyright', 'privacy_enabled', 'terms_enabled', 'contact_enabled')}),
        ('المظهر', {'fields': ('primary_color', 'secondary_color')}),
    )

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_percent', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title']
    list_per_page = 25
