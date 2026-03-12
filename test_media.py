import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if 'RAILWAY_ENVIRONMENT' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings_railway')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings_dev')

import django
django.setup()

from django.conf import settings
from django.core.files.storage import default_storage
from core.models import ProductImage, Campaign
from ads.models import Advertisement

try:
    from ads.models import Banner
except Exception:
    Banner = None

print(f"SETTINGS={os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"MEDIA_URL={getattr(settings, 'MEDIA_URL', '')}")
print(f"MEDIA_ROOT={getattr(settings, 'MEDIA_ROOT', '')}")
print(f"STORAGE_BACKEND={default_storage.__class__.__module__}.{default_storage.__class__.__name__}")
print(f"R2_PUBLIC_BASE_URL={os.environ.get('R2_PUBLIC_BASE_URL', '')}")
print(f"R2_PUBLIC_DOMAIN={os.environ.get('R2_PUBLIC_DOMAIN', '')}")
print(f"AWS_S3_ENDPOINT_URL={os.environ.get('AWS_S3_ENDPOINT_URL', '')}")
print(f"AWS_STORAGE_BUCKET_NAME={os.environ.get('AWS_STORAGE_BUCKET_NAME', '')}")

img_count = ProductImage.objects.count()
camp_count = Campaign.objects.count()
print(f"COUNT ProductImage={img_count}")
print(f"COUNT Campaign={camp_count}")
print(f"COUNT Advertisement={Advertisement.objects.count()}")
if Banner is not None:
    print(f"COUNT Banner={Banner.objects.count()}")

pi = ProductImage.objects.order_by('-id').first()
if pi:
    print(f"LAST ProductImage id={pi.id} name={pi.image.name if pi.image else ''}")
    try:
        print(f"LAST ProductImage url={pi.get_image_url()}")
        if pi.image and pi.image.name:
            print(f"storage.exists={default_storage.exists(pi.image.name)}")
    except Exception as e:
        print(f"ProductImage url error={e}")

camp = Campaign.objects.order_by('-id').first()
if camp:
    print(f"LAST Campaign id={camp.id} title={camp.title}")
    try:
        print(f"LAST Campaign url={camp.get_banner_url()}")
        if camp.banner_image and camp.banner_image.name:
            print(f"storage.exists={default_storage.exists(camp.banner_image.name)}")
    except Exception as e:
        print(f"Campaign url error={e}")

ad = Advertisement.objects.order_by('-id').first()
if ad:
    print(f"LAST Advertisement id={ad.id} title={ad.title}")
    try:
        print(f"LAST Advertisement url={ad.image.url if ad.image else ''}")
    except Exception as e:
        print(f"Advertisement url error={e}")

if Banner is not None:
    b = Banner.objects.order_by('-id').first()
    if b:
        print(f"LAST Banner id={b.id} title={b.title}")
        try:
            print(f"LAST Banner url={b.get_image_url()}")
            if b.image and b.image.name:
                print(f"storage.exists={default_storage.exists(b.image.name)}")
        except Exception as e:
            print(f"Banner url error={e}")
