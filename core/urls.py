from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.hybrid_home, name='home'),
    path('classic/', views.home, name='home_classic'),
    path('stores/', views.store_list, name='store_list'),
    path('stores/<int:store_id>/', views.store_detail, name='store_detail'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('owner-login/', views.owner_login, name='owner_login'),
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
    
    path('checkout/', views.checkout, name='checkout'),
    path('my/orders/', views.order_list, name='order_list'),
    path('my/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Address URLs
    path('my/addresses/', views.address_list, name='address_list'),
    path('my/addresses/create/', views.address_create, name='address_create'),
    path('my/addresses/edit/<int:address_id>/', views.address_edit, name='address_edit'),
    path('my/addresses/delete/<int:address_id>/', views.address_delete, name='address_delete'),
    path('profile/', views.account_settings, name='profile'),
    path('my/account/', views.account_settings, name='account_settings'),
    path('notifications/', views.notifications_page, name='notifications'),
    path('about/', views.about_page, name='about'),
    path('services/', views.services_page, name='services'),
    
    # Store owner URLs removed - simplified system
    
    path('dashboard/admin/', views.admin_overview, name='admin_overview'),
    path('dashboard/admin/stores/', views.admin_stores, name='admin_stores'),
    
    # Super Owner Dashboard URLs
    path('dashboard/super-owner/', views.super_owner_dashboard, name='super_owner_dashboard'),
    path('dashboard/super-owner/stores/', views.super_owner_stores, name='super_owner_stores'),
    path('dashboard/super-owner/stores/add/', views.super_owner_add_store, name='super_owner_add_store'),
    path('dashboard/super-owner/stores/edit/<int:store_id>/', views.super_owner_edit_store, name='super_owner_edit_store'),
    path('dashboard/super-owner/products/', views.super_owner_products, name='super_owner_products'),
    path('dashboard/super-owner/products/add/', views.super_owner_add_product, name='super_owner_add_product'),
    path('dashboard/super-owner/products/edit/<int:product_id>/', views.super_owner_edit_product, name='super_owner_edit_product'),
    path('dashboard/super-owner/orders/', views.super_owner_orders, name='super_owner_orders'),
    path('dashboard/super-owner/settings/', views.super_owner_settings, name='super_owner_settings'),
    path('dashboard/footer-settings/', views.footer_settings, name='footer_settings'),
    
    path('featured-products/', views.featured_products, name='featured_products'),
    path('products/most-sold/', views.most_sold_products, name='most_sold_products'),
    
    # Debug URLs for testing
    path('debug-owner-login/', views.debug_owner_login, name='debug_owner_login'),
]
