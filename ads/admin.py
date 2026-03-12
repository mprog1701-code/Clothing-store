from django.contrib import admin
from django.utils.html import format_html
from .models import Banner, Advertisement


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'placement', 'is_active', 'priority', 'updated_at']
    list_filter = ['placement', 'is_active']
    search_fields = ['title']


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = [
        'preview_image',
        'title',
        'position_badge',
        'type_badge',
        'order',
        'status_badge',
        'validity_period',
        'stats',
        'actions_column',
    ]
    list_filter = ['position', 'ad_type', 'is_active', 'start_date']
    search_fields = ['title', 'description']
    list_editable = ['order']
    fieldsets = (
        ('معلومات أساسية', {'fields': ('title', 'description', 'image', 'link')}),
        ('موضع الإعلان', {'fields': ('position', 'ad_type', 'order'), 'description': 'حدد أين سيظهر الإعلان في الموقع أو التطبيق'}),
        ('الجدولة', {'fields': ('is_active', 'start_date', 'end_date')}),
        ('الإحصائيات', {'fields': ('impressions', 'clicks'), 'classes': ('collapse',)}),
    )

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="60" style="border-radius: 8px; object-fit: cover;" />', obj.image.url)
        return '-'
    preview_image.short_description = 'الصورة'

    def position_badge(self, obj):
        colors = {
            'home_top': '#e74c3c',
            'home_middle': '#3498db',
            'home_bottom': '#27ae60',
            'mobile_banner': '#e94560',
            'mobile_card': '#8b2f97',
        }
        color = colors.get(obj.position, '#95a5a6')
        return format_html('<span style="background: {}; color: white; padding: 5px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>', color, obj.get_position_display())
    position_badge.short_description = 'الموضع'

    def type_badge(self, obj):
        return format_html('<span style="background: #34495e; color: white; padding: 5px 10px; border-radius: 12px; font-size: 11px;">{}</span>', obj.get_ad_type_display())
    type_badge.short_description = 'النوع'

    def status_badge(self, obj):
        if obj.is_valid():
            return format_html('<span style="background: #27ae60; color: white; padding: 5px 10px; border-radius: 12px; font-size: 11px;">✓ نشط</span>')
        return format_html('<span style="background: #95a5a6; color: white; padding: 5px 10px; border-radius: 12px; font-size: 11px;">⏸ متوقف</span>')
    status_badge.short_description = 'الحالة'

    def validity_period(self, obj):
        start = obj.start_date.strftime('%Y-%m-%d') if obj.start_date else '—'
        end = obj.end_date.strftime('%Y-%m-%d') if obj.end_date else 'مفتوح'
        return format_html('<div style="font-size: 11px;"><div>📅 من: {}</div><div>📅 إلى: {}</div></div>', start, end)
    validity_period.short_description = 'الفترة'

    def stats(self, obj):
        ctr = (obj.clicks / obj.impressions * 100) if obj.impressions > 0 else 0
        return format_html('<div style="font-size: 11px;"><div>👁️ {}</div><div>👆 {} ({}%)</div></div>', obj.impressions, obj.clicks, round(ctr, 1))
    stats.short_description = 'الإحصائيات'

    def actions_column(self, obj):
        return format_html('<a href="/admin/ads/advertisement/{}/change/" class="button">تعديل</a>', obj.id)
    actions_column.short_description = 'إجراء'
