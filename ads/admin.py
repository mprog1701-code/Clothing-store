from django.contrib import admin
from .models import Banner

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "placement", "is_active", "priority", "starts_at", "ends_at", "updated_at")
    list_filter = ("placement", "is_active", "starts_at", "ends_at")
    search_fields = ("title",)
    actions = ["enable_selected", "disable_selected"]
    ordering = ("-priority",)
    readonly_fields = ("created_at", "updated_at")

    def enable_selected(self, request, queryset):
        queryset.update(is_active=True)

    def disable_selected(self, request, queryset):
        queryset.update(is_active=False)
