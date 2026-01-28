from core.models import SiteSettings
from django.conf import settings

def site_settings(request):
    """Context processor to make site settings available in all templates"""
    settings_obj, created = SiteSettings.objects.get_or_create(id=1)
    features = getattr(settings, 'FEATURE_FLAGS', {})
    return {'settings': settings_obj, 'features': features}
