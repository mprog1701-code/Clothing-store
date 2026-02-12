from core.models import SiteSettings, FeatureFlag
from django.conf import settings
from django.core.cache import cache

def site_settings(request):
    """Context processor to make site settings available in all templates"""
    settings_obj, created = SiteSettings.objects.get_or_create(id=1)
    features = dict(getattr(settings, 'FEATURE_FLAGS', {}) or {})
    features.setdefault('NEGOTIATION_ENABLED', True)
    cached = cache.get('feature_flags_cache')
    if cached is None:
        try:
            objs = FeatureFlag.objects.all()
            cached = {o.key: bool(o.enabled) for o in objs}
        except Exception:
            cached = {}
        cache.set('feature_flags_cache', cached, 300)
    for k, v in (cached or {}).items():
        features[k] = v
    return {'settings': settings_obj, 'features': features}
