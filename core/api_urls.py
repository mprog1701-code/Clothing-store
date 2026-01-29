from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AuthViewSet, StoreViewSet, ProductViewSet, AddressViewSet, OrderViewSet, FeatureFlagAdminList, FeatureFlagAdminUpdate

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'stores', StoreViewSet, basename='stores')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'addresses', AddressViewSet, basename='addresses')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/feature-flags', FeatureFlagAdminList.as_view()),
    path('admin/feature-flags/<str:key>', FeatureFlagAdminUpdate.as_view()),
]
