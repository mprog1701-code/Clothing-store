from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.hybrid_home, name='home'),
    path('offline/', views.offline_fallback, name='offline'),
    path('health/', views.health, name='health'),
    path('classic/', views.home, name='home_classic'),
    path('stores/', views.store_list, name='store_list'),
    path('stores/<int:store_id>/', views.store_detail, name='store_detail'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    path('announcements/', views.announcements, name='announcements'),
    
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('owner-login/', views.owner_login, name='owner_login'),
    path('admin-portal/login/', views.admin_portal_login, name='admin_portal_login'),
    path('admin-portal/dashboard/', views.admin_portal_dashboard, name='admin_portal_dashboard'),
    path('admin-portal/orders/', views.admin_portal_orders, name='admin_portal_orders'),
    path('admin-portal/products/', views.admin_portal_products, name='admin_portal_products'),
    path('admin-portal/stores/', views.admin_portal_stores, name='admin_portal_stores'),
    path('admin-portal/customers/', views.admin_portal_customers, name='admin_portal_customers'),
    path('admin-portal/settings/', views.admin_portal_settings, name='admin_portal_settings'),
    path('owner-password-reset/', views.owner_password_reset, name='owner_password_reset'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Main Dashboard
    path('dashboard/', views.main_dashboard, name='main_dashboard'),
    path('dashboard/store/products/', views.store_products, name='store_products'),
    path('dashboard/store/orders/', views.store_orders, name='store_orders'),
    
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:index>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/items', views.cart_items_json, name='cart_items_json'),
    
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/apply-coupon/', views.apply_coupon_json, name='apply_coupon_json'),
    path('my/orders/', views.order_list, name='order_list'),
    path('my/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('api/rate-app/', views.rate_app_json, name='rate_app_json'),
    path('api/stores/<int:store_id>/rate/', views.rate_store_json, name='rate_store_json'),
    
    # Address URLs
    path('my/addresses/', views.address_list, name='address_list'),
    path('my/addresses/create/', views.address_create, name='address_create'),
    path('my/addresses/edit/<int:address_id>/', views.address_edit, name='address_edit'),
    path('my/addresses/delete/<int:address_id>/', views.address_delete, name='address_delete'),
    path('my/addresses/pick/', views.address_picker, name='address_picker'),
    path('my/addresses/save-json/', views.address_save_json, name='address_save_json'),
    path('profile/', views.account_settings, name='profile'),
    path('my/account/', views.account_dashboard, name='account_settings'),
    path('my/account/settings/', views.account_settings, name='account_settings_page'),
    path('notifications/', views.notifications_page, name='notifications'),
    path('about/', views.about_page, name='about'),
    path('services/', views.services_page, name='services'),
    path('privacy/', views.privacy_page, name='privacy'),
    path('terms/', views.terms_page, name='terms'),
    path('contact/', views.contact_page, name='contact'),
    
    # Store owner URLs removed - simplified system
    
    path('dashboard/admin/', views.admin_overview, name='admin_overview'),
    path('dashboard/admin/stores/', views.admin_stores, name='admin_stores'),
    path('dashboard/admin/db-diagnostics/', views.admin_db_diagnostics, name='admin_db_diagnostics'),
    
    # Super Owner Dashboard URLs
    path('dashboard/super-owner/', views.super_owner_dashboard, name='super_owner_dashboard'),
    path('dashboard/super-owner/owners/', views.super_owner_owners, name='super_owner_owners'),
    path('dashboard/super-owner/stores/', views.super_owner_stores, name='super_owner_stores'),
    # إزالة صفحة الإضافة السريعة وصفحة الإضافة القديمة
    path('dashboard/super-owner/stores/create/', views.super_owner_create_store, name='super_owner_create_store'),
    path('dashboard/super-owner/owners/search/', views.super_owner_owner_search_json, name='super_owner_owner_search_json'),
    path('dashboard/super-owner/owners/create/', views.super_owner_create_owner_json, name='super_owner_create_owner_json'),
    path('dashboard/super-owner/owners/disable/<int:owner_id>/', views.super_owner_disable_owner_json, name='super_owner_disable_owner_json'),
    path('dashboard/super-owner/stores/<int:store_id>/', views.super_owner_store_center, name='super_owner_store_center'),
    path('dashboard/super-owner/stores/<int:store_id>/settings/', views.super_owner_edit_store, name='super_owner_store_settings'),
    path('dashboard/super-owner/stores/edit/<int:store_id>/', views.super_owner_edit_store, name='super_owner_edit_store'),
    path('dashboard/super-owner/products/', views.super_owner_products, name='super_owner_products'),
    path('dashboard/super-owner/products/add/', views.super_owner_add_product, name='super_owner_add_product'),
    path('dashboard/super-owner/products/edit/<int:product_id>/', views.super_owner_edit_product, name='super_owner_edit_product'),
    path('dashboard/super-owner/images/bind-color/', views.bind_image_to_color, name='bind_image_to_color'),
    path('dashboard/super-owner/inventory/', views.super_owner_inventory, name='super_owner_inventory'),
    # تم إزالة مسارات Excel بالكامل
    path('dashboard/super-owner/orders/', views.super_owner_orders, name='super_owner_orders'),
    path('dashboard/super-owner/orders/update-status-json/', views.super_owner_update_order_status_json, name='super_owner_update_order_status_json'),
    path('dashboard/super-owner/orders/update-delivery-json/', views.super_owner_update_delivery_json, name='super_owner_update_delivery_json'),
    path('dashboard/super-owner/orders/delete-json/', views.super_owner_delete_order_json, name='super_owner_delete_order_json'),
    path('dashboard/super-owner/orders/statuses-json/', views.super_owner_orders_statuses_json, name='super_owner_orders_statuses_json'),
    path('dashboard/super-owner/settings/', views.super_owner_settings, name='super_owner_settings'),
    path('dashboard/super-owner/announcements/', views.super_owner_announcements, name='super_owner_announcements'),
    path('dashboard/super-owner/reports/', views.super_owner_reports, name='super_owner_reports'),
    path('dashboard/super-owner/issues/', views.super_owner_issues, name='super_owner_issues'),
    path('dashboard/footer-settings/', views.footer_settings, name='footer_settings'),
    
    path('featured-products/', views.featured_products, name='featured_products'),
    path('products/most-sold/', views.most_sold_products, name='most_sold_products'),
    path('healthz/', views.healthz, name='healthz'),
    path('orders/track/<int:order_id>/<str:token>/', views.order_track, name='order_track'),
    path('orders/track/update-json/', views.order_track_update_json, name='order_track_update_json'),
    path('share/delivery/<str:token>/', views.share_delivery, name='share_delivery'),
    path('share/store/<str:token>/', views.share_store, name='share_store'),
    path('share/status/update-json/', views.share_status_update_json, name='share_status_update_json'),
    
    # Debug URLs for testing
    path('debug-owner-login/', views.debug_owner_login, name='debug_owner_login'),
    path('debug/log-js/', views.log_js_error, name='log_js_error'),
    path('dashboard/super-owner/technical-debugger/', views.technical_debugger, name='technical_debugger'),
]
