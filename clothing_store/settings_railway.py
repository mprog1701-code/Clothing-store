"""
Django settings for clothing_store project.
FIXED VERSION - Corrected for Railway deployment
"""

from pathlib import Path
from decimal import Decimal
import os
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
if not DEBUG:
    # Fallback to allow seeing errors if specifically requested via env var
    # This is useful for debugging 500 errors in production
    if os.environ.get('FORCE_DEBUG', 'False') == 'True':
        DEBUG = True

# 🔧 FIX 1: Simplified ALLOWED_HOSTS
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'mathfilters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'storages',
    
    # Local apps
    'core',
    'merchants',
    'catalog',
    'orders',
    'ads',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clothing_store.urls'

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

WSGI_APPLICATION = 'clothing_store.wsgi.application'

# 🔧 FIX 3: Simplified Database Configuration
# Check if we're on Railway or production
IS_RAILWAY = 'RAILWAY_ENVIRONMENT' in os.environ
IS_RENDER = 'RENDER' in os.environ
IS_PRODUCTION = IS_RAILWAY or IS_RENDER or (not DEBUG)

# Default to SQLite to prevent ImproperlyConfigured error
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    try:
        # Use dj-database-url to parse DATABASE_URL
        import dj_database_url
        
        print(f"DEBUG: Parsing DATABASE_URL...", file=sys.stderr)
        
        db_config = dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
        )
        
        # Verify we got a valid config with an engine
        if db_config and db_config.get('ENGINE'):
            DATABASES = {'default': db_config}
            print(f"DEBUG: Configured Database with engine: {db_config['ENGINE']}", file=sys.stderr)
        else:
            print("WARNING: DATABASE_URL parsed but yielded no ENGINE. Keeping SQLite.", file=sys.stderr)
            
    except Exception as e:
        print(f"ERROR: Failed to configure database: {e}. Keeping SQLite.", file=sys.stderr)
else:
    print("DEBUG: No DATABASE_URL found in environment. Using SQLite.", file=sys.stderr)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 🔧 FIX 4: Simplified Static Files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True
WHITENOISE_USE_FINDERS = True


# Media files
MEDIA_URL = '/media/'
_railway_volume = os.environ.get('RAILWAY_VOLUME_PATH')
MEDIA_ROOT = (Path(_railway_volume) if _railway_volume else BASE_DIR) / 'media'

AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', '')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'auto')
AWS_S3_SIGNATURE_VERSION = os.environ.get('AWS_S3_SIGNATURE_VERSION', 's3v4')
AWS_S3_ADDRESSING_STYLE = os.environ.get('AWS_S3_ADDRESSING_STYLE', 'path')
AWS_QUERYSTRING_AUTH = False
AWS_S3_CUSTOM_DOMAIN = os.environ.get('R2_PUBLIC_DOMAIN') or os.environ.get('R2_PUBLIC_BASE_URL') or os.environ.get('AWS_S3_CUSTOM_DOMAIN')

if AWS_STORAGE_BUCKET_NAME and AWS_S3_ENDPOINT_URL:
    DEFAULT_FILE_STORAGE = 'core.storage.R2MediaStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'core.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# 🔧 FIX 6: Simplified CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "http://192.168.1.102:19006",
    "http://192.168.1.102:8081",
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # Add production origins from environment
    prod_origins = os.environ.get('CORS_ORIGINS', '')
    if prod_origins:
        CORS_ALLOWED_ORIGINS.extend([o.strip() for o in prod_origins.split(',') if o.strip()])

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Custom authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Delivery fee
DELIVERY_FEE = Decimal('5000')  # 5000 IQD

# 🔧 FIX 7: Security Settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
    'https://*.onrender.com',
    'https://*.vercel.app',
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS += [
        'http://192.168.1.102:8000',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

# Only enable security features in production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# 🔧 FIX 8: Simplified Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
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
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# DRF Spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Clothing Store API',
    'DESCRIPTION': 'REST API for Clothing Store',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# 🔧 FIX 10: Disable Cache Temporarily
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# 🔧 FIX 9: Print diagnostics only in DEBUG
if DEBUG:
    print(f"DEBUG: {DEBUG}")
    print(f"IS_RAILWAY: {IS_RAILWAY}")
    print(f"IS_PRODUCTION: {IS_PRODUCTION}")
    print(f"DATABASE: {DATABASES['default'].get('ENGINE', 'unknown')}")
    print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")

###################
# JAZZMIN SETTINGS #
###################
JAZZMIN_SETTINGS = {
    "site_title": "متجر الملابس",
    "site_header": "إدارة المتجر",
    "site_brand": "لوحة التحكم",
    "welcome_sign": "مرحباً بك في لوحة تحكم المتجر",
    "copyright": "Clothing Store Ltd",
    "search_model": ["core.User", "core.Store"],
    "user_avatar": None,
    "usermenu_links": [
        {"name": "الدعم الفني", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "core.User"}
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["core", "catalog", "orders", "auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "core.User": "fas fa-user-shield",
        "core.Store": "fas fa-store",
        "catalog.Category": "fas fa-list",
        "catalog.Product": "fas fa-tshirt",
        "catalog.Variant": "fas fa-tags",
        "orders.Order": "fas fa-shopping-cart",
        "orders.OrderItem": "fas fa-receipt",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-success",
    "navbar": "navbar-success navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "theme": "flatly",
    # "dark_mode_theme": "darkly",  # Deprecated
    "button_classes": {
        "primary": "btn-success",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Disable caching in development/testing to see changes immediately
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
