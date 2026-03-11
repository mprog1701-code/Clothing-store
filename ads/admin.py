from django.contrib import admin
from .models import Banner, Advertisement


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'placement', 'is_active', 'priority', 'updated_at']
    list_filter = ['placement', 'is_active']
    search_fields = ['title']


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'ad_type', 'is_active', 'order', 'updated_at']
    list_filter = ['position', 'ad_type', 'is_active']
    search_fields = ['title']
