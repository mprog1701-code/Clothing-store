from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Store, Product, ProductImage, ProductVariant, Address, Order, OrderItem, SiteSettings, Campaign


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'phone', 'role', 'city', 'is_active']
    list_filter = ['role', 'is_active', 'city']
    search_fields = ['username', 'email', 'phone']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role', 'city')}),
    )


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'created_at']
    search_fields = ['name', 'owner__username']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'category', 'size_type', 'base_price', 'is_active', 'created_at']
    list_filter = ['category', 'size_type', 'is_active', 'created_at']
    search_fields = ['name', 'store__name']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_main']
    list_filter = ['is_main']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'color', 'stock_qty', 'price_override']
    list_filter = ['size', 'color']
    search_fields = ['product__name']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'area', 'street']
    search_fields = ['user__username', 'city', 'area']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'store', 'status', 'total_amount', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'store__name']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'variant', 'quantity', 'price']
    search_fields = ['order__id', 'product__name']

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
