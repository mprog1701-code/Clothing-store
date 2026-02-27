"""
URL configuration for clothing_store project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.decorators.http import require_GET
from django.contrib.staticfiles import finders
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def _serve_static(rel_path, content_type):
    file_path = finders.find(rel_path)
    content = None
    if file_path:
        with open(file_path, 'rb') as f:
            content = f.read()
    elif staticfiles_storage.exists(rel_path):
        content = staticfiles_storage.open(rel_path).read()
    if content is None:
        return HttpResponseNotFound()
    return HttpResponse(content, content_type=content_type)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('api/', include('core.api_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # PWA files at root scope
    path('manifest.json', lambda request: _serve_static('pwa/manifest.json', 'application/manifest+json')),
    path('service-worker.js', lambda request: _serve_static('pwa/service-worker.js', 'application/javascript')),
    path('app.html', lambda request: _serve_static('pwa/app.html', 'text/html')),
]

if settings.DEBUG and settings.MEDIA_URL.startswith('/') and hasattr(settings, 'MEDIA_ROOT'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
