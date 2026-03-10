from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AuthViewSet, StoreViewSet, ProductViewSet, AddressViewSet, OrderViewSet, FeatureFlagAdminList, FeatureFlagAdminUpdate, CategoryList, BannerList, BannerHomeTop, CartViewSet, DevSeed, Health, AdsList

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'stores', StoreViewSet, basename='stores')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'addresses', AddressViewSet, basename='addresses')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/feature-flags', FeatureFlagAdminList.as_view()),
    path('admin/feature-flags/<str:key>', FeatureFlagAdminUpdate.as_view()),
    path('categories', CategoryList.as_view()),
    path('banners', BannerList.as_view()),
    path('banners/home-top/', BannerHomeTop.as_view()),
    path('ads/', AdsList.as_view()),
    path('dev/seed', DevSeed.as_view()),
    path('health', Health.as_view()),
]
