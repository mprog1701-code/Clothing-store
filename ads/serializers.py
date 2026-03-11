from rest_framework import serializers
from django.conf import settings
from .models import Advertisement, _normalize_url


class AdvertisementSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Advertisement
        fields = [
            'id',
            'title',
            'description',
            'image',
            'image_url',
            'link',
            'position',
            'ad_type',
            'order',
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        try:
            request = self.context.get('request')
            if request:
                return _normalize_url(request.build_absolute_uri(obj.image.url))
            base = getattr(settings, 'MEDIA_URL', '/media/')
            return _normalize_url(f"{base.rstrip('/')}/{obj.image.name}")
        except Exception:
            return None
