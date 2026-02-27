from django.contrib import admin
from .models import Store
from catalog.models import Product

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "city", "updated_at")
    list_filter = ("is_active", "city")
    search_fields = ("name", "slug")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = []
