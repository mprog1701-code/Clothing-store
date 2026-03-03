from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Store
from catalog.models import Product

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status_badge", "is_active", "city", "logo_thumb", "updated_at")
    list_display_links = ("name", "slug")
    list_filter = ("is_active", "city", "updated_at")
    search_fields = ("name", "slug", "city", "phone")
    ordering = ("name",)
    list_editable = ("is_active", "city")
    readonly_fields = ("created_at", "updated_at", "logo_preview", "cover_preview")
    fieldsets = (
        ("التعريف", {"fields": ("name", "slug", "is_active")}),
        ("العنوان والاتصال", {"fields": ("address_line1", "address_line2", "city", "country", "phone")}),
        ("الصور", {"fields": ("logo", "cover", "logo_preview", "cover_preview")}),
        ("التواريخ", {"fields": ("created_at", "updated_at")}),
    )
    def status_badge(self, obj):
        color = "#10b981" if obj.is_active else "#ef4444"
        text = "نشط" if obj.is_active else "موقوف"
        return mark_safe(f"<span style='padding:4px 8px;border-radius:10px;background:{color}22;color:{color};font-weight:600'>{text}</span>")
    status_badge.short_description = "الحالة"
    def logo_thumb(self, obj):
        try:
            if obj.logo:
                return mark_safe(f"<img src='{obj.logo.url}' style='width:36px;height:36px;object-fit:cover;border-radius:6px'/>")
        except Exception:
            pass
        return ""
    logo_thumb.short_description = "الشعار"
    def logo_preview(self, obj):
        try:
            if obj.logo:
                return mark_safe(f"<img src='{obj.logo.url}' style='width:96px;height:96px;object-fit:cover;border-radius:8px'/>")
        except Exception:
            pass
        return ""
    def cover_preview(self, obj):
        try:
            if obj.cover:
                return mark_safe(f"<img src='{obj.cover.url}' style='width:160px;height:90px;object-fit:cover;border-radius:8px'/>")
        except Exception:
            pass
        return ""
