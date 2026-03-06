
import os
import dj_database_url
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

print(f"DEBUG: Loading settings_railway.py")
print(f"DEBUG: Env vars keys: {[k for k in os.environ.keys() if 'DATA' in k or 'POST' in k]}")

# -----------------------------------------------------------------------------
# 1. SECURITY SETTINGS
# -----------------------------------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-prod-key-fallback')

DEBUG = False

# Security Headers for Railway
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Allowed Hosts
ALLOWED_HOSTS = ['*']
env_hosts = os.environ.get('ALLOWED_HOSTS')
if env_hosts:
    ALLOWED_HOSTS = [host.strip() for host in env_hosts.split(',') if host.strip()]

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = []
env_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS')
if env_csrf:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in env_csrf.split(',') if origin.strip()]
else:
    # Fallback for Railway domains
    CSRF_TRUSTED_ORIGINS = ['https://*.railway.app', 'https://*.up.railway.app']

# -----------------------------------------------------------------------------
# 2. APPLICATION DEFINITION
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    'jazzmin',
    'mathfilters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    
    # Local
    'core',
    'merchants',
    'catalog',
    'orders',
    'ads',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -----------------------------------------------------------------------------
# 3. CORE SETTINGS (The ones causing issues)
# -----------------------------------------------------------------------------
ROOT_URLCONF = "clothing_store.urls"
WSGI_APPLICATION = "clothing_store.wsgi.application"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# -----------------------------------------------------------------------------
# 4. DATABASE
# -----------------------------------------------------------------------------
# Diagnostic: Check DATABASE_URL
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    print(f"DEBUG: DATABASE_URL found (length={len(DATABASE_URL)})")
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=0,
            conn_health_checks=True,
        )
    }
else:
    print("WARNING: DATABASE_URL not found in environment variables!")
    print("WARNING: Using local sqlite3 fallback to prevent crash.")
    # Fallback to sqlite3 if Postgres is not available
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# -----------------------------------------------------------------------------
# 5. PASSWORD VALIDATION
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------------------------------------
# 6. I18N & L10N
# -----------------------------------------------------------------------------
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# 7. STATIC & MEDIA FILES
# -----------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Include the root 'static' directory
if (BASE_DIR / 'static').exists():
    STATICFILES_DIRS = [BASE_DIR / 'static']
else:
    # Fallback or empty if not found, though it should exist
    STATICFILES_DIRS = []

# Use non-manifest storage to avoid crashes on missing files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------------------------------------
# 8. DRF & API
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

CORS_ALLOW_ALL_ORIGINS = True  # Simplified for debugging, restrict later if needed

# -----------------------------------------------------------------------------
# 9. LOGGING & DIAGNOSTICS
# -----------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

print('LOADED SETTINGS: settings_railway')
print(f'ROOT_URLCONF={ROOT_URLCONF}')
print(f'WSGI_APPLICATION={WSGI_APPLICATION}')
print(f'BASE_DIR={BASE_DIR}')

# -----------------------------------------------------------------------------
# 10. JAZZMIN SETTINGS
# -----------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "متجر الملابس",
    "site_header": "لوحة التحكم",
    "site_brand": "إدارة المتجر",
    "site_logo": None,
    "welcome_sign": "مرحباً بك",
    "copyright": "متجر الملابس - العراق 2026",
    "search_model": ["core.User", "catalog.Product", "orders.Order"],
    
    "topmenu_links": [
        {"name": "الموقع", "url": "/", "new_window": True},
        {"name": "المنتجات", "url": "admin:catalog_product_changelist"},
        {"name": "الطلبات", "url": "admin:orders_order_changelist"},
    ],
    
    "show_sidebar": True,
    "navigation_expanded": True,
    
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "core.User": "fas fa-user-circle",
        "catalog.Product": "fas fa-tshirt",
        "catalog.Category": "fas fa-tags",
        "catalog.ProductVariant": "fas fa-palette",
        "catalog.ProductImage": "fas fa-images",
        "orders.Order": "fas fa-shopping-cart",
        "orders.OrderItem": "fas fa-list",
        "merchants.Store": "fas fa-store",
        "ads.Advertisement": "fas fa-bullhorn",
    },
    
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
