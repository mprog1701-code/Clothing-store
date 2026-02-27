from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("id", "user__username")
    inlines = [CartItemInline]
    readonly_fields = ("created_at", "updated_at")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "store", "user", "total", "updated_at")
    list_filter = ("status", "store", "created_at")
    search_fields = ("id", "user__username")
    actions = ["set_status_pending", "set_status_processing", "set_status_completed", "set_status_cancelled"]
    inlines = [OrderItemInline]
    readonly_fields = ("total_items", "subtotal", "delivery_fee", "total", "created_at", "updated_at")

    def set_status_pending(self, request, queryset):
        queryset.update(status="pending")

    def set_status_processing(self, request, queryset):
        queryset.update(status="processing")

    def set_status_completed(self, request, queryset):
        queryset.update(status="completed")

    def set_status_cancelled(self, request, queryset):
        queryset.update(status="cancelled")

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "variant", "price", "qty", "updated_at")
    search_fields = ("order__id", "variant__sku")
    readonly_fields = ("created_at", "updated_at")
