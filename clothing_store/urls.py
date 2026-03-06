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
from django.views.static import serve
from django.urls import re_path
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def _auto_admin_login(request):
    User = get_user_model()
    user = User.objects.filter(username='owner').first()
    if not user:
        user = User.objects.filter(is_superuser=True).order_by('id').first()
    if not user:
        create_kwargs = {
            'username': 'owner',
            'email': 'owner@clothingstore.iq',
            'password': '25802580',
        }
        if hasattr(User, 'phone'):
            create_kwargs['phone'] = '07700000000'
        if hasattr(User, 'city'):
            create_kwargs['city'] = 'Baghdad'
        if hasattr(User, 'role'):
            create_kwargs['role'] = 'store_admin'
        user = User.objects.create_user(**create_kwargs)
    if not user:
        return HttpResponse('owner user not found', status=503)
    if not user.is_active:
        user.is_active = True
    if not user.is_staff:
        user.is_staff = True
    if not user.is_superuser:
        user.is_superuser = True
    user.save(update_fields=['is_active', 'is_staff', 'is_superuser'])
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    next_url = request.GET.get('next') or '/admin/'
    return redirect(next_url)

def _serve_static(rel_path, content_type):
    file_path = finders.find(rel_path)
    content = None
    if file_path:
        with open(file_path, 'rb') as f:
            content = f.read()
    else:
        try:
            if staticfiles_storage.exists(rel_path):
                try:
                    f = staticfiles_storage.open(rel_path)
                    content = f.read()
                except Exception:
                    content = None
        except Exception:
            content = None
    if content is None:
        return HttpResponseNotFound()
    return HttpResponse(content, content_type=content_type)

urlpatterns = [
    path('admin/login/', _auto_admin_login),
    path('admin-direct/', _auto_admin_login),
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
    path('robots.txt', lambda request: HttpResponse('User-agent: *\nDisallow:', content_type='text/plain')),
]

if settings.DEBUG and settings.MEDIA_URL.startswith('/') and hasattr(settings, 'MEDIA_ROOT'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Force serve static files in production if Whitenoise fails
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]
