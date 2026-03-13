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
        'preview',
        'title',
        'media_type_icon',
        'position_badge',
        'order',
        'slider_settings',
        'status_badge',
        'date_range',
    ]
    
    list_filter = ['position', 'media_type', 'is_active']
    search_fields = ['title', 'description']
    list_editable = ['order']
    
    fieldsets = (
        ('📢 معلومات الإعلان', {
            'fields': ('title', 'description')
        }),
        ('🎬 الوسائط', {
            'fields': ('media_type', 'image', 'video', 'video_url'),
            'description': 'اختر نوع الوسائط ثم ارفع الملف المناسب'
        }),
        ('🔗 الرابط', {
            'fields': ('link', 'open_in_app'),
        }),
        ('📍 الموضع والترتيب', {
            'fields': ('position', 'order'),
            'description': '''
                <strong>الموضع:</strong> اختر أين سيظهر الإعلان<br>
                <strong>الترتيب:</strong> الرقم الأقل يظهر أولاً في السلايدر (1، 2، 3...)
            '''
        }),
        ('⚙️ إعدادات السلايدر', {
            'fields': ('auto_slide', 'slide_duration'),
            'description': 'التحكم بالانتقال التلقائي بين الإعلانات'
        }),
        ('📅 الجدولة', {
            'fields': ('is_active', 'start_date', 'end_date'),
        }),
    )

    def preview(self, obj):
        if obj.media_type == 'image' and obj.image:
            return format_html('<img src="{}" width="100" height="60" style="border-radius: 8px; object-fit: cover;" />', obj.image.url)
        elif obj.media_type == 'video':
            return '🎬 فيديو'
        return '-'
    preview.short_description = 'معاينة'

    def media_type_icon(self, obj):
        icons = {
            'image': '🖼️ صورة',
            'video': '🎬 فيديو',
        }
        return icons.get(obj.media_type, obj.media_type)
    media_type_icon.short_description = 'النوع'

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

    def slider_settings(self, obj):
        if obj.auto_slide:
            return format_html(
                '<span>🔄 تلقائي - {} ث</span>',
                obj.slide_duration
            )
        return '👆 يدوي فقط'
    slider_settings.short_description = 'السلايدر'

    def status_badge(self, obj):
        if obj.is_valid():
            return format_html('<span style="background: #27ae60; color: white; padding: 5px 10px; border-radius: 12px; font-size: 11px;">✓ نشط</span>')
        return format_html('<span style="background: #95a5a6; color: white; padding: 5px 10px; border-radius: 12px; font-size: 11px;">⏸ متوقف</span>')
    status_badge.short_description = 'الحالة'

    def date_range(self, obj):
        start = obj.start_date.strftime('%Y-%m-%d') if obj.start_date else '—'
        end = obj.end_date.strftime('%Y-%m-%d') if obj.end_date else 'مفتوح'
        return format_html('<div style="font-size: 11px;"><div>📅 من: {}</div><div>📅 إلى: {}</div></div>', start, end)
    date_range.short_description = 'الفترة'
