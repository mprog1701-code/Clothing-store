from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['variant', 'qty', 'price']
    readonly_fields = ['variant', 'qty', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'store', 'status_badge', 'total_display', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at', 'store']
    search_fields = ['id', 'user__username', 'user__email', 'user__phone']
    readonly_fields = ['created_at', 'updated_at', 'total']
    inlines = [OrderItemInline]

    fieldsets = (
        ('معلومات الطلب', {
            'fields': ('user', 'store', 'status')
        }),
        ('المبالغ', {
            'fields': ('total', 'delivery_fee', 'payment_method')
        }),
        ('العنوان والملاحظات', {
            'fields': ('address_text', 'notes') if hasattr(Order, 'notes') else ('address_text',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'preparing': '#007bff',
            'shipped': '#6c757d',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        labels = {
            'pending': 'قيد الانتظار',
            'confirmed': 'مؤكد',
            'preparing': 'قيد التجهيز',
            'shipped': 'تم الشحن',
            'delivered': 'تم التوصيل',
            'cancelled': 'ملغي',
            'open': 'مفتوح',
        }
        return format_html(
            '<span style="background:{};color:white;padding:5px 12px;border-radius:5px;font-weight:bold;">{}</span>',
            color, labels.get(obj.status, obj.status)
        )
    status_badge.short_description = 'الحالة'

    def total_display(self, obj):
        return format_html('<strong style="color:#27ae60;">{:,} د.ع</strong>', int(obj.total))
    total_display.short_description = 'المجموع'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "variant", "price", "qty", "updated_at")
    search_fields = ("order__id", "variant__sku")
    readonly_fields = ("created_at", "updated_at")
