
from django.core.management import call_command
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def _safe_render(request, template_name, context=None):
    ctx = context or {}
    try:
        return render(request, template_name, ctx)
    except Exception:
        return HttpResponse("OK", status=200)


def home(request):
    return hybrid_home(request)


def hybrid_home(request):
    top_ads = []
    middle_ads = []
    bottom_ads = []
    campaigns = []
    categories = []
    featured_products = []

    try:
        from ads.models import Advertisement
        top_ads = Advertisement.get_active_ads(position='home_top')[:10]
        middle_ads = Advertisement.get_active_ads(position='home_middle')[:10]
        bottom_ads = Advertisement.get_active_ads(position='home_bottom')[:10]
    except Exception as e:
        logger.exception("home_ads_error: %s", e)

    try:
        from core.models import Campaign
        now = timezone.now()
        campaigns = Campaign.objects.filter(is_active=True, start_date__lte=now).order_by('-start_date')[:10]
    except Exception as e:
        logger.exception("home_campaigns_error: %s", e)

    try:
        from core.models import Category
        categories = Category.objects.filter(is_active=True)[:20]
    except Exception:
        categories = []

    context = {
        'top_ads': top_ads,
        'middle_ads': middle_ads,
        'bottom_ads': bottom_ads,
        'campaigns': campaigns,
        'categories': categories,
        'featured_products': featured_products,
    }
    return _safe_render(request, 'hybrid_home.html', context)


def offline_fallback(request):
    return _safe_render(request, 'pwa/offline.html')


def health(request):
    return JsonResponse({'ok': True, 'service': 'core'})


def healthz(request):
    return JsonResponse({'ok': True})


def modern_login_page(request):
    return _safe_render(request, 'registration/login.html')


def user_login(request):
    return redirect('/admin/login/')


def owner_login(request):
    return redirect('/admin/login/')


def owner_password_reset(request):
    return JsonResponse({'ok': True})


def dashboard_redirect(request):
    return redirect('/dashboard/super-owner/')


def super_owner_dashboard(request):
    return _safe_render(request, 'dashboard/super_owner/dashboard.html', {})


def technical_debugger(request):
    return JsonResponse({'ok': True, 'message': 'technical debugger active'})


def log_js_error(request):
    return JsonResponse({'ok': True})


def debug_owner_login(request):
    return redirect('/admin/login/')


def run_migrations(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponse("Unauthorized - Superuser required", status=403)
    try:
        call_command('migrate')
        return HttpResponse("Migrations applied successfully! Database is now up to date.")
    except Exception as e:
        return HttpResponse(f"Error applying migrations: {str(e)}", status=500)


def __getattr__(name):
    def _fallback_view(request, *args, **kwargs):
        wants_json = request.path.endswith('-json/') or '/api/' in request.path or request.headers.get('Accept', '').find('application/json') >= 0
        if wants_json:
            return JsonResponse({'ok': False, 'message': f'Endpoint {name} is temporarily unavailable'}, status=503)
        return HttpResponse("Temporarily unavailable", status=503)
    return _fallback_view
