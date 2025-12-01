from core.models import SiteSettings

def site_settings(request):
    """Context processor to make site settings available in all templates"""
    settings_obj, created = SiteSettings.objects.get_or_create(id=1)
    return {'settings': settings_obj}